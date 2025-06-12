import time
import random
from typing import Optional


class RemoteExecutionError(Exception):
    pass


class RemoteRebootDetected(Exception):
    pass


class RemoteExecutorMock:
    def __init__(self, hostname: str, username: str, key_file: Optional[str] = None, port: int = 22):
        self.hostname = hostname
        self.username = username
        self.key_file = key_file
        self.port = port
        self.connected = False
        self.boot_time = self._simulate_boot_time()
        self.simulated_reboot_after = 5  # Simulate reboot after 5 runs
        self.run_count = 0

    def _simulate_boot_time(self):
        return f"2025-06-12 10:{random.randint(10, 59)}:00"

    def _ping(self):
        # Simulate ping always succeeds
        print(f" Ping to {self.hostname} succeeded.")
        return True

    def is_alive(self) -> bool:
        """Simulate checking SSH access, fallback to ping."""
        print(f"🔍 Checking if host {self.hostname} is alive via simulated SSH...")
        if self.run_count < self.simulated_reboot_after:
            self.connected = True
            return True
        else:
            # Simulate SSH failure
            print(f"Simulated SSH failure. Trying ping...")
            if self._ping():
                self.connected = False
                return False
            else:
                return False

    def reconnect(self) -> bool:
        print(f"Reconnecting to {self.hostname}...")
        if not self.is_alive():
            return False

        new_boot_time = self._get_boot_time()
        if self.boot_time and self.boot_time != new_boot_time:
            old = self.boot_time
            self.boot_time = new_boot_time
            raise RemoteRebootDetected(f"Remote reboot detected! Old: {old}, New: {new_boot_time}")
        self.boot_time = new_boot_time
        return True

    def _get_boot_time(self) -> str:
        """Simulate reboot by returning a new boot time after N runs."""
        if self.run_count == self.simulated_reboot_after:
            print("Simulating a reboot!")
            return self._simulate_boot_time()
        return self.boot_time

    def stream_execute(self, command: str, retry_on_reboot=True):
        print(f"Executing: '{command}' (simulated)...")
        if not self.connected:
            try:
                self.reconnect()
                if retry_on_reboot:
                    return self.stream_execute(command, retry_on_reboot=False)
                else:
                    raise RemoteExecutionError("Reconnect failed.")
            except RemoteRebootDetected as e:
                print(f"Reboot handled: {e}")
                return
            except Exception as e:
                raise RemoteExecutionError(f"Reconnect failed: {e}")

        # Simulate command output
        print("Simulated STDOUT:")
        print(f"{command} => simulated output at {time.strftime('%H:%M:%S')}")

        # Simulate return code
        if self.run_count == self.simulated_reboot_after:
            raise RemoteExecutionError("Simulated command failure after reboot.")

    def _wait_for_reboot_and_reconnect(self, timeout=60, interval=5):
        print("Waiting for remote host to reboot and come back online (simulated)...")
        start = time.time()
        while time.time() - start < timeout:
            if self._get_boot_time() != self.boot_time:
                print("Host rebooted and reconnected.")
                return True
            print("Still waiting...")
            time.sleep(interval)
        raise RemoteExecutionError(" Timeout: Host did not come back online.")


if __name__ == "__main__":
    executor = RemoteExecutorMock(
        hostname="IP address",
        username="offline_user",
        key_file=None,
        port=22
    )

    print("Starting simulated remote command execution...\n")
    for i in range(10):
        print(f"\n--- Simulated Run {i + 1} ---")
        try:
            executor.run_count = i
            executor.stream_execute("uptime")
        except RemoteRebootDetected as e:
            print(f"Reboot detected: {e}")
        except RemoteExecutionError as e:
            print(f"Error: {e}")
        time.sleep(1)
