import threading
import time
import schedule  # You'll need to install this: pip install schedule
from PIL import Image, ImageDraw, ImageFont  # For meme image creation
import os
import requests  # For Hugging Face API

# Import functions and variables from our modules
from transcription_module import (
    continuous_transcription_loop,
    get_last_n_minutes_text,
    load_whisper_model,
    # transcribed_text_buffer # For direct inspection if needed, but get_last_n_minutes_text is preferred
)

# Remove keyword_module imports (no longer needed)
from web_search_module_google_scrape import perform_web_search_google_scrape

# --- Configuration ---
KEYWORD_EXTRACTION_INTERVAL_MINUTES = 1  # For testing; change to 10 for production
# Ensure RECORD_CHUNK_DURATION_SECONDS in transcription_module.py is reasonable (e.g., 15-30s)

# --- Global Stop Event for Graceful Shutdown ---
stop_event = threading.Event()


# --- Summarization Function ---
def summarize_text(text):
    """
    Summarize text using (in order):
    1. Hugging Face Inference API (facebook/bart-large-cnn)
    2. Local transformers (facebook/bart-large-cnn)
    3. OpenAI GPT (ChatGPT, if OPENAI_API_KEY is set)
    4. Gemini (Google Generative Language API, if GEMINI_API_KEY is set)
    Returns summary string or None if all fail.
    """
    # 1. Hugging Face API
    print("[LOG] Summarizing transcript using Hugging Face API...")
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    hf_api_key = os.environ.get(
        "HUGGINGFACE_API_KEY", "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"
    )
    if hf_api_key:
        print(
            f"[LOG] Using Hugging Face API key: {'(from env)' if os.environ.get('HUGGINGFACE_API_KEY') else '(default provided)'}"
        )
    headers = {"Accept": "application/json", "Authorization": f"Bearer {hf_api_key}"}
    payload = {"inputs": text}
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if (
                isinstance(result, list)
                and len(result) > 0
                and "summary_text" in result[0]
            ):
                summary = result[0]["summary_text"]
                print(f"[OUTPUT] Summary (HuggingFace API): {summary}")
                return summary
            else:
                print(f"[ERROR] Unexpected response from Hugging Face: {result}")
        else:
            print(
                f"[ERROR] Hugging Face API error: {response.status_code} {response.text}"
            )
    except Exception as e:
        print(f"[ERROR] Exception during Hugging Face API summarization: {e}")
    # 2. Local transformers
    print("[LOG] Falling back to local summarization using transformers...")
    try:
        from transformers import pipeline

        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        max_chunk = 1024
        text_chunks = [text[i : i + max_chunk] for i in range(0, len(text), max_chunk)]
        summaries = []
        for chunk in text_chunks:
            out = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
            if out and isinstance(out, list) and "summary_text" in out[0]:
                summaries.append(out[0]["summary_text"])
        summary = " ".join(summaries)
        print(f"[OUTPUT] Summary (local): {summary}")
        return summary
    except ImportError:
        print(
            "[ERROR] transformers library not installed. Run 'pip install transformers torch'."
        )
    except Exception as e:
        print(f"[ERROR] Local summarization failed: {e}")
    # 3. OpenAI GPT (ChatGPT)
    print("[LOG] Falling back to OpenAI GPT (ChatGPT) summarization...")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        try:
            import openai

            openai.api_key = openai_api_key
            prompt = f"Summarize the following lecture transcript in a concise, context-aware way:\n{text}"
            # Linter: openai.ChatCompletion.create is the correct method
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.5,
            )
            summary = response["choices"][0]["message"]["content"].strip()
            print(f"[OUTPUT] Summary (OpenAI GPT): {summary}")
            return summary
        except ImportError:
            print("[ERROR] openai library not installed. Run 'pip install openai'.")
        except Exception as e:
            print(f"[ERROR] OpenAI GPT summarization failed: {e}")
    else:
        print("[LOG] OPENAI_API_KEY not set, skipping OpenAI GPT summarization.")
    # 4. Gemini (Google Generative Language API)
    print("[LOG] Falling back to Gemini summarization...")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        try:
            try:
                import google.generativeai as genai  # Linter: may not resolve if not installed, this is expected
            except ImportError:
                print(
                    "[ERROR] google-generativeai library not installed. Run 'pip install google-generativeai'."
                )
                return None
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-pro")
            prompt = f"Summarize the following lecture transcript in a concise, context-aware way:\n{text}"
            response = model.generate_content(prompt)
            summary = getattr(response, "text", None)
            if summary:
                summary = summary.strip()
                print(f"[OUTPUT] Summary (Gemini): {summary}")
                return summary
            else:
                print(
                    f"[ERROR] Gemini response did not contain summary text: {response}"
                )
        except Exception as e:
            print(f"[ERROR] Gemini summarization failed: {e}")
    else:
        print("[LOG] GEMINI_API_KEY not set, skipping Gemini summarization.")
    print("[ERROR] All summarization methods failed.")
    return None


