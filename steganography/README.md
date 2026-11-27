# Steganography at the Mfano Media Club

The media club has tucked short codes into its open-day material. Each case
uses an original file in this checkout. Open a terminal in the repository
root and solve the cases offline. The linked sections of 0xRick's tool guide
are optional reading.

## STEG-01 · The unsigned notice

The editor says there is an edition code immediately after the word
**edition**, but the notice looks ordinary. Open the original UTF-8 file.
[Club notice](evidence/club-notice.txt)

Some Unicode characters occupy no visible space. Python 3 can print their
names in reading order. Run this command from the repository root.

```sh
python3 - <<'PY'
from pathlib import Path
from unicodedata import name

notice = Path("steganography/evidence/club-notice.txt").read_text(encoding="utf-8")
for character in notice:
    if not character.isascii():
        print(name(character))
PY
```

Read each Unicode name as one character. For example, `TAG DIGIT FOUR` means
`4`, and `TAG LOW LINE` means `_`. Keep the letters lowercase and put the
result inside `MFANO{...}`. 0xRick lists Unicode text as one medium for
hiding a message. [Unicode Text Steganography](https://0xrick.github.io/lists/stego/#unicode-text-steganography)

## Submit a code

Run the command for your challenge and paste the completed flag at the
prompt. To preview a submission, add `--dry-run`.

```sh
./labctl labs --track STEG
./labctl hints STEG-01
./labctl submit STEG-01
./labctl solved --track STEG
```

For the scoring tools on Linux, follow the [CLI setup](../cli/README.md#install-and-open).
