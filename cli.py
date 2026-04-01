import aur 
import pacman
import actions
import display

import questionary
import httpx as hx # unironically httpx is so similar to https that it's efficient to just import it as hx instead lmao
import os
import sys
from rich import print
def main():
    if os.geteuid() != 0:
        print("\\[impala] [bold]IMPALA requires root privileges to run. Please run as root or with sudo.[/bold]")
        sys.exit(1)

    os.makedirs("/tmp/impala", exist_ok=True)

    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    flags = [arg for arg in sys.argv[1:] if arg.startswith("-")]

    if not args:
        print("\\[impala] [bold]No command provided. Use 'impala help' for usage information.[/bold]")
        sys.exit(1)

    if args[0] == "help":
        print("Usage: impala <[install, remove, upgrade, help, whatever else i decided to put (update this later)]>, <package name>")
        print("Example: impala install firefox")
        sys.exit(0)

    elif args[0] == "install":
        if len(args) < 2:
            print("\\[impala] [bold]Nothing provided to search for. Use 'impala help' for usage information.[/bold]")
            sys.exit(1)

        try:
            aur_results = aur.search(args[1:])
            pacman_results = pacman.search_repos(args[1:])

        except hx.RequestError:
            print(f"\\[impala] [bold red]Error occurred while searching for packages. This is most likely a network issue causing the AUR to become unreachable. If the issue persists, check your internet connection and run `ping aur.archlinux.org` to test for downtime.[/bold red]")
            sys.exit(1)

        if not aur_results and not pacman_results:
            print(f"\\[impala] [bold red]No packages found matching [/bold red][green]'{args[1:]}'[/green][bold red]. Try a less specific query? (example: [/bold red][green]'jdk8' -> 'jdk'[/green][bold red] and select the correct one.)[/bold red]")
            sys.exit(0)

        global_results = sorted(aur_results + pacman_results, key=lambda x: x["Name"])

        display.pkgtable(global_results)

        pkgs = questionary.text("Package(s) to install (#): ").ask()
        if not pkgs or not pkgs.split():
            print("\\[impala] [bold]No packages selected. Installation cancelled.[/bold]")
            sys.exit(0)

        valid_pkgs = []
        for pkg in pkgs.split():
            if pkg.isdigit() and 0 < int(pkg) <= len(global_results):
                valid_pkgs.append(pkg)
            else:
                print(f"\\[impala] [bold red]Invalid input: {pkg}. Please enter a valid package number. Other packages will still be processed.[/bold red]")
        
        if not valid_pkgs:
            print("\\[impala] [bold]No valid packages selected. Installation cancelled.[/bold]")
            sys.exit(0)

        print(f"[bold white]Selected packages to install:[/bold white]")
                
        for index, pkg in enumerate(valid_pkgs):
            if global_results[int(pkg) - 1]['Repo'] == "[AUR]":
                print(f"[bold yellow]({index + 1})[/bold yellow] [green]{global_results[int(pkg) - 1]['Name']}[/green] from [cyan italic]{global_results[int(pkg) - 1]['Repo']}[/cyan italic]")
            else:
                print(f"[bold yellow]({index + 1})[/bold yellow] [green]{global_results[int(pkg) - 1]['Name']}[/green] from [bold](pacman.conf)[/bold] [cyan italic]{global_results[int(pkg) - 1]['Repo']}[/cyan italic]")

        if not questionary.confirm("Proceed with installation?").ask():
            print("\\[impala] [bold]Installation cancelled.[/bold]")
            sys.exit(0)
        failed_installs = []
        for pkg in valid_pkgs:
            if global_results[int(pkg) - 1]['Repo'] == "[AUR]":
                if not actions.install_aur(global_results[int(pkg) - 1]):
                    failed_installs.append(global_results[int(pkg) - 1])
            else:
                if not actions.install_pacman(global_results[int(pkg) - 1]):
                    failed_installs.append(global_results[int(pkg) - 1])

        if failed_installs:
            display.pkgtable(failed_installs)
            print(f"\\[impala] [bold red]Failed to install {len(failed_installs)} package(s). Please check the above list and try installing manually. If an AUR package failed, it is likely due to a bad PKGBUILD, consider installing a similar package instead, or contact the maintainers.[/bold red]")

    elif args[0] == "remove":
        if len(args) < 2:
            print("\\[impala] [bold]No package name provided. Use 'impala help' for usage information.[/bold]")
            sys.exit(1)

        installed_results = pacman.search_installed(args[1])
        if not installed_results:
            print(f"\\[impala] [bold red]No installed packages found matching [/bold red][green]'{args[1]}'[/green][bold red]. Try a less specific query? (example: [/bold red][green]'jdk8' -> 'jdk'[/green][bold red] and select the correct one.)[/bold red]")
            sys.exit(0)

        display.pkgtable(installed_results)
        pkgs = questionary.text("Package(s) to remove (#): ").ask()
        valid_pkgs = []
        for pkg in pkgs.split():
            if pkg.isdigit() and 0 < int(pkg) <= len(installed_results):
                valid_pkgs.append(pkg)
            else:
                print(f"\\[impala] [bold red]Invalid input: {pkg}. Please enter a valid package number. Other packages will still be processed.[/bold red]")

        if not valid_pkgs:
            print("\\[impala] [bold]No valid packages selected. Removal cancelled.[/bold]")
            sys.exit(0)

        print(f"[bold white]Selected packages to remove:[/bold white]")

        for index, pkg in enumerate(valid_pkgs):
            print(f"[bold yellow]({index + 1})[/bold yellow] [green]{installed_results[int(pkg) - 1]['Name']}[/green] from [cyan italic]{installed_results[int(pkg) - 1]['Repo']}[/cyan italic]")
        
        if not questionary.confirm("Proceed with removal?").ask():
            print("\\[impala] [bold]Removal cancelled.[/bold]")
            sys.exit(0)

        failed_removals = []
        for pkg in valid_pkgs:
            if not actions.remove(installed_results[int(pkg) - 1]):
                failed_removals.append(installed_results[int(pkg) - 1])

        if failed_removals:
            display.pkgtable(failed_removals)
            print(f"\\[impala] [bold red]Failed to remove {len(failed_removals)} package(s). Please check the above list and try removing manually.[/bold red]")

    elif args[0] == "upgrade" or args[0] == "update":
        aur_updates = actions.find_upgrades()
        pacman_updates = pacman.find_upgrades()
        print(pacman_updates)
        display.pkgtable(aur_updates + pacman_updates)
        if not questionary.confirm("Proceed with upgrade?").ask():
            print("\\[impala] [bold]Upgrade cancelled.[/bold]")
            sys.exit(0)

        failed_upgrades = actions.upgrade(aur_updates)
        if failed_upgrades:
            display.pkgtable(failed_upgrades)
            print(f"\\[impala] [bold red]Failed to upgrade {len(failed_upgrades)} package(s). Please check the above list and try upgrading manually. If an AUR package failed, it is likely due to a bad PKGBUILD, consider installing a similar package instead, or contact the maintainers.[/bold red]")
        else:
            print(f"\\[impala] [bold green]All packages upgraded successfully![/bold green]")
            sys.exit(0)


if __name__ == "__main__":
    main()