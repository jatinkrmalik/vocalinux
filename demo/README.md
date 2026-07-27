# Vocalinux demo video

Product walkthrough for GitHub, YouTube, and [vocalinux.com](https://vocalinux.com/#demo).

| File | Purpose |
|------|---------|
| `vocalinux-demo.mp4` | 1920×1080 H.264 + AAC launch cut (~53s) |
| `vocalinux-demo-poster.jpg` | Poster frame for the website `<video>` element |

## What it shows

1. Hook + title
2. Live dictation into Mousepad
3. Privacy beat
4. Fast settings montage (Speech Engine, Recognition, Audio, Shortcuts, General, Advanced, tray, About)
5. Install CTA

## How it was made (free / open source only)

No paid APIs or cloud TTS keys.

| Piece | Tool | Notes |
|-------|------|-------|
| Screen capture | `ffmpeg` x11grab + Cursor screen recording | Live UI tour + dictation |
| Edit / motion | `ffmpeg` (`zoompan`, `xfade`) + ImageMagick | Eased zooms, wipe/slide transitions |
| Narration | [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (`af_heart`) via `kokoro` | Apache-2.0, offline |
| Dictation demo voice | Kokoro (`am_michael`) | Separate voice from narrator |
| Music | Procedural beat bed (Python/NumPy) mixed with [SoundHelix](https://www.soundhelix.com/) example track | SoundHelix examples are free for any use; beat bed is original |
| Title cards / labels | ImageMagick + project icons | GPL-3.0 with the app |

YouTube description credit line you can paste:

```text
Music: original beat bed + SoundHelix example track (https://www.soundhelix.com/)
Voice: Kokoro-82M (https://huggingface.co/hexgrad/Kokoro-82M)
```
