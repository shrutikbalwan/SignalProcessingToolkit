# ESP32 Predictive Maintenance example

Run the tutorial in `docs/tutorials/esp32_predictive_maintenance.md` to create
healthy and faulty recordings. The recordings are deterministic synthetic
fixtures (seed 7), generated locally under the repository MIT license; no
dataset or model binary is redistributed.

Generate both recordings explicitly with:

```bash
PYTHONPATH=src python examples/esp32_predictive_maintenance/generate_recordings.py
```

The ESP32 packet format is documented in `docs/api/acquisition.md` and includes
magic, version, sequence, timestamp, channel/sample counts, float32 payload and
CRC-32 checksum.
