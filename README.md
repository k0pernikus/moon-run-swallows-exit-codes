# moon run swallows a task's exit code

`moon run <task>` returns exit code `1` for any task failure — the task's real exit code is
discarded. A CI allow-list keyed on the real code (e.g. GitLab `allow_failure: exit_codes`) is
therefore defeated: the code it would match never reaches CI.

## Reproduce

`fail.sh` exits with a random code from `70`, `80`, `90`. The task wraps it; the CI job allow-lists
all three. moon collapses every one to `1`, so the allow-list never matches and the job fails red
instead of passing.

```
$ mise install                 # installs the pinned moon 2.4.2
$ ./fail.sh; echo "exit: $?"
fail.sh exiting with code 80
exit: 80

$ moon run demo:fail-with-random-allowed-to-fail-codes; echo "exit: $?"
  × Task demo:fail-with-random-allowed-to-fail-codes failed to run.
  ╰─▶ Process ./fail.sh failed: exit code 80
exit: 1
```

Run directly, the script returns its real code (`70`/`80`/`90`); through `moon run` it is always
`1`.

## The CI signal

`.github/workflows/repro.yml` allow-lists `70/80/90` and fails on any other code. Because moon
returns `1`, the job is **red while the bug is present**; if moon propagated the real code it would
match the allow-list and the job would pass — so a future green run means the bug is fixed.

## Layout

- `fail.sh` — exits a random `70`/`80`/`90`.
- `moon.yml`, `.moon/` — the `demo:fail-with-random-allowed-to-fail-codes` task wrapping it.
- `mise.toml` — pins moon `2.4.2`.
- `.github/workflows/repro.yml` — the red-on-bug CI signal.
