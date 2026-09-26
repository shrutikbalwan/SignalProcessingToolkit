import time

from signal_processing_toolkit.dashboard.services.acquisition_service import AcquisitionService
from signal_processing_toolkit.streaming.sources import SyntheticSource


def test_acquisition_service_reads_off_thread_and_stops() -> None:
    source = SyntheticSource(real_time=False, chunk_size=16)
    service = AcquisitionService(source, max_queue=2)
    service.start()
    deadline = time.monotonic() + 1.0
    while service.queue_depth == 0 and time.monotonic() < deadline:
        time.sleep(0.01)
    chunks = service.poll()
    service.stop()
    assert chunks
    assert chunks[0].sample_count == 16
    assert not service.running
