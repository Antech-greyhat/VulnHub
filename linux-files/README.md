# Linux file manipulation: start here

Eight short exercises introduce reading, writing, filtering and combining text
files before the web challenges. All school records are invented. You need
Python 3.10+, Bash, coreutils, grep and less; Docker is not needed for this track.
On Kali, Debian or Ubuntu, missing tools can be installed with:

```sh
sudo apt install python3 bash coreutils grep less
```

## Prepare, practise and submit

Run this once from the repository folder:

```sh
python3 -B linux-files/lab.py prepare
```

This creates your exercise files under `var/linux-files/`. It refuses to replace
an existing workspace, preserving your answers. Work through FM-01 to FM-08 in
order. Start a shell in the first exercise:

```sh
cd var/linux-files/FM-01
```

Use `pwd` to see where you are and `ls` to list the files. Paths in each task are
relative to that exercise's directory. A **command** is the program name, an
**option** changes its behavior, and a **pipe** (`|`) sends one command's output
to another. For example, `cat example.txt | wc -l` counts the file's lines.
Use `man cat` or `cat --help` to look up options. `q` exits a manual or `less`.

After making the requested output, return to the repository folder to check it:

```sh
cd ../../..
python3 -B linux-files/lab.py check FM-01
./labctl submit FM-01
```

The checker reveals the challenge's flag only after the output is correct. Paste
it into labctl's hidden box to record the solve. Checking does not change your
score. For another exercise, replace FM-01 in the directory and commands.
`./labctl labs --track FM` lists the exercises; `./labctl hints FM-01` offers a clue.

To start another attempt without overwriting your first, use a new directory:

```sh
python3 -B linux-files/lab.py prepare --workspace var/linux-files-attempt-2
python3 -B linux-files/lab.py check FM-01 --workspace var/linux-files-attempt-2
```

## FM-01: Read and combine — cat

Read `part-a.txt` and `part-b.txt`. Combine them in that order into `answer.txt`.
The first file deliberately has no final newline: do not add a space or a line
break between the parts. Learn how `cat` handles more than one input file and
how `>` sends its output to a file.

## FM-02: Write a handover — echo, > and >>

`handover.txt` contains an outdated note. Use `echo` to **replace** it with the
first line below, then **append** the other two lines. Produce exactly these
three lines, each ending with a newline:

```text
School backup handover
Owner: learner
Status: ready
```

Read the result with `cat`. `>` overwrites a file; `>>` appends. Quote text with
spaces or shell punctuation. Use separate `echo` commands rather than relying
on the nonportable behavior of `echo -e`.

## FM-03: Search a long document — less

Open `handbook.txt` with `less`. Search for `backup-window` using `/`, move to
the next match with `n`, and distinguish the ACTIVE entry from the RETIRED one.
Copy the complete ACTIVE line into `answer.txt`, with a final newline. Practise
Space/Page Down, `b`/Page Up, `g` for the start, `G` for the end, and `q` to quit.

## FM-04: Read the bookends — head and tail

Inspect `session.log` without printing all its lines. Write its first line and
its last line, in that order, into `bookends.txt`. Use explicit line counts:
`head` and `tail` normally show ten lines. Combine replacement and append
redirection so the first line is preserved when you add the last one.

## FM-05: Restore time order — tac

`newest-first.log` has one event per line, newest first. Produce
`oldest-first.log` with the oldest event first, using `tac`. It reverses the
order of lines while keeping each line's characters intact. Compare the input
and output with `cat`.

## FM-06: Count real failures — grep and wc

`backup.log` mixes successful jobs, failed jobs, debug messages containing the
word ERROR, and a different service named backup-check. Select only lines that
**start with `ERROR backup `**, keeping their original order, into
`failures.txt`. Count those selected lines with `wc -l` and put only the number
in `count.txt` (padding around the number is accepted). Both files are checked.

Learn grep's `^` anchor and literal spaces. Counting a matching word anywhere
in the log overcounts; `wc -w` counts words rather than records. Reading wc's
input through a pipe or `<` avoids adding a filename to its output.

## FM-07: Pair aligned columns — paste

The corresponding lines in `names.txt` and `scores.txt` describe the same
student. Use `paste` to create `results.tsv`: name first, score second, separated
by one tab, one student per line, with no header. Do not concatenate all names
before all scores. A TSV file is a text table whose columns are separated by tabs.

## FM-08: Match records by ID — join

`roster.txt` and `marks.txt` are deliberately in different orders. Each begins
with a student ID, followed by one value. Create `joined.txt` containing only
IDs present in **both** files, in ascending ID order, with columns
`student-ID name score` separated by single spaces and no header.

Use `LC_ALL=C sort` to prepare each input by its first field, then `join` to
match equal keys. Set the same locale for sorting and joining. One roster ID has
no marks and one marks ID has no roster entry: an inner join omits both. `paste`
would pair rows by position and give the wrong student a score.

## What to remember

The checker assesses your result, not your shell history. For the intended
practice, use each task's named commands and explain why its options and
redirections work. Keep the original inputs for comparison. Once this track is
complete, move on to [permissions and ownership](../linux-ownership/README.md),
then P1's web and Linux labs.
