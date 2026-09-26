"""Optional serial hardware acquisition without import-time pyserial dependency."""

from signal_processing_toolkit.hardware.protocol import (
    BINARY_MAGIC,
    BINARY_VERSION,
    BinaryPacketParser,
    CSVPacketParser,
    SensorPacket,
    encode_binary_packet,
    encode_csv_packet,
)
from signal_processing_toolkit.hardware.serial_source import (
    PySerialBackend,
    SerialBackend,
    SerialPortInfo,
    SerialSensorSource,
    SerialSourceConfig,
    SerialSourceMetrics,
    enumerate_serial_ports,
)

__all__ = [
    "BINARY_MAGIC",
    "BINARY_VERSION",
    "BinaryPacketParser",
    "CSVPacketParser",
    "PySerialBackend",
    "SensorPacket",
    "SerialBackend",
    "SerialPortInfo",
    "SerialSensorSource",
    "SerialSourceConfig",
    "SerialSourceMetrics",
    "encode_binary_packet",
    "encode_csv_packet",
    "enumerate_serial_ports",
]
