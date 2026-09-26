import sys

import rich_click as click

from moon_repro.signals import finished_marker


@click.command(help="Exit 0 iff every named task wrote its .NAME-finished marker.")
@click.argument("names", nargs=-1, required=True)
def cli(names: tuple[str, ...]) -> None:
    missing = [name for name in names if not finished_marker(name).is_file()]
    if not missing:
        sys.exit(0)

    for name in missing:
        click.echo(f"{name} did not run to completion", err=True)
    sys.exit(1)
