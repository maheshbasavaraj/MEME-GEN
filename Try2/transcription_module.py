import speech_recognition as sr
import pyaudio
import time
import wave
import os
import whisper # Assuming 'pip install openai-whisper'
import torch # For checking CUDA
from collections import deque # For efficient rolling buffer of text

# --- Configuration from Step 2 ---
RECORD_CHUNK_DURATION_SECONDS = 15 # Duration of each small audio chunk to record and transcribe
WHISPER_MODEL_SIZE = "tiny"      # "tiny", "base", "small", "medium", "large"
TEMP_AUDIO_FILENAME = "temp_lecture_segment.wav"
MAX_TRANSCRIPT_BUFFER_MINUTES = 11 # Keep slightly more than 10 mins to be safe
MAX_TRANSCRIPT_SEGMENTS = int((MAX_TRANSCRIPT_BUFFER_MINUTES * 60) / RECORD_CHUNK_DURATION_SECONDS) # Approx number of chunks

# --- Global Variables for Transcription State ---
# This deque will store tuples of (timestamp, transcribed_text_chunk)
# Using deque for efficient appends and pops from either end.
transcribed_text_buffer = deque(maxlen=MAX_TRANSCRIPT_SEGMENTS)
is_gpu_available_for_whisper = False
whisper_model = None # To load model only once

# --- Helper: List Microphones (from Step 2) ---
def list_microphones():
    # ... (same as before) ...
    p = pyaudio.PyAudio()
    print("Available audio input devices:")
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if dev_info['maxInputChannels'] > 0:
            print(f"  {i}: {dev_info['name']} (Input Channels: {dev_info['maxInputChannels']})")
    p.terminate()


# --- Whisper Model Loading ---
def load_whisper_model():
    global whisper_model, is_gpu_available_for_whisper
    if whisper_model is None:
        print(f"Loading Whisper model ({WHISPER_MODEL_SIZE})... This may take a moment.")
        try:
            is_gpu_available_for_whisper = torch.cuda.is_available()
            if is_gpu_available_for_whisper:
                print("CUDA GPU detected. Whisper will attempt to use fp16.")
            else:
                print("No CUDA GPU detected or PyTorch CUDA not set up. Whisper will run on CPU (fp16=False).")
            whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
            print("Whisper model loaded successfully.")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            whisper_model = None # Ensure it's None if loading failed
            raise # Re-raise exception to stop execution if model can't load

# --- Audio Recording (from Step 2, slightly modified for clarity) ---
def record_audio_chunk(filename, duration, rate=16000, chunk_size=1024, channels=1, format=pyaudio.paInt16):
    p = pyaudio.PyAudio()
    # list_microphones() # Uncomment to select a specific microphone index if needed
    # stream = p.open(format=format, channels=channels, rate=rate, input=True,
    #                 frames_per_buffer=chunk_size, input_device_index=YOUR_MIC_INDEX_HERE)
    stream = p.open(format=format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk_size)
    # print(f"Recording {duration}s chunk...")
    frames = []
    for _ in range(0, int(rate / chunk_size * duration)):
        try:
            data = stream.read(chunk_size, exception_on_overflow=False) # Non-blocking read
            frames.append(data)
        except IOError as e:
            # This can happen if input overflows, common with non-blocking reads if not consumed fast enough
            # or if there's an issue with the audio stream.
            # print(f"PyAudio IOError during recording: {e}. Skipping this frame.")
            pass # Optionally log or handle more gracefully

    # print("Recording finished for chunk.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    if not frames:
        print("No frames recorded for chunk, possibly an audio input issue.")
        return False

    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(format)) # Use PyAudio instance for get_sample_size
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    return True

# --- Transcription with Whisper (from Step 2, uses global model) ---
def transcribe_chunk_with_whisper(audio_filename):
    global whisper_model, is_gpu_available_for_whisper
    if whisper_model is None:
        print("Whisper model not loaded. Cannot transcribe.")
        return "[Whisper model not loaded]"
    if not os.path.exists(audio_filename):
        print(f"Audio file {audio_filename} not found for transcription.")
        return "[Audio file not found]"

    try:
        # print(f"Transcribing {audio_filename}...")
        result = whisper_model.transcribe(audio_filename, fp16=is_gpu_available_for_whisper)
        # print(f"Raw Whisper result: {result}") # For debugging
        transcribed_text = result.get("text", "").strip()
        if not transcribed_text: # Handle cases where whisper might return empty text for silence
            return "[Silence or no speech detected]"
        return transcribed_text
    except Exception as e:
        return f"[Error during Whisper transcription: {e}]"
    finally:
        if os.path.exists(audio_filename):
            try:
                os.remove(audio_filename)
            except Exception as e_del:
                print(f"Warning: Could not delete temporary audio file {audio_filename}: {e_del}")

