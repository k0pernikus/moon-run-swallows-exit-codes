# moon run swallows a task's exit code

Up to moon 2.4.x, `moon run <task>` returned exit code `1` for any task failure and discarded the task's real exit
code. A CI allow-list keyed on the real code (e.g. GitLab `allow_failure: exit_codes`) was therefore defeated: the
code it would match never reached CI.

Reported as [moonrepo/moon#2615](https://github.com/moonrepo/moon/issues/2615) and fixed by
[moonrepo/moon#2618](https://github.com/moonrepo/moon/pull/2618). This repository pins moon `2.5.5`, which
propagates the code, and keeps the reported version `2.4.2` as a second job so the old behavior stays visible.

## Reproduce

`fail.sh` exits with a random code from `70`, `80`, `90`.

```
$ mise install                 # installs the pinned moon 2.5.5
$ ./fail.sh; echo "exit: $?"
fail.sh exiting with code 80
exit: 80

$ moon run demo:fail-with-random-allowed-to-fail-codes; echo "exit: $?"
  × Task demo:fail-with-random-allowed-to-fail-codes failed to run.
  ╰─▶ Process ./fail.sh failed: exit code 80
exit: 80

$ mise exec aqua:moonrepo/moon@2.4.2 -- moon run demo:fail-with-random-allowed-to-fail-codes; echo "exit: $?"
  × Task demo:fail-with-random-allowed-to-fail-codes failed to run.
  ╰─▶ Process ./fail.sh failed: exit code 80
exit: 1
```

Measured locally, three runs each: moon 2.4.2 exited `1` every time, moon 2.5.5 exited `80`, `70` and `90`, the same
codes the script exited with.

## The CI signal

GitHub Actions has no GitLab-style `allow_failure: exit_codes`, so `allowed-to-fail.sh` simulates it: it runs the
given command and exits `0` iff the command's exit code is `70`/`80`/`90`, propagating any other code.
`.github/workflows/repro.yml` runs three jobs:

- `direct` runs `./fail.sh` straight through the allow-list; the real code matches and the job passes.
- `via-moon` runs the same script through `moon run` on the pinned 2.5.5; moon propagates the code, the allow-list
  matches, and the job passes.
- `via-moon-reported` runs it through moon 2.4.2 and uses `expect-exit-code.sh` to assert that moon exits `1`. The job
  passes while the old version still collapses the code, so it documents the reported behavior without leaving the
  run red.

## Layout

- `fail.sh` — exits a random `70`/`80`/`90`.
- `allowed-to-fail.sh` — runs a command, exits `0` iff its code is allow-listed (`70`/`80`/`90`).
- `expect-exit-code.sh` — runs a command, exits `0` iff its code equals the expected one.
- `moon.yml`, `.moon/` — the `demo:fail-with-random-allowed-to-fail-codes` task wrapping it.
- `mise.toml` — pins moon `2.5.5`.
- `.github/workflows/repro.yml` — the `direct`, `via-moon` and `via-moon-reported` jobs.
