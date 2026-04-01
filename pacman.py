import subprocess

# For installation, removal, and upgrade actions, see actions.py. This file is for searching repositories and installed packages only.

def search_repos(query, expanded=False, return_type="pretty"):
    subprocess.run(["pacman", "-Sy"])
    pacman_data = subprocess.run(["pacman", "-Ss", query[0]], capture_output=True, text=True)
    packages = []
    storage = None

    if return_type == "raw":
        return pacman_data.stdout
    elif return_type == "pretty":
        for index, line in enumerate(pacman_data.stdout.split("\n")):
            if index % 2 == 0:
                storage = line
            else:
                if (all(Query.lower() in storage.lower() or (expanded and Query.lower() in line.lower()) for Query in query)):
                    packages.append({
                            "Name": (storage.split("/")[1].split()[0]),
                            "Repo": storage.split("/")[0],
                            "Version": storage.split()[1],
                            "Description": line.strip()
                        })
                    
        return packages
    else:
        print("Invalid return type. Use 'raw' or 'pretty'.")

def search_installed(query, return_type="pretty"):
    pacman_data = subprocess.run(["pacman", "-Qs", query], capture_output=True, text=True)
    packages = []
    storage = None

    if return_type == "raw":
        return pacman_data.stdout
    elif return_type == "pretty":
        for index, line in enumerate(pacman_data.stdout.split("\n")):
            if index % 2 == 0:
                storage = line
            else:
                packages.append({
                        "Name": (storage.split("/")[1].split()[0]),
                        "Repo": storage.split("/")[0],
                        "Version": storage.split()[1],
                        "Description": line.strip()
                    })
        return packages
    else:
        print("Invalid return type. Use 'raw' or 'pretty'.")

def search_custom(return_type="pretty"):
    pacman_data = subprocess.run(["pacman", "-Qm"], capture_output=True, text=True)
    packages = []
    for line in pacman_data.stdout.split("\n"):
        if line:
            packages.append({
                    "Name": line.split()[0],
                    "Version": line.split()[1],
                })
            
    if return_type == "raw":
        return pacman_data.stdout
    elif return_type == "pretty":
        return packages
    else:
        print("Invalid return type. Use 'raw' or 'pretty'.")

def find_upgrades():
    subprocess.run(["pacman", "-Sy"])
    pacman_data = subprocess.run(["pacman", "-Qu"], capture_output=True, text=True)
    packages = []
    for line in pacman_data.stdout.split("\n"):
        if line:
            packages.append({
                    "Name": line.split()[0],
                    "Version": line.split("-> ")[1],
                    "Repo": "local",
                    "Description": "No description available for local packages."
                })
    return packages