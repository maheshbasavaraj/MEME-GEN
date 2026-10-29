import pyaudio
import time
import wave
import os
import whisper
import torch
from collections import deque
import logging

# --- Configuration ---
RECORD_CHUNK_DURATION_SECONDS = 15
WHISPER_MODEL_SIZE = "tiny"
TEMP_AUDIO_FILENAME = "temp_lecture_segment.wav"
MAX_TRANSCRIPT_BUFFER_MINUTES = 11
MAX_TRANSCRIPT_SEGMENTS = int((MAX_TRANSCRIPT_BUFFER_MINUTES * 60) / RECORD_CHUNK_DURATION_SECONDS)

# --- Global Variables ---
transcribed_text_buffer = deque(maxlen=MAX_TRANSCRIPT_SEGMENTS)
is_gpu_available_for_whisper = False
whisper_model = None

# --- Whisper Model Loading ---
def load_whisper_model():
    global whisper_model, is_gpu_available_for_whisper
    if whisper_model is None:
        logging.info(f"Loading Whisper model ({WHISPER_MODEL_SIZE})...")
        try:
            is_gpu_available_for_whisper = torch.cuda.is_available()
            if is_gpu_available_for_whisper:
                logging.info("CUDA GPU detected. Whisper will use fp16.")
            else:
                logging.info("No CUDA GPU detected. Whisper will run on CPU.")
            whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
            logging.info("Whisper model loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading Whisper model: {e}")
            whisper_model = None
            raise

# --- Audio Recording ---
def record_audio_chunk(filename, duration, rate=16000, chunk_size=1024):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate, input=True, frames_per_buffer=chunk_size)
    frames = []
    for _ in range(0, int(rate / chunk_size * duration)):
        try:
            data = stream.read(chunk_size, exception_on_overflow=False)
            frames.append(data)
        except IOError as e:
            logging.warning(f"PyAudio IOError during recording: {e}. Skipping frame.")
            pass
    stream.stop_stream()
    stream.close()
    p.terminate()

    if not frames:
        logging.warning("No frames recorded for chunk.")
        return False

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
    return True

# --- Transcription with Whisper ---
def transcribe_chunk_with_whisper(audio_filename):
    if whisper_model is None:
        logging.error("Whisper model not loaded. Cannot transcribe.")
        return "[Whisper model not loaded]"
    if not os.path.exists(audio_filename):
        logging.error(f"Audio file {audio_filename} not found for transcription.")
        return "[Audio file not found]"

    try:
        result = whisper_model.transcribe(audio_filename, fp16=is_gpu_available_for_whisper)
        transcribed_text = result.get("text", "").strip()
        if not transcribed_text:
            return "[Silence or no speech detected]"
        return transcribed_text
    except Exception as e:
        logging.error(f"Error during Whisper transcription: {e}")
        return f"[Error during Whisper transcription: {e}]"
    finally:
        if os.path.exists(audio_filename):
            try:
                os.remove(audio_filename)
            except Exception as e_del:
                logging.warning(f"Could not delete temporary audio file {audio_filename}: {e_del}")

# --- Get Text Buffer ---
def get_last_n_minutes_text(minutes=10):
    if not transcribed_text_buffer:
        return ""
    all_texts = [text_chunk for _, text_chunk in transcribed_text_buffer if not text_chunk.startswith("[")]
    return " ".join(all_texts)

# --- Main Transcription Loop ---
def continuous_transcription_loop(stop_event):
    logging.info("Starting continuous transcription.")
    if whisper_model is None:
        try:
            load_whisper_model()
        except Exception:
            logging.critical("Failed to load Whisper model in transcription loop. Exiting.")
            return

    last_status_print_time = time.time()

    while not stop_event.is_set():
        start_time = time.time()
        if record_audio_chunk(TEMP_AUDIO_FILENAME, RECORD_CHUNK_DURATION_SECONDS):
            transcribed_chunk = transcribe_chunk_with_whisper(TEMP_AUDIO_FILENAME)
            current_timestamp = time.time()
            transcribed_text_buffer.append((current_timestamp, transcribed_chunk))

            if not transcribed_chunk.startswith("["):
                logging.info(f"Transcribed: {transcribed_chunk[:100]}...")
            elif time.time() - last_status_print_time > 30:
                logging.info(f"Status: {transcribed_chunk}")
                last_status_print_time = time.time()
        else:
            logging.warning("Skipped transcription due to recording error.")

        elapsed_time = time.time() - start_time
        sleep_time = RECORD_CHUNK_DURATION_SECONDS - elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)

    logging.info("Exiting continuous transcription loop.")
