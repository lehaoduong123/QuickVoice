#!/usr/bin/env python3
"""
QuickVoice — Local Voice-to-Text
=================================
Hold a keyboard shortcut to record, release to transcribe.
Transcribed text is pasted at your cursor automatically.

Usage:
    python quickvoice.py
"""

import io
import sys
import time
import wave
import threading
import subprocess

import pyaudio
import pyperclip
from pynput import keyboard
from faster_whisper import WhisperModel
from AppKit import NSApplication

import config
from indicator import RecordingIndicator


# ─── Globals ─────────────────────────────────────────────────────
model = None
audio = None
stream = None
frames = []
is_recording = False
record_start_time = 0.0
lock = threading.Lock()
indicator = None


# ─── Model Loading ───────────────────────────────────────────────
def load_model():
    """Load the Whisper model. Downloads on first run, cached after."""
    global model
    print(f"⏳ Loading Whisper model '{config.MODEL_SIZE}'...")
    model = WhisperModel(
        config.MODEL_SIZE,
        device="cpu",
        compute_type=config.COMPUTE_TYPE,
    )
    print(f"✓ Model '{config.MODEL_SIZE}' loaded and ready.")


# ─── Audio Recording ────────────────────────────────────────────
def start_recording():
    """Begin capturing audio from the microphone."""
    global audio, stream, frames, is_recording, record_start_time

    with lock:
        if is_recording:
            return
        is_recording = True

    frames = []
    record_start_time = time.time()

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=config.AUDIO_FORMAT,
        channels=config.CHANNELS,
        rate=config.SAMPLE_RATE,
        input=True,
        frames_per_buffer=config.CHUNK_SIZE,
        stream_callback=_audio_callback,
    )
    stream.start_stream()
    print("🎙  Recording... (release key to stop)")
    if indicator:
        indicator.show()


def _audio_callback(in_data, frame_count, time_info, status):
    """PyAudio callback — accumulates audio frames."""
    frames.append(in_data)
    return (in_data, pyaudio.paContinue)


def stop_recording():
    """Stop recording and return the captured audio as a WAV byte buffer."""
    global audio, stream, is_recording

    with lock:
        if not is_recording:
            return None
        is_recording = False

    # Check minimum duration
    duration = time.time() - record_start_time
    if duration < config.MIN_RECORD_SECONDS:
        print("⚡ Too short — ignored.")
        _cleanup_audio()
        if indicator:
            indicator.hide()
        return None

    # Stop the stream
    if stream and stream.is_active():
        stream.stop_stream()
    _cleanup_audio()

    print(f"⏹  Stopped recording ({duration:.1f}s)")
    if indicator:
        indicator.show_transcribing()

    # Convert frames to WAV in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(config.CHANNELS)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(config.SAMPLE_RATE)
        wf.writeframes(b"".join(frames))
    wav_buffer.seek(0)
    return wav_buffer


def _cleanup_audio():
    """Release PyAudio resources."""
    global audio, stream
    if stream:
        stream.close()
        stream = None
    if audio:
        audio.terminate()
        audio = None


# ─── Transcription ───────────────────────────────────────────────
def transcribe(wav_buffer):
    """Transcribe a WAV audio buffer using Whisper."""
    if wav_buffer is None:
        return ""

    print("🔄 Transcribing...")
    segments, info = model.transcribe(
        wav_buffer,
        language=config.LANGUAGE,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=200,   # Split on shorter pauses
            speech_pad_ms=100,
        ),
    )

    text = " ".join(segment.text.strip() for segment in segments).strip()

    if config.SHOW_TRANSCRIPT:
        detected = info.language if config.LANGUAGE is None else config.LANGUAGE
        print(f"🌐 Language: {detected} | Prob: {info.language_probability:.0%}")
        print(f"📝 \"{text}\"")

    return text


# ─── Paste to Cursor ─────────────────────────────────────────────
def paste_text(text):
    """Copy text to clipboard and simulate ⌘V to paste at cursor."""
    if not text:
        return

    pyperclip.copy(text)

    if config.AUTO_PASTE:
        # Small delay to let clipboard update before pasting
        time.sleep(0.15)

        # Use osascript to simulate ⌘V — pastes into the frontmost app
        result = subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to keystroke "v" using command down',
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("✓ Pasted to cursor.")
        else:
            print(f"⚠️  Paste failed — text is in clipboard (⌘V manually).")
            print(f"   Tip: Grant Accessibility permission to your terminal in")
            print(f"   System Settings → Privacy & Security → Accessibility")
    else:
        print("✓ Copied to clipboard (auto-paste disabled).")


# ─── Hotkey Listener ─────────────────────────────────────────────
def on_press(key):
    """Called when any key is pressed."""
    if key == config.RECORD_KEY:
        start_recording()


def on_release(key):
    """Called when any key is released."""
    if key == config.RECORD_KEY:
        # Run transcription in a thread to avoid blocking the listener
        threading.Thread(target=_process_recording, daemon=True).start()


def _process_recording():
    """Stop recording, transcribe, and paste."""
    try:
        wav_buffer = stop_recording()
        if wav_buffer is None:
            return
        text = transcribe(wav_buffer)
        paste_text(text)
    finally:
        if indicator:
            indicator.hide()


# ─── Main ─────────────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  QuickVoice — Local Voice-to-Text")
    print("=" * 50)
    print()
    sys.stdout.flush()

    # Load model
    load_model()

    # Describe the hotkey
    key_name = config.RECORD_KEY.name if hasattr(config.RECORD_KEY, "name") else str(config.RECORD_KEY)
    print()
    print(f"🎤 Hold [{key_name}] to record, release to transcribe.")
    print(f"   Languages: auto-detect (EN / ZH / VI)")
    print(f"   Press Ctrl+C to quit.")
    print()
    sys.stdout.flush()

    # Initialize the indicator
    global indicator
    indicator = RecordingIndicator()

    # Function to monitor and restart the listener if it fails
    def monitor_listener():
        while True:
            try:
                with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                    print("✓ Keyboard listener started.")
                    sys.stdout.flush()
                    listener.join()
            except Exception as e:
                print(f"⚠️  Keyboard listener failed: {e}")
                print("   Retrying in 30 seconds...")
                sys.stdout.flush()
                time.sleep(30)

    # Start listener in a background thread so the main thread can run the AppKit event loop
    threading.Thread(target=monitor_listener, daemon=True).start()

    # Run the native macOS event loop on the main thread (required for the UI overlay)
    app = NSApplication.sharedApplication()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n👋 QuickVoice stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