def formulate_meme_prompt(keywords, web_search_results):
    print("[LOG] Entering formulate_meme_prompt")
    if not keywords:
        print("[LOG] No keywords provided to formulate_meme_prompt")
        return "A generic funny meme."
    base_prompt = f"A meme about {' and '.join(keywords)}."
    if web_search_results:
        first_snippet = web_search_results[0].get("snippet", "")
        if first_snippet:
            print(f"[LOG] Using web snippet in prompt: {first_snippet}")
            return f"{base_prompt} Context from web: {first_snippet}"
    print(f"[LOG] Prompt without web snippet: {base_prompt}")
    return base_prompt


def add_text_to_image(base_image_path, text_to_add, output_image_path):
    print(
        f"[LOG] Adding text to image. Base: {base_image_path}, Output: {output_image_path}"
    )
    try:
        img = Image.open(base_image_path)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            print("[LOG] Could not load 'arial.ttf', using default font.")
            font = ImageFont.load_default()
        text_position = (10, 10)
        text_color = (255, 255, 255)
        if len(text_to_add) > 50:
            print("[LOG] Text too long, truncating for image overlay.")
            text_to_add = text_to_add[:47] + "..."
        draw.text(text_position, text_to_add, font=font, fill=text_color)
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        img.save(output_image_path)
        print(f"[LOG] Image saved to {output_image_path}")
        return output_image_path
    except FileNotFoundError:
        print(f"[ERROR] Base image not found at {base_image_path}")
        return ""
    except Exception as e:
        print(f"[ERROR] Could not add text to image: {e}")
        return ""


def meme_generation_job():
    print("[LOG] meme_generation_job started.")
    # 1. Get the accumulated text from the transcriber
    current_lecture_segment = get_last_n_minutes_text(minutes=10)
    if current_lecture_segment:
        print(
            "[OUTPUT] Transcript segment (first 500 chars):\n"
            + current_lecture_segment[:500]
        )
    else:
        print("[OUTPUT] No transcript segment available.")
    if not current_lecture_segment or len(current_lecture_segment.split()) < 10:
        print("[LOG] Not enough new text to summarize. Skipping job.")
        return
    # 2. Summarize the transcript
    summary = summarize_text(current_lecture_segment)
    if not summary:
        print("[ERROR] Summarization failed. Skipping this cycle.")
        return
    # 3. Web Search using summary as query
    print(f"[LOG] Performing web search for summary: {summary}")
    web_search_results = perform_web_search_google_scrape(
        [summary], num_results=2, pause_time=2.5
    )
    if web_search_results:
        print("[OUTPUT] Web Search Results:")
        for i, result in enumerate(web_search_results):
            print(
                f"  [OUTPUT] Result {i+1}: Title: {result.get('title', 'N/A')}, Link: {result.get('link')}, Snippet: {result.get('snippet', 'N/A')}, Source: {result.get('source')}"
            )
    else:
        print(
            "[OUTPUT] No web search results found or an error occurred during scraping."
        )
    # 4. Meme Generation
    print("[LOG] Generating meme image...")
    meme_prompt = summary  # Use the summary directly as the meme prompt
    print(f"[OUTPUT] Meme prompt: {meme_prompt}")
    base_image_path = "memes/placeholder_meme.png"
    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    output_meme_filename = f"memes/generated_meme_{timestamp_str}.png"
    meme_image_path = add_text_to_image(
        base_image_path, meme_prompt, output_meme_filename
    )
    if meme_image_path:
        print(f"[OUTPUT] Meme saved to: {meme_image_path}")
    else:
        print("[ERROR] Meme generation failed.")
    print("[LOG] meme_generation_job complete.")


def main():
    print("Starting Lecture Meme Generator Application...")

    # Load the Whisper model once before starting the transcription thread
    try:
        print("Pre-loading Whisper model...")
        load_whisper_model()  # From transcription_module
    except Exception as e:
        print(
            f"Fatal Error: Could not load Whisper model. Application cannot start. {e}"
        )
        return

    # Start the continuous transcription in a separate thread
    transcription_thread = threading.Thread(
        target=continuous_transcription_loop, args=(stop_event,), daemon=True
    )
    transcription_thread.start()
    print("Transcription thread started.")

    # Give the transcription a moment to start
    print(f"Waiting a few seconds for transcription to initialize...")
    time.sleep(5)

    # Schedule the meme generation job
    print(
        f"Scheduling keyword extraction and web search job every {KEYWORD_EXTRACTION_INTERVAL_MINUTES} minute(s)."
    )
    schedule.every(KEYWORD_EXTRACTION_INTERVAL_MINUTES).minutes.do(meme_generation_job)

    print("Application running. Press Ctrl+C to stop.")
    try:
        while not stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCtrl+C received. Shutting down...")
    finally:
        print("Setting stop event for threads...")
        stop_event.set()
        if transcription_thread.is_alive():
            print("Waiting for transcription thread to finish...")
            transcription_thread.join(
                timeout=30
            )  # Wait for transcription to finish gracefully
            if transcription_thread.is_alive():
                print("Transcription thread did not stop in time.")
        print("Application shut down.")


if __name__ == "__main__":
    main()