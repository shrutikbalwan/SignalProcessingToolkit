# Signal Processing Toolkit - Architecture Document

## 1. Project Overview

**Signal Processing Toolkit** is a professional desktop application for signal generation, analysis, processing, filtering, and visualization. Built with clean architecture principles, modular design, and scalable patterns.

---

## 2. Complete Project Architecture

### High-Level Architecture Pattern: **Clean Architecture + MVC**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PRESENTATION LAYER (UI)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Views     │  │ Controllers │  │  ViewModels │  │  Dialogs    │       │
│  │  (PyQt6)    │◄─┤  (MVC)      │◄─┤  (State)    │  │  (Modals)   │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
└─────────┼────────────────┼────────────────┼────────────────┼──────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  Use Cases  │  │  Services   │  │  DTOs       │  │  Events     │       │
│  │  (Interactors)           │  │  (Business) │  │  (Data Xfer)│  │  (Pub/Sub)│       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
└─────────┼────────────────┼────────────────┼────────────────┼──────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DOMAIN LAYER                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  Entities   │  │  Repositories│ │  Domain     │  │  Exceptions │       │
│  │  (Models)   │  │  (Interfaces)│ │  Services   │  │             │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
└─────────┼────────────────┼────────────────┼────────────────┼──────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INFRASTRUCTURE LAYER                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  DSP Engine │  │  File I/O   │  │  Audio      │  │  Image      │       │
│  │  (NumPy/    │  │  (CSV/WAV/  │  │  Engine     │  │  Engine     │       │
│  │   SciPy)    │  │   Excel)    │  │  (PyAudio)  │  │  (OpenCV)   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Folder Structure

