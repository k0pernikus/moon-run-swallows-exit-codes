# moon run swallows a task's exit code

`moon run <task>` returns exit code `1` for any task failure — the task's real exit code is
discarded. A CI allow-list keyed on the real code (e.g. GitLab `allow_failure: exit_codes`) is
therefore defeated: the code it would match never reaches CI.

## Reproduce

`fail.sh` exits with a random code from `70`, `80`, `90`. The task wraps it; the `via-moon` CI job
allow-lists all three. moon collapses every one to `1`, so the allow-list never matches and the job
fails red instead of passing.

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

GitHub Actions has no GitLab-style `allow_failure: exit_codes`, so `allowed-to-fail.sh` simulates
it: it runs the given command and exits `0` iff the command's exit code is `70`/`80`/`90`,
propagating any other code. `.github/workflows/repro.yml` feeds both invocation styles through it,
as parallel jobs:

- `direct` runs `./fail.sh` straight — the real code reaches the allow-list and matches; the job
  is green.
- `via-moon` runs the same script through `moon run` — moon collapses the code to `1`, the
  allow-list never matches; the job is red. The log still shows the real code in moon's
  `Process ./fail.sh failed: exit code <N>` line, right above the wrapper's `observed exit code 1`.

Same allow-list on both jobs; the only variable is the moon wrapper. The workflow run as a whole
stays red on purpose — the red `via-moon` job IS the bug signal.

## Layout

- `fail.sh` — exits a random `70`/`80`/`90`.
- `allowed-to-fail.sh` — runs a command, exits `0` iff its code is allow-listed (`70`/`80`/`90`).
- `moon.yml`, `.moon/` — the `demo:fail-with-random-allowed-to-fail-codes` task wrapping it.
- `mise.toml` — pins moon `2.4.2`.
- `.github/workflows/repro.yml` — the `direct` (green) and `via-moon` (red) jobs.
