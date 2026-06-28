# SignalProcessingToolkit
Professional Signal Processing Toolkit built with Python and PyQt6 featuring FFT analysis, digital filters, signal generation, visualization, audio processing, and image processing.
# Signal Processing Toolkit

Professional desktop application for signal generation, analysis, processing, and visualization.

## Features

- **Signal Generation**: Create sine, square, triangle, sawtooth, chirp, noise, and custom waveforms
- **Frequency Analysis**: FFT, spectrograms, power spectral density, cepstrum analysis
- **Digital Filtering**: FIR/IIR filters (Butterworth, Chebyshev, Elliptic) with real-time response visualization
- **Audio Processing**: Record, playback, and process audio with support for WAV, MP3, FLAC, OGG
- **Image Processing**: 2D FFT, convolution, filtering, and morphological operations
- **Visualization**: Interactive plots with pyqtgraph and matplotlib backends
- **Plugin Architecture**: Extensible system for custom signal processors

## Requirements

- Python 3.12+
- PyQt6 6.6+
- NumPy 1.26+
- SciPy 1.11+

## Installation

### From Source

```bash
git clone https://github.com/signal-processing-toolkit/spt.git
cd spt
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
pre-commit install
```

## Quick Start

```bash
# Run the application
python -m signal_processing_toolkit

# Or from source
python src/main.py
```

## Project Structure

```
signal-processing-toolkit/
├── src/
│   ├── signal_processing_toolkit/
│   │   ├── app.py              # Application core
│   │   ├── main.py             # Entry point
│   │   ├── config.py           # Configuration management
│   │   ├── constants.py        # Application constants
│   │   ├── logger.py           # Logging utilities
│   │   ├── core/               # Core infrastructure
│   │   ├── audio/              # Audio processing
│   │   ├── dsp/                # Digital signal processing
│   │   ├── image/              # Image processing
│   │   ├── models/             # Data models
│   │   ├── plots/              # Visualization
│   │   ├── repositories/       # Data persistence
│   │   ├── services/           # Business logic
│   │   ├── ui/                 # User interface
│   │   ├── use_cases/          # Application use cases
│   │   └── utils/              # Utilities
│   └── tests/
├── assets/                     # Icons, images, resources
├── docs/                       # Documentation
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml              # Project configuration
└── LICENSE                     # MIT License
```

## Configuration

The application uses Pydantic Settings for configuration. Create a `.env` file:

```env
SPT_DEBUG=false
SPT_THEME=dark
SPT_DEFAULT_SAMPLING_RATE=44100
SPT_DATA_DIR=~/.spt/data
SPT_EXPORT_DIR=~/.spt/exports
```

## Development

### Code Quality

```bash
# Format code
ruff format .
black .

# Lint
ruff check .

# Type check
mypy src/

# Run tests
pytest

# Run tests with coverage
pytest --cov=signal_processing_toolkit
```

### Building Documentation

```bash
cd docs
make html
```

## Architecture

The application follows Clean Architecture principles:

- **Core**: Domain logic, entities, events, exceptions
- **Use Cases**: Application-specific business rules
- **Interfaces**: UI controllers, presenters
- **Infrastructure**: Data access, external services, platform-specific code

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Support

- Issues: [GitHub Issues](https://github.com/signal-processing-toolkit/spt/issues)
- Documentation: [Read the Docs](https://signal-processing-toolkit.readthedocs.io)