```
SignalProcessingToolkit/
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── LICENSE
├── .gitignore
├── pyproject.toml
├── ARCHITECTURE.md
├── CHANGELOG.md
├── assets/
│   ├── icons/
│   │   ├── app.ico
│   │   ├── toolbar/
│   │   ├── sidebar/
│   │   └── status/
│   ├── images/
│   │   ├── logos/
│   │   └── backgrounds/
│   ├── audio/
│   │   └── samples/
│   ├── sample_data/
│   │   ├── signals/
│   │   ├── images/
│   │   └── audio/
│   └── themes/
│       ├── dark.qss
│       ├── light.qss
│       └── colors.json
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── user_guide/
│   └── developer_guide/
├── screenshots/
├── tests/
│   ├── unit/
│   │   ├── test_dsp/
│   │   ├── test_filters/
│   │   ├── test_audio/
│   │   └── test_models/
│   ├── integration/
│   ├── fixtures/
│   └── conftest.py
├── src/
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration management
│   ├── app.py                  # Application bootstrap
│   ├── __init__.py
│   │
│   ├── core/                   # Core application framework
│   │   ├── __init__.py
│   │   ├── application.py      # Main application class
│   │   ├── events.py           # Event bus / pub-sub
│   │   ├── settings.py         # Settings management
│   │   ├── logging_config.py   # Logging configuration
│   │   ├── exceptions.py       # Custom exceptions
│   │   ├── constants.py        # Application constants
│   │   └── plugins/
│   │       ├── __init__.py
│   │       ├── manager.py
│   │       └── interface.py
│   │
│   ├── models/                 # Domain models (Entities)
│   │   ├── __init__.py
│   │   ├── signal.py           # Signal entity
│   │   ├── audio.py            # Audio entity
│   │   ├── image.py            # Image entity
│   │   ├── filter_design.py    # Filter design entity
│   │   ├── fft_result.py       # FFT analysis result
│   │   ├── project.py          # Project entity
│   │   └── enums.py            # Domain enums
│   │
│   ├── repositories/           # Repository interfaces & implementations
│   │   ├── __init__.py
│   │   ├── interfaces/
│   │   │   ├── __init__.py
│   │   │   ├── signal_repository.py
│   │   │   ├── audio_repository.py
│   │   │   ├── image_repository.py
│   │   │   └── project_repository.py
│   │   └── implementations/
│   │       ├── __init__.py
│   │       ├── file_signal_repository.py
│   │       ├── file_audio_repository.py
│   │       ├── file_image_repository.py
│   │       └── file_project_repository.py
│   │
│   ├── services/               # Domain services (Business logic)
│   │   ├── __init__.py
│   │   ├── signal_service.py
│   │   ├── audio_service.py
│   │   ├── image_service.py
│   │   ├── filter_service.py
│   │   ├── fft_service.py
│   │   ├── sampling_service.py
│   │   ├── convolution_service.py
│   │   ├── correlation_service.py
│   │   ├── window_service.py
│   │   └── noise_service.py
│   │
│   ├── use_cases/              # Application use cases (Interactors)
│   │   ├── __init__.py
│   │   ├── signal/
│   │   │   ├── __init__.py
│   │   │   ├── generate_signal.py
│   │   │   ├── process_signal.py
│   │   │   ├── analyze_signal.py
│   │   │   └── export_signal.py
│   │   ├── audio/
│   │   │   ├── __init__.py
│   │   │   ├── load_audio.py
│   │   │   ├── play_audio.py
│   │   │   ├── process_audio.py
│   │   │   └── export_audio.py
│   │   ├── image/
│   │   │   ├── __init__.py
│   │   │   ├── load_image.py
│   │   │   ├── process_image.py
│   │   │   └── export_image.py
│   │   └── project/
│   │       ├── __init__.py
│   │       ├── new_project.py
│   │       ├── save_project.py
│   │       └── load_project.py
│   │
│   ├── dto/                    # Data Transfer Objects
│   │   ├── __init__.py
│   │   ├── signal_dto.py
│   │   ├── audio_dto.py
│   │   ├── image_dto.py
│   │   ├── filter_dto.py
│   │   ├── fft_dto.py
│   │   └── export_dto.py
│   │
│   ├── dsp/                    # Digital Signal Processing Engine
│   │   ├── __init__.py
│   │   ├── generators/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── sine.py
│   │   │   ├── cosine.py
│   │   │   ├── square.py
│   │   │   ├── triangle.py
│   │   │   ├── sawtooth.py
│   │   │   ├── pulse.py
│   │   │   ├── chirp.py
│   │   │   ├── gaussian.py
│   │   │   ├── noise.py
│   │   │   └── dc.py
│   │   ├── operations/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── arithmetic.py
│   │   │   ├── scaling.py
│   │   │   ├── time_shift.py
│   │   │   ├── time_reversal.py
│   │   │   ├── clipping.py
│   │   │   ├── normalization.py
│   │   │   ├── rectification.py
│   │   │   └── mixing.py
│   │   ├── sampling/
│   │   │   ├── __init__.py
│   │   │   ├── sampler.py
│   │   │   ├── reconstruction.py
│   │   │   └── aliasing.py
│   │   ├── convolution/
│   │   │   ├── __init__.py
│   │   │   ├── linear.py
│   │   │   └── circular.py
│   │   ├── correlation/
│   │   │   ├── __init__.py
│   │   │   ├── auto_correlation.py
│   │   │   └── cross_correlation.py
│   │   ├── fft/
│   │   │   ├── __init__.py
│   │   │   ├── fft_engine.py
│   │   │   ├── spectrum.py
│   │   │   ├── peak_detection.py
│   │   │   └── inverse_fft.py
│   │   ├── windows/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── rectangular.py
│   │   │   ├── hamming.py
│   │   │   ├── hanning.py
│   │   │   ├── blackman.py
│   │   │   ├── bartlett.py
│   │   │   └── kaiser.py
│   │   ├── filters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── fir/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── lowpass.py
│   │   │   │   ├── highpass.py
│   │   │   │   ├── bandpass.py
│   │   │   │   └── bandstop.py
│   │   │   ├── iir/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── butterworth.py
│   │   │   │   ├── chebyshev1.py
│   │   │   │   ├── chebyshev2.py
│   │   │   │   └── elliptic.py
│   │   │   └── design.py
│   │   └── noise/
│   │       ├── __init__.py
│   │       ├── generators.py
│   │       ├── removers.py
│   │       └── metrics.py
│   │
│   ├── audio/                  # Audio processing module
│   │   ├── __init__.py
│   │   ├── engine.py           # Audio playback engine
│   │   ├── equalizer.py        # Graphic equalizer
│   │   ├── effects.py          # Audio effects
│   │   ├── analyzer.py         # Real-time audio analyzer
│   │   └── formats.py          # Audio format handlers
│   │
│   ├── image/                  # Image signal processing
│   │   ├── __init__.py
│   │   ├── loader.py           # Image loading
│   │   ├── histogram.py        # Histogram operations
│   │   ├── fft2d.py            # 2D FFT
│   │   ├── filters.py          # Image filters
│   │   ├── edge_detection.py   # Edge detection
│   │   ├── morphology.py       # Morphological operations
│   │   └── enhancement.py      # Image enhancement
│   │
│   ├── plots/                  # Visualization components
│   │   ├── __init__.py
│   │   ├── base.py             # Base plot widget
│   │   ├── time_domain.py      # Time domain plot
│   │   ├── frequency_domain.py # Frequency domain plot
│   │   ├── spectrogram.py      # Spectrogram plot
│   │   ├── power_spectrum.py   # Power spectrum plot
│   │   ├── impulse_response.py # Impulse response plot
│   │   ├── phase_response.py   # Phase response plot
│   │   ├── synchronized.py     # Synchronized multi-plot
│   │   ├── cursors.py          # Cursor/measurement tools
│   │   ├── exporters.py        # Plot export (PNG, PDF)
│   │   └── themes.py           # Plot themes
│   │
│   ├── ui/                     # User Interface (PyQt6)
│   │   ├── __init__.py
│   │   ├── main_window.py      # Main window
│   │   ├── views/              # MVC Views
│   │   │   ├── __init__.py
│   │   │   ├── dashboard_view.py
│   │   │   ├── signal_generator_view.py
│   │   │   ├── signal_operations_view.py
│   │   │   ├── fft_view.py
│   │   │   ├── filters_view.py
│   │   │   ├── sampling_view.py
│   │   │   ├── audio_view.py
│   │   │   ├── image_view.py
│   │   │   └── settings_view.py
│   │   ├── controllers/        # MVC Controllers
│   │   │   ├── __init__.py
│   │   │   ├── base_controller.py
│   │   │   ├── signal_generator_controller.py
│   │   │   ├── signal_operations_controller.py
│   │   │   ├── fft_controller.py
│   │   │   ├── filters_controller.py
│   │   │   ├── sampling_controller.py
│   │   │   ├── audio_controller.py
│   │   │   ├── image_controller.py
│   │   │   └── main_controller.py
│   │   ├── viewmodels/         # ViewModels (MVVM pattern)
│   │   │   ├── __init__.py
│   │   │   ├── base_viewmodel.py
│   │   │   ├── signal_generator_vm.py
│   │   │   ├── fft_vm.py
│   │   │   ├── filters_vm.py
│   │   │   └── audio_vm.py
│   │   ├── components/         # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   ├── sidebar.py
│   │   │   ├── toolbar.py
│   │   │   ├── statusbar.py
│   │   │   ├── parameter_panel.py
│   │   │   ├── plot_area.py
│   │   │   ├── dialogs/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── export_dialog.py
│   │   │   │   ├── filter_design_dialog.py
│   │   │   │   ├── settings_dialog.py
│   │   │   │   └── about_dialog.py
│   │   │   ├── widgets/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── signal_plot_widget.py
│   │   │   │   ├── parameter_slider.py
│   │   │   │   ├── parameter_spinbox.py
│   │   │   │   ├── waveform_selector.py
│   │   │   │   └── theme_switcher.py
│   │   │   └── cards/
│   │   │       ├── __init__.py
│   │   │       ├── metric_card.py
│   │   │       ├── signal_card.py
│   │   │       └── plot_card.py
│   │   ├── styles/             # QSS Stylesheets
│   │   │   ├── __init__.py
│   │   │   ├── dark_theme.py
│   │   │   ├── light_theme.py
│   │   │   ├── components.qss
│   │   │   └── animations.qss
│   │   └── resources/          # Qt Resources
│   │       ├── __init__.py
│   │       ├── icons.qrc
│   │       └── resources_rc.py
│   │
│   ├── utils/                  # Utility functions
│   │   ├── __init__.py
│   │   ├── math_utils.py
│   │   ├── file_utils.py
│   │   ├── validation.py
│   │   ├── formatters.py
│   │   ├── decorators.py
│   │   └── helpers.py
│   │
│   └── resources/              # Application resources
│       ├── __init__.py
│       ├── default_project.json
│       ├── default_settings.json
│       └── sample_signals/
```

