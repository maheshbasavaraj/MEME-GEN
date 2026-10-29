import speech_recognition as sr
# For listing devices, not directly used by SpeechRecognition's mic class. Not needed if using Whisper
import pyaudio  # For listing devices, not directly used by SpeechRecognition's mic class
import time
import wave  # For saving audio if using Whisper directly with PyAudio
import os

# --- Configuration ---
RECORD_DURATION_SECONDS = 15  # Duration of each audio chunk to record for this test
USE_WHISPER = True  # Set to False to use Google Web Speech API via SpeechRecognition
WHISPER_MODEL_SIZE = "base"  # "tiny", "base", "small", "medium", "large". Larger is slower but more accurate.
TEMP_AUDIO_FILENAME = "temp_lecture_segment.wav"  # Used if USE_WHISPER is True


# --- Helper: List Microphones (Useful for debugging if default mic isn't working) ---
def list_microphones():
    p = pyaudio.PyAudio()
    print("Available audio input devices:")
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if dev_info["maxInputChannels"] > 0:
            print(
                f"  {i}: {dev_info['name']} (Input Channels: {dev_info['maxInputChannels']})"
            )
    p.terminate()


# --- Option A: Transcription using SpeechRecognition library (Google Web Speech API) ---
def transcribe_with_speechrecognition(recognizer, audio_source):
    print(
        f"Listening for {RECORD_DURATION_SECONDS} seconds (using Google Web Speech API)..."
    )
    try:
        audio_data = recognizer.listen(
            audio_source, phrase_time_limit=RECORD_DURATION_SECONDS
        )
        print("Processing audio...")
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.WaitTimeoutError:
        return "[No speech detected within the time limit]"
    except sr.UnknownValueError:
        return "[Google Web Speech API could not understand audio]"
    except sr.RequestError as e:
        return f"[Could not request results from Google Web Speech API service; {e}]"


# --- Option B: Transcription using OpenAI Whisper (Local) ---
# This requires PyAudio to record and save the file first, then Whisper transcribes the file.
def record_audio_for_whisper(
    filename, duration, rate=16000, chunk=1024, channels=1, format=pyaudio.paInt16
):
    p = pyaudio.PyAudio()
    # You might need to specify device_index if default is not your mic
    # list_microphones() # Uncomment to see device list and indices
    # For example, if your mic is index 2:
    # stream = p.open(format=format, channels=channels, rate=rate, input=True,
    #                 frames_per_buffer=chunk, input_device_index=2)
    stream = p.open(
        format=format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk
    )
    print(f"Recording {duration} seconds for Whisper...")
    frames = []
    for _ in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)
    print("Recording finished.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b"".join(frames))
    wf.close()


def transcribe_with_whisper(audio_filename):
    print("Loading Whisper model...")
    # Make sure you've run `pip install openai-whisper`
    # and have `ffmpeg` in your PATH
    try:
        import whisper
    except ImportError:
        print("Whisper not installed. Please run 'pip install openai-whisper'")
        return "[Whisper library not found]"
    import os  # for os.path.exists if you're cleaning up audio_filename

    # You would define audio_filename elsewhere
    # audio_filename = "temp_lecture_segment.wav"

    try:
        import torch

        use_fp16 = torch.cuda.is_available()
        if use_fp16:
            print("CUDA GPU detected. Using fp16 for Whisper.")
        else:
            print(
                "No CUDA GPU detected or PyTorch CUDA not set up. Whisper using fp32 (likely on CPU)."
            )
    except ImportError:
        print("PyTorch not found. Whisper using fp32 (likely on CPU).")
        use_fp16 = False

    try:
        model_name = "tiny"
        model = whisper.load_model(model_name)
        print(
            f"Transcribing {audio_filename} with Whisper ({model_name} model, fp16={use_fp16})..."
        )
        result = model.transcribe(audio_filename, fp16=use_fp16)
        transcribed_text = result["text"]
        # return transcribed_text # if in a function
        print(f"Transcription: {transcribed_text}")

    except Exception as e:
        print(f"An error occurred: {e}")
        # return f"[Error: {e}]" # if in a function
    finally:
        if os.path.exists(audio_filename):
            os.remove(audio_filename)  # Clean up temp file


# --- Main Logic ---
#if __name__ == "__main__":
def voice_transcriber():
    # list_microphones() # Uncomment this line if you need to find your microphone's index

    transcribed_lecture_segments = []  # This will store our text chunks

    r = sr.Recognizer()
    # Adjust microphone sensitivity if needed
    # r.energy_threshold = 4000 # Example: Higher value means less sensitive
    # r.dynamic_energy_threshold = True # Can help in noisy environments

    print("Starting Lecture Segment Transcription Test...")

    if USE_WHISPER:
        record_audio_for_whisper(TEMP_AUDIO_FILENAME, RECORD_DURATION_SECONDS)
        transcribed_text = transcribe_with_whisper(TEMP_AUDIO_FILENAME)
    else:
        # Use SpeechRecognition library's microphone access
        # You might need to specify device_index here too if default isn't working.
        # e.g., mic = sr.Microphone(device_index=1)
        with sr.Microphone() as source:
            print("Adjusting for ambient noise, please wait...")
            r.adjust_for_ambient_noise(source, duration=1)  # Adjust for 1 second
            transcribed_text = transcribe_with_speechrecognition(r, source)

    print("\n--- Transcribed Text ---")
    print(transcribed_text)
    print("------------------------\n")

    if transcribed_text and not transcribed_text.startswith(
        "["
    ):  # Avoid storing error messages
        transcribed_lecture_segments.append(transcribed_text)

    print("Current collected segments:")
    for i, segment in enumerate(transcribed_lecture_segments):
        print(f"Segment {i+1}: {segment[:100]}...")  # Print first 100 chars

    # In the full app, this script would loop, and `transcribed_lecture_segments`
    # would be managed to keep only the last 10 minutes of text.
