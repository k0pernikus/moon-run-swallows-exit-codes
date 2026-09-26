import subprocess

import rich_click as click

PASS_THROUGH = {
    "ignore_unknown_options": True,
    "allow_interspersed_args": False,
}

command_argument = click.argument("command", nargs=-1, required=True, type=click.UNPROCESSED)


def exit_code_of(command: tuple[str, ...]) -> int:
    return subprocess.run(command, check=False).returncode
