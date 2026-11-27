# Steganography at the Mfano Media Club

The media club has tucked short codes into its open-day material. Each case
uses an original file in this checkout. Open a terminal in the repository
root and solve the cases offline. Each optional hint links to a section of
[0xRick's steganography reference](https://0xrick.github.io/lists/stego/).

The notice uses Python 3, the ticket uses ImageMagick, and the chime uses
Steghide. On Kali, Debian or Ubuntu, install all three with
`sudo apt install python3 imagemagick steghide`.

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

## STEG-02 · The unpunched ticket

The ticket desk records a three-digit serial by punching dots in three rows.
The design looks ready to print, but the punch marks are missing. Start with
the original PNG so you have its transparency channel. [Open-day ticket](evidence/open-day-ticket.png)

The alpha channel stores how opaque each pixel is. Two almost-opaque pixels
can look alike on screen. Extract the channel and stretch its lightest and
darkest values across the full range. This writes a new image. Choose an
unused output filename for `ticket-alpha.png`.

```sh
magick steganography/evidence/open-day-ticket.png -alpha extract -auto-level ticket-alpha.png
```

ImageMagick 6 calls the command `convert`. Open `ticket-alpha.png` in an image
viewer. Count the dots in each row, top to bottom, and join the three digits.
Put them after `t1ck3t_` inside the flag. For the idea behind changing image
levels to uncover a message, see [0xRick's Stegsolve notes](https://0xrick.github.io/lists/stego/#stegsolve).

## STEG-03 · The sound desk's archive slip

The studio's three-note chime carries an archive slip. The editor left the
passphrase on the accompanying cue sheet. Use the original
[WAV recording](evidence/studio-chime.wav) and [cue sheet](evidence/studio-cue.txt).

```sh
cat steganography/evidence/studio-cue.txt
steghide extract -sf steganography/evidence/studio-chime.wav -xf -
```

At the passphrase prompt, type the value beside `Archive phrase` and press
Enter. The `-sf` option selects the recording. The `-xf -` option prints the
recovered slip in the terminal. Put its `Archive code` inside `MFANO{...}`.
0xRick describes the media formats Steghide supports and its extraction
command in the [Steghide section](https://0xrick.github.io/lists/stego/#steghide).

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
