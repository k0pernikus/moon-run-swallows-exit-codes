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

## Multiple tasks still collapse, and stop each other

moon 2.5.5 propagates a task's code only when `moon run` names exactly one fully qualified target
([`exec.rs` after #2618](https://github.com/moonrepo/moon/blob/7a7d3e8d5aff5a15ed89b52c64a13c0ff161ea4d/crates/app/src/commands/exec.rs)).
With two targets, or an unqualified one such as `moon run :test`, any failure exits `1`. moon also stops the whole run
at the first failed task and kills the tasks still running.

`slow-pass.sh` sleeps 5 seconds, then writes `.slow-pass-finished` and exits `0`. Run it beside the allowed-code task:

```
$ moon run demo:fail-with-random-allowed-to-fail-codes demo:slow-pass; echo "exit: $?"
  × Task demo:fail-with-random-allowed-to-fail-codes failed to run.
  ╰─▶ Process ./fail.sh failed: exit code 90
exit: 1

$ test -f .slow-pass-finished; echo "exit: $?"
exit: 1
```

The allowed code never reaches CI, and `slow-pass` never finishes. Measured locally, two runs: moon exited `1` both
times and `.slow-pass-finished` was absent both times.

`allowFailure: true` stops the kill, but it maps every failure to `0`:

```
$ moon run demo:allow-failure-random-allowed-code demo:slow-pass; echo "exit: $?"
exit: 0

$ moon run demo:allow-failure-genuine-failure demo:slow-pass; echo "exit: $?"
exit: 0
```

The allowed code disappears, so CI cannot mark the job as a warning. A genuine failure (`genuine-failure.sh` exits `1`)
disappears as well, so CI marks it as a pass.

Two more jobs cover this:

- `via-moon-multiple-tasks` runs the two tasks through the allow-list and then asserts that `slow-pass` finished. It
  stays red until moon can be told which codes are allowed failures, so that a run covering several tasks keeps going
  past them and still exits a code CI can allow-list.
- `via-moon-allow-failure` uses `expect-exit-code.sh` to assert that `allowFailure` exits `0` for an allowed code and
  for a genuine failure alike. It passes, documenting why `allowFailure` cannot express the need.

## Layout

- `fail.sh` — exits a random `70`/`80`/`90`.
- `slow-pass.sh` — sleeps 5 seconds, writes `.slow-pass-finished`, exits `0`.
- `genuine-failure.sh` — exits `1`, a code no allow-list names.
- `allowed-to-fail.sh` — runs a command, exits `0` iff its code is allow-listed (`70`/`80`/`90`).
- `expect-exit-code.sh` — runs a command, exits `0` iff its code equals the expected one.
- `moon.yml`, `.moon/` — the `demo:*` tasks wrapping those scripts, two of them with `allowFailure: true`.
- `mise.toml` — pins moon `2.5.5`.
- `.github/workflows/repro.yml` — the `direct`, `via-moon`, `via-moon-reported`, `via-moon-multiple-tasks` and
  `via-moon-allow-failure` jobs.
