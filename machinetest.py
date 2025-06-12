import pytest
from vmconnector import RemoteExecutor, RemoteExecutionError


def test_ssh_and_command():
    executor = RemoteExecutor(
        hostname="host",
        username="user",
        key_file="key",
        port=22
    )

    try:
        assert executor.is_alive(), "Host should be alive."
        executor.stream_execute("echo hello")
    except RemoteExecutionError as e:
        pytest.skip(f"SSH not available or command failed: {e}")


def test_reconnect_and_uptime():
    executor = RemoteExecutor(
        hostname="host",
        username="user",
        key_file="key",
        port=22
    )

    try:
        assert executor.reconnect() == True
        assert executor.boot_time is not None
    except RemoteExecutionError as e:
        pytest.skip(f"Cannot test reconnect: {e}")


def test_failed_command():
    executor = RemoteExecutor(
        hostname="host",
        username="user",
        key_file="key",
        port=22
    )

    with pytest.raises(RemoteExecutionError):
        executor.stream_execute("false")