---

## 4. MVC Architecture Detail

### Model Layer (Domain Models)
```python
# Entities - Pure data classes with business logic
Signal          # time_data, frequency, sampling_rate, metadata
AudioSignal     # inherits Signal + channels, bit_depth, format
ImageSignal     # pixel_data, width, height, color_space
FilterDesign    # type, order, cutoff, ripple, coefficients
FFTResult       # frequencies, magnitude, phase, power, peaks
Project         # name, signals, settings, history
```

### View Layer (PyQt6 Widgets)
```python
# Views - Pure presentation, no business logic
SignalGeneratorView    # Waveform selection, parameter inputs, preview plot
FFTView                # Spectrum plot, cursor readouts, peak markers
FilterView             # Filter designer, response plots, pole-zero plot
AudioView              # Waveform, spectrogram, playback controls
ImageView              # Image display, histogram, frequency domain
```

### Controller Layer (MVC Controllers)
```python
# Controllers - Handle user input, coordinate Model↔View
SignalGeneratorController
    - on_waveform_changed(type)
    - on_parameter_changed(param, value)
    - on_generate_clicked()
    - on_export_clicked()

FFTController
    - on_signal_loaded(signal)
    - on_window_changed(window_type)
    - on_cursor_moved(frequency)
    - on_peak_detected(peaks)
```

