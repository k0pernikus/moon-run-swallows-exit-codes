# moon run swallows a task's exit code

`moon run <task>` returns exit code `1` for any task failure — the task's real exit code is
discarded.

## Reproduce

```
$ mise install                 # installs the pinned moon 2.4.2
$ ./fail.sh; echo "exit: $?"
exit: 42

$ moon run demo:fail; echo "exit: $?"
  × Task demo:fail failed to run.
  ╰─▶ Process ./fail.sh failed: exit code 42
exit: 1
```

The task exits `42`; run directly it returns `42`; through `moon run` it returns `1`. moon's own
diagnostic prints the real code, yet the process exit is `1`.

## Why it matters

A CI system selects a job status from the exit code — for example GitLab
`allow_failure: exit_codes: [N]` marks a job "passed with warnings" on exactly code `N`. A task
runner wrapping the command must propagate that code; because `moon run` collapses every failure to
`1`, a specific code cannot be distinguished from a generic failure.

## Layout

- `fail.sh` — exits `42`.
- `moon.yml`, `.moon/` — a `demo:fail` task wrapping it.
- `mise.toml` — pins moon `2.4.2`.
