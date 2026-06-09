#!/usr/bin/env bash
# Turn assets/demo_raw.mp4 (full-length, real synthesis) into assets/demo.gif,
# speeding up only the synthesis window so the GIF stays short.
#
# Usage: assets/make_gif.sh [T1] [T2] [TARGET_SECONDS]
#   T1             start of the synthesis window (s)         default 9.5
#   T2             end of the synthesis window (s)           default D-20.7
#   TARGET_SECONDS desired length of the sped-up window (s)  default 14
set -euo pipefail
cd "$(dirname "$0")/.."

RAW=assets/demo_raw.webm
SPEED_MP4=assets/demo_speed.webm
PALETTE=assets/palette.png
GIF=assets/demo.gif

D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RAW")
T1=${1:-9.5}
T2=${2:-$(awk "BEGIN{printf \"%.2f\", $D - 20.7}")}
TARGET=${3:-12}      # desired length of the sped-up synthesis window (s)
G=${4:-1.3}          # global speed factor applied to the whole demo
FPS=16
WIDTH=960
SPEED=$(awk "BEGIN{printf \"%.4f\", ($T2 - $T1) / $TARGET}")

echo "raw duration: ${D}s  |  synth window: [${T1}, ${T2}]  |  synth speedup: ${SPEED}x  |  global: ${G}x"

# Three segments: intro (1x*G), synthesis (SPEED*G), tail (1x*G).
ffmpeg -y -i "$RAW" -filter_complex "
  [0:v]trim=0:${T1},setpts=(PTS-STARTPTS)/${G}[a];
  [0:v]trim=${T1}:${T2},setpts=(PTS-STARTPTS)/(${SPEED}*${G})[b];
  [0:v]trim=${T2},setpts=(PTS-STARTPTS)/${G}[c];
  [a][b][c]concat=n=3:v=1[out]
" -map "[out]" -an -c:v libvpx-vp9 -b:v 0 -crf 28 "$SPEED_MP4"

# Two-pass palette for clean GIF colors at a README-friendly width.
ffmpeg -y -i "$SPEED_MP4" -vf "fps=${FPS},scale=${WIDTH}:-1:flags=lanczos,palettegen=stats_mode=diff" "$PALETTE"
ffmpeg -y -i "$SPEED_MP4" -i "$PALETTE" \
  -lavfi "fps=${FPS},scale=${WIDTH}:-1:flags=lanczos,paletteuse=dither=bayer:bayer_scale=3" "$GIF"

echo "wrote $GIF ($(du -h "$GIF" | cut -f1)), $SPEED_MP4 ($(du -h "$SPEED_MP4" | cut -f1))"
