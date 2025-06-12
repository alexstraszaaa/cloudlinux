import subprocess
from typing import Optional
import time
import platform


class RemoteExecutionError(Exception):
    # Raised when the remote command execution fails.
    pass


class RemoteRebootDetected(Exception):
    # Raised when a remote reboot is detected.
    pass


class RemoteExecutor:
    def __init__(self, hostname: str, username: str, key_file: Optional[str] = None, port: int = 22):
        self.hostname = hostname
        self.username = username
        self.key_file = key_file
        self.port = port
        self.connected = False
        self.boot_time = None

    def is_alive(self) -> bool:
        # Checks if the remote host is reachable and updates boot time if SSH works.
        # Falls back to ping if SSH fails.

        check_command = self._build_ssh_command("uptime -s")
        try:
            result = subprocess.run(
                check_command,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                current_boot_time = result.stdout.strip()
                self.boot_time = current_boot_time
                self.connected = True
                return True
            else:
                print(f"SSH failed (code {result.returncode}), trying ping...")
        except Exception as e:
            print(f"SSH exception: {e}, trying ping...")

        ping_command = ["ping", "-c", "1", self.hostname] if platform.system() != "Windows" else ["ping", "-n", "1",
                                                                                                  self.hostname]

        try:
            ping_result = subprocess.run(
                ping_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if ping_result.returncode == 0:
                print("Ping succeeded — host is alive but SSH is unreachable.")
                return False
            else:
                print("Ping failed — host appears to be down.")
                return False
        except Exception as e:
            print(f"Ping exception: {e}")
            return False

    def reconnect(self) -> bool:
        # Attempts to re-establish connection and update boot time.

        # Raises:
        # RemoteRebootDetected: If the remote host has rebooted.

        print(f"Reconnecting to {self.hostname}...")
        try:

            if not self.is_alive():
                return False

            current_boot_time = self.boot_time
            new_boot_time = self._get_boot_time()

            if current_boot_time and current_boot_time != new_boot_time:
                self.boot_time = new_boot_time
                raise RemoteRebootDetected(f"Remote host rebooted! Old: {current_boot_time}, New: {new_boot_time}")

            self.boot_time = new_boot_time
            return True

        except RemoteRebootDetected:
            raise
        except Exception as e:
            print(f"Reconnect error: {e}")
            return False

    def was_rebooted(self) -> bool:
        # Checks if the remote system has rebooted since last successful connect.
        try:
            code, out, _ = self.execute("uptime -s", timeout=5)
            if code == 0:
                current_boot_time = out.strip()
                rebooted = self.boot_time is not None and self.boot_time != current_boot_time
                self.boot_time = current_boot_time
                return rebooted
            return False
        except RemoteExecutionError:
            return False

    def _build_ssh_command(self, command: str) -> list:
        ssh_cmd = [
            "ssh",
            "-p", str(self.port),
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            f"{self.username}@{self.hostname}",
            command
        ]
        if self.key_file:
            ssh_cmd.insert(1, "-i")
            ssh_cmd.insert(2, self.key_file)
        return ssh_cmd

    def _get_boot_time(self) -> str:
        try:
            cmd = self._build_ssh_command("uptime -s")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.stdout.strip()
        except Exception:
            return ""

    def stream_execute(self, command: str, retry_on_reboot=True):
        # Stream output of remote command live to the console.
        if not self.connected:
            try:
                self.reconnect()
                if retry_on_reboot:
                    return self.stream_execute(command, retry_on_reboot=False)
                else:
                    raise
            except Exception as e:
                raise RemoteExecutionError(f"Reconnect failed: {e}")

        ssh_command = self._build_ssh_command(command)

        try:
            with subprocess.Popen(
                    ssh_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
            ) as process:
                print(" Streaming STDOUT:")
                for line in process.stdout:
                    print(line, end='')

                print("\n Streaming STDERR:")
                for line in process.stderr:
                    print(line, end='')

                process.wait()

                if process.returncode == 255:
                    print(" SSH failed — host likely rebooting...")
                    self._wait_for_reboot_and_reconnect()
                    if retry_on_reboot:
                        return self.stream_execute(command, retry_on_reboot=False)
                    else:
                        raise RemoteExecutionError("SSH failed and retry exhausted.")
                elif process.returncode != 0:
                    raise RemoteExecutionError(f"Command failed with code {process.returncode}")

        except RemoteRebootDetected as e:
            print(f" Reboot detected while streaming: {e}")
            if retry_on_reboot:
                return self.stream_execute(command, retry_on_reboot=False)
            else:
                raise
        except Exception as e:
            raise RemoteExecutionError(f"Streaming command failed: {e}")

    def _wait_for_reboot_and_reconnect(self, timeout=300, interval=5) -> bool:
        print("Waiting for remote host to reboot and come back online...")
        start_time = time.time()
        old_boot_time = self.boot_time

        while time.time() - start_time < timeout:
            try:
                new_boot_time = self._get_boot_time()
                if new_boot_time:
                    self.connected = True
                    if old_boot_time and new_boot_time != old_boot_time:
                        print(f" Reboot confirmed! Old: {old_boot_time}, New: {new_boot_time}")
                    elif not old_boot_time:
                        print(" First connection after host start.")
                    else:
                        print(" Host is back, no reboot detected.")
                    self.boot_time = new_boot_time
                    return True
            except Exception as e:
                print(f" Exception while checking reboot status: {e}")

            print(" Host still unreachable, retrying...")
            time.sleep(interval)

        raise RemoteExecutionError(" Timeout: Remote host did not come back online.")


if __name__ == "__main__":
    executor = RemoteExecutor(
        hostname="hostname",
        username="username",
        key_file="key",
        port=22
    )

    for i in range(300):
        print(f"\n--- Run {i + 1} ---")
        try:
            executor.stream_execute("uptime")
        except RemoteRebootDetected as e:
            print(f" Reboot handled: {e}")
            continue
        except RemoteExecutionError as e:
            print(f" Error: {e}")
        time.sleep(1)
