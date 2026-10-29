# Try4 — Try3-derived lecture meme generator

Try4 keeps Try3's working pipeline: microphone → English transcription → witty caption →
Imgflip template → saved meme. OpenRouter replaces the Gemini/OpenAI caption
writer and has a local fallback.

Install:

```powershell
pip install -r requirements.txt
```

Install FFmpeg separately for Whisper:

```powershell
winget install Gyan.FFmpeg
```

Create a `.env` file in this folder:

```text
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openrouter/free
TAVILY_API_KEY=your_tavily_key_here
IMGFLIP_USERNAME=your_imgflip_username
IMGFLIP_PASSWORD=your_imgflip_password
TRANSCRIBER_MODEL=distil-whisper/distil-large-v3-openai
TRANSCRIBER_DEVICE=auto
```

`distil-large-v3` is an English-focused, higher-accuracy replacement for the
old `tiny` model. The first run downloads its model files. Set
`TRANSCRIBER_DEVICE=cpu` to force CPU mode or `cuda` for a compatible NVIDIA GPU.
The model is cached in Try4's `.model-cache/` directory on `F:`, not on the
system drive.

Recording and transcription run separately, so the microphone continues to
capture the lecture while the previous clip is being decoded.

If `TAVILY_API_KEY` is set, each meme cycle performs one safe Tavily search
using a short, recent lecture excerpt. Its results only provide meme-format
context; the caption remains grounded in the lecture. Leave the key blank to
skip web search entirely.

Before testing, check that Windows is using the correct microphone:

```powershell
python main.py --list-mics
```

Put the number for the intended input device in `.env`, for example
`MIC_DEVICE_INDEX=2`. Leave it blank to use the Windows default.

Test one real recording and wait for its transcription:

```powershell
python main.py --once --wait 30
```

To test only the transcriber (no OpenRouter or Imgflip request), use:

```powershell
python main.py --transcribe-only --wait 30
```

Read the exact result at the end of `app.log`.

Run continuously (one meme every five minutes by default):

```powershell
python main.py
```

Use `--no-display` to save the image without opening it. If OpenRouter or
Imgflip is unavailable, Try4 still produces a local PNG fallback instead of
silently skipping the meme.
