# Beginner OSINT at the Mfano Book Fair

The school newspaper is fact-checking its visitor guide before the Saturday
book fair. Use the three saved public sources below to check the venue, credit
a photograph and locate a desk. Everything in this open-source intelligence
(OSINT) exercise is fictional. You can do each case independently, offline,
with a text editor or by opening the files here on GitHub.

## OSINT-01 · Which hall is hosting the book swap?

Two venues appear in the [public notices](sources/notices.csv). The Fair
Committee organises the swap. Compare the publisher and date of each notice
about that activity. Which hall did the committee confirm? Look up that hall
in the [visitor map's booking table](sources/visitor-map.md) and submit its code.

## OSINT-02 · Who published the photograph first?

The newspaper wants to credit the photograph captioned **The first crate**.
The [press index](sources/press-index.csv) keeps one row per clipping. Find
the earliest publication with that exact caption and check whom the reprints
credit. Submit the original clipping's `edition_code`. All times in both
archives are East Africa Time (UTC+3).

## OSINT-03 · Where can visitors return books?

Find the Library Volunteers' directions for **Book returns** in the
[public notices](sources/notices.csv). Use both landmarks to locate their desk
on the [visitor map](sources/visitor-map.md). Squares that share an edge touch
above, below, left or right. Submit the desk code printed in that square.

## Submit a finding

Wrap the code exactly as printed in `MFANO{...}`. For example, a practice
code of `d3m0_01` would give `MFANO{d3m0_01}`. From the repository root on
Linux, use the matching challenge ID and paste the flag at the prompt.

```sh
./labctl labs --track OSINT
./labctl hints OSINT-01
./labctl submit OSINT-01
./labctl solved --track OSINT
```
