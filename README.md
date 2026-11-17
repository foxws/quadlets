# Quadlets

Services and self-hosted applications as plain [Podman Quadlets](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html). They need Podman 6+ and systemd, and have no placeholders: install them as they are.

Every directory is one application, with a `pods.yml` that describes it: its label, description, author, icon, category, website, source repository and notes. [Pods](https://github.com/foxws/pods) lists these in its catalog. A service has two sources:

- `development/` publishes its port on `127.0.0.1` and needs no secrets, like a local development stack.
- `production/` keeps it on its own network and reads passwords and keys from Podman secrets.

| Application | Sources | Development port |
| ----------- | ------- | ---------------- |
| postgres | production, development | 5432 |
| mariadb | production, development | 3306 |
| mysql | production, development | 3307 |
| redis | production, development | 6379 |
| valkey | production, development | 6380 |
| memcached | production, development | 11211 |
| meilisearch | production, development | 7700 |
| typesense | production, development | 8108 |
| rustfs | production, development | 9000, console 9001 |
| mailpit | development | SMTP 1025, inbox 8025 |
| jellyfin, immich, vaultwarden, memos, syncthing, adguardhome, homarr, glances, qbittorrent, sabnzbd | the directory itself | see their `pods.yml` |

The homelab applications come from [francoism90/dotfiles](https://github.com/francoism90/dotfiles). Some bind a directory of your home folder, such as `~/Media` for Jellyfin, through a `.volume` with `Type=none`: point its `Device=` somewhere else before installing if you keep it elsewhere, and make sure the directory exists.

## Installing

With Pods, pick an application from the catalog on the Install application page. Pods creates the secrets it needs.

By hand, create the secrets the `.container` files name, then install the directory:

```bash
printf '%s' "$(openssl rand -base64 24)" | podman secret create postgres-password -
podman quadlet install --application=postgres postgres/production/
systemctl --user start postgres.service
```

## Connecting from an application

Join the service's network and use its name as the host:

```ini
[Container]
Network=systemd-postgres
# DB_HOST=postgres, DB_PORT=5432
```

## pods.yml

```yaml
version: 1
name: mariadb
label: MariaDB
description: Relational database compatible with MySQL
author: foxws
icon: i-lucide-database        # a Lucide icon
category: Databases
website: https://mariadb.org
repository: https://github.com/MariaDB/server
notes: Shown before installing.

sources:                       # paths are relative to this directory
  production:
    path: production
  development:
    path: development

secrets:
  mariadb-root-password:
    description: Password of the MariaDB root user
    generate: true
```