### ViewModel Layer (State Management)
```python
# ViewModels - UI State, data binding, commands
SignalGeneratorViewModel
    - waveform_type: Observable[str]
    - amplitude: Observable[float]
    - frequency: Observable[float]
    - generated_signal: Observable[Signal]
    - generate_command: Command
    - export_command: Command
```

---

## 5. Module Interaction Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         MODULE INTERACTIONS                                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                 │
│  │   Signal    │────►│  Signal     │────►│   FFT       │                 │
│  │ Generator   │     │ Operations  │     │  Analysis   │                 │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                 │
│         │                   │                   │                         │
│         ▼                   ▼                   ▼                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                 │
│  │  Sampling   │     │ Convolution │     │ Correlation │                 │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                 │
│         │                   │                   │                         │
│         ▼                   ▼                   ▼                         │
│  ┌─────────────────────────────────────────────────────────────┐         │
│  │                    FILTER MODULE                            │         │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐   │         │
│  │  │   FIR   │  │   IIR   │  │ Window  │  │  Response   │   │         │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └──────┬──────┘   │         │
│  └───────┼────────────┼────────────┼────────────┼───────────┘         │
│          │            │            │            │                      │
│          ▼            ▼            ▼            ▼                      │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │                  NOISE PROCESSING                           │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │      │
│  │  │ Generate │  │  Remove  │  │  Metrics │  │  Adaptive  │  │      │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │      │
│  └──────────────────────────────┬──────────────────────────────┘      │
│                                 │                                     │
│         ┌───────────────────────┼───────────────────────┐             │
│         ▼                       ▼                       ▼             │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────┐     │
│  │   AUDIO     │         │   IMAGE     │         │   EXPORT    │     │
│  │  MODULE     │         │  MODULE     │         │  MODULE     │     │
│  └─────────────┘         └─────────────┘         └─────────────┘     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. File Responsibilities

