# FM-09 · Search the workshop board with grep

The school workshop board lists both `bench2` and `bench[2]`. Find the current
handover for `bench[2]`. The board and its practice accounts are fictional.

Before starting this exercise, complete concatenate’s room on TryHackMe.
[Regular Expressions](https://tryhackme.com/room/catregex)

## Get the practice file

For a new workspace, run the preparation command once from the repository
root. It copies the board into `var/linux-files/FM-09/`. [Workshop practice file](workshop-board.txt)

```sh
python3 -B linux-files/lab.py prepare
```

If you prepared your workspace before FM-09 was added, use these commands
from the repository root to add the board alongside your existing work.

```sh
mkdir -p var/linux-files/FM-09
cp -i linux-files/workshop-board.txt var/linux-files/FM-09/
```

Once the board is in place, enter the exercise directory.

```sh
cd var/linux-files/FM-09
```

## Choose how grep reads a pattern

`grep 'PATTERN' file.txt` prints each whole line containing a match. Quote the
pattern so the shell passes characters such as `*` and `[` to grep. Try these
searches on the board and compare the line numbers from the last two.

```sh
grep 'paint' workshop-board.txt
grep -n 'bench[1]' workshop-board.txt
grep -nF 'bench[1]' workshop-board.txt
```

By default, grep reads a **basic regular expression** (BRE). In a regex,
`[1]` matches the character `1`. The historical command `fgrep` is equivalent
to `grep -F`, which treats every character in the pattern literally, including
the brackets. The historical `egrep` is equivalent to `grep -E`, which uses
**extended regular expressions** (ERE). In ERE, `(archived|draft)` matches either
word. [GNU grep on basic and extended regular expressions](https://www.gnu.org/software/grep/manual/html_node/Basic-vs-Extended.html)

The first two commands below select the same rows. The first uses one extended
expression anchored at the start of the line. The second supplies two patterns
with `-e`. Each `-e` supplies one pattern, and a match on any of them selects
the line. You can repeat `-e` in basic, extended, or fixed-string mode.

```sh
grep -E '^(archived|draft)[|]' workshop-board.txt
grep -e '^archived[|]' -e '^draft[|]' workshop-board.txt
grep -F -e 'paint tray' -e 'hand drill' workshop-board.txt
```

## Options to try

| Option | What it does |
| --- | --- |
| `-R` | Searches files recursively under the given directory, following symbolic links. |
| `-h` | Hides filename prefixes when searching multiple files. |
| `-c` | Prints the number of matching lines per input file. Two matches on one line count once. |
| `-i` | Ignores case when matching. |
| `-l` | Prints the names of files containing a match. |
| `-n` | Prefixes selected lines with their line number, starting at 1. |
| `-v` | Selects lines that match none of the supplied patterns. |
| `-E` | Uses extended regular expressions for all supplied patterns. |
| `-F` | Treats the patterns as fixed strings. |
| `-e PATTERN` | Adds a pattern to the search. Repeat for additional patterns. |

Try `printf '%s\n' 'paint paint' 'hinge' | grep -c 'paint'`. It prints `1`
because both occurrences of `paint` are on the same line.

## Find the handover

Each data row uses the format `state|bench|field|value`.
For questions 3–5, use the `current` records for the literal label `bench[2]`.
In the FM-09 directory, create `answers.txt` with these five answers in order,
one per line. Copy values exactly, including case, punctuation and the final newline.

1. Do `egrep` and `fgrep` interpret patterns differently? Write `Yea` or `Nay`.
2. Which short grep option selects lines that do not match the pattern? Include the dash.
3. What username is on the handover?
4. What practice password is listed for that user?
5. What comment did that user leave?

From `var/linux-files/FM-09`, return to the repository root to check your
answers and submit the flag the checker prints.

```sh
cd ../../..
python3 -B linux-files/lab.py check FM-09
./labctl submit FM-09
```
