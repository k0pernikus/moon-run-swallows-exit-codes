import sys

import rich_click as click

from moon_repro.signals import TOLERATED_CODES
from moon_repro.trailing_command import PASS_THROUGH, command_argument, exit_code_of


@click.command(
    context_settings=PASS_THROUGH,
    help="""Run COMMAND and exit 0 iff its exit code is a tolerated code (the even codes from 66 to 78), \
simulating GitLab's allow_failure: exit_codes; any other code passes through.""",
)
@command_argument
def cli(command: tuple[str, ...]) -> None:
    code = exit_code_of(command)
    click.echo(f"observed exit code {code}", err=True)
    if code not in TOLERATED_CODES:
        sys.exit(code)

    click.echo(f"exit code {code} is allowed to fail", err=True)
    sys.exit(0)
