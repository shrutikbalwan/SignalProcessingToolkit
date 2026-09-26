# ESP32 sensor protocol example

The toolkit accepts either newline CSV or the version-one binary format documented in
[`docs/api/acquisition.md`](../../docs/api/acquisition.md).

## Accelerometer CSV

The following Arduino-style loop sends one three-axis sample per line. Replace the placeholder
sensor reads with the API for the installed accelerometer.

```cpp
uint32_t sequence = 0;

void setup() {
  Serial.begin(115200);
}

void loop() {
  const float timestamp = micros() * 1.0e-6f;
  const float ax = readAccelerometerX();
  const float ay = readAccelerometerY();
  const float az = readAccelerometerZ();
  Serial.printf("%lu,%.6f,%.6f,%.6f,%.6f\n",
                sequence++, timestamp, ax, ay, az);
  delayMicroseconds(1000);  // nominal 1 kHz
}
```

Configure the host with `channel_names=("accel_x", "accel_y", "accel_z")`, units `m/s^2`, and
`sampling_rate=1000`.

## Microphone CSV

For a single ADC or I2S microphone sample, send `sequence,timestamp,sample`:

```cpp
const int32_t sample = readMicrophoneSample();
Serial.printf("%lu,%.6f,%ld\n", sequence++, micros() * 1.0e-6, sample);
```

High-rate raw microphone streams should use the binary format and group multiple samples in one
packet. Build the packed 23-byte header, append sample-major IEEE-754 float32 values, then append a
little-endian CRC-32 over header and payload. The constants are magic `0x53 0x50 0x54 0x21`
(`SPT!` on the wire) and version `1`. The Python `encode_binary_packet` implementation is the
executable reference for byte-for-byte validation before deploying firmware.