| File/Module | Responsibility | Layer |
|-------------|---------------|-------|
| `main.py` | Application entry, QApplication setup | Presentation |
| `app.py` | Application bootstrap, DI container | Application |
| `config.py` | Configuration management (YAML/JSON) | Core |
| `core/application.py` | Main application lifecycle | Core |
| `core/events.py` | Event bus for decoupled communication | Core |
| `models/signal.py` | Signal entity with validation | Domain |
| `models/audio.py` | Audio-specific signal entity | Domain |
| `models/image.py` | Image signal entity | Domain |
| `models/filter_design.py` | Filter specification entity | Domain |
| `models/fft_result.py` | FFT analysis result entity | Domain |
| `repositories/interfaces/*` | Repository contracts (abstractions) | Domain |
| `repositories/implementations/*` | File-based persistence | Infrastructure |
| `services/signal_service.py` | Signal processing orchestration | Domain |
| `services/filter_service.py` | Filter design & application | Domain |
| `services/fft_service.py` | FFT computation & analysis | Domain |
| `use_cases/signal/*` | Signal-related use cases | Application |
| `use_cases/audio/*` | Audio-related use cases | Application |
| `use_cases/image/*` | Image-related use cases | Application |
| `dsp/generators/*` | Signal waveform generation | Infrastructure |
| `dsp/operations/*` | Signal arithmetic & transforms | Infrastructure |
| `dsp/sampling/*` | Sampling theory implementations | Infrastructure |
| `dsp/convolution/*` | Convolution algorithms | Infrastructure |
| `dsp/correlation/*` | Correlation algorithms | Infrastructure |
| `dsp/fft/*` | FFT implementation & analysis | Infrastructure |
| `dsp/windows/*` | Window function implementations | Infrastructure |
| `dsp/filters/fir/*` | FIR filter designs | Infrastructure |
| `dsp/filters/iir/*` | IIR filter designs | Infrastructure |
| `dsp/filters/design.py` | Filter design factory | Infrastructure |
| `dsp/noise/*` | Noise generation & removal | Infrastructure |
| `audio/engine.py` | Audio playback/recording | Infrastructure |
| `audio/equalizer.py` | Real-time equalizer | Infrastructure |
| `image/*` | Image processing algorithms | Infrastructure |
| `plots/*` | Visualization components | Presentation |
| `ui/main_window.py` | Main window container | Presentation |
| `ui/views/*` | Module-specific views | Presentation |
| `ui/controllers/*` | Module-specific controllers | Presentation |
| `ui/viewmodels/*` | UI state management | Presentation |
| `ui/components/*` | Reusable UI widgets | Presentation |
| `ui/styles/*` | Theming & styling | Presentation |

---

## 7. Dependency Diagram

```
DEPENDENCY RULE: Inner layers know nothing of outer layers
                    Dependencies point INWARD

┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION (UI)                        │
│  ui/main_window.py                                          │
│  ui/views/*                                                 │
│  ui/controllers/*                                           │
│  ui/viewmodels/*                                            │
│  ui/components/*                                            │
│  plots/*                                                    │
│                                                             │
│  DEPENDS ON: Use Cases, DTOs, Models, Core                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION (Use Cases)                  │
│  use_cases/signal/*                                         │
│  use_cases/audio/*                                          │
│  use_cases/image/*                                          │
│  use_cases/project/*                                        │
│  dto/*                                                      │
│                                                             │
│  DEPENDS ON: Domain Services, Repositories, Models, Core   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                       DOMAIN                                │
│  models/* (Entities)                                        │
│  repositories/interfaces/* (Contracts)                      │
│  services/* (Domain Services)                               │
│                                                             │
│  DEPENDS ON: Core, Python Stdlib                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE                          │
│  dsp/* (DSP Engine)                                         │
│  audio/* (Audio Engine)                                     │
│  image/* (Image Engine)                                     │
│  repositories/implementations/*                             │
│  core/plugins/*                                             │
│                                                             │
│  DEPENDS ON: NumPy, SciPy, PyAudio, OpenCV, PyQt6          │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Class Structure (Key Classes)

### Signal Entity
```python
@dataclass
class Signal:
    """Domain entity representing a digital signal."""
    time_data: np.ndarray          # Time domain samples
    sampling_rate: float           # Hz
    frequency: float = 0.0         # Fundamental frequency (Hz)
    amplitude: float = 1.0         # Peak amplitude
    phase: float = 0.0             # Phase offset (radians)
    metadata: SignalMetadata = field(default_factory=SignalMetadata)
    
    # Computed properties
    @property
    def duration(self) -> float: ...
    @property
    def nyquist_frequency(self) -> float: ...
    @property
    def rms(self) -> float: ...
    @property
    def peak_to_peak(self) -> float: ...
    
    # Domain methods
    def apply_window(self, window: WindowFunction) -> 'Signal': ...
    def resample(self, new_rate: float) -> 'Signal': ...
    def add_noise(self, noise_level: float) -> 'Signal': ...
