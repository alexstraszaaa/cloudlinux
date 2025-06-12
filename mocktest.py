import pytest
from vmconnectormock import RemoteExecutorMock, RemoteExecutionError, RemoteRebootDetected


def test_mock_execution_no_reboot():
    executor = RemoteExecutorMock("localhost", "user")
    executor.simulated_reboot_after = 100
    for i in range(3):
        executor.run_count = i
        try:
            executor.stream_execute("uptime")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")


def test_mock_execution_with_reboot():
    executor = RemoteExecutorMock("localhost", "user")
    executor.simulated_reboot_after = 2

    for i in range(4):
        executor.run_count = i
        try:
            executor.stream_execute("uptime")
        except RemoteRebootDetected as e:
            print(f" Caught simulated reboot: {e}")
        except RemoteExecutionError as e:
            print(f" Simulated connection issue: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")
