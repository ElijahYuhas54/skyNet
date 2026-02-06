import re
from config import ERROR_THRESHOLDS


def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def analyze_switch_health(health_data):
    """Analyze switch health data for issues. Returns list of (issue, fix) tuples."""
    issues = []

    env = health_data.get("environment", "")
    power = health_data.get("power", "")
    cpu = health_data.get("cpu", "")
    memory = health_data.get("memory", "")

    env_lower = env.lower()

    # Fan issues
    if "fan" in env_lower:
        for line in env.splitlines():
            line_lower = line.lower()
            if "fan" in line_lower and any(x in line_lower for x in ["fail", "fault", "bad", "not ok", "not present"]):
                issues.append({
                    "issue": "Fan failure detected",
                    "fix": "show environment all | include Fan\n! Physical inspection required - replace failed fan"
                })
                break

    # PSU issues
    if any(x in env_lower for x in ["power supply", "ps-", "psu"]):
        for line in env.splitlines():
            line_lower = line.lower()
            if any(x in line_lower for x in ["power supply", "ps-", "psu"]):
                if any(x in line_lower for x in ["fail", "fault", "bad", "not ok", "shutdown"]):
                    issues.append({
                        "issue": "Power supply issue",
                        "fix": "show environment power all\n! Check PSU seating or replace failed PSU"
                    })
                    break

    # Temperature issues - find the actual high temp
    temp_matches = re.findall(r'(\d+)\s*[Cc]', env)
    high_temp = None
    for temp in temp_matches:
        if int(temp) > 60:
            high_temp = int(temp)
            break

    if high_temp:
        issues.append({
            "issue": f"High temperature: {high_temp}C",
            "fix": "show environment temperature\n! Check airflow, clean vents, verify fans operational"
        })

    # PoE power issues
    if power:
        poe_exhausted = False
        for line in power.splitlines():
            line_lower = line.lower()
            if "fault" in line_lower or "faulty" in line_lower:
                issues.append({
                    "issue": "PoE port fault",
                    "fix": "show power inline\n! Identify faulty port, check connected device, try:\nconf t\n  interface <port>\n  power inline never\n  power inline auto"
                })
            if "available" in line_lower and "0.0" in line and not poe_exhausted:
                poe_exhausted = True
                issues.append({
                    "issue": "PoE budget exhausted - no power available",
                    "fix": "show power inline\n! Reduce PoE load or upgrade PSU:\nshow power inline priority\n! Lower priority devices will be cut first"
                })

    # CPU issues
    if cpu:
        cpu_match = re.search(r'(\d+)%', cpu)
        if cpu_match:
            cpu_pct = int(cpu_match.group(1))
            if cpu_pct > 80:
                issues.append({
                    "issue": f"High CPU: {cpu_pct}%",
                    "fix": "show processes cpu sorted | head 10\nshow logging | include CPU\n! Identify top process consuming CPU"
                })

    # Memory issues
    if memory:
        mem_match = re.search(r'Processor\s+\S+\s+(\d+)\s+(\d+)', memory)
        if mem_match:
            total = int(mem_match.group(1))
            used = int(mem_match.group(2))
            if total > 0:
                pct = (used / total) * 100
                if pct > 90:
                    issues.append({
                        "issue": f"High memory usage: {pct:.0f}%",
                        "fix": "show memory statistics\nshow processes memory sorted | head 10\n! Consider reload if memory leak suspected"
                    })

    # Module issues
    for line in env.splitlines():
        line_lower = line.lower()
        if "module" in line_lower or "slot" in line_lower:
            if any(x in line_lower for x in ["fail", "fault", "error", "bad"]):
                issues.append({
                    "issue": "Module failure",
                    "fix": "show module\nshow inventory\n! Try reseating module or replace if failed"
                })
                break

    # DHCP Snooping violations
    log = health_data.get("log", "")
    if log:
        snooping_count = log.lower().count("dhcp_snooping")
        if snooping_count > 0:
            mac_matches = re.findall(r'MAC sa:\s*([0-9a-fA-F:.]+)', log)
            unique_macs = set(mac_matches)
            mac_str = ', '.join(unique_macs) if unique_macs else 'unknown'
            issues.append({
                "issue": f"DHCP Snooping violations: {snooping_count} events (MAC: {mac_str})",
                "fix": f"show ip dhcp snooping binding\nshow mac address-table address {list(unique_macs)[0] if unique_macs else '<mac>'}\n! Device spoofing DHCP - find port and investigate"
            })

    return issues


