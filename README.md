# moon run swallows a task's exit code

Up to moon 2.4.x, `moon run <task>` returned exit code `1` for any task failure and discarded the task's real exit
code. A CI allow-list keyed on the real code (e.g. GitLab `allow_failure: exit_codes`) was therefore defeated: the
code it would match never reached CI.

Reported as [moonrepo/moon#2615](https://github.com/moonrepo/moon/issues/2615) and fixed by
[moonrepo/moon#2618](https://github.com/moonrepo/moon/pull/2618) for a single task. A run covering several tasks
still collapses the code and stops the other tasks, reported as
[moonrepo/moon#2728](https://github.com/moonrepo/moon/issues/2728).

## Setup

moon `2.5.5` and uv are pinned in `mise.toml`. The tasks and the CI checks are Python console scripts in
`src/moon_repro/`, installed into the project's `.venv`:

```
$ mise install
$ uv sync --locked
```

## One task: fixed in moon 2.5.x

`random-tolerated-code` exits a random tolerated code of the bitmap described [below](#tolerated-codes-as-a-bitmap):
one of the seven even codes from `66` to `78`.

```
$ moon run demo:random-tolerated-code; echo "exit: $?"
random-tolerated-code exiting with code 68

task_runner::run_failed

  × Task demo:random-tolerated-code failed to run.
  ╰─▶ Process uv failed: exit code 68
exit: 68

$ mise exec aqua:moonrepo/moon@2.4.2 -- moon run demo:random-tolerated-code; echo "exit: $?"
random-tolerated-code exiting with code 74
Error: task_runner::run_failed

  × Task demo:random-tolerated-code failed to run.
  ╰─▶ Process uv failed: exit code 74
exit: 1
```

GitHub Actions has no GitLab-style `allow_failure: exit_codes`, so `allowed-to-fail` simulates it: it runs the given
command and exits `0` iff the command's exit code is one of the tolerated codes, passing any other code through. Three
jobs cover the single task:

- `direct` runs `random-tolerated-code` straight through the allow-list; the job passes.
- `via-moon` runs it through `moon run` on the pinned 2.5.5; moon passes the code through, and the job passes.
- `via-moon-reported` runs it through moon 2.4.2 and asserts with `expect-exit-code` that moon exits `1`, documenting
  the reported behavior without leaving the run red.

## Several tasks: still collapsed, and stopped at the first failure

moon 2.5.5 passes a task's code through only when `moon run` names exactly one fully qualified target
([`exec.rs` after #2618](https://github.com/moonrepo/moon/blob/7a7d3e8d5aff5a15ed89b52c64a13c0ff161ea4d/crates/app/src/commands/exec.rs#L288-L323)).
With two targets, or an unqualified one such as `moon run :test`, any failure exits `1`. moon also stops the whole run
at the first failed task and kills the tasks still running.

### Tolerated codes as a bitmap

The several-task case uses the exit codes a real test task reports: a bitmap of what a passing run tolerated.

| bit | value | meaning                                              |
|:----|:------|:-----------------------------------------------------|
| 0   | 1     | reserved: `1` is the error exit code, never set here |
| 1   | 2     | a tolerated infrastructure defect                    |
| 2   | 4     | a skipped test                                       |
| 3   | 8     | a test that passed only on a retry                   |

A run where everything passed on its first try exits `0`, and a run that hits an error exits `1`. A passing run that
tolerated something exits `64 | <bits>`. The `64` keeps every tolerated code clear of the test runner's own codes `0`
to `5`, and bit 0 stays unset, so every tolerated code is even. With these three bits the tolerated codes are the seven
even codes from `66` to `78`, and a CI allow-list names exactly those.

`signal-task exit <name> <bit> <seconds>` sleeps, writes `.<name>-finished` and exits `64 | <bit>`. Three tasks use
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
  ╰─▶ Process uv failed: exit code 68
exit: 68
```

### Wanted

Run together, all three tasks run to completion, and moon exits the bitwise OR of their codes, so every bit any task
set reaches CI:

```
$ moon run demo:tolerated-defect demo:skipped demo:retried; echo "exit: $?"
exit: 78

$ uv run --no-sync expect-finished tolerated-defect skipped retried; echo "exit: $?"
exit: 0
```

`64 | 2 | 4 | 8 = 78`, binary `1001110`: the defect, the skip and the retry are all visible in the one code. A task
exiting a code the allow-list does not name still stops the run, kills the other tasks and exits `1`, exactly as today.

### Actual

```
$ moon run demo:tolerated-defect demo:skipped demo:retried; echo "exit: $?"
▮▮▮▮ demo:tolerated-defect (1s 63ms, 06e95660)
▮▮▮▮ demo:retried (1s 67ms, f37c8651)
▮▮▮▮ demo:skipped (1s 65ms, bd67d0d0)
demo:tolerated-defect | tolerated-defect finished after 1s, exiting 64 | 2 = 66

task_runner::run_failed

  × Task demo:tolerated-defect failed to run.
  ╰─▶ Process uv failed: exit code 66
exit: 1

$ uv run --no-sync expect-finished tolerated-defect skipped retried; echo "exit: $?"
skipped did not run to completion
retried did not run to completion
exit: 1
```

moon exits `1` as soon as `tolerated-defect` exits `66`, and kills `skipped` and `retried` after one second, before
they finish. No tolerated code reaches CI, and neither does the skip or the retry. Measured locally with moon 2.5.5,
two runs: moon exited `1` both times, and only `.tolerated-defect-finished` existed afterwards.

`allowFailure: true` stops the kill, but it maps every failure to `0`:

```
$ moon run demo:tolerated-defect-allow-failure demo:skipped-allow-failure demo:retried-allow-failure; echo "exit: $?"
exit: 0

$ moon run demo:allow-failure-genuine-failure demo:tolerated-defect-allow-failure; echo "exit: $?"
exit: 0
```

All three tasks run to completion, but the OR disappears, so CI cannot mark the job as a warning. A genuine failure
(`genuine-failure` exits `1`) disappears as well, so CI marks it as a pass.

### Workaround

Until moon can combine tolerated codes, the tasks must not exit them. `signal-task record <name> <bit> <seconds>`
writes its bit to `.<name>-signal` and exits `0`, so moon runs every task to completion and exits `0`. A separate step
after moon, `fold-recorded-signals`, reads every recorded bit and exits `64 | <OR>`, which CI then matches against its
allow-list:

```
$ moon run demo:tolerated-defect-recorded demo:skipped-recorded demo:retried-recorded; echo "exit: $?"
demo:tolerated-defect-recorded | tolerated-defect finished after 1s, recorded signal 2 in .tolerated-defect-signal
         demo:skipped-recorded | skipped finished after 3s, recorded signal 4 in .skipped-signal
         demo:retried-recorded | retried finished after 5s, recorded signal 8 in .retried-signal
exit: 0

$ uv run --no-sync fold-recorded-signals; echo "exit: $?"
fold-recorded-signals: 3 recorded signal(s), OR = 14, exiting 78
exit: 78
```

A genuine failure still fails: it stops the run at the moon step, so CI never reaches the gate.

```
$ moon run demo:genuine-failure demo:skipped-recorded; echo "exit: $?"
 demo:genuine-failure | genuine-failure exiting with code 1

task_runner::run_failed

  × Task demo:genuine-failure failed to run.
  ╰─▶ Process uv failed: exit code 1
exit: 1
```

It costs a second step after every moon invocation, and every task needs a mode in which it records instead of
exiting.

### Jobs

- `via-moon-each-task` asserts that each signal task alone exits its own code through moon: `66`, `68` and `72`. It
  passes.
- `via-moon-multiple-tasks` asserts that the three tasks together exit `78` and that all three ran to completion. It
  stays red until moon can be told which codes are tolerated and to combine them with a bitwise OR.
- `via-moon-allow-failure` asserts that `allowFailure` exits `0` for the three tolerated codes and for a genuine failure
  alike, while every task runs to completion. It passes, documenting why `allowFailure` cannot express the need.
- `via-moon-workaround` asserts that the recording tasks run to completion with moon exiting `0`, that the gate exits
  `78`, and that a genuine failure still exits `1`. It passes.

## Layout

- `src/moon_repro/` — one module per task or check, each a rich-click command exposed as a console script:
    - `random_tolerated_code.py` — exits a random tolerated code, one of the even codes from `66` to `78`.
    - `genuine_failure.py` — exits `1`, a code no allow-list names.
    - `signal_task.py` — sleeps, writes `.<name>-finished`, then exits `64 | <bit>` or records the bit and exits `0`.
    - `fold_recorded_signals.py` — the workaround's gate: exits `64 | <OR>` of the recorded bits.
    - `allowed_to_fail.py` — runs a command, exits `0` iff its code is a tolerated code.
    - `expect_exit_code.py` — runs a command, exits `0` iff its code equals the expected one.
    - `expect_finished.py` — exits `0` iff every named task wrote its `.<name>-finished` marker.
    - `signals.py`, `trailing_command.py` — the signal bits, the tolerated codes derived from them, the marker names and
      the pass-through command argument, shared by the modules above.
- `moon.yml`, `.moon/` — the `demo:*` tasks; the `*-allow-failure` tasks set `allowFailure: true`, the `*-recorded`
  tasks run the workaround's recording mode.
- `mise.toml`, `mise.lock` — pin moon `2.5.5` and uv.
- `pyproject.toml`, `uv.lock` — the console scripts and their one dependency, rich-click.
- `.github/actions/setup/` — installs the pinned tools, syncs the project and puts its scripts on `PATH`.
- `.github/workflows/repro.yml` — the jobs above.
