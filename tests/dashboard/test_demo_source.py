from signal_processing_toolkit.dashboard.services.demo_source import DemoSource


def test_demo_source_is_deterministic_and_restarts() -> None:
    source = DemoSource()
    source.start()
    first = source.next_chunk(8)
    source.stop()
    assert source.next_chunk(8) == []
    source.reset()
    source.start()
    assert source.next_chunk(8) == first
