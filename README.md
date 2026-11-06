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
python labctl.py submit 'MFANO{...}'   # check a flag
python labctl.py status           # show stages and your progress (score does the same)
```

Your progress stays in `.labprogress.json`, which git ignores.

## Flags

Exploiting a bug reveals a flag that looks like `MFANO{...}`. `flags.sha256` holds only the hashes, so `labctl` can check a flag without storing the answer. See `SCOREBOARD.md` for how many bugs exist in each OWASP category.

## About this project

Writeups will be added later. This lab was built with AI agents for learning.
