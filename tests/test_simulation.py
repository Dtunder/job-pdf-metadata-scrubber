import pytest
from unittest.mock import patch
import simulation


def test_simulator_connect_success():
    sim = simulation.ExternalServiceSimulator()
    with pytest.raises(simulation.ConnectionFailure):
        sim.connect(fail_times=2)
    with pytest.raises(simulation.ConnectionFailure):
        sim.connect(fail_times=2)
    assert sim.connect(fail_times=2) == "Connected successfully"


def test_simulator_process_data_success():
    sim = simulation.ExternalServiceSimulator()
    with pytest.raises(simulation.TimeoutError):
        sim.process_data(timeout_times=1)
    assert sim.process_data(timeout_times=1) == "Data processed"


def test_reliable_connect():
    simulation.simulator = simulation.ExternalServiceSimulator()
    result = simulation.reliable_connect()
    assert result == "Connected successfully"


def test_reliable_process_fallback():
    simulation.simulator = simulation.ExternalServiceSimulator()
    result = simulation.reliable_process()
    assert result == "Processed locally (fallback)"


def test_workflow():
    simulation.simulator = simulation.ExternalServiceSimulator()
    result = simulation.execute_system_workflow()
    assert result == "Connected successfully. Processed locally (fallback)."


def test_workflow_exception():
    simulation.simulator = simulation.ExternalServiceSimulator()
    with patch(
        "simulation.reliable_connect", side_effect=Exception("Unexpected")
    ):
        result = simulation.execute_system_workflow()
        assert result == "Workflow failed"
