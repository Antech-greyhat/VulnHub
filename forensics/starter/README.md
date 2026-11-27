# Beginner forensics in the print room

The Mfano print room has saved its queue, an email and three copies of the book
fair programme. Each exercise answers one question using these fictional files.
Start with F-08. All commands below run from the repository root on Linux.
They read the evidence in place and work offline.

## F-08 · Which print job finished first?

Which job first finished printing `programme.pdf` on the **hall** printer?
The [queue export](print-queue.csv) lists events from the same morning in East
Africa Time. Read the heading to see what each column means.

```sh
cat forensics/starter/print-queue.csv
```

Find the rows that match the printer, document and `printed` event. Compare
their timestamps and take the `job_id` from the earliest matching row.

## F-09 · Which message received a reply?

The committee saved a [print-room email](print-room.eml). Find the ID of the
message the print room was directly answering. Open the file as plain text
to see its headers above the blank line.

```sh
cat forensics/starter/print-room.eml
```

`Message-ID` identifies the saved email. `In-Reply-To` names its direct
parent, and `References` lists the thread history. For your answer, take the
part of the parent's ID between `<` and `@`.

## F-10 · Which copy matches the handover?

Three files have similar contents. Which one is byte-for-byte identical to
the programme recorded in the [handover note](handover.txt)? SHA-256 produces
a 64-character fingerprint of a file's contents.

```sh
cat forensics/starter/handover.txt
sha256sum forensics/starter/copies/*.txt
```

Compare the complete digest from the note with the first column of the command
output. Take the matching copy's filename and drop the directory and `.txt`.

## Submit a finding

Wrap the code you found in `MFANO{...}`, preserving its digits and underscores.
For example, a practice ID of `d3m0_01` would give `MFANO{d3m0_01}`. Use the
matching challenge ID at the submission prompt.

```sh
./labctl hints F-08
./labctl submit F-08
./labctl solved --track F
```

For more practice with images, sound and video, open the
[mock exam leak case](../README.md#the-case).
