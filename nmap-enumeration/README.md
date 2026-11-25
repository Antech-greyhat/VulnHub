# Nmap enumeration practice

**Run this training network locally. All services and records are fake.**

Twelve exercises build on the network enumeration you learned on TryHackMe.
NM-01 to NM-10 are guided; NM-11 and NM-12 ask you to choose your own commands.
You use Nmap to discover hosts, inspect ports and services, and run named NSE
scripts. Save a scan report, have its findings checked, then submit the revealed
`MFANO{...}` flag through the project's usual `labctl` menu.

The exercises use a separate Docker network. They work alongside the existing
portal, and you do not need to log into it or start its containers.

## Setup on Linux or Kali

If Docker is new to you, follow the Docker installation and group/login steps
in [the ownership guide](../linux-ownership/README.md). You need Docker and
either the `docker compose` plugin or `docker-compose`. Nmap is installed in the
scanner image, so installing it on your host is optional.

From the **VulnHub repository on your host**, run:

```sh
docker info
./nmap-enumeration/lab
```

The first build downloads Debian packages; later builds reuse Docker's cache.
Once the scanner shell opens, start with:

```sh
targets
task NM-01
```

The prompt starts with `nmap-lab:`. Commands in the exercise sections below run
**inside that scanner shell**, whose working directory is `/practice`.
The shell has the raw-packet capability needed for SYN and UDP scans, so you
do not need `sudo` there. Type `exit` to return to your host.

## Know your scope

| Address | Purpose |
| ------- | ------- |
| `172.30.77.0/28` | The small, internal practice network |
| `172.30.77.10` | Main service target |
| `172.30.77.11` | Second service target |
| `172.30.77.2` | Your scanner |
| `172.30.77.1` | Docker bridge gateway; it may answer host discovery |

There are no published host ports or host directory mounts. The scanner's
only network is marked `internal`, which prevents routing to external networks.
Use the two service targets for port scans. In this shell `127.0.0.1` means the
scanner itself, not your host's web portal.

The services include HTTP, HTTPS, SSH, anonymous read-only FTP and local DNS.
SSH provides service and host-key information without an account login. FTP
offers only invented, read-only records. DNS has no upstream resolver. Each
exercise uses discovery requests; it does not require password guessing,
exploitation, uploads or scripts from the `brute`, `exploit` or `dos` categories.

## Check a report and submit its flag

Open a **second terminal on your host**, in the repository. After completing
NM-01 in the scanner, run:

```sh
./nmap-enumeration/lab check NM-01 scans/01.xml
./labctl submit NM-01
```

The checker reads the named file from the scanner, verifies the scan type and
required findings, and prints a flag only when they match. Copy that flag into
the hidden `labctl` input. A `Not yet:` message explains what the report lacks;
it does not record a solve. The checker expects successfully completed Nmap
XML, not a screenshot, a copied terminal transcript, or a scan of another network.

Use the same sequence for each ID and report filename. For example, after
NM-06, check `NM-06 scans/06.xml`, then submit to `NM-06`. You can also use:

```sh
./labctl labs --track NM
./labctl unsolved --track NM
./labctl hints NM-06
./labctl status
```

These checks support your own practice; they are not an anti-cheating system.
The source, tests and maintainer answer key can reveal answers, so leave
`tests/` and `docs/.internal/` until after you have solved the exercises.

## Flags you will practise

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

## Continue, stop and keep your work

On the host:

```sh
./nmap-enumeration/lab status
./nmap-enumeration/lab shell   # return to the running scanner
./nmap-enumeration/lab stop    # pause the dedicated training services
./nmap-enumeration/lab        # rebuild/start and open the scanner again
```

Reports in `scans/` live in a dedicated Docker-managed volume. Stopping or
rebuilding preserves them, and existing `labctl` progress stays on the host.
Use a new basename when repeating an exercise so Nmap does not overwrite a
report you want to keep. This launcher has no command that deletes reports or
volumes. Leave the stored reports until you decide how to archive or recycle them.

If Docker reports an overlapping address pool, another local network uses
`172.30.77.0/28`. Stop this training launch and inspect your Docker networks;
do not change the CIDR in only one file, because the guide and checker use the
same target addresses. If `check` cannot find a report, verify it was saved
inside the scanner under `scans/`, and wait for Nmap's completion message.

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
