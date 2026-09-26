import logging

logger = logging.getLogger(__name__)

try:
    from signal_processing_toolkit.plots.base import BasePlotWidget
except ImportError:
    logger.warning("Plot widgets unavailable (pyqtgraph not installed)")
    BasePlotWidget = None  # type: ignore

try:
    from signal_processing_toolkit.plots.frequency_domain import FrequencyDomainPlot
    from signal_processing_toolkit.plots.power_spectrum import PowerSpectrumPlot
    from signal_processing_toolkit.plots.spectrogram import SpectrogramPlot
    from signal_processing_toolkit.plots.time_domain import TimeDomainPlot
except ImportError:
    TimeDomainPlot = None  # type: ignore
    FrequencyDomainPlot = None  # type: ignore
    SpectrogramPlot = None  # type: ignore
    PowerSpectrumPlot = None  # type: ignore

from signal_processing_toolkit.plots.themes import (  # type: ignore  # noqa: E402
    DARK_THEME,
    LIGHT_THEME,
    PlotTheme,
)

__all__ = [
    "BasePlotWidget",
    "TimeDomainPlot",
    "FrequencyDomainPlot",
    "SpectrogramPlot",
    "PowerSpectrumPlot",
    "PlotTheme",
    "DARK_THEME",
    "LIGHT_THEME",
]
