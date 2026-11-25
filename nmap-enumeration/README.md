# Nmap enumeration practice

> [!CAUTION]
> **Keep this training network local. All services and records are fake.**
> Port-scan only `172.30.77.10` and `172.30.77.11` from the provided scanner.
> The documentation links at the end are references, not scan targets.

Twelve exercises build on the network enumeration you learned on TryHackMe.
NM-01 to NM-10 are guided; NM-11 and NM-12 ask you to choose your own commands.
You use Nmap to discover hosts, inspect ports and services, and run named NSE
scripts. Save a scan report, have its findings checked, then submit the revealed
`MFANO{...}` flag through the project's usual `labctl` menu.

The exercises use a separate Docker network. They work alongside the existing
portal, and you do not need to log into it or start its containers.

## Contents

- [Install and check the tools](#install-and-check-the-tools)
- [Your first solve: two terminals](#your-first-solve-two-terminals)
- [Know your scope](#know-your-scope)
- [Cautions](#cautions)
- [Scan options](#scan-options)
- [Exercises NM-01 to NM-12](#nm-01-discover-before-scanning-ports)
- [Start, stop and return later](#start-stop-and-return-later)
- [Troubleshooting](#troubleshooting)
- [Extra practice](#extra-practice)
- [Official references](#official-references)

## Install and check the tools

Use a terminal on your Linux machine or Kali VM. In this guide, **host** means
the Linux machine or VM where Docker runs. Both host terminals must be on that
same machine. The **scanner** is the separate shell opened by the launcher.

| Tool | Where it is needed |
| ---- | ------------------ |
| Git | Host, to get or update the project |
| Docker and Docker Compose | Host, to build and run the training environment |
| Bash 4+, jq, whiptail, coreutils, util-linux | Host, for `./labctl` and flag scoring |
| Nmap | Provided inside the scanner image |

You can skip installation if these tools are already working. Otherwise, on
Kali, Debian or Ubuntu, install the host tools:

```sh
sudo apt update
sudo apt install -y git bash jq whiptail coreutils util-linux docker.io
```

Install the Compose package for your distribution. On **Kali or Debian**:

```sh
sudo apt install -y docker-compose
```

On **Ubuntu**:

```sh
sudo apt install -y docker-compose-v2
```

Start Docker and allow your own Linux account to use it:

```sh
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Log out and back in, then open a new terminal. Membership in the Docker group
grants administrator-level access to Docker; use a trusted account on your own
lab machine. The [ownership guide](../linux-ownership/README.md#first-time-docker-setup)
also walks through these steps.

Check readiness on the host:

```sh
docker info
docker compose version
```

`docker info` must show server information without an error. If your installation
provides the older standalone Compose command, check `docker-compose version`
instead. The launcher supports either form. An installation failure can mean
your distribution needs its Docker package repository; see the
[Docker Engine installation guide](https://docs.docker.com/engine/install/).

Get the project if you have not cloned it yet:

```sh
git clone https://github.com/Antech-greyhat/VulnHub.git
cd VulnHub
```

For an existing checkout, open that folder in your terminal. When you want to
update it, save your work first and use `git pull --ff-only`. The commands below
use `./labctl` directly, so installing a shortcut on your host is optional.

## Your first solve: two terminals

### 1. Start from host terminal A

In the **VulnHub repository folder on the host**, run:

```sh
./labctl labs --track NM
./nmap-enumeration/lab
```

The list should show NM-01 through NM-12. The launcher builds two images,
starts the scanner and service targets, then opens the scanner shell. The
first build needs internet and can take a few minutes; later builds reuse
Docker's downloaded packages and cached image layers. Wait for this prompt:

```text
nmap-lab:/practice#
```

You are now inside the scanner. Its working directory is `/practice`; `scans/`
is where you save reports. The shell has the raw-packet capability needed for
SYN and UDP scans, so the exercise commands work without `sudo` there.

### 2. Run NM-01 inside the scanner

At the `nmap-lab:` prompt, run:

```sh
targets
task NM-01
nmap -n -sn 172.30.77.0/28 -oX scans/01.xml
ls -l scans/01.xml
```

`targets` lists the practice network; `task NM-01` displays the exercise.
The scan discovers hosts without scanning their ports. Identify both service
targets, `172.30.77.10` and `172.30.77.11`; the scanner and gateway may appear too.
Wait for `Nmap done` and the returned prompt before checking the report.
The `ls` command should show the saved XML file inside the scanner.

### 3. Check and submit from host terminal B

Keep the scanner open. Open a **second terminal on the same host or VM**, and
change into the same VulnHub checkout. Run:

```sh
./nmap-enumeration/lab check NM-01 scans/01.xml
./labctl submit NM-01
```

The first command reads the report from the scanner and prints a `MFANO{...}`
flag when the required findings match. Copy that exact flag into the hidden
input opened by the second command. Use Tab to select the confirmation button
and Enter to submit. Keep `MFANO` uppercase and copy the contents exactly;
do not translate the digits or guess a plain-English version.

If the checker prints `Not yet:`, return to the scanner and correct the missing
finding. Checking a report reveals the flag; submitting it through `labctl`
records the solve. A flag for a different ID is rejected, and repeat submissions
count only once.

### 4. Check progress and continue

On the host:

```sh
./labctl solved --track NM
./labctl unsolved --track NM
./labctl hints NM-02
```

Back in the scanner, use `task NM-02`, perform its scan, and save its report as
`scans/02.xml`. On the host, check `NM-02 scans/02.xml`, then submit to `NM-02`.
Repeat that flow for every ID. NM-01 to NM-10 provide commands; NM-11 and NM-12
ask you to choose your own commands using the skills you have practised.

| Action | Where to run it |
| ------ | --------------- |
| Start, check reports, submit flags, view progress, stop services | Host terminal in the checkout |
| `targets`, `task`, Nmap scans, inspect `scans/` | Scanner shell at the `nmap-lab:` prompt |

The checker accepts successfully completed Nmap XML saved with `-oX` or `-oA`.
A terminal transcript, screenshot, or normal text report renamed to `.xml`
does not contain the required structured evidence. These checks support your
own practice; the source and maintainer answer key can reveal answers, so leave
`tests/` and `docs/.internal/` until after you have solved the exercises.

## Know your scope

| Address | Purpose |
| ------- | ------- |
| `172.30.77.0/28` | The small, internal practice network |
| `172.30.77.10` | Main service target |
| `172.30.77.11` | Second service target |
| `172.30.77.2` | Your scanner |
| `172.30.77.1` | Docker bridge gateway; it may answer host discovery |

There are no published host ports or host bind mounts. The scanner's
only network is marked `internal`, which prevents routing to external networks.
Use the two service targets for port scans. In this shell `127.0.0.1` means the
scanner itself, not your host's web portal.

The services include HTTP, HTTPS, SSH, anonymous read-only FTP and local DNS.
SSH provides service and host-key information without an account login. FTP
offers only invented, read-only records. DNS has no upstream resolver. Each
exercise uses discovery requests; it does not require password guessing,
exploitation, uploads or scripts from the `brute`, `exploit` or `dos` categories.

## Cautions

- **Keep scans inside the practice scope.** Use `172.30.77.0/28` for NM-01 host
  discovery and the two service targets for port scans. The host, scanner and
  gateway are different machines or interfaces. In the scanner, `127.0.0.1`
  points back to the scanner itself.
- **Keep Docker's isolation.** Preserve the internal network and the absence
  of published ports and host bind mounts. Do not switch to host networking,
  mount the Docker socket, or publish these services to reach them from outside.
- **Read script help and choose names deliberately.** Follow the named scripts
  in the exercises. Broad script selections can run more operations than you
  intend. Keep `http-methods.retest` and `http-methods.test-all` disabled; they
  can send requests that change server state. These labs use service inspection,
  read-only requests and the fake FTP catalogue's anonymous listing.
- **Give scans time to finish.** Use the normal `-T3` timing while learning.
  Ctrl+C can stop a scan, but an unfinished XML report will not pass the checker.
  Run the exercise again with a fresh report name when necessary.
- **Protect your reports and progress.** Reusing an output filename overwrites
  the report. Choose a new basename when keeping earlier attempts. Avoid Docker
  volume-pruning commands: the report volume and other projects' volumes may
  contain work you want to keep. Your score is stored separately in the host's
  `.labprogress.json`.
- **Stop the lab when you finish.** `exit` leaves the scanner shell while the
  containers keep running. Use `./nmap-enumeration/lab stop` on the host to pause
  this training environment. Leave Docker running if your other projects need it.

The HTTPS certificate is an invented, self-signed training certificate. You
can inspect it with Nmap without installing it as trusted on your host. SSH
exercises retrieve public host keys; they do not require an account login.
When reporting a broken exercise, share its ID, command and error message;
keep completed flags out of public issues.

## Scan options

Here, **options** means Nmap's command-line flags. The `MFANO{...}` flags you
earn and submit are the separate challenge rewards.

| Option | Meaning |
| ------ | ------- |
| `-n` | Skip reverse DNS lookups; keep these scans about the local IPs |
| `-sn` | Discover hosts without scanning their ports |
| `-Pn` | Skip host discovery for a target you already know is up |
| `-sT` / `-sS` | TCP connect scan / TCP SYN scan |
| `-sU` | UDP scan; a missing reply alone does not confirm an open port |
| `-p 21,22` / `-p 1-100` / `-p-` | A port list / a range / all TCP ports 1–65535 |
| `-sV` / `--version-light` | Probe services / use the lighter version probe set |
| `--script` / `--script-args` | Choose named NSE scripts / configure them |
| `--script-help` | Read a script's purpose and arguments before using it |
| `-T3` | The normal timing template; adequate for this small network |
| `--reason` / `--open` | Explain port states / display open or possibly open ports |
| `-v` | Show more detail |
| `-oX file.xml` | Save structured evidence for the checker |
| `-oA scans/name` | Save `name.nmap`, `name.gnmap`, and `name.xml` together |

An `open` TCP port has a listener. A `closed` port replied but has no listener.
`filtered` means Nmap cannot determine the state because probes or replies are
blocked. UDP `open|filtered` is ambiguous: use a protocol reply or service probe
to establish `open`. Port-based names alone are guesses; `-sV` provides evidence.

## NM-01: Discover before scanning ports

If you finished NM-01 in the walkthrough, continue with NM-02. Use a fresh
report filename if you want to repeat the discovery scan and keep the first one.

Discover the practice subnet without a port scan. Identify both service
targets; the scanner and gateway can also appear in the output.

```sh
nmap -n -sn 172.30.77.0/28 -oX scans/01.xml
```

On this directly connected Docker network, Nmap normally uses ARP discovery.
Record which hosts are up. Check `NM-01 scans/01.xml` on the host and submit.

## NM-02: TCP connections and port states

Scan a selected set of ports using TCP connect scanning. Include a control
port with no listener so you can compare `open` and `closed`.

```sh
nmap -n -Pn -sT -p 21,22,80,443,9999 --reason -oX scans/02.xml 172.30.77.10
```

This scan completes the TCP connection. The checker needs the four listeners
and the closed control port. Do not add `--open` here: seeing the closed result
is part of the exercise. Check `NM-02 scans/02.xml` on the host.

## NM-03: SYN scans and the full port range

Find a listener beyond the usual default port list. Use a SYN scan, all TCP
ports, and the normal timing template. Compare this technique with NM-02.

```sh
nmap -n -sS -p- -T3 --open --reason -oX scans/03.xml 172.30.77.10
```

SYN scanning inspects the handshake response without completing the ordinary
application connection. `--open` changes the display; it does not shrink the
port range being scanned. Record every discovered listener, then check
`NM-03 scans/03.xml` on the host.

## NM-04: Confirm service names and versions

Use light version probes against the selected TCP listeners.

```sh
nmap -n -sV --version-light -p 21,22,80,443 -oX scans/04.xml 172.30.77.10
```

Record the FTP and SSH products and versions, the HTTP service, and the
TLS-wrapped HTTP service. Version numbers can change as the Debian image is
updated; the checker does not require one exact package version. Check
`NM-04 scans/04.xml` on the host.

## NM-05: UDP and DNS replies

Read the DNS script help, then scan only the training DNS port.

```sh
nmap --script-help dns-nsid
nmap -n -sU -sV -p 53 --script dns-nsid -oX scans/05.xml 172.30.77.10
```

The script asks the target for nameserver identity and version information.
Look for the `bind.version` reply and a confirmed `open` UDP state. An
`open|filtered` result by itself is insufficient. Check `NM-05 scans/05.xml`.
DNS also has a TCP listener here: treat `53/tcp` and `53/udp` as separate
inventory entries when you build the final report.

## NM-06: Read HTTP titles and headers

Inspect the site's title and response headers using two named scripts.

```sh
nmap --script-help http-title,http-headers
nmap -n -sV -p 80 --script http-title,http-headers -oX scans/06.xml 172.30.77.10
```

Record the page title and the header identifying the site's lab role.
These findings tell you more than a guessed service name. Check
`NM-06 scans/06.xml` on the host.

## NM-07: Crawler exclusions and HTTP methods

Read the crawler exclusions and inspect the methods advertised for the
staff-notices path. This exercise also introduces script arguments.

```sh
nmap --script-help http-robots.txt,http-methods
nmap -n -sV -p 80 --script http-robots.txt,http-methods \
  --script-args http-methods.url-path=/staff-notices/ \
  -oX scans/07.xml 172.30.77.10
```

Record both excluded paths and the supported read-only methods. A `robots.txt`
entry is a crawler instruction, not an access restriction. Use the script's
default method inspection; do not enable `http-methods.retest` or
`http-methods.test-all`, which can send state-changing requests. Check
`NM-07 scans/07.xml` on the host.

## NM-08: TLS certificate information

Inspect the invented certificate presented by the HTTPS service.

```sh
nmap -n -sV -p 443 --script ssl-cert -v -oX scans/08.xml 172.30.77.10
```

Record the subject and both DNS names in the certificate. The self-signed
certificate is a training fixture; finding a name does not authorize scanning
some similarly named external host. Check `NM-08 scans/08.xml` on the host.

## NM-09: SSH identity without a login

Retrieve the SSH server's public host-key fingerprints.

```sh
nmap --script-help ssh-hostkey
nmap -n -sV -p 22 --script ssh-hostkey -oX scans/09.xml 172.30.77.10
```

Record an RSA fingerprint and its key length. A host key identifies a server;
it is not a user's password or private key. Check `NM-09 scans/09.xml`.

## NM-10: Anonymous FTP inventory

Inspect the intentionally public, read-only catalogue with `ftp-anon`.

```sh
nmap --script-help ftp-anon
nmap -n -sV -p 21 --script ftp-anon -oX scans/10.xml 172.30.77.10
```

Record the successful anonymous response and the handover document's filename
from the listing. No credential guesses or file writes are needed. Check
`NM-10 scans/10.xml` on the host.

## NM-11: Find the archive service yourself

The second service target has an HTTP inventory on a high TCP port. Starting
with the address found in NM-01, choose your own port-discovery command, then
confirm the service with version detection and named HTTP scripts.

Save a report as `scans/11.xml` containing that listener's detected HTTP
service, page title, and lab-role response header. Use the Nmap reference if
you need a reminder. Check `NM-11 scans/11.xml` on the host.

## NM-12: Produce a final inventory

Build one report for the main target that combines TCP SYN scanning, UDP
scanning and service detection. Include the six TCP listeners you found in
NM-02/NM-03 and the DNS UDP listener. Collect the HTTP title and role header,
TLS certificate names, SSH RSA fingerprint and DNS version reply using the
named scripts you have practised.

Choose the combined TCP/UDP port specification yourself; the Nmap reference
shows the `T:` and `U:` syntax. Save all three output formats with the basename
`scans/12`, then check `NM-12 scans/12.xml` on the host. Review `scans/12.nmap`
in the scanner and explain what each service finding demonstrates before
submitting your final flag.

## Start, stop and return later

Type `exit` in the scanner when you want to return to host terminal A. To pause
the training services, run this **on the host**:

```sh
./nmap-enumeration/lab stop
```

Next time, open the checkout on your host and run:

```sh
./nmap-enumeration/lab
```

The launcher builds or reuses the images, starts the services and opens the
scanner. Your reports are still in `scans/`, and `./labctl solved --track NM`
shows your saved progress. The services start independently of the web portal;
the web lab's `labctl start`, `stop` and `reset` commands manage the web stack.

All commands in this reference run **on the host**, from the checkout:

| Command | Result |
| ------- | ------ |
| `./nmap-enumeration/lab` | Build, start and open the scanner |
| `./nmap-enumeration/lab start` | Build and start in the background, then return to the host prompt |
| `./nmap-enumeration/lab shell` | Open another scanner shell when the services are already running |
| `./nmap-enumeration/lab check NM-01 scans/01.xml` | Check that report and reveal the earned flag |
| `./nmap-enumeration/lab status` | Show the training containers' status |
| `./nmap-enumeration/lab stop` | Stop the training services and keep reports and scores |
| `./nmap-enumeration/lab build` | Build images only |
| `./nmap-enumeration/lab --help` | Show help without starting Docker |

`shell` alone does not start stopped services. Use the default launcher, or
run `start` followed by `shell`, when returning after a stop. Reports live in a
dedicated Docker-managed volume mounted at `/practice/scans`; they are not a
`scans/` folder in your host checkout. Stopping or rebuilding preserves them.
The launcher provides no command that deletes reports, volumes or scores.

To inspect a saved report **inside the scanner**:

```sh
ls -l scans
less scans/01.xml
```

Use a fresh filename when repeating a scan. In the final exercise, `-oA scans/12`
saves three files; inspect `scans/12.nmap` for the readable report and pass
`scans/12.xml` to the checker on the host.

## Troubleshooting

| Symptom | What to do |
| ------- | ---------- |
| Docker cannot connect to its daemon | Run `docker info` on the host to see the error. On a Linux system with Docker installed but stopped, use `sudo systemctl start docker`. |
| Permission denied on `docker.sock` | Follow the Docker group and logout/login steps above. Do not make the socket world-writable. |
| Compose was not found | Install the package for your distribution above, then check `docker compose version` or `docker-compose version`. |
| `jq` or `whiptail` is missing | Install the host scoring tools from the setup section. Nmap itself comes with the scanner image. |
| `task` or `targets` is not found | You are probably at the host prompt. Run the launcher and wait for the `nmap-lab:` scanner prompt. |
| The launcher asks for a normal terminal | Run it in an interactive Linux terminal on your host or VM. |
| `shell` reports that the scanner is not running | Use `./nmap-enumeration/lab` to build/start/open, or use `start` then `shell`. |
| The checker cannot find `scans/01.xml` | Inspect `scans/` inside the scanner. Save with `-oX scans/01.xml` there, then use the same relative path in the host checker command. |
| The checker prints `Not yet:` | Read the message, use `task NM-xx` in the scanner, and collect the missing scan type, service probe or named script finding. Wait for the scan to finish before checking again. |
| `labctl` rejects a flag | Select the matching exercise ID and copy the exact returned flag. Do not submit the report filename or change its spelling. |
| Docker reports an overlapping address pool | Inspect your host's Docker networks with `docker network ls`. Do not remove another project's network or change the CIDR in only one file; this guide and the checker use the same fixed addresses. |
| A training service exits during startup | The launcher prints the service's error. Update the checkout, retry the default launcher, and include the service name and error when reporting the problem. |

For an overlap you cannot resolve while preserving existing projects, use a
separate Linux/Kali lab VM. Stopping this lab keeps its reports; removing
Docker volumes would discard them.

## Extra practice

For extra comparison on these same targets, try `-sL -n`, `-F`, `--top-ports 10`
and `-r`. Explain why shorter port lists can miss the archive service. Read
about `-O`, `-A` and `-sC` too: containers share a kernel, so OS guesses are not
stable lab answers, and `-A`/`-sC` select additional operations or scripts. The
scored exercises use explicit scan types and script names.

## Official references

- [Nmap home and documentation](https://nmap.org/)
- [Reference guide and option summary](https://nmap.org/book/man-briefoptions.html)
- [NSE documentation index](https://nmap.org/nsedoc/)
- [Nmap source repository](https://github.com/nmap/nmap)
- Scripts: [dns-nsid](https://nmap.org/nsedoc/scripts/dns-nsid.html),
  [http-title](https://nmap.org/nsedoc/scripts/http-title.html),
  [http-headers](https://nmap.org/nsedoc/scripts/http-headers.html),
  [http-robots.txt](https://nmap.org/nsedoc/scripts/http-robots.txt.html),
  [http-methods](https://nmap.org/nsedoc/scripts/http-methods.html),
  [ssl-cert](https://nmap.org/nsedoc/scripts/ssl-cert.html),
  [ssh-hostkey](https://nmap.org/nsedoc/scripts/ssh-hostkey.html),
  [ftp-anon](https://nmap.org/nsedoc/scripts/ftp-anon.html).
