# The Origin of the Alebrijes (middle-school video, ~5 min)

A narrated, illustrated 1080p video about how Pedro Linares' 1936 fever dream
gave birth to alebrijes, how the tradition spread to Oaxaca's copal-wood
carvers, and where alebrijes are today (giant parade, *Coco*). It ends with a
pause-and-answer quiz and a "design your own alebrije" challenge.

| Part | Time (approx.) |
|---|---|
| Title + hook: the dream creatures | 0:00 |
| What is an alebrije? | 0:30 |
| Pedro Linares, cartonero (1906) | 1:00 |
| 1936 fever → the dream → first alebrijes | 1:30 |
| Famous fans (Rivera, Kahlo) | 2:30 |
| 1975: to Oaxaca, copal-wood alebrijes | 2:55 |
| National Prize (1990), giant parade (2007–) | 3:45 |
| *Coco*: movie idea vs. real history | 4:10 |
| Quick quiz (with 5-second countdown) + answers | 4:35 |
| Your turn: design your own alebrije | 5:05 |

- `SCRIPT.md` / `scenes.json` — narration script, scene by scene
- `build.py` — assembles the video with ffmpeg: Ken Burns motion on each
  illustration, scene title chips, fact stickers, quiz/countdown cards,
  crossfades, music ducked under the voice, and English captions (`.srt` plus
  a soft-subtitle track in the MP4)
- `assets/sessions.json` — ElevenLabs flow and generation IDs for every
  narration clip, illustration and the music track

## Build

```
# put the downloaded media in assets/audio/<scene>.mp3, assets/img/<name>.png, assets/music.mp3
python3 build.py      # -> alebrijes_origin.mp4, alebrijes_origin.srt
```

Needs ffmpeg and Pillow. Illustrations are AI-generated artistic recreations,
not historical photographs; the end card says so.

## Status / next steps (for whoever finishes the build)

All media is already generated in ElevenLabs flow `fLhvgDtvZEPQvCRuG3Lm`; do
**not** regenerate it. To finish:

1. For each session ID in `assets/sessions.json`, call
   `creative_get_flow_run_status` (flow above) to get a fresh signed URL
   (they expire after 2 h) and download it with curl to
   `assets/audio/<key>.mp3`, `assets/img/<key>.png` (use the `master_url`
   PNG, not the webp preview) and `assets/music.mp3`. Needs network access to
   `storage.googleapis.com`.
2. Listen-check the music: it was generated without the instrumental flag. If
   it has vocals, regenerate once with `eleven_music_v2_5`, `instrumental: true`.
3. `python3 build.py`, then spot-check frames. The target is about 5:00; trim
   `LEAD`/`TAIL` or the end card if it runs long.
4. Commit `alebrijes_origin.mp4`, `alebrijes_origin.srt` and `assets/`.