def build_counter_lookup(counters):
    """Build a dict keyed by interface name for quick lookups"""
    lookup = {}
    for intf in counters:
        name = intf.get("interface", "")
        lookup[name] = intf
    return lookup


def normalize_port_name(short_name):
    """Convert short names (Gi1/0/1) to match show interfaces output"""
    # show interfaces status uses short names, show interfaces uses full names
    # This maps common prefixes
    prefixes = {
        "Gi": "GigabitEthernet",
        "Te": "TenGigabitEthernet",
        "Fo": "FortyGigabitEthernet",
        "Tw": "TwentyFiveGigE",
        "Hu": "HundredGigE",
        "Fa": "FastEthernet",
    }
    for short, full in prefixes.items():
        if short_name.startswith(short) and not short_name.startswith(full):
            return short_name.replace(short, full, 1)
    return short_name


def has_ever_had_traffic(intf):
    last_in = str(intf.get("last_input", "")).lower()
    last_out = str(intf.get("last_output", "")).lower()
    return not ("never" in last_in and "never" in last_out)


def mac_seen_on_interface(mac_table, interface):
    for entry in mac_table:
        if entry.get("destination_port") == interface:
            return True
    return False


def parse_errdisable_reasons(errdisable_output):
    """Parse 'show interfaces status err-disabled' to get port->reason mapping"""
    reasons = {}
    for line in errdisable_output.splitlines():
        # Typical format: Gi1/0/5  err-disabled  bpduguard
        parts = line.split()
        if len(parts) >= 2:
            port = parts[0]
            # Last column is usually the reason
            reason = parts[-1] if len(parts) > 2 else "unknown"
            if any(x in port for x in ["Gi", "Te", "Fa", "Fo", "Tw", "Hu", "Eth"]):
                reasons[port] = reason
    return reasons


def analyze_interfaces(port_status, counters, mac_table, errdisable_output=""):
    """
    port_status: from 'show interfaces status' - physical ports only
    counters: from 'show interfaces' - has error counters
    mac_table: from 'show mac address-table'
    errdisable_output: from 'show interfaces status err-disabled'
    """
    summary = {
        "total_ports": 0,
        "good_ports": 0,
        "problem_ports": 0,
        "unused_ports": {
            "disabled": [],
            "err_disabled": [],
            "no_traffic": [],
            "notconnect": []
        },
        "issues": []
    }

    counter_lookup = build_counter_lookup(counters)
    errdisable_reasons = parse_errdisable_reasons(errdisable_output)

    for port in port_status:
        name = port.get("port", "")
        status = str(port.get("status", "")).lower()

        summary["total_ports"] += 1

        # Get counter data for this port
        full_name = normalize_port_name(name)
        counter_data = counter_lookup.get(full_name, {})

        # Check port status
        if status == "disabled":
            summary["unused_ports"]["disabled"].append(name)
            continue

        if "err" in status:
            reason = errdisable_reasons.get(name, "unknown")
            summary["unused_ports"]["err_disabled"].append(f"{name} ({reason})")
            continue

        if status == "notconnect":
            # Check if it ever had traffic
            ever_had_traffic = has_ever_had_traffic(counter_data)
            mac_seen = mac_seen_on_interface(mac_table, name)

            if not ever_had_traffic and not mac_seen:
                summary["unused_ports"]["no_traffic"].append(name)
            else:
                summary["unused_ports"]["notconnect"].append(name)
            continue

        # Port is connected - check for errors
        if status == "connected":
            crc = safe_int(counter_data.get("crc"))
            in_err = safe_int(counter_data.get("input_errors"))
            out_err = safe_int(counter_data.get("output_errors"))

            issues = []

            if crc > ERROR_THRESHOLDS["crc"]:
                issues.append(f"CRC errors: {crc}")

            if in_err > ERROR_THRESHOLDS["input"]:
                issues.append(f"Input errors: {in_err}")

            if out_err > ERROR_THRESHOLDS["output"]:
                issues.append(f"Output errors: {out_err}")

            if issues:
                summary["problem_ports"] += 1
                for issue in issues:
                    summary["issues"].append(issue)
            else:
                summary["good_ports"] += 1

    # Count issues by type
    issue_counts = {}
    for issue in summary["issues"]:
        if "CRC" in issue:
            issue_counts["CRC errors"] = issue_counts.get("CRC errors", 0) + 1
        elif "Input" in issue:
            issue_counts["Input errors"] = issue_counts.get("Input errors", 0) + 1
        elif "Output" in issue:
            issue_counts["Output errors"] = issue_counts.get("Output errors", 0) + 1

    summary["issue_counts"] = issue_counts

    return summary
