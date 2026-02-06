import csv

def load_switch_ips(file_path):
    ips = []

    if file_path.endswith(".txt"):
        with open(file_path, "r") as f:
            ips = [line.strip() for line in f if line.strip()]

    elif file_path.endswith(".csv"):
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ips.append(row["ip"])

    return ips
