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
`.github/workflows/repro.yml` runs three jobs for a single task:

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

### Tolerated codes as a bitmap

The multi-task case uses the exit codes a real test task reports: a bitmap of what a passing run tolerated.

| bit | value | meaning                                              |
|:----|:------|:-----------------------------------------------------|
| 0   | 1     | reserved: `1` is the error exit code, never set here |
| 1   | 2     | a tolerated infrastructure defect                    |
| 2   | 4     | a skipped test                                       |
| 3   | 8     | a test that passed only on a retry                   |

A run where everything passed on its first try exits `0`, and a run that hits an error exits `1`. A passing run that
tolerated something exits `64 | <bits>`. The `64` keeps every tolerated code clear of the test runner's own codes `0`
to `5`, and bit 0 stays unset, so every tolerated code is even and between `66` and `78`. A CI allow-list names exactly
those codes.

`exit-with-signal.sh <name> <bit> <seconds>` sleeps, writes `.<name>-finished` and exits `64 | <bit>`. Three tasks use
it, each setting one bit and finishing at a different time:

| task               | bit | finishes after | exits |
|:-------------------|:----|:---------------|:------|
| `tolerated-defect` | `2` | 1 second       | `66`  |
| `skipped`          | `4` | 3 seconds      | `68`  |
| `retried`          | `8` | 5 seconds      | `72`  |

Each task alone reaches CI unchanged since #2618:

```
$ moon run demo:skipped; echo "exit: $?"
skipped finished after 3s, exiting 64 | 4 = 68

task_runner::run_failed

  × Task demo:skipped failed to run.
  ╰─▶ Process ./exit-with-signal.sh failed: exit code 68
exit: 68
```

### Wanted

Run together, all three tasks run to completion, and moon exits the bitwise OR of their codes, so every bit any task
set reaches CI:

```
$ moon run demo:tolerated-defect demo:skipped demo:retried; echo "exit: $?"
exit: 78

$ ./expect-finished.sh tolerated-defect skipped retried; echo "exit: $?"
exit: 0
```

`64 | 2 | 4 | 8 = 78`, binary `1001110`: the defect, the skip and the retry are all visible in the one code. A task
exiting a code the allow-list does not name still stops the run, kills the other tasks and exits `1`, exactly as today.

### Actual

```
$ moon run demo:tolerated-defect demo:skipped demo:retried; echo "exit: $?"
demo:tolerated-defect | tolerated-defect finished after 1s, exiting 64 | 2 = 66

task_runner::run_failed

  × Task demo:tolerated-defect failed to run.
  ╰─▶ Process ./exit-with-signal.sh failed: exit code 66
exit: 1

$ ./expect-finished.sh tolerated-defect skipped retried; echo "exit: $?"
skipped did not run to completion
retried did not run to completion
exit: 1
```

moon exits `1` as soon as `tolerated-defect` exits `66`, and kills `skipped` and `retried` before they finish. No
tolerated code reaches CI, and neither does the skip or the retry. Measured locally with moon 2.5.5, two runs: moon
exited `1` both times, and only `.tolerated-defect-finished` existed afterwards.

`allowFailure: true` stops the kill, but it maps every failure to `0`:

```
$ moon run demo:tolerated-defect-allow-failure demo:skipped-allow-failure demo:retried-allow-failure; echo "exit: $?"
exit: 0

$ moon run demo:allow-failure-genuine-failure demo:tolerated-defect-allow-failure; echo "exit: $?"
exit: 0
```

All three tasks run to completion, but the OR disappears, so CI cannot mark the job as a warning. A genuine failure
(`genuine-failure.sh` exits `1`) disappears as well, so CI marks it as a pass.

Three more jobs cover this:

- `via-moon-each-task` asserts that each signal task alone exits its own code through moon: `66`, `68` and `72`. It
  passes.
- `via-moon-multiple-tasks` asserts that the three tasks together exit `78` and that all three ran to completion. It
  stays red until moon can be told which codes are tolerated and to combine them with a bitwise OR.
- `via-moon-allow-failure` asserts that `allowFailure` exits `0` for the three tolerated codes and for a genuine failure
  alike, while every task runs to completion. It passes, documenting why `allowFailure` cannot express the need.

## Layout

- `fail.sh` — exits a random `70`/`80`/`90`.
- `exit-with-signal.sh` — sleeps, writes `.<name>-finished`, exits `64 | <bit>`.
- `genuine-failure.sh` — exits `1`, a code no allow-list names.
- `allowed-to-fail.sh` — runs a command, exits `0` iff its code is allow-listed (`70`/`80`/`90`).
- `expect-exit-code.sh` — runs a command, exits `0` iff its code equals the expected one.
- `expect-finished.sh` — exits `0` iff every named task wrote its `.<name>-finished` marker.
- `moon.yml`, `.moon/` — the `demo:*` tasks wrapping those scripts; the `*-allow-failure` tasks set
  `allowFailure: true`.
- `mise.toml` — pins moon `2.5.5`.
- `.github/workflows/repro.yml` — the `direct`, `via-moon`, `via-moon-reported`, `via-moon-each-task`,
  `via-moon-multiple-tasks` and `via-moon-allow-failure` jobs.
