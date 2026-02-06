def get_switch_health(conn):
    """Collect all switch health data"""
    return {
        "environment": conn.send_command("show environment all"),
        "power": conn.send_command("show power inline"),
        "inventory": conn.send_command("show inventory"),
        "cpu": conn.send_command("show processes cpu | include CPU"),
        "memory": conn.send_command("show memory statistics"),
        "log": conn.send_command("show logging | include DHCP_SNOOPING"),
        "errdisable": conn.send_command("show interfaces status err-disabled"),
    }


def get_interface_status(conn):
    """Returns physical port status (show interfaces status)"""
    return conn.send_command("show interfaces status", use_textfsm=True)


def get_interface_counters(conn):
    """Returns interface error counters"""
    return conn.send_command("show interfaces", use_textfsm=True)


def get_mac_table(conn):
    """Returns MAC address table with interface mapping"""
    return conn.send_command(
        "show mac address-table",
        use_textfsm=True
    )
