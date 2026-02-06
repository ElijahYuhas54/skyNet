from device_loader import load_switch_ips
from credential_loader import load_credentials
from switch_connector import connect_to_switch
from health_checks import (
    get_switch_health,
    get_interface_status,
    get_interface_counters,
    get_mac_table
)
from analyzer import analyze_interfaces, analyze_switch_health
from reporter import print_switch_report, print_remediation_summary
from config import DEVICE_TYPE

SWITCH_LIST_FILE = "data/switch_ipAddresses.txt"
CREDENTIAL_FILE = "data/switch_password.txt"


def main():
    ips = load_switch_ips(SWITCH_LIST_FILE)
    creds = load_credentials(CREDENTIAL_FILE)

    all_issues = []  # Collect all issues for final summary

    for ip in ips:
        try:
            print(f"\n[+] Connecting to {ip}")
            conn = connect_to_switch(ip, creds, DEVICE_TYPE)

            print("[+] Collecting switch health")
            health_data = get_switch_health(conn)
            health_issues = analyze_switch_health(health_data)

            print("[+] Collecting interface status")
            port_status = get_interface_status(conn)

            print("[+] Collecting interface counters")
            counters = get_interface_counters(conn)

            print("[+] Collecting MAC address table")
            mac_table = get_mac_table(conn)

            interface_summary = analyze_interfaces(port_status, counters, mac_table, health_data.get("errdisable", ""))
            print_switch_report(ip, health_issues, interface_summary)

            # Collect issues for remediation summary
            if health_issues:
                all_issues.append({"ip": ip, "health": health_issues, "interfaces": interface_summary})

            conn.disconnect()

        except Exception as e:
            print(f"[!] Failed to process {ip}: {e}")

    # Print remediation summary at the end
    print_remediation_summary(all_issues)


if __name__ == "__main__":
    main()
