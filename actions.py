import subprocess
import pacman
import aur
import display 
import os
import glob
import re
from rich import print

def install_aur(pkg, skip_print=False):
    if not skip_print:
        print(f"\\[impala] [bold]Installing {pkg['Name']} from AUR...[/bold]")
    if subprocess.run(["sudo", "-u", os.environ.get("SUDO_USER"), "git", "clone", f"https://aur.archlinux.org/{pkg['Name']}.git"], cwd="/tmp/impala").returncode != 0:
        subprocess.run(["rm", "-rf", f"/tmp/impala/{pkg['Name']}"])
        if subprocess.run(["sudo", "-u", os.environ.get("SUDO_USER"), "git", "clone", f"https://aur.archlinux.org/{pkg['Name']}.git"], cwd="/tmp/impala").returncode != 0:
            print(f"\\[impala] [bold red]Failed to clone {pkg['Name']} from AUR. Please check your network connection and try installing manually.[/bold red]")
            return False
        
    pkgdeps = []
    srcinfo = subprocess.run(["sudo", "-u", os.environ.get("SUDO_USER"), "makepkg", "--printsrcinfo"], cwd=f"/tmp/impala/{pkg['Name']}", capture_output=True, text=True).stdout
    for line in srcinfo.split("\n"):
        if line.strip().startswith("makedepends =") or line.strip().startswith("depends ="):
            pkgdeps.append(line.split("=", 1)[1].strip())

    needed_deps = subprocess.run(["pacman", "-T", *pkgdeps], capture_output=True, text=True).stdout.split()

    for dep in needed_deps:
        if subprocess.run(["pacman", "-Sp", re.split(r'[><=]', dep)[0]], capture_output=True, text=True).stdout:
            print(f"\\[impala] [bold]Installing dependency {dep} from (pacman.conf)...[/bold]")
            if subprocess.run(["pacman", "-S", re.split(r'[><=]', dep)[0], "--noconfirm"]).returncode != 0:
                print(f"\\[impala] [bold red]Failed to install dependency {dep} from (pacman.conf). Attempting to install from AUR...[/bold red]")
                dep_results = aur.search([re.split(r'[><=]', dep)[0]])
                if dep_results:
                    for _dep in dep_results:
                        if _dep["Name"] == re.split(r'[><=]', dep)[0]:
                            install_aur(_dep, skip_print=True)
                            break
                else:
                    print(f"\\[impala] [bold red]Failed to install dependency {dep} from (pacman.conf) and AUR. Installation may fail.[/bold red]")
        else:
            print(f"\\[impala] [bold]Dependency {dep} not found in (pacman.conf). Attempting to install from AUR...[/bold]")
            dep_results = aur.search([re.split(r'[><=]', dep)[0]])
            if dep_results:
                for _dep in dep_results:
                    if _dep["Name"] == re.split(r'[><=]', dep)[0]:
                        install_aur(_dep, skip_print=True)
                        break
            else:
                print(f"\\[impala] [bold red]Failed to find dependency {dep} in both (pacman.conf) and AUR. Installation may fail.[/bold red]")

    if subprocess.run(["sudo", "-u", os.environ.get("SUDO_USER"), "makepkg"], cwd=f"/tmp/impala/{pkg['Name']}").returncode == 0:
        print(f"\\[impala] [bold green]Successfully built {pkg['Name']} from AUR! Installing...[/bold green]")
    else:
        print(f"\\[impala] [bold red]Failed to build {pkg['Name']} from AUR. Please check the PKGBUILD and try installing manually.[/bold red]")
        subprocess.run(["rm", "-rf", f"/tmp/impala/{pkg['Name']}"])
        return False
    pkg_files = glob.glob(f"/tmp/impala/{pkg['Name']}/*.pkg.tar*")
    if pkg_files:
        if subprocess.run(["pacman", "-U"] + pkg_files + ["--noconfirm"]).returncode != 0:
            print(f"\\[impala] [bold red]Failed to install {pkg['Name']} from AUR. Please check the PKGBUILD and try installing manually.[/bold red]")
            subprocess.run(["rm", "-rf", f"/tmp/impala/{pkg['Name']}"])
            return False
        else:
            print(f"\\[impala] [bold green]Successfully installed {pkg['Name']} from AUR![/bold green]")
            subprocess.run(["rm", "-rf", f"/tmp/impala/{pkg['Name']}"])
            return True
    else:
        print(f"\\[impala] [bold red]Failed to find built package for {pkg['Name']}. Installation may have failed.[/bold red]")
        subprocess.run(["rm", "-rf", f"/tmp/impala/{pkg['Name']}"])
        return False

def install_pacman(pkg):
    print(f"\\[impala] [bold]Installing {pkg['Name']} from (pacman.conf) [{pkg['Repo']}...[/bold]")
    if subprocess.run(["pacman", "-S", pkg["Name"], "--noconfirm"]).returncode == 0:
        print(f"\\[impala] [bold green]Successfully installed {pkg['Name']} from (pacman.conf)![/bold green]")
        return True
    else:
        print(f"\\[impala] [bold red]Failed to install {pkg['Name']} from (pacman.conf). Please check your package database and try installing manually.[/bold red]")
        return False

def remove(pkg):
    if subprocess.run(["pacman", "-Rs", pkg["Name"], "--noconfirm"]).returncode == 0:
        print(f"\\[impala] [bold green]Successfully removed {pkg['Name']}![/bold green]")
        return True
    else:
        print(f"\\[impala] [bold red]Failed to remove {pkg['Name']}. Please check your package database and try removing manually.[/bold red]")
        return False

def find_upgrades():
    custom_packages = pacman.search_custom()
    aur_updates = []
    if custom_packages:
        for pkg in custom_packages:
            results = aur.search(pkg["Name"])
            if len(results) > 0:
                found = False
                for result in results:
                    if result["Name"] == pkg["Name"]:
                        found = True
                        if result["Version"] != pkg["Version"]:
                            print(f"\\[impala] [bold green]{pkg['Name']}[/bold green] is out of date with version \\[impala] [bold green]{result['Version']}[/bold green] available...")
                            aur_updates.append(result)
                            break
                        else:
                            print(f"\\[impala] [bold green]{pkg['Name']}[/bold green] is up to date with version \\[impala] [bold green]{pkg['Version']}[/bold green]. Skipping...")
                            break
                if not found:
                    print(f"\\[impala] [green]{pkg['Name']}[/green] from [cyan italic]an unknown source[/cyan italic] has no AUR version available. This package will not receive updates through IMPALA.")
            else:
                print(f"\\[impala] [green]{pkg['Name']}[/green] from [cyan italic]an unknown source[/cyan italic] has no AUR version available. This package will not receive updates through IMPALA.")
    else:
        print(f"\\[impala] [bold green]No AUR/custom packages found. Proceeding with upgrade...[/bold green]")
    
    return aur_updates

def upgrade(aur_updates):
    subprocess.run(["pacman", "-Syu", "--noconfirm"])
    failed_upgrades = []
    for pkg in aur_updates:
        print(f"\\[impala] [bold]Upgrading {pkg['Name']} from AUR...[/bold]")
        if not install_aur(pkg, skip_print=True):
            failed_upgrades.append(pkg)
    return failed_upgrades