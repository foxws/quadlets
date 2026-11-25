# Quadlets

Podman Quadlets for services and self-hosted applications, listed in the [Pods](https://github.com/foxws/pods) catalog. They need Podman 6+ and install as they are: no placeholders and no templating.

## Layout

- Each top-level directory is one application, with a `pods.yml` next to its units. `name` in `pods.yml` must match the directory name.
- Services (databases, caches, search) have two sources, declared under `sources:` in `pods.yml`:
  - `development/`: no secrets, port published on `127.0.0.1`.
  - `production/`: secrets from Podman secrets, reachable only on its own network.
- Homelab applications (jellyfin, immich, vaultwarden, …) keep their units in the application directory itself and have no `sources:`.
- Every `Secret=` in a unit must be declared under `secrets:` in `pods.yml`. Use `generate: true` for random passwords.
- When you add an application, add it to the table in `README.md`. Pick a host port that no `PublishPort=` uses and no `Network=host` application listens on (their ports are in their `pods.yml` notes).

## Pods

[Pods](https://github.com/foxws/pods) is a web UI that installs these applications over SSH through lpod. It lists every root directory that has a `pods.yml` in its catalog. The units must still install with plain `podman quadlet install`, so Pods never changes them.

The `pods.yml` schema belongs to Pods: [docs/manifest.md](https://github.com/foxws/pods/blob/main/docs/manifest.md), parsed by `ManifestData`. Check it there, not in `check-manifests.py`, which validates only part of it. Besides the catalog keys, `sources` and `secrets`, Pods reads:

- `routes`: upstreams the Pods proxy can give a hostname, as `upstream: <container>:<port>`, where the container name is `systemd-<name>` unless `ContainerName=` says otherwise. Add one for every web UI. Hostnames never go in `pods.yml`.
  - The proxy reaches an upstream by joining the application's networks, so a routed application needs a `<name>.network` and `Network=<name>.network` (on the `.pod` for a pod). For a pod, the upstream is its `PodName=`: the pod name resolves on the network, but the names of the containers in it don't.
  - Applications on `Network=host` or `pasta` (glances, homarr, qbittorrent, sabnzbd, syncthing) and AdGuard Home, whose DNS clients need their real addresses, have no route. Their notes can point to a drop-in that publishes the web UI on the host's address, which the proxy routes to by IP ([Pods docs/proxy.md](https://github.com/foxws/pods/blob/main/docs/proxy.md), Upstreams).
- `after_install` / `after_update`: commands Pods runs in a container from the application page, such as creating an admin.
- `secrets` with `format: dotenv`, or `from` + `key` to read one key from a dotenv secret.
- `ondemand` and `timers`, for applications that sleep when idle or run on a schedule.

A manifest Pods can't parse is ignored with a warning, so a typo fails silently in the catalog.

## Unit conventions

- Publish ports only on loopback: `PublishPort=127.0.0.1:<host>:<container>`.
- Services join a `<name>.network` with `NetworkName=systemd-<name>` and `NetworkAlias=<name>`. Routed applications join one with `NetworkName=systemd-<name>` and no alias. Give the `.network` and `.volume` files `Label=<name>`.
- Refer to sibling units by file name (`Volume=x-data.volume:/data`, `Network=x.network`, `Pod=x.pod`). In `[Unit]`, use the generated service names (`After=x-database.service`).
- Pass secrets as `Secret=<name>,type=env,target=<VAR>`. Never put secret values in tracked files.
- Set `AutoUpdate=registry` on images that track a moving tag (`:11.8`, `:release`, `:latest`).
- Add a health check when the image has a probe: `Notify=healthy`, `HealthCmd=`, `HealthStartupCmd=`, `HealthStartupInterval=`.
- Set `StopTimeout=` five seconds below `[Service] TimeoutStopSec=` (25/30 or 55/60). Without it, Podman kills the container after 10 seconds.
- Usual `[Service]`: `Restart=on-failure` (`always` for services), `RestartSec=5`, `TimeoutStartSec=300`, and `SuccessExitStatus=143` for images that exit 143 on SIGTERM.
- `[Install] WantedBy=default.target` on `.container` and `.pod` files. `.volume` and `.network` files don't need one.
- Named volumes for application state use `:rw,Z,U` when inline (`Volume=app-config:/config:rw,Z,U`). Host directories are bound through a `.volume` with `Type=none`, `Options=bind` and `Device=%h/<dir>`, and need a comment and a note in `pods.yml`.
- SELinux denies containers access to an unlabeled home directory, so relabel every host bind: `Z` for a directory only this application uses (`Volume=glance-config.volume:/app/config:rw,Z`), `z` for one other containers may share, such as `~/Media` or `~/Downloads/<app>` (`Volume=jellyfin-media.volume:/media:rw,z`). Add `U` only when the container runs as a user other than yours; with `UserNS=keep-id` it's a slow no-op on a large tree. Never relabel `%h` itself.
- An image that won't start without a config file can seed one from `[Service] ExecStartPre=` when it's missing, as `glance/` does.
- Write comments as whole lines (`# …`) above the key they explain, never after a value.
- Ship defaults that work for most users, and leave per-host changes to drop-ins (`<unit>.d/*.conf` next to the installed unit), which survive updates. Notes in `pods.yml` point to a drop-in, never to editing the unit. lpod writes its own drop-ins (on-demand, the Pods proxy, ports), so a unit must keep working when a drop-in adds `[Unit]`, `[Container]` or `[Service]` keys.
- In `Exec*=` lines, write `%%` for a literal `%` and `$$` for a literal `$`.

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

`QUADLET_UNIT_DIRS` needs an absolute path: with a relative one, the generator parses nothing and still exits 0. In the VS Code flatpak, `gh`, PyYAML and the generator are only on the host, so prefix those commands with `flatpak-spawn --host --directory=$PWD`.
