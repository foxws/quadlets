---
name: add-app
description: Add a new application or service to this repository as Podman Quadlets with a pods.yml manifest. Use when the user says "add X", "package X", or "make a quadlet for X".
argument-hint: <name>
---

# Add application: $ARGUMENTS

Follow the conventions in AGENTS.md. They win over anything general you know about Quadlet. Load the `quadlet` skill for how the keys behave, and run its review checklist before step 4.

## 1. Decide the shape

- **Service** (database, cache, search, mail catcher): `development/` and `production/` sources, like `mariadb/`. Mailpit-like dev tools get only `development/`.
- **Homelab application**: units in `$ARGUMENTS/` itself, like `jellyfin/` (one container) or `immich/` (a `.pod` with several containers).

Read the closest existing application before writing anything, and copy its structure.

## 2. Gather facts from upstream

Use the upstream docs or compose file, not memory:

- The fully qualified image (`docker.io/…`, `ghcr.io/…`), and a tag that matches the repo's style: a major/minor tag for services, `latest`/`release` for applications that only publish those.
- Container ports, data paths, the user it runs as, and whether it needs `/dev/dri` or host directories.
- Required environment variables and which of them are secrets.
- A health probe the image ships (`pg_isready`, `healthcheck.sh`, `curl` on `/health`). Check that the binary exists in the image.
- How long it takes to stop, to choose 25/30 or 55/60 for `StopTimeout`/`TimeoutStopSec`.

Pick a host port that no other application uses. Search `PublishPort=` across the repo, and the notes of the `Network=host` applications (sabnzbd takes 8080, qbittorrent 8090, syncthing 8384, glances 61208).

## 3. Write the files

- `.container` (and `.pod`, `.volume`, `.network`, `.env` as needed), following AGENTS.md.
- `pods.yml`: `version: 1`, `name`, `label`, `description`, `author: francoism90` for applications (`foxws` for services), an `icon` from Lucide (`i-lucide-…`), `category`, `website`, `repository`, and `notes` with the port, any host binds or devices, and first-run steps. Add `sources:` for services and `secrets:` for every `Secret=`.
- The Pods keys from AGENTS.md: a `routes:` entry for every web UI (`upstream: systemd-<name>:<container port>`; for a `.pod`, check which name the proxy reaches before you pick one), and `after_install:` for first-run commands the image offers, such as creating an admin. A route needs a `<name>.network` the proxy can join (see AGENTS.md). Take the exact syntax from Pods' `docs/manifest.md` and `docs/proxy.md`. Fetch them with `gh api repos/foxws/pods/contents/docs/manifest.md -H "Accept: application/vnd.github.raw"` (`flatpak-spawn --host gh …` in the VS Code flatpak).
- A row in the `README.md` table.

## 4. Check

Run what CI runs, against the new directories:

```bash
flatpak-spawn --host --directory=$PWD sh -c 'for d in $ARGUMENTS $ARGUMENTS/development $ARGUMENTS/production; do [ -d "$d" ] && QUADLET_UNIT_DIRS="$PWD/$d" /usr/libexec/podman/quadlet -dryrun -user > /dev/null && echo "ok $d"; done'
flatpak-spawn --host --directory=$PWD python3 .github/scripts/check-manifests.py
```

Drop `flatpak-spawn --host --directory=$PWD` outside the VS Code flatpak. The manifest check needs PyYAML, which the host has and the sandbox doesn't. If it's missing, say so and don't skip the check silently. Also review the generated output for each `.container` (drop `> /dev/null`) to confirm the ports, secrets and volumes come out as intended.

## 5. Report

List the files you added, the host port, any secrets or host binds, and which checks you ran and which you didn't. Don't install or start anything unless asked.
