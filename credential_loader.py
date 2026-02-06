def load_credentials(file_path):
    """Load multiple credential sets from file. Secret is shared across all."""
    creds_list = []
    current = {}
    secret = None

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("Username"):
                if current.get("username") and current.get("password"):
                    creds_list.append(current)
                current = {"username": line.split(":", 1)[1].strip()}
            elif line.startswith("Password"):
                current["password"] = line.split(":", 1)[1].strip()
            elif line.startswith("Secret"):
                secret = line.split(":", 1)[1].strip()

    if current.get("username") and current.get("password"):
        creds_list.append(current)

    # Apply shared secret to all credential sets
    for creds in creds_list:
        creds["secret"] = secret

    return creds_list
