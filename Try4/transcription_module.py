"""English lecture capture using Distil-Whisper large-v3."""

from collections import deque
from pathlib import Path
import os
from queue import Empty, Full, Queue
import tempfile
import threading
import time
import wave

RECORD_SECONDS = 30
SAMPLE_RATE = 16_000
CHUNK_SIZE = 1_024
MAX_BUFFER_SECONDS = 15 * 60
MAX_TRANSCRIPT_SEGMENTS = MAX_BUFFER_SECONDS // RECORD_SECONDS
MODEL_REPOSITORY = os.getenv(
    "TRANSCRIBER_MODEL", "distil-whisper/distil-large-v3-openai"
)
MODEL_CACHE = Path(__file__).parent / ".model-cache"


def recent_text(buffer, lock, minutes=10):
    """Return successful transcript chunks recorded during the time window."""
    cutoff = time.time() - minutes * 60
    with lock:
        return " ".join(text for timestamp, text in buffer if timestamp >= cutoff and text)


def load_transcriber():
    """Load the English-focused Distil-Whisper checkpoint with FFmpeg decoding."""
    # The Xet helper stalls under this machine's application-control policy.
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    try:
        import torch
        import whisper
        from huggingface_hub import hf_hub_download
    except ImportError as error:
        raise RuntimeError("Install openai-whisper, torch, and huggingface-hub first.") from error

    requested_device = os.getenv("TRANSCRIBER_DEVICE", "auto").lower()
    use_cuda = requested_device == "cuda" or (
        requested_device == "auto" and torch.cuda.is_available()
    )
    device = "cuda" if use_cuda else "cpu"
    print(f"Downloading/loading English Distil-Whisper large-v3 on {device}...")
    model_path = hf_hub_download(
        repo_id=MODEL_REPOSITORY,
        filename="model.bin",
        cache_dir=MODEL_CACHE,
    )
    return whisper.load_model(model_path, device=device), use_cuda


def list_microphones():
    """Return available input devices so Windows' wrong default can be avoided."""
    try:
        import pyaudio
    except ImportError as error:
        raise RuntimeError("Install PyAudio before listing microphones.") from error

    audio = pyaudio.PyAudio()
    try:
        return [
            (index, info["name"])
            for index in range(audio.get_device_count())
            if (info := audio.get_device_info_by_index(index)).get("maxInputChannels", 0) > 0
        ]
    finally:
        audio.terminate()


def record_audio_chunk(duration=RECORD_SECONDS):
    """Record one WAV file and return its path. All audio resources are closed."""
    try:
        import pyaudio
    except ImportError as error:
        raise RuntimeError("Install PyAudio before recording.") from error

    descriptor, filename = tempfile.mkstemp(suffix=".wav")
    os.close(descriptor)  # Windows otherwise keeps the path locked.
    path = Path(filename)
    audio = pyaudio.PyAudio()
    stream = None
    frames = []
    sample_width = 2
    try:
        options = {
            "format": pyaudio.paInt16,
            "channels": 1,
            "rate": SAMPLE_RATE,
            "input": True,
            "frames_per_buffer": CHUNK_SIZE,
        }
        device_index = os.getenv("MIC_DEVICE_INDEX", "").strip()
        if device_index:
            try:
                options["input_device_index"] = int(device_index)
            except ValueError as error:
                raise RuntimeError("MIC_DEVICE_INDEX must be a number from --list-mics.") from error
        stream = audio.open(**options)
        sample_width = audio.get_sample_size(pyaudio.paInt16)
        for _ in range(int(SAMPLE_RATE / CHUNK_SIZE * duration)):
            frames.append(stream.read(CHUNK_SIZE, exception_on_overflow=False))
    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        audio.terminate()

    if not frames:
        path.unlink(missing_ok=True)
        raise RuntimeError("No microphone frames were recorded.")

    try:
        with wave.open(str(path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(sample_width)
            output.setframerate(SAMPLE_RATE)
            output.writeframes(b"".join(frames))
        return path
    except Exception:
        path.unlink(missing_ok=True)
        raise


def transcribe_audio(model, audio_path, use_fp16):
    """Transcribe one completed English recording with stable decoding settings."""
    result = model.transcribe(
        str(audio_path),
        language="en",
        task="transcribe",
        beam_size=5,
        temperature=0,
        condition_on_previous_text=False,
        no_speech_threshold=0.45,
        initial_prompt=os.getenv("TRANSCRIBER_HOTWORDS") or None,
        fp16=use_fp16,
    )
    return result.get("text", "").strip()


def add_transcript(buffer, lock, text):
    """Add a transcript and discard entries outside the rolling time window."""
    if not text:
        return
    with lock:
        buffer.append((time.time(), text))
        cutoff = time.time() - MAX_BUFFER_SECONDS
        while buffer and buffer[0][0] < cutoff:
            buffer.popleft()


def _record_loop(stop_event, recordings):
    """Keep recording while the transcription worker handles earlier clips."""
    while not stop_event.is_set():
        path = None
        try:
            path = record_audio_chunk()
            while not stop_event.is_set():
                try:
                    recordings.put(path, timeout=1)
                    path = None
                    break
                except Full:
                    print("Transcriber is catching up; waiting before recording another clip.")
        except Exception as error:
            print(f"Recording skipped: {error}")
            stop_event.wait(1)
        finally:
            if path is not None:
                path.unlink(missing_ok=True)


def capture_loop(stop_event, buffer, lock):
    """Continuously record and transcribe without losing speech during decoding."""
    try:
        model, use_fp16 = load_transcriber()
    except Exception as error:
        print(f"Cannot start transcription: {error}")
        return

    recordings = Queue(maxsize=3)
    recorder = threading.Thread(target=_record_loop, args=(stop_event, recordings), daemon=True)
    recorder.start()
    print("Listening for lecture audio...")
    while not stop_event.is_set() or not recordings.empty():
        audio_path = None
        try:
            audio_path = recordings.get(timeout=1)
            try:
                text = transcribe_audio(model, audio_path, use_fp16)
            finally:
                audio_path.unlink(missing_ok=True)
                audio_path = None

            if text:
                add_transcript(buffer, lock, text)
                print(f"Transcribed: {text[:120]}")
        except Empty:
            continue
        except Exception as error:
            print(f"Transcription skipped: {error}")
            stop_event.wait(1)
        finally:
            if audio_path is not None:
                audio_path.unlink(missing_ok=True)

    recorder.join(timeout=RECORD_SECONDS + 2)


def demo():
    lock = threading.Lock()
    buffer = deque([(time.time() - 601, "old"), (time.time(), "new")])
    assert recent_text(buffer, lock, minutes=10) == "new"
    print("Transcript window check passed.")


if __name__ == "__main__":
    demo()