```

### Filter Design Entity
```python
@dataclass
class FilterDesign:
    """Domain entity for filter specification."""
    filter_type: FilterType        # LOWPASS, HIGHPASS, BANDPASS, BANDSTOP
    response_type: ResponseType    # FIR, IIR
    design_method: DesignMethod    # BUTTERWORTH, CHEBYSHEV1, etc.
    order: int
    cutoff_frequency: float | Tuple[float, float]  # Hz
    sampling_rate: float
    passband_ripple: float = 1.0   # dB
    stopband_attenuation: float = 40.0  # dB
    
    # Computed
    @property
    def coefficients(self) -> FilterCoefficients: ...
    @property
    def frequency_response(self) -> FrequencyResponse: ...
    @property
    def pole_zero_map(self) -> PoleZeroMap: ...
    def is_stable(self) -> bool: ...
```

### Service Interfaces
```python
class ISignalRepository(Protocol):
    """Repository contract for signal persistence."""
    def save(self, signal: Signal, path: Path) -> None: ...
    def load(self, path: Path) -> Signal: ...
    def export_csv(self, signal: Signal, path: Path) -> None: ...
    def export_wav(self, signal: Signal, path: Path) -> None: ...

class ISignalService(Protocol):
    """Domain service for signal processing operations."""
    def add(self, s1: Signal, s2: Signal) -> Signal: ...
    def multiply(self, s1: Signal, s2: Signal) -> Signal: ...
    def convolve(self, signal: Signal, impulse: Signal) -> Signal: ...
    def correlate(self, s1: Signal, s2: Signal) -> CorrelationResult: ...
    def apply_filter(self, signal: Signal, filter_design: FilterDesign) -> Signal: ...
```

---

## 9. Naming Conventions

### Python Code
| Element | Convention | Example |
|---------|------------|---------|
| Modules | `snake_case` | `signal_generator.py` |
| Classes | `PascalCase` | `SignalGenerator` |
| Functions/Methods | `snake_case` | `generate_sine_wave()` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_SAMPLING_RATE` |
| Private methods | `_snake_case` | `_compute_fft()` |
| Properties | `snake_case` | `sampling_rate` |
| Type aliases | `PascalCase` | `SignalArray = np.ndarray` |
| Enums | `PascalCase` | `class WaveformType(Enum)` |

### UI Components
| Element | Convention | Example |
|---------|------------|---------|
| Qt Widgets | `PascalCase` + `Widget` | `SignalPlotWidget` |
| Views | `PascalCase` + `View` | `SignalGeneratorView` |
| Controllers | `PascalCase` + `Controller` | `FFTController` |
| ViewModels | `PascalCase` + `ViewModel` | `AudioViewModel` |
| Dialogs | `PascalCase` + `Dialog` | `ExportDialog` |

### Files & Directories
| Element | Convention |
|---------|------------|
| Directories | `snake_case` (lowercase) |
| Test files | `test_<module>.py` |
| Fixtures | `fixtures/<name>.json` |
| Resources | `resources/<category>/<name>.<ext>` |

---

## 10. Coding Standards

### Type Hints (Mandatory)
```python
# All public functions MUST have type hints
def generate_sine_wave(
    frequency: float,
    sampling_rate: float,
    duration: float,
    amplitude: float = 1.0,
    phase: float = 0.0
) -> Signal:
    ...

# Use TypedDict for complex dict structures
class SignalParams(TypedDict):
    frequency: float
    amplitude: float
    phase: float
```

