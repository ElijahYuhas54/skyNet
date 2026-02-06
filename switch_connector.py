from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException

def connect_to_switch(ip, creds_list, device_type):
    """Try each credential set until one works"""
    last_error = None

    for creds in creds_list:
        device = {
            "device_type": device_type,
            "host": ip,
            "username": creds["username"],
            "password": creds["password"],
            "secret": creds["secret"],
            "disabled_algorithms": {
                "pubkeys": ["rsa-sha2-256", "rsa-sha2-512"],
            },
        }

        try:
            conn = ConnectHandler(**device)
            conn.enable()
            return conn
        except NetmikoAuthenticationException as e:
            last_error = e
            continue

    raise last_error
