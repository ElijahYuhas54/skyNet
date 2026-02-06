def print_switch_report(ip, switch_health_issues, interface_summary):
    unused = interface_summary["unused_ports"]
    total_unused = sum(len(v) for v in unused.values())

    print("\n" + "=" * 50)
    print(f"Switch: {ip}")
    print("=" * 50)

    # Switch Health Section
    if switch_health_issues:
        print("\n[!] Switch Health Issues:")
        for item in switch_health_issues:
            print(f"  - {item['issue']}")
    else:
        print("\n[OK] Switch Health: No issues")

    # Interface Summary
    print(f"\nPorts: {interface_summary['total_ports']} total | {interface_summary['good_ports']} healthy | {interface_summary['problem_ports']} with errors | {total_unused} inactive")

    # Inactive breakdown (counts only)
    if total_unused > 0:
        parts = []
        if unused["disabled"]:
            parts.append(f"{len(unused['disabled'])} shutdown")
        if unused["err_disabled"]:
            parts.append(f"{len(unused['err_disabled'])} err-disabled")
        if unused["notconnect"]:
            parts.append(f"{len(unused['notconnect'])} down (prev active)")
        if unused["no_traffic"]:
            parts.append(f"{len(unused['no_traffic'])} unused")
        print(f"  Inactive: {', '.join(parts)}")

    # Show err-disabled ports (these need attention)
    if unused["err_disabled"]:
        print(f"  [!] Err-disabled: {', '.join(unused['err_disabled'])}")

    # Interface errors (counts only)
    if interface_summary["issue_counts"]:
        print("\n[!] Port Errors:")
        for error_type, count in interface_summary["issue_counts"].items():
            print(f"  - {error_type}: {count} ports")
    else:
        print("\n[OK] Port Errors: None")


def print_remediation_summary(all_issues):
    """Print remediation commands for all detected issues"""
    if not all_issues:
        return

    print("\n")
    print("=" * 60)
    print("REMEDIATION SUMMARY")
    print("=" * 60)

    for switch in all_issues:
        ip = switch["ip"]
        health = switch["health"]
        interfaces = switch["interfaces"]

        has_issues = health or interfaces["unused_ports"]["err_disabled"] or interfaces["issue_counts"]

        if not has_issues:
            continue

        print(f"\n--- {ip} ---")

        # Health issue fixes
        for item in health:
            print(f"\n[Issue] {item['issue']}")
            print("[Fix]")
            for line in item['fix'].split('\n'):
                print(f"  {line}")

        # Err-disabled port fixes
        if interfaces["unused_ports"]["err_disabled"]:
            print(f"\n[Issue] Err-disabled ports: {len(interfaces['unused_ports']['err_disabled'])}")
            print("[Fix]")
            print("  show interfaces status err-disabled")
            print("  ! To recover a port:")
            print("  conf t")
            print("    interface <port>")
            print("    shutdown")
            print("    no shutdown")
            print("  ! Or enable auto-recovery:")
            print("  errdisable recovery cause all")
            print("  errdisable recovery interval 300")

        # Port error fixes
        if interfaces["issue_counts"]:
            if "CRC errors" in interfaces["issue_counts"]:
                print(f"\n[Issue] CRC errors on {interfaces['issue_counts']['CRC errors']} ports")
                print("[Fix]")
                print("  show interfaces | include CRC|line protocol")
                print("  ! Usually cable or transceiver issue - check physical layer")
                print("  ! Try different cable or SFP")

            if "Input errors" in interfaces["issue_counts"]:
                print(f"\n[Issue] Input errors on {interfaces['issue_counts']['Input errors']} ports")
                print("[Fix]")
                print("  show interfaces counters errors")
                print("  ! Check duplex/speed mismatch:")
                print("  show interfaces status")
                print("  ! Try hard-coding speed/duplex if auto-negotiation failing")

            if "Output errors" in interfaces["issue_counts"]:
                print(f"\n[Issue] Output errors on {interfaces['issue_counts']['Output errors']} ports")
                print("[Fix]")
                print("  show interfaces counters errors")
                print("  ! Often congestion - check for oversubscription")
                print("  show interfaces <port> | include output drops")

    print("\n" + "=" * 60)
