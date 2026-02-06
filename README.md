# SkyNet - Cisco Switch Health Monitor

Automated health monitoring tool for Cisco IOS switches. Connects via SSH, collects health data, and provides actionable remediation steps.

## Features

- **Switch Health Monitoring**
  - Fan status
  - Power supply status
  - Temperature alerts
  - CPU/Memory usage
  - Module failures
  - PoE budget and faults
  - DHCP Snooping violations

- **Interface Analysis**
  - Physical port status (connected, shutdown, err-disabled)
  - CRC, input, and output error detection
  - Identifies unused ports vs previously active ports
  - Err-disabled reason tracking (bpduguard, psecure-violation, etc.)

- **Remediation Summary**
  - Provides CLI commands to troubleshoot each issue
  - Grouped by switch at the end of the report

## Setup

### Requirements

```
pip install netmiko
```

### Configuration

1. **Add switch IPs** to `data/switch_ipAddresses.txt` (one per line):
   ```
   10.10.22.101
   10.10.2.9
   10.10.4.9
   ```

2. **Add credentials** to `data/switch_password.txt`:
   ```
   Username: admin
   Password: yourpassword
   Username: backup_user
   Password: backuppassword
   Secret: enablesecret
   ```
   - Multiple username/password pairs supported (tries in order)
   - Secret is shared across all credential sets

## Usage

```bash
python main.py
```

## Output Example

```
==================================================
Switch: 10.10.22.101
==================================================

[!] Switch Health Issues:
  - High temperature: 62C
  - PoE budget exhausted - no power available

Ports: 48 total | 42 healthy | 1 with errors | 5 inactive
  Inactive: 2 shutdown, 1 err-disabled, 2 unused
  [!] Err-disabled: Gi1/0/15 (bpduguard)

[!] Port Errors:
  - CRC errors: 1 ports

============================================================
REMEDIATION SUMMARY
============================================================

--- 10.10.22.101 ---

[Issue] High temperature: 62C
[Fix]
  show environment temperature
  ! Check airflow, clean vents, verify fans operational

[Issue] Err-disabled ports: 1
[Fix]
  show interfaces status err-disabled
  ! To recover a port:
  conf t
    interface <port>
    shutdown
    no shutdown
```

## File Structure

```
skyNet/
├── main.py              # Entry point
├── config.py            # Thresholds and device type
├── credential_loader.py # Parse credentials file
├── device_loader.py     # Parse switch IP list
├── switch_connector.py  # SSH connection handling
├── health_checks.py     # Collect data from switches
├── analyzer.py          # Analyze health and interfaces
├── reporter.py          # Format and print reports
└── data/
    ├── switch_ipAddresses.txt
    └── switch_password.txt
```

## Thresholds

Edit `config.py` to adjust error thresholds:

```python
ERROR_THRESHOLDS = {
    "crc": 10,
    "input": 10,
    "output": 10
}
```

## Supported Platforms

- Cisco IOS
- Cisco IOS-XE (Catalyst 9000 series)
- Tested on: C9300, C9300X, C3850