### Docstrings (Google Style)
```python
def design_fir_filter(
    filter_type: FilterType,
    cutoff: float | Tuple[float, float],
    sampling_rate: float,
    order: int,
    window: WindowType = WindowType.HAMMING
) -> FilterCoefficients:
    """Design an FIR filter using window method.
    
    Args:
        filter_type: Type of filter (LOWPASS, HIGHPASS, etc.)
        cutoff: Cutoff frequency in Hz. Tuple for bandpass/bandstop.
        sampling_rate: Sampling frequency in Hz.
        order: Filter order (must be even for bandpass/bandstop).
        window: Window function to apply.
    
    Returns:
        FilterCoefficients containing numerator (b) and denominator (a).
    
    Raises:
        ValueError: If order is invalid for filter type.
        DesignError: If filter design fails.
    
    Example:
        >>> coeffs = design_fir_filter(FilterType.LOWPASS, 1000, 8000, 50)
        >>> signal = apply_filter(input_signal, coeffs)
    """
```

### Error Handling
```python
# Custom exceptions hierarchy
class DSPError(Exception): pass
class FilterDesignError(DSPError): pass
class SignalProcessingError(DSPError): pass
class FileFormatError(DSPError): pass

# Use Result pattern for fallible operations
@dataclass
class Result(Generic[T]):
    success: bool
    value: T | None = None
    error: Exception | None = None
    
    @classmethod
    def ok(cls, value: T) -> 'Result[T]': ...
    @classmethod
    def err(cls, error: Exception) -> 'Result[T]': ...
```

### Logging
```python
# Structured logging with context
logger = logging.getLogger(__name__)

def process_signal(signal: Signal, params: ProcessingParams) -> Signal:
    logger.info(
        "Processing signal",
        extra={
            "signal_id": signal.metadata.id,
            "duration": signal.duration,
            "sampling_rate": signal.sampling_rate,
            "operation": params.operation.value
        }
    )
    ...
```

### Configuration
```python
# config.py - Pydantic settings
class AppSettings(BaseSettings):
    # General
    app_name: str = "Signal Processing Toolkit"
    version: str = "1.0.0"
    debug: bool = False
    
    # UI
    theme: Theme = Theme.DARK
    language: str = "en"
    auto_save_interval: int = 300  # seconds
    
    # DSP
    default_sampling_rate: float = 44100.0
    default_duration: float = 1.0
    fft_size: int = 4096
    
    # Paths
    data_dir: Path = Path.home() / ".spt" / "data"
    export_dir: Path = Path.home() / ".spt" / "exports"
    plugins_dir: Path = Path.home() / ".spt" / "plugins"
    
    class Config:
        env_file = ".env"
        env_prefix = "SPT_"
```

---

## 11. Development Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Project structure & configuration
- [ ] Core framework (events, settings, logging, DI)
- [ ] Domain models (Signal, Audio, Image, FilterDesign)
- [ ] Repository interfaces & file implementations
- [ ] Basic UI framework (MainWindow, Sidebar, Theme system)
- [ ] Plotting infrastructure (PyQtGraph + Matplotlib integration)

### Phase 2: Signal Generator Module (Week 2-3)
- [ ] DSP Generators (all 10 waveform types)
- [ ] Signal Generator View & Controller
- [ ] Real-time preview plot
- [ ] Parameter validation & binding
- [ ] Export generated signals

### Phase 3: Signal Operations (Week 3-4)
- [ ] Arithmetic operations (add, subtract, multiply, scale)
- [ ] Time operations (shift, reverse, clip)
- [ ] Signal processing (normalize, rectify, mix)
- [ ] Operations View with multi-signal support
- [ ] Undo/Redo framework

### Phase 4: Sampling Module (Week 4)
- [ ] Sampling/Reconstruction algorithms
- [ ] Aliasing demonstration
- [ ] Interactive sampling rate slider
- [ ] Visual comparison plots

