from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np

from .filters import simulate_fir, simulate_sos
from .fixed import FixedPointConfig, quantize


@dataclass(frozen=True)
class ExportArtifact:
    source: str
    header: str
    test_vectors: str
    metadata: dict[str, Any]

    @property
    def cpp_source(self) -> str:
        """The generated C source is also valid C++17 source."""
        return self.source


def _array(name: str, values: np.ndarray, ctype: str = "int16_t") -> str:
    flat = ", ".join(str(int(value)) for value in values.reshape(-1))
    return f"static const {ctype} {name}[{values.size}] = {{{flat}}};"


def export_filter(
    coefficients: np.ndarray,
    *,
    config: FixedPointConfig | None = None,
    sample_rate: float,
    frame_size: int,
    channels: int = 1,
    name: str = "filter",
    kind: str = "fir",
    vectors: np.ndarray | None = None,
    backend: str = "portable",
    language: str = "c",
) -> ExportArtifact:
    """Generate portable C plus CMSIS/ESP-DSP compatible coefficient arrays.

    The emitted MAC and memory values are estimates, not cycle-accurate claims.
    """
    config = config or FixedPointConfig()
    if sample_rate <= 0 or frame_size < 1 or channels < 1:
        raise ValueError("sample_rate, frame_size and channels must be positive")
    if backend not in {"portable", "cmsis", "esp-dsp"}:
        raise ValueError("backend must be portable, cmsis or esp-dsp")
    if language not in {"c", "cpp"}:
        raise ValueError("language must be c or cpp")
    values, clipped = quantize(np.asarray(coefficients, dtype=float), config)
    payload = values.astype("<i8").tobytes()
    checksum = hashlib.sha256(payload).hexdigest()
    timestamp = datetime.now(UTC).isoformat()
    metadata: dict[str, Any] = {
        "generator_version": "1.0",
        "generated_at": timestamp,
        "checksum_sha256": checksum,
        "format": config.format.value,
        "rounding": config.rounding.value,
        "overflow": config.overflow.value,
        "sample_rate": sample_rate,
        "frame_size": frame_size,
        "channels": channels,
        "kind": kind,
        "backend": backend,
        "language": language,
        "coefficient_count": int(values.size),
        "coefficient_memory_bytes": int(values.size * config.format.storage_bits // 8),
        "mac_estimate_per_frame": int(frame_size * values.size),
        "performance_note": "MAC and memory figures are estimates; measure on the target.",
        "clipped_coefficients": clipped,
    }
    ctype = {"q7": "int8_t", "q15": "int16_t", "q31": "int32_t"}[config.format.value]
    guard = "".join(char if char.isalnum() else "_" for char in name.upper())
    metadata_json = json.dumps(metadata, sort_keys=True)
    header = f"""/* SignalProcessingToolkit embedded export v1.0
 * SHA-256: {checksum}
 * Metadata: {metadata_json}
 */
#ifndef SPT_{guard}_H
#define SPT_{guard}_H
#include <stdint.h>
#define SPT_SAMPLE_RATE {sample_rate!r}f
#define SPT_FRAME_SIZE {frame_size}
#define SPT_CHANNELS {channels}
{_array(name + "_coefficients", values, ctype)}
#endif
"""
    if kind.lower() == "sos":
        if values.size % 6:
            raise ValueError("SOS coefficients must contain six values per section")
        sections = values.reshape(-1, 6)
        section_lines = "\n".join(
            _array(f"{name}_section_{index}", section, ctype)
            for index, section in enumerate(sections)
        )
        source = (
            f"""/* Generated SOS implementation; benchmark on target hardware. */
#include <stdint.h>
#include <stddef.h>
#include \"{name}.h\"
{section_lines}
static int64_t {name}_state[{len(sections)}][2] = {{0}};
void {name}_process(const {ctype} *input, {ctype} *output, size_t count) {{
    for (size_t n = 0; n < count; ++n) {{
        int64_t value = input[n];
"""
            + "".join(
                f"""        {{
            const int64_t *c = {name}_section_{index};
            int64_t y = (c[0] * value + {name}_state[{index}][0]) / {config.format.scale};
            {name}_state[{index}][0] = c[1] * value - c[3] * y + {name}_state[{index}][1];
            {name}_state[{index}][1] = c[2] * value - c[4] * y;
            value = y;
        }}
"""
                for index in range(len(sections))
            )
            + f"""        output[n] = ({ctype})value;
    }}
}}
"""
        )
    else:
        source = f"""/* Generated portable implementation; benchmark on target hardware. */
#include <stdint.h>
#include <stddef.h>
#include \"{name}.h\"
void {name}_process(const {ctype} *input, {ctype} *output, size_t count) {{
    for (size_t n = 0; n < count; ++n) {{
        int64_t acc = 0;
        for (size_t k = 0; k < {values.size} && k <= n; ++k)
            acc += (int64_t)input[n-k] * {name}_coefficients[k];
        acc = (acc + ({config.format.scale} / 2)) / {config.format.scale};
        if (acc > {config.format.limits[1]}) acc = {config.format.limits[1]};
        if (acc < {config.format.limits[0]}) acc = {config.format.limits[0]};
        output[n] = ({ctype})acc;
    }}
}}
"""
    if vectors is None:
        vectors = np.zeros(min(frame_size, 16), dtype=float)
    vector_values = np.asarray(vectors, dtype=float).reshape(-1)
    vector_q, _ = quantize(vector_values, config)
    if kind.lower() == "fir":
        expected = simulate_fir(vector_values, np.asarray(coefficients), config).output
    elif kind.lower() == "sos":
        expected = simulate_sos(vector_values, np.asarray(coefficients), config).output
    else:
        raise ValueError("kind must be 'fir' or 'sos'")
    test_vectors = json.dumps(
        {"input": vector_q.tolist(), "expected": expected.tolist(), "metadata": metadata}, indent=2
    )
    return ExportArtifact(source, header, test_vectors, metadata)
