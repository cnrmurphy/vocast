# VHS tape for the vocast README demo.
# Render with:  vhs assets/demo.tape
# Produces assets/demo_raw.mp4 (full length); the synthesis window is sped up
# afterward by assets/make_gif.sh to produce assets/demo.gif.
#
# Runs against a clean throwaway library at /tmp/vocast-demo-home (which symlinks
# the real ~/.cache so the Kokoro weights are reused, not re-downloaded).

# WebM, not MP4: this system's ffmpeg is built without libx264.
Output assets/demo_raw.webm

Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 720
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms

# --- Hidden setup: point at the clean library, activate venv, clean prompt ---
Hide
Type "export HOME=/tmp/vocast-demo-home PYTHONWARNINGS=ignore HF_HUB_OFFLINE=1 && cd /home/conor/workspace/vocast && source .venv/bin/activate && export PS1='\[\e[1;32m\]$\[\e[0m\] ' && clear"
Enter
Sleep 1s
Show

# --- 1. Show the subcommands ---
Type "vocast --help"
Sleep 600ms
Enter
Sleep 3.5s

# --- 2. Add an article from a URL (LIVE: fetch -> synthesize -> added) ---
Type "vocast add https://registerspill.thorstenball.com/p/joy-and-curiosity-89"
Sleep 600ms
Enter
# Block until synthesis finishes (the "added ..." line appears), up to 10 min.
# Synthesis runs slower here than standalone because the screenshotting contends
# for CPU with Kokoro, so the timeout is generous.
Wait+Screen@600s /added /
Sleep 2s

# --- 3. List the library ---
Type "vocast list"
Sleep 600ms
Enter
Sleep 4s

# --- 4. Ambiguous query -> disambiguation prompt (then cancel) ---
Type "vocast play joy"
Sleep 600ms
Enter
Sleep 3.5s
Enter
Sleep 2.5s

# --- 5. Serve the podcast feed ---
Type "vocast serve"
Sleep 600ms
Enter
Sleep 4.5s
Ctrl+C
Sleep 2s