# --- Function to get the combined text from the last N minutes ---
def get_last_n_minutes_text(minutes=10):
    """
    Combines text chunks from the buffer that fall within the last N minutes.
    Note: This is a simplified version. A more robust way would be to use timestamps
    on each chunk, but for now, we rely on the deque's maxlen.
    This function assumes RECORD_CHUNK_DURATION_SECONDS is constant.
    """
    # For now, since deque manages the total duration via MAX_TRANSCRIPT_SEGMENTS,
    # we just join all current segments. The scheduler will call this every 10 mins.
    # A more precise implementation would filter by actual timestamps.
    if not transcribed_text_buffer:
        return ""

    # The deque already limits to roughly MAX_TRANSCRIPT_BUFFER_MINUTES.
    # We just need to join the text parts.
    # Each item in buffer is (timestamp, text_chunk)
    all_texts = [text_chunk for _, text_chunk in transcribed_text_buffer if not text_chunk.startswith("[")]
    return " ".join(all_texts)


# --- Main Transcription Loop (to be run by the application) ---
def continuous_transcription_loop(stop_event=None): # stop_event for graceful shutdown later
    """
    Continuously records audio in chunks, transcribes them, and adds to a buffer.
    """
    global transcribed_text_buffer
    print("Starting continuous transcription. Press Ctrl+C to stop.")
    load_whisper_model() # Load the model once at the start
    if whisper_model is None:
        print("Failed to load Whisper model. Exiting transcription loop.")
        return

    last_print_time = time.time()

    try:
        while True:
            if stop_event and stop_event.is_set():
                print("Stop event received. Exiting transcription loop.")
                break

            start_time = time.time()

            if record_audio_chunk(TEMP_AUDIO_FILENAME, RECORD_CHUNK_DURATION_SECONDS):
                transcribed_chunk = transcribe_chunk_with_whisper(TEMP_AUDIO_FILENAME)
                current_timestamp = time.time()
                transcribed_text_buffer.append((current_timestamp, transcribed_chunk))

                # Optional: Print the latest chunk for real-time feedback
                if not transcribed_chunk.startswith("["): # Don't print errors/silence too much
                    print(f"[{time.strftime('%H:%M:%S')}] Transcribed: {transcribed_chunk[:100]}...")
                elif time.time() - last_print_time > 30 : # Print status occasionally even if silence
                    print(f"[{time.strftime('%H:%M:%S')}] Status: {transcribed_chunk}")
                    last_print_time = time.time()

            else:
                print("Skipped transcription for a chunk due to recording error.")


            # Ensure loop runs roughly every RECORD_CHUNK_DURATION_SECONDS
            elapsed_time = time.time() - start_time
            sleep_time = RECORD_CHUNK_DURATION_SECONDS - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)
            # else:
                # print(f"Warning: Transcription cycle took longer ({elapsed_time:.2f}s) than chunk duration ({RECORD_CHUNK_DURATION_SECONDS}s).")


    except KeyboardInterrupt:
        print("Transcription loop interrupted by user (Ctrl+C).")
    except Exception as e:
        print(f"An error occurred in the transcription loop: {e}")
    finally:
        print("Exiting continuous transcription.")
        # Cleanup if needed, though temp file is deleted in transcribe_chunk_with_whisper

# --- How this integrates with Step 3 (Keyword Extraction) ---
# The TF-IDF keyword extraction functions (extract_keywords_tfidf, preprocess_text_for_tfidf, update_lecture_corpus)
# would reside in their own module (e.g., keyword_extractor.py) or within your main app logic.

# In your main application (which we'll build with the scheduler in Step 8):
# 1. The `continuous_transcription_loop` would run in a separate thread.
# 2. Every 10 minutes, the scheduler would:
#    a. Call `get_last_n_minutes_text()` to get the accumulated transcript.
#    b. Pass this text to `extract_keywords_tfidf()`.
#    c. Use the keywords for web search and meme generation.
#    d. Call `update_lecture_corpus()` with the processed version of the 10-minute text.

#if __name__ == "__main__":
'''def lecture_transcriber():
    # list_microphones() # Uncomment to check microphone index if needed

    # This is just to test the continuous transcription part.
    # In the full app, this loop would likely be started in a thread.
    print("Running transcription test. This will continuously record and transcribe.")
    print(f"Each audio chunk is {RECORD_CHUNK_DURATION_SECONDS}s.")
    print(f"The buffer will hold roughly the last {MAX_TRANSCRIPT_BUFFER_MINUTES} minutes of text.")
    continuous_transcription_loop()

    # To test getting the text (you'd do this from another part of your app):
    # time.sleep(60) # Let it run for a minute
    # recent_lecture_text = get_last_n_minutes_text()
    # print("\n--- Accumulated Text (last ~10 mins) ---")
    # print(recent_lecture_text)'''