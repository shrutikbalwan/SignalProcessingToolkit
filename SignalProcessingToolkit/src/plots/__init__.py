import logging

logger = logging.getLogger(__name__)

try:
    from src.plots.base import BasePlotWidget
except ImportError:
    logger.warning("Plot widgets unavailable (pyqtgraph not installed)")
    BasePlotWidget = None  # type: ignore

try:
    from src.plots.frequency_domain import FrequencyDomainPlot
    from src.plots.power_spectrum import PowerSpectrumPlot
    from src.plots.spectrogram import SpectrogramPlot
    from src.plots.time_domain import TimeDomainPlot
except ImportError:
    TimeDomainPlot = None  # type: ignore
    FrequencyDomainPlot = None  # type: ignore
    SpectrogramPlot = None  # type: ignore
    PowerSpectrumPlot = None  # type: ignore

from src.plots.themes import DARK_THEME, LIGHT_THEME, PlotTheme  # type: ignore  # noqa: E402

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
