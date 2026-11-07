# Forensics: the mock exam leak

> These files are fake evidence made for this lab. They contain no real people,
> no real exam papers and no malware. You do not need the web portal running.

## The case

The Form 4 mock chemistry paper leaked two days before the exam. The discipline
office seized seven files from the school's shared drive, a staff laptop and the
corridor CCTV. Each file hides one flag. Find them all.

Every file is in [`evidence/`](evidence/). Work on a copy so you can always go
back to the original.

## Flag format

Every flag looks like `MFANO{...}`. The part inside the braces is words in
**leetspeak**, joined by `_`, for example `MFANO{c4n_h4ck_f0r_r34l}` (`a→4`,
`e→3`, `i→1`, `o→0`, sometimes `s→5`). Copy the digits exactly as you find them.

Pictures, sound and video show the flag in capitals. Keep `MFANO` in capitals,
write the inside part in lowercase, and keep every digit. In the pixel font, a
zero `0` has a slash through it, and a one `1` has a hook at the top while an
`I` has bars at the top and bottom.

```sh
python labctl.py submit 'MFANO{...}'
python labctl.py status
```

## The evidence

| Stage | File | Type | Difficulty |
| ----- | ---- | ---- | ---------- |
| F-01 | `01_noticeboard.png` | Image | Easy |
| F-02 | `02_staff_photo.png` | Image | Easy-Medium |
| F-03 | `03_prize_giving.png` | Image | Medium |
| F-04 | `04_school_bell.gif` | GIF | Easy-Medium |
| F-05 | `05_radio_call.wav` | Audio | Easy-Medium |
| F-06 | `06_assembly_recording.wav` | Audio | Medium |
| F-07 | `07_corridor_cctv.avi` | Video | Medium |

### F-01 The noticeboard

A notice the deputy principal drafted. The picture looks ordinary. The file
itself may say more than the picture does.

### F-02 The staff photo

The staff photo is far bigger than a picture of that size should be. Find out
what else is inside it.

### F-03 The prize-giving photo

Nothing is attached to this one, and the metadata is clean. The pixels
themselves have been tampered with, but not enough for you to see it.

### F-04 The school bell

An animation from the school website. Watch it carefully. Watching it is not
enough.

### F-05 The radio call

The security guard's radio picked up a strange series of beeps on the night of
the leak. Morse has codes for digits as well as letters. The words you decode go
inside the braces, joined by `_`.

### F-06 The assembly recording

A recording from the school hall that sounds like hum and hiss. Don't just
listen to it.

### F-07 The corridor CCTV

Six seconds of corridor CCTV from the night the paper leaked. Someone walks past
the camera, but was anything else captured?

## Tools that help

You do not need all of them. Each one is free.

- **Metadata:** `exiftool`, `strings`, `pngcheck`
- **Hidden files:** `binwalk`, `foremost`, `xxd` or any hex editor, `unzip`
- **Image steganography:** `zsteg`, StegSolve, CyberChef, Python with Pillow
- **GIF and video frames:** `ffmpeg`, ImageMagick `convert`/`magick`, ezgif.com
  (only for files from this lab), VLC frame stepping, `ffprobe`
- **Audio:** Audacity (spectrogram view), Sonic Visualiser, a Morse decoder

Stuck? Find out how each file type is built first: PNG chunks, GIF frames and
delays, WAV samples, AVI frames and metadata. Each flag hides in one of those
parts.
