# Linux permissions and ownership

Seven exercises follow the [file manipulation track](../linux-files/README.md).
They teach `chmod`, `chown` and `chgrp` using real Linux users and groups.
**Permissions** control access; **ownership** identifies a file's user and group.
Docker provides a separate practice environment so you can change ownership
without changing your host's files. You do not need to know Docker commands to
launch the exercises.

New to the project? First complete [steps 1–2 of the main setup guide](../README.md#install-and-run)
to install the basic tools and clone it into `~/VulnHub`. In this guide, the
**host** is your normal Linux desktop; the **sandbox** is the practice shell
opened by the launcher. The main guide also gives the default menu route and
backup Compose route for starting the web lab.

## First-time Docker setup

An **image** is the prepared Linux environment. A **container** is one running
copy of it. The launcher downloads/builds the image, then opens a container as
the practice user `learner`. No web portal or Compose setup is needed.

On Kali, Debian or Ubuntu, run these on your **host** once:

1. Install Docker:

   ```sh
   sudo apt update
   sudo apt install -y docker.io
   ```

2. Start its background service:

   ```sh
   sudo systemctl enable --now docker
   ```

3. Allow your Linux account to use Docker:

   ```sh
   sudo usermod -aG docker "$USER"
   ```

   Log out and log back in, then open a new terminal. Membership in the Docker
   group grants administrator-level access to Docker; use it on your own lab
   machine. If Docker is already configured, keep your existing setup.

4. Confirm Docker is ready:

   ```sh
   docker info
   ```

   It should display client and server information. If it fails, use the
   troubleshooting table below. Other distributions can follow the
   [official Docker Engine installation guide](https://docs.docker.com/engine/install/),
   then use the same launcher.

## Launch, work, check and submit

From the repository folder on your **host**, run:

```sh
cd ~/VulnHub
./linux-ownership/lab
```

The first build needs internet and can take a few minutes. Later launches reuse
the downloaded image and cached build steps. Wait until the prompt begins with
`(Mfano sandbox)`. You are now **inside the container**, in `/practice`, logged
in as `learner`.

Inside the sandbox:

```sh
task FO-01
cd /practice/FO-01
ls -l
# Make the changes requested by the task.
check-ownership FO-01
```

Use `task FO-02` and `cd /practice/FO-02` for the next exercise. The checker
inspects real ownership and modes, then tests access as the fictional accounts.
It reveals a flag only when the task is complete. A wrong change prints a
helpful message; you can correct it and check again.

Keep that sandbox open. Open a **second host terminal**, return to this checkout,
and submit the earned flag:

```sh
cd ~/VulnHub
./labctl submit FO-01
```

Paste the flag into the hidden box. Use the matching ID for each task.
`./labctl labs --track FO` and `./labctl hints FO-01` work on the host too.
Checking inside the sandbox does not record your score; submitting on the host
does. If you use only one terminal, copy the flag before typing `exit` and then
submit it on the host.

To stop, type `exit` or press Ctrl+D in the sandbox. The launcher removes that
disposable container and returns you to the host. Your practice changes are
discarded; your submitted score remains in the host's `.labprogress.json`.
Run `./linux-ownership/lab` again for a fresh attempt. Finish related tasks in
one session or record each earned flag before leaving. The cached image remains
available for the next launch. No host folders, Docker socket, or ports are
shared with the practice container.

## Read ls -l first

`ls -l` shows a file's mode, owner and group. Use `ls -ld directory-name` to see
the directory's own metadata. For example:

```text
-rw-r----- 1 learner teachers ... example.txt
```

The first character is the type (`-` file, `d` directory). The next nine are
three sets of permissions: owner, group, others. `r` means read, `w` write, and
`x` execute. For a **directory**, `x` means search/traverse: entering it or
accessing a known filename inside it. Directory `r` lists names, while `w`
together with `x` allows adding/removing entries. File permissions apply
separately from the containing directory's permissions.

`chmod` changes modes. Symbolic modes use `u` (owner), `g` (group), `o` (others),
`+` (add), `-` (remove) and `=` (set). Numeric modes add `r=4`, `w=2`, `x=1`
for each class: `rw-` is 6, `r--` is 4, and `---` is 0.
`chown` changes the owner (or `owner:group` together); `chgrp` changes the group.

Changing a file you own usually needs no sudo. Changing its owner usually needs
administrator permission. Some tasks therefore use `sudo chown`, `sudo chgrp`
or `sudo chmod` **inside this sandbox**. The practice account can run these
without a password. A group change without sudo works when you own the file and
belong to the target group; `id` shows your group memberships.

## FO-01: Private notes — symbolic chmod

Work on `private-notes.txt`. It is owned by learner and starts readable and
writable by everybody. Use symbolic `chmod` to remove read/write access for
group and others while preserving the owner's read/write access. The finished
mode must be `0600`, with owner and group both learner. Preserve the content.

## FO-02: Team reference — numeric chmod

Work on `team-readme.txt`, already owned by learner with group teachers. Use
numeric `chmod` to allow owner read/write, group read only, and no access for
others: `0640`. No execute or special permission bits should be present. The
teacher account must be able to read the file but not write it.

## FO-03: A directory you can list but cannot traverse

`inbox` starts with mode `0640`; `inbox/report.txt` is already `0640`, owned by
learner with group teachers. Fix the **directory** to `0750`: owner can list,
traverse and manage entries; teachers can list and traverse; others have no
access. Keep the report file's original mode and content. The teacher must be
able to read the report but cannot create entries in inbox. Do not apply an
executable directory mode recursively to ordinary files.

## FO-04: Return a misplaced file — chown

`misplaced.txt` is mistakenly owned by root, with group learner and mode `0640`.
Transfer only its owner to learner. Preserve group learner, mode and content.
Inspect it before and after with `ls -l`. This task requires `sudo chown` inside
the container because learner does not own the file at the start.

## FO-05: Share with the right team — chgrp

`report.txt` is owned by learner, has group learner and mode `0640`. Change only
its group to teachers using `chgrp`. Keep owner, mode and content. Learner is
already a member of teachers, so this task can be completed without sudo.
The teacher account gains read access, while outsiders remain excluded.

## FO-06: Hand over an archive — chown owner:group and chmod

`handover.txt` starts owned by learner with group learner and mode `0666`.
Transfer it to owner archivist and group archive using `chown`'s `owner:group`
form, and tighten its mode to `0640`. Preserve the content. Archivist must have
read/write access and learner must lose read access after the handover. Think
about when you will still own the file; changing permissions after transferring
ownership requires `sudo chmod` in the sandbox.

## FO-07: Keep new files in the team — directory setgid

`shared` is owned by learner with group teachers and starts at `0777`. Make it
a shared workspace for learner and teachers only, with mode `2770`. The leading
2 sets **setgid on a directory**, which makes new entries inherit its group.
Ordinary files do not need executable or setgid bits for this task.

The teacher account's primary group is teacher and its supplementary groups
include teachers. The checker creates a uniquely named mock `group-check-*.txt`
as teacher and verifies that the file inherits teachers. Inspect that file with
`ls -l` after passing the check. Outsiders must be unable to enter or write in
the directory. This is a bonus step after basic ownership and permissions.

## Troubleshooting

| Symptom | What to do on the host |
| --- | --- |
| `Docker is not installed` | Complete step 1 above. |
| `Cannot connect to the Docker daemon` | Run `sudo systemctl start docker`, then `docker info`. |
| `permission denied` for docker.sock | Complete the group step, log out and back in, then retry `docker info`. |
| Download, DNS or package error during first build | Check internet access and retry the launcher; Docker keeps completed build layers. |
| Launcher asks for a normal terminal | Run it directly in a terminal, without a pipe or output redirection. |
| `./linux-ownership/lab: No such file` | Use `pwd` and `ls`; return to the cloned VulnHub repository folder. |
| `labctl` not found inside the sandbox | Submit on the host with `./labctl`; the practice image contains only the filesystem exercises. |
| Lost practice changes after exit | Each launch starts fresh. Host submissions are preserved; repeat the exercise if its flag was not submitted. |

After FO-07, continue with [file discovery](../linux-discovery/README.md), then P1.
Avoid broad changes such as `chmod -R 777` or
changing ownership of `/` on your host: all requested changes belong to the
specific practice paths in this container.
