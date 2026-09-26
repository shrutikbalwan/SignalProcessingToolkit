from dataclasses import replace

import numpy as np

from signal_processing_toolkit.demo import ExperimentConfig, PredictiveMaintenanceWorkbench


def test_predictive_maintenance_workbench_end_to_end(tmp_path) -> None:
    config = ExperimentConfig(duration_seconds=0.512, frame_size=64, model_window=128, model_hop=64)
    workbench = PredictiveMaintenanceWorkbench(config)
    healthy = workbench.run()
    faulty = PredictiveMaintenanceWorkbench(replace(config, faulty=True)).run()
    assert healthy.packet_count > 0
    assert healthy.packet_loss == 0
    assert healthy.raw_samples.shape == healthy.processed_samples.shape
    assert faulty.measurements["crest_factor"] >= healthy.measurements["crest_factor"]
    snapshot = workbench.dashboard_snapshot(faulty)
    assert snapshot.inference_latency_seconds >= 0
    assert snapshot.event_count > 0
    session = workbench.save(healthy, tmp_path / "session")
    reopened = PredictiveMaintenanceWorkbench.reopen(session)
    np.testing.assert_array_equal(healthy.raw_samples, reopened.raw_samples)
    np.testing.assert_array_equal(healthy.processed_samples, reopened.processed_samples)
    assert (session / "diagnostic_report.md").is_file()
    assert (session / "filter.h").is_file()
