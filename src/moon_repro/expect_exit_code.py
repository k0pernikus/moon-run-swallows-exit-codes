import sys

import rich_click as click

from moon_repro.trailing_command import PASS_THROUGH, command_argument, exit_code_of


@click.command(context_settings=PASS_THROUGH, help="Run COMMAND and exit 0 iff its exit code is EXPECTED.")
@click.argument("expected", type=int)
@command_argument
def cli(expected: int, command: tuple[str, ...]) -> None:
    code = exit_code_of(command)
    click.echo(f"observed exit code {code}, expected {expected}", err=True)
    if code != expected:
        sys.exit(1)

    sys.exit(0)
