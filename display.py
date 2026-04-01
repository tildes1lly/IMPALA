import rich
from rich import print
from rich.table import Table

def pkgtable(packages):
    # fuck this is so scuffed but it works and i dont care enough to make it better
    table = Table(title=f"Found {len(packages)} Packages", box=rich.box.DOUBLE_EDGE)
    table.add_column("#", style="yellow", justify="center")
    table.add_column("Repo", style="magenta", justify="center")
    table.add_column("Name", style="cyan", justify="center")
    table.add_column("Version", style="green", justify="center")
    table.add_column("Description", style="white", no_wrap=True, max_width=75, justify="center")

    for  index, package in enumerate(packages):
        table.add_row(str(index + 1), package["Repo"], package["Name"], package["Version"], package["Description"])
    print(table)