### Phase 5: Convolution & Correlation (Week 5)
- [ ] Linear & Circular convolution
- [ ] Auto & Cross correlation
- [ ] Impulse response visualization
- [ ] Lag detection & display

### Phase 6: FFT Analysis (Week 5-6)
- [ ] FFT/IFFT implementation
- [ ] Spectrum types (Magnitude, Power, Phase)
- [ ] Peak detection & dominant frequency
- [ ] Interactive zoom, cursors, measurements
- [ ] Spectrogram view

### Phase 7: Window Functions (Week 6)
- [ ] All 6 window implementations
- [ ] Side-by-side comparison
- [ ] Frequency response analysis
- [ ] Window selector component

### Phase 8: Digital Filters (Week 6-7)
- [ ] FIR design (4 types × window methods)
- [ ] IIR design (4 types × 4 methods)
- [ ] Filter designer dialog
- [ ] Response plots (Magnitude, Phase, Impulse, Pole-Zero)
- [ ] Real-time filter application

### Phase 9: Noise Processing (Week 7)
- [ ] Noise generators (3 types)
- [ ] Noise removal filters (4 types)
- [ ] SNR/Noise Power calculations
- [ ] Adaptive filter implementation

### Phase 10: Audio Processing (Week 7-8)
- [ ] WAV import/export
- [ ] Playback engine (play/pause/stop/volume)
- [ ] Real-time equalizer (10-band)
- [ ] Audio FFT & spectrogram
- [ ] Noise reduction & filtering

### Phase 11: Image Signal Processing (Week 8)
- [ ] Grayscale image loading
- [ ] Histogram & equalization
- [ ] 2D FFT & frequency filtering
- [ ] Edge detection (Sobel, Canny, Laplacian)
- [ ] Morphological operations
- [ ] Enhancement (sharpen, blur, denoise)

### Phase 12: Export & Reporting (Week 8-9)
- [ ] Graph export (PNG, PDF, SVG)
- [ ] Data export (CSV, Excel)
- [ ] PDF report generation
- [ ] Project save/load

### Phase 13: Polish & Bonus Features (Week 9-10)
- [ ] Dark/Light theme toggle
- [ ] Recent files & autosave
- [ ] Keyboard shortcuts
- [ ] Settings page
- [ ] Plugin architecture
- [ ] Multi-language support (i18n)
- [ ] Live signal monitor
- [ ] Real-time FFT
- [ ] Drag & drop support
- [ ] Comprehensive tests
- [ ] Documentation

### Phase 14: Release Preparation (Week 10)
- [ ] Performance optimization
- [ ] Memory profiling
- [ ] Cross-platform testing
- [ ] Installer creation
- [ ] README & documentation
- [ ] Version tagging

---

## 12. Technology Stack Summary

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Language | Python | 3.12+ | Primary language |
| GUI Framework | PyQt6 | 6.6+ | Desktop UI |
| Real-time Plots | PyQtGraph | 0.13+ | High-performance plots |
| Static Plots | Matplotlib | 3.8+ | Publication-quality plots |
| Numerical | NumPy | 1.26+ | Array computing |
| Scientific | SciPy | 1.11+ | DSP algorithms |
| Audio | PyAudio / sounddevice | 0.2.13+ | Audio I/O |
| Image | OpenCV (cv2) | 4.9+ | Image processing |
| Config | Pydantic | 2.5+ | Settings validation |
| Testing | pytest | 7.4+ | Unit/Integration tests |
| Linting | Ruff | 0.1+ | Fast linting |
| Formatting | Black | 23+ | Code formatting |
| Type Checking | mypy | 1.7+ | Static analysis |
| Packaging | pyproject.toml | - | Modern packaging |

---

## 13. Quality Gates

### Pre-commit Checks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest
        entry: pytest --tb=short
        language: system
        pass_filenames: false
```

### CI Pipeline
```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e ".[dev]"
      - run: ruff check src tests
      - run: black --check src tests
      - run: mypy src
      - run: pytest --cov=src --cov-report=xml
      - run: pytest tests/integration
```

---

*Architecture Document Version: 1.0*  
*Last Updated: 2026*  
*Author: Signal Processing Toolkit Team*