# Quadlets

Podman Quadlets for services and self-hosted applications, listed in the [Pods](https://github.com/foxws/pods) catalog. They need Podman 6+ and install as they are: no placeholders and no templating.

## Layout

- Each top-level directory is one application, with a `pods.yml` next to its units. `name` in `pods.yml` must match the directory name.
- Services (databases, caches, search) have two sources, declared under `sources:` in `pods.yml`:
  - `development/`: no secrets, port published on `127.0.0.1`.
  - `production/`: secrets from Podman secrets, reachable only on its own network.
- Homelab applications (jellyfin, immich, vaultwarden, …) keep their units in the application directory itself and have no `sources:`.
- Every `Secret=` in a unit must be declared under `secrets:` in `pods.yml`. Use `generate: true` for random passwords.
- When you add an application, add it to the table in `README.md`.

## Unit conventions

- Publish ports only on loopback: `PublishPort=127.0.0.1:<host>:<container>`.
- Services join a `<name>.network` with `NetworkName=systemd-<name>` and `NetworkAlias=<name>`. Give the `.network` and `.volume` files `Label=<name>`.
- Refer to sibling units by file name (`Volume=x-data.volume:/data`, `Network=x.network`, `Pod=x.pod`). In `[Unit]`, use the generated service names (`After=x-database.service`).
- Pass secrets as `Secret=<name>,type=env,target=<VAR>`. Never put secret values in tracked files.
- Set `AutoUpdate=registry` on images that track a moving tag (`:11.8`, `:release`, `:latest`).
- Add a health check when the image has a probe: `Notify=healthy`, `HealthCmd=`, `HealthStartupCmd=`, `HealthStartupInterval=`.
- Set `StopTimeout=` five seconds below `[Service] TimeoutStopSec=` (25/30 or 55/60). Without it, Podman kills the container after 10 seconds.
- Usual `[Service]`: `Restart=on-failure` (`always` for services), `RestartSec=5`, `TimeoutStartSec=300`, and `SuccessExitStatus=143` for images that exit 143 on SIGTERM.
- `[Install] WantedBy=default.target` on `.container` and `.pod` files. `.volume` and `.network` files don't need one.
- Named volumes for application state use `:rw,Z,U` when inline (`Volume=app-config:/config:rw,Z,U`). Host directories are bound through a `.volume` with `Type=none`, `Options=bind` and `Device=%h/<dir>`, and need a comment and a note in `pods.yml`.
- Write comments as whole lines (`# …`) above the key they explain, never after a value.

## References

Check Quadlet and systemd behaviour against the docs, not memory. The best source is the host's man pages (`podman-container.unit(5)`, `podman-systemd.unit(5)`, `systemd.service(5)`), since they match the installed version. After those come Context7 (`/websites/podman_io`, `/systemd/systemd`) and <https://docs.podman.io>. `.claude/skills/quadlet/SKILL.md` summarises the parts this repo relies on.

## Checks

CI (`.github/workflows/check.yml`) runs:

```bash
python3 .github/scripts/check-manifests.py   # needs PyYAML
for d in $(find . -name '*.container' -o -name '*.pod' -o -name '*.volume' -o -name '*.network' -o -name '*.kube' | grep -v '^./.github/' | xargs -n1 dirname | sort -u); do
    QUADLET_UNIT_DIRS="$PWD/${d#./}" /usr/libexec/podman/quadlet -dryrun -user > /dev/null || echo "FAIL $d"
done
```

`QUADLET_UNIT_DIRS` needs an absolute path: with a relative one, the generator parses nothing and still exits 0. In the VS Code flatpak, run the generator with `flatpak-spawn --host --directory=$PWD`. PyYAML is missing in the sandbox, so run the manifest check in a toolbox.
