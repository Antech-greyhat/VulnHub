# Security policy

## This lab is vulnerable on purpose

Mfano High School Portal is a **deliberately vulnerable** training lab. SQL
injection, XSS, command injection, SSRF, weak credentials, leaked secrets and
the rest are the point of the project, so please **don't** report them as
vulnerabilities.

## What to report

Open an issue (or contact the maintainer privately for anything sensitive) if
you find:

- a way the lab **escapes your machine**, for example a port bound to `0.0.0.0`
  by default, or a container that calls out to a real external service;
- a **real** secret or credential committed by mistake (all the lab's secrets
  are fake and labelled that way);
- a problem in `labctl` or the tooling that could harm the host running it.

## Running it safely

- Run it on `127.0.0.1` only. Never deploy it to a public server or cloud VM.
- To reach it from another device, put it behind Tailscale or Cloudflare Access.
- Only attack systems you own or have written permission to test.
