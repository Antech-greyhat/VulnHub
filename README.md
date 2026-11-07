> # ⚠️ **THIS IS A DELIBERATELY VULNERABLE LAB. NEVER DEPLOY IT PUBLICLY.**
>
> **It has security holes on purpose. Run it on your own machine only. If you host it for yourself, put it behind Tailscale or Cloudflare Access so that only you can reach it.**

# Mfano High School Portal

Mfano High School Portal is a fake Kenyan school portal for learning penetration testing. "Mfano" means "example". Every student, mark, fee balance and M-Pesa-style payment in it is made up, and it makes no real payment calls.

## Run it

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/) and Python 3.

```sh
git clone https://github.com/Antech-greyhat/VulnHub.git
cd VulnHub
docker compose up --build
```

Open <http://127.0.0.1:8080>.

| Role | Username | Password |
| ---- | -------- | -------- |
| Student | `MHS1007` | `Student@123` |
| Admin | `admin` | `Mfano@Admin2026` |

Every student from `MHS1001` to `MHS1030` uses the same demo password.

## Use labctl

```sh
python labctl.py start            # build and run the lab
python labctl.py stop             # stop it
python labctl.py reset            # rebuild the database with fresh mock data
python labctl.py shell            # open a shell inside the app container
python labctl.py audit            # scan dependencies with pip-audit
python labctl.py submit 'MFANO{...}'   # check a flag
python labctl.py status           # show stages and your progress (score does the same)
```

## Supply-chain practice

One dependency is pinned to an old, known-vulnerable version on purpose. Find it
with:

```sh
pip install pip-audit
python labctl.py audit      # or: pip-audit -r requirements.txt
```

The lesson is detection: see the advisory, note the fixed version, move on. Do
not run any exploit against an external target.

Your progress stays in `.labprogress.json`, which git ignores.

## Networking practice

The lab runs a few services on your machine's loopback so you can practise
port and service discovery against **your own lab only**.

```sh
nmap -sV 127.0.0.1
```

Ports you should expect to find:

| Port | Service | Notes |
| ---- | ------- | ----- |
| 8080 | Web portal | The Flask app |
| 5432 | PostgreSQL | A "results backup" database |

A small internal grading service also runs, but it is **not** published to your
machine, so nmap will not see it. Reaching it is a later exercise.

To poke at the backup database you can use any Postgres client, e.g. `psql`.

> **Only scan and probe this lab, on your own machine. Never scan hosts,
> networks, or services you do not own or have written permission to test.**

## A note on the server tools

The admin "server tools" (diagnostics, bulk upload, logo import) are powerful on
purpose and can run commands and fetch URLs from the lab box. This is exactly
why the lab must stay on your own machine.

> **Never deploy this anywhere public. Run it on localhost only, or behind
> Tailscale / Cloudflare Access so that only you can reach it.**

## Forensics practice

The [`forensics/`](forensics/) folder has seven offline challenges about a
leaked exam paper: three images, a GIF, two audio clips and a CCTV video. You
do not need Docker for them. Read [`forensics/README.md`](forensics/README.md)
for the case brief, then submit flags with `labctl` as usual.

## Flags

Exploiting a bug reveals a flag that looks like `MFANO{...}`. `flags.sha256` holds only the hashes, so `labctl` can check a flag without storing the answer. See `SCOREBOARD.md` for how many bugs exist in each OWASP category.

## About this project

Writeups will be added later. This lab was built with AI agents for learning.
