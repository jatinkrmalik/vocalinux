# Vocalinux demo video

Product walkthrough used on GitHub and [vocalinux.com](https://vocalinux.com/#demo).

| File | Purpose |
|------|---------|
| `vocalinux-demo.mp4` | 1920×1080 H.264 + AAC, ~75s |
| `vocalinux-demo-poster.jpg` | Poster frame for the website `<video>` element |

## What it shows

1. Title card
2. Double-tap Ctrl tip
3. Live dictation into Mousepad on a Linux desktop
4. Privacy reminder (audio stays on-device)
5. Settings screenshots (engine + shortcuts)
6. Install command / GitHub outro

## How it was made (free / open source only)

No paid APIs or cloud TTS keys were used.

| Piece | Tool | License / notes |
|-------|------|-----------------|
| Screen capture | `ffmpeg` x11grab | LGPL/GPL |
| Editing / mux | `ffmpeg` | LGPL/GPL |
| Spoken narration + demo speech | [Piper](https://github.com/rhasspy/piper) (`en_US-lessac-medium`) | MIT (voice models from rhasspy/piper-voices) |
| Ambient music bed | Generated locally with Python + SoX (sine pad + reverb) | Original to this repo; free to reuse with the video |
| Title cards | ImageMagick + project icon assets | Project assets (GPL-3.0 with the app) |
| Live app footage | Vocalinux + Mousepad on XFCE | This project |

## Rebuilding

There is no checked-in render script yet; regenerating needs a desktop session, virtual mic, and the Piper binary/voice used above. Prefer editing the finished `vocalinux-demo.mp4` in place unless you are intentionally reshooting the live segment.
