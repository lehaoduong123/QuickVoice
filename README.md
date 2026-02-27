# QuickVoice 🎙️

**Local voice-to-text for macOS** — hold a key, speak, release, and transcribed text is pasted at your cursor. Powered by OpenAI's Whisper, running 100% locally.

## Features

- 🔒 **Fully local** — no cloud, no API keys, your audio never leaves your machine
- ⌨️ **Hold-to-record** — hold Right ⌘, speak, release to transcribe & paste
- 🌐 **Multilingual** — auto-detects English, Chinese, Vietnamese (and 90+ other languages)
- ⚡ **Fast** — uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (4-5x faster than OpenAI's implementation)
- 🔁 **Auto-start** — optional macOS Launch Agent to start on login

## Quick Start

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4) or Intel
- Python 3.10+
- [Homebrew](https://brew.sh)

### Install & Run

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/QuickVoice.git
cd QuickVoice

# Run the setup script (installs portaudio + Python deps)
chmod +x setup.sh
./setup.sh

# Start QuickVoice
python3 quickvoice.py
```

### First Run

On first launch, the Whisper model will be downloaded (~500MB for `small`). After that, it's cached locally.

## macOS Permissions Setup

QuickVoice needs two macOS permissions to work. Without these, hotkey detection and audio recording will fail.

### 1. Accessibility (required for global hotkey)

1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Click the **+** button (unlock with your password if needed)
3. Add your **terminal app** (e.g., Terminal, iTerm2, Warp, VS Code)
4. Make sure the toggle is **ON**

> Without this, you'll see: `"This process is not trusted! Input event monitoring will not be possible"`

### 2. Microphone (required for audio recording)

1. Open **System Settings** → **Privacy & Security** → **Microphone**
2. Find your **terminal app** in the list
3. Make sure the toggle is **ON**

> If your terminal isn't listed, it will appear automatically the first time QuickVoice tries to record. Click **Allow** when prompted.

### 3. Automation (required for auto-paste)

1. Open **System Settings** → **Privacy & Security** → **Automation**
2. Find your **terminal app** and enable **System Events**

> Without this, transcribed text will be copied to your clipboard but won't auto-paste. You can still paste manually with ⌘V.

## Usage

1. Run `python3 quickvoice.py`
2. **Hold Right ⌘** to start recording
3. **Speak** in any supported language
4. **Release** — text is transcribed and pasted at your cursor

## Configuration

Edit [`config.py`](config.py) to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `MODEL_SIZE` | `"small"` | Whisper model: `tiny`, `base`, `small`, `medium`, `large-v3` |
| `RECORD_KEY` | `Key.cmd_r` | Key to hold for recording |
| `LANGUAGE` | `None` | Auto-detect, or force: `"en"`, `"zh"`, `"vi"` |
| `AUTO_PASTE` | `True` | Auto-paste transcription at cursor via ⌘V |
| `COMPUTE_TYPE` | `"int8"` | Inference optimization: `int8`, `float16`, `float32` |

## Auto-Start on Login

The setup script installs a macOS Launch Agent:

```bash
./setup.sh           # Install & enable auto-start
./setup.sh uninstall  # Remove auto-start
```

## Project Structure

```
QuickVoice/
├── quickvoice.py              # Main application
├── config.py                  # User-configurable settings
├── requirements.txt           # Python dependencies
├── setup.sh                   # Install & auto-start helper
└── com.quickvoice.agent.plist # macOS Launch Agent
```

## Tech Stack

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — CTranslate2-based Whisper inference
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) — microphone recording
- [pynput](https://pynput.readthedocs.io/) — global keyboard listener
- [pyperclip](https://github.com/asweigart/pyperclip) — clipboard access

## License

MIT
