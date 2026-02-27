"""
QuickVoice Configuration
========================
Edit these settings to customize your voice-to-text experience.
"""

from pynput.keyboard import Key

# ─── Whisper Model ───────────────────────────────────────────────
# Model options: "tiny", "base", "small", "medium", "large-v3"
# Larger = more accurate but slower. "base" is a good default for Apple Silicon.
MODEL_SIZE = "small"

# Compute type for inference optimization
# Options: "int8" (fastest), "float16", "float32" (most precise)
# "int8" is recommended for Apple Silicon CPU inference.
COMPUTE_TYPE = "int8"

# ─── Language ────────────────────────────────────────────────────
# Set to None for auto-detection (works well for EN/ZH/VI).
# Force a specific language: "en", "zh", "vi"
LANGUAGE = None

# ─── Hotkey ──────────────────────────────────────────────────────
# The key to hold for recording. Release to transcribe.
# Default: Right Command key (Key.cmd_r)
# Alternatives: Key.cmd, Key.ctrl_r, Key.f18, etc.
RECORD_KEY = Key.cmd_r

# ─── Audio Settings ──────────────────────────────────────────────
SAMPLE_RATE = 16000       # Whisper expects 16kHz audio
CHANNELS = 1              # Mono recording
CHUNK_SIZE = 1024         # Audio buffer chunk size
AUDIO_FORMAT = 8          # pyaudio.paInt16 = 8

# ─── Behavior ────────────────────────────────────────────────────
# Minimum recording duration in seconds (avoids accidental taps)
MIN_RECORD_SECONDS = 0.3

# Whether to auto-paste transcribed text at the cursor (via ⌘V)
AUTO_PASTE = True

# Show transcribed text in the terminal
SHOW_TRANSCRIPT = True
