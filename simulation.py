import logging

from resilience import retry, fallback, RetryExhaustedError
from config import config

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


class ConnectionFailure(Exception):
    pass


class BadConfiguration(Exception):
    pass


class ExternalServiceSimulator:
    def __init__(self) -> None:
        self.connection_attempts: int = 0
        self.processing_attempts: int = 0

    def connect(self, fail_times: int = 2) -> str:
        """Simulate a connection that fails initially."""
        self.connection_attempts += 1
        if self.connection_attempts <= fail_times:
            raise ConnectionFailure("Connection reset by peer.")
        return "Connected successfully"

    def process_data(self, timeout_times: int = 1) -> str:
        """Simulate processing data that times out initially."""
        self.processing_attempts += 1
        if self.processing_attempts <= timeout_times:
            raise TimeoutError("Request timed out.")
        return "Data processed"


simulator = ExternalServiceSimulator()


def local_fallback_processing() -> str:
    """Fallback method for data processing."""
    return "Processed locally (fallback)"


@retry(
    exceptions=(ConnectionFailure,),
    max_attempts=config.SIMULATION_CONNECT_MAX_ATTEMPTS,
    base_delay=config.SIMULATION_CONNECT_BASE_DELAY,
)
def reliable_connect() -> str:
    logger.info("Attempting to connect...")
    return simulator.connect(fail_times=config.SIMULATION_FAIL_TIMES)


@fallback(fallback_func=local_fallback_processing, exceptions=(RetryExhaustedError,))
@retry(
    exceptions=(TimeoutError,),
    max_attempts=config.SIMULATION_PROCESS_MAX_ATTEMPTS,
    base_delay=config.SIMULATION_PROCESS_BASE_DELAY,
)
def reliable_process() -> str:
    logger.info("Attempting to process data...")
    # This will fail twice if timeout_times is >= 2, triggering RetryExhaustedError
    # The fallback catches RetryExhaustedError and executes local_fallback_processing
    return simulator.process_data(timeout_times=config.SIMULATION_TIMEOUT_TIMES)


def execute_system_workflow() -> str:
    try:
        conn_status = reliable_connect()
        proc_status = reliable_process()
        return f"{conn_status}. {proc_status}."
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        return "Workflow failed"
