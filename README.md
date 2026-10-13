# appblocker

> Block specific applications on a schedule — a small root daemon that reads the clock,
> matches processes, and closes them. No cron to babysit, no GUI, no build step.

![Linux](https://img.shields.io/badge/OS-Linux-informational)
![systemd](https://img.shields.io/badge/init-systemd-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

> **Status:** building in public — this first push is the documentation layer. The
> `modules/` and `scripts/` trees land in the next commits.

## Problem it solves

`cron` can kill an app, but only *after* it opened — the user relaunches it a second later.
Renaming the binary breaks a naive `pgrep` match. A Flatpak app has no binary in `$PATH` at
all. And a schedule that only blocks "today" forgets that a window starting at 20:00 ends
**tomorrow**.

`appblocker` answers all three: it matches processes by **cgroup** (immune to renames, and
Flatpak-aware), it supports windows that **cross midnight**, and it runs under `systemd` as
root so the schedule survives reboots and logouts.

It is a **self-control** tool, not a security boundary: the honest promise is *deliberate,
reverted and audited* — not "unbreakable".

## How it works

| # | Layer | What it does | Module |
|---|-------|--------------|--------|
| 0 | Base | Single global config (`config.toml`) | `00-base` |
| 1 | Policy | Which app, which days, which windows | `01-policy` |
| 2 | Daemon | Loop: read clock → match `/proc` → terminate; plus its systemd unit | `02-daemon` |
| 3 | CLI | `appblocker status / windows / check / test / reload` | `03-cli` |

One pass of the daemon:

```text
clock ─▶ in window? ─▶ match /proc (cgroup) ─▶ SIGTERM ─▶ SIGKILL
```

Diagrams: [enforcement flow](docs/diagrams/enforcement-flow.md) ·
[schedule lifecycle](docs/diagrams/schedule-lifecycle.md).

## Quickstart

```bash
git clone https://github.com/ails-w/appblocker.git
cd appblocker
sudo scripts/install.sh --dry-run   # see the plan
sudo scripts/install.sh             # install config, daemon and unit
sudo scripts/verify.sh              # check the daemon, config and matchers
```

Then edit `/etc/appblocker/policy.d/10-stremio.toml` with **your** targets and windows:

```bash
sudo appblocker reload     # daemon reloads the policy and keeps running
appblocker status          # current state + active windows
```

> **Not yet in the repo:** `modules/`, `scripts/` and the daemon source are the next
> commits. Until then this Quickstart is the target, not something you can run.

## What I learned / Key decisions

- **Match by cgroup, not by name.** A Flatpak app runs inside
  `app-flatpak-<id>.scope`; matching that substring is rename-proof and needs no `$PATH`
  entry. Name matching breaks the moment the binary is renamed.
- **Kill the whole scope, not the PID.** Stremio is a single process, but Steam is a tree
  (`reaper` → `proton` → game). Terminating the process set closes the leaves too.
- **Cross-midnight windows are a first-class case.** A `20:00 → 02:00` window selected on
  Friday must fire on Saturday. The scheduler checks "today's start" **and** "yesterday's
  tail", or the tail silently disappears.
- **`Restart=always` is not enough.** `systemctl stop` is an *intentional* stop and systemd
  will not restart it — so on-behalf-of friction comes from root-owned config, not from the
  restart policy alone.
- **Root is a hard limit.** Anyone with `sudo` (or the `docker` group, or physical access)
  can disarm it. Full list: [`docs/threat-model.md`](docs/threat-model.md).

## Known limitations

- **Not a wall against root**, `NOPASSWD`, or powerful groups (`docker` ≈ root).
- **Physical access / live USB / rescue boot** bypasses everything.
- **System clock changes** affect the window check.
- **MVP closes apps, it does not deny `exec`.** A blocked app can open and be closed
  within one polling interval. Kernel-level denial (`fanotify`) is a future option.
- **One policy per machine** in this version.

## Documentation

| Area | Document |
|------|----------|
| How the layers fit together | [`docs/architecture.md`](docs/architecture.md) |
| What it protects — and what it does not | [`docs/threat-model.md`](docs/threat-model.md) |
| Install order | [`docs/install.md`](docs/install.md) |
| How to verify | [`docs/verification.md`](docs/verification.md) |
| Something broke | [`docs/troubleshooting.md`](docs/troubleshooting.md) |
| Common questions | [`docs/faq.md`](docs/faq.md) |
| Concepts, section by section | [`docs/learning/`](docs/learning/) |
| Diagrams | [`docs/diagrams/`](docs/diagrams/) |

## Repository layout

```text
modules/   one self-contained capability per module (files + apply/verify/rollback README)
docs/      architecture, threat model, install, verification, learning, diagrams
scripts/   install / uninstall / verify helpers
```

> **Mirror rule:** each module keeps its files under `modules/NN-name/files/<target path>`.
> The path inside the repo **is** the path on the filesystem, so `install` copies one to the
> other and nothing is ever retyped by hand.

## License

MIT — see [LICENSE](LICENSE).
