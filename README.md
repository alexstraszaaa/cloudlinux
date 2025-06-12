
## Instructions

1. Clone this repository.
2. Open the repository directory in your terminal.
3. Run the project using your preferred Python environment.

---
## Strategy

The initial testing strategy involved powering on a virtual machine (VM) and establishing an SSH connection. Various scenarios—such as rebooting the VM and inducing SSH connectivity issues—were created to trigger and handle different error cases.

### Unexpected Reboot Detection

To simulate a reboot, the VM was restarted manually. The `reconnect()` method was then tested to verify proper reboot detection and recovery.

### Connectivity Check with `is_alive()`

The `is_alive()` method was enhanced to use the `ping` command. This allows the system to confirm the machine is active and reachable even when SSH is temporarily unavailable.

### Transition to Mock-Based Testing

Once the SSH and reboot behaviors were validated on a live VM, the project was adapted to support offline simulation using mocks. This allows consistent and automated testing without needing an active network or VM.

---

## Handling Long-Running and Disruptive Commands

* **Pre-checks**: Use `ping` and `ssh` to verify availability before execution.
* **Pytest Simulations**: Simulate network conditions and test recovery scenarios.
* **Reboot Detection and Recovery**: Use `uptime -s` or boot ID checks to detect system restarts and recover gracefully.

---

