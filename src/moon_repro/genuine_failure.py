import sys

import rich_click as click


@click.command(help="Exit 1, a code no allow-list names.")
def cli() -> None:
    click.echo("genuine-failure exiting with code 1", err=True)
    sys.exit(1)
