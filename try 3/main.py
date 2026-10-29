import threading
import time
import schedule
from PIL import Image, ImageDraw, ImageFont
import os
import requests
import logging
import random
import textwrap
from dotenv import load_dotenv

import webbrowser

# Load environment variables from .env file
load_dotenv()

# Import functions from our modules
from transcription_module import (
    continuous_transcription_loop,
    get_last_n_minutes_text,
    load_whisper_model,
)
from web_search_module_google_scrape import perform_web_search_google_scrape
from topics import INTERESTED_TOPICS, NOT_INTERESTED_TOPICS

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(module)s] - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# --- Configuration ---
MEME_GENERATION_INTERVAL_MINUTES = 5  # Generate a meme every 5 minutes

# --- Global Stop Event for Graceful Shutdown ---
stop_event = threading.Event()


# --- Imgflip Meme Generation ---
def create_meme_with_imgflip(text, output_filename):
    """
    Creates a meme using the Imgflip API and saves it.
    """
    IMGFLIP_API_URL = "https://api.imgflip.com/caption_image"
    username = os.environ.get("IMGFLIP_USERNAME")
    password = os.environ.get("IMGFLIP_PASSWORD")

    if not all([username, password]):
        logging.error("IMGFLIP_USERNAME and IMGFLIP_PASSWORD not found in .env file. Skipping meme generation.")
        return None

    # 1. Get popular meme templates
    try:
        response = requests.get("https://api.imgflip.com/get_memes")
        response.raise_for_status()
        data = response.json()
        if not data['success']:
            logging.error(f"Imgflip API error when getting templates: {data.get('error_message')}")
            return None
        templates = data['data']['memes']
        # Filter for templates with 2 text boxes, as they are common
        two_box_templates = [t for t in templates if t['box_count'] == 2]
        if not two_box_templates:
            logging.warning("No two-box meme templates found, using any popular one.")
            two_box_templates = templates
        template = random.choice(two_box_templates)
        logging.info(f"Selected meme template: {template['name']} (ID: {template['id']})")
    except Exception as e:
        logging.error(f"Failed to get meme templates from Imgflip: {e}")
        return None

    # 2. Split text for top and bottom boxes
    # Simple split: first half top, second half bottom
    words = text.split()
    split_point = len(words) // 2
    top_text = " ".join(words[:split_point])
    bottom_text = " ".join(words[split_point:])

    # 3. Caption the image
    params = {
        "template_id": template['id'],
        "username": username,
        "password": password,
        "text0": top_text,
        "text1": bottom_text
    }
    try:
        response = requests.post(IMGFLIP_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if not data['success']:
            logging.error(f"Imgflip API error when captioning image: {data.get('error_message')}")
            return None
        
        meme_url = data['data']['url']
        logging.info(f"Successfully created meme, URL: {meme_url}")

        # 4. Download the image
        meme_response = requests.get(meme_url)
        meme_response.raise_for_status()
        with open(output_filename, 'wb') as f:
            f.write(meme_response.content)
        logging.info(f"Meme image saved to {output_filename}")
        return output_filename

    except Exception as e:
        logging.error(f"Failed to create or download meme from Imgflip: {e}")
        return None


def summarize_for_meme(text: str, topic: str) -> str | None:
    """
    Summarizes the transcript with a focus on creating a short, witty, and context-aware caption for a meme.
    It prioritizes powerful LLMs (Gemini, OpenAI) for the best results.
    """
    logging.info("Attempting to summarize text for a meme...")
    
    # Define the specialized prompt
    prompt = f"""
    You are a comedy writer. Your job is to find the single funniest or most absurd idea in the following text and turn it into a short, punchy meme caption.
    Make it sarcastic, ironic, or just plain weird. Keep it under 15 words.
    The meme should be related to the topic: {topic}.

    Text:
    "{text}"

    Meme Caption:
    """
    
    # --- Attempt 1: Google Gemini ---
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        logging.info("Using Google Gemini for summarization.")
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            summary = getattr(response, "text", "").strip()
            if summary:
                logging.info(f"Summary (Gemini): {summary}")
                return summary
        except Exception as e:
            logging.error(f"Gemini summarization failed: {e}")

    # --- Attempt 2: OpenAI GPT ---
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        logging.info("Falling back to OpenAI GPT for summarization.")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7,
            )
            summary = response.choices[0].message.content.strip()
            if summary:
                logging.info(f"Summary (OpenAI): {summary}")
                return summary
        except Exception as e:
            logging.error(f"OpenAI GPT summarization failed: {e}")

    logging.error("All summarization methods failed.")
    return None


def formulate_meme_prompt(summary, web_search_results):
    # (This function remains the same as before)
    logging.info("Entering formulate_meme_prompt")
    if not summary:
        logging.warning("No summary provided to formulate_meme_prompt")
        return "A generic funny meme."
    base_prompt = summary
    if web_search_results:
        first_snippet = web_search_results[0].get("snippet", "")
        if first_snippet and "not available" not in first_snippet:
            logging.info(f"Using web snippet to enhance prompt: {first_snippet}")
            return f"{first_snippet} - {summary}"
    return base_prompt


def identify_topics_from_text(text: str) -> list[str]:
    """
    Uses an LLM to identify the main topics from a given text segment.
    """
    logging.info("Identifying topics from text...")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        logging.error("GEMINI_API_KEY not found. Cannot identify topics.")
        return []

    prompt = f"""
    Analyze the following text and identify the top 2-3 main topics or subjects being discussed.
    Return these topics as a comma-separated list. For example: "Artificial Intelligence, Machine Learning, Python Programming"

    Text:
    "{text}"

    Topics:
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        topics_text = getattr(response, "text", "").strip()
        if topics_text:
            identified_topics = [topic.strip() for topic in topics_text.split(',')]
            logging.info(f"Identified topics: {identified_topics}")
            return identified_topics
        return []
    except Exception as e:
        logging.error(f"Topic identification failed: {e}")
        return []


def verify_meme_relevance(original_text: str, meme_caption: str, topic: str) -> bool:
    """
    Uses an LLM to verify if a meme caption is relevant, funny, and professional.
    """
    logging.info(f"Verifying meme caption: '{meme_caption}'")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        logging.error("GEMINI_API_KEY not found. Skipping verification.")
        return True # Default to true if verification can't run

    prompt = f"""
    You are a content moderator for a professional, academic setting. Your task is to evaluate a generated meme caption based on a lecture transcript.

    The caption MUST be:
    1.  **Relevant:** It must clearly relate to a concept in the original text.
    2.  **Witty/Clever:** It should be genuinely funny or clever, not just a random statement.
    3.  **Meaningful:** It must have a clear and understandable meaning.
    4.  **Topical:** It must be related to the topic: {topic}.
    5.  **Professional:** It must NOT contain any offensive, inappropriate, or sexual content.

    Original Text:
    "{original_text}"

    Generated Meme Caption:
    "{meme_caption}"

    Based on these rules, is the caption acceptable? Respond with only "YES" or "NO".
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        decision = getattr(response, "text", "").strip().upper()
        logging.info(f"Verification result: {decision}")
        return decision == "YES"
    except Exception as e:
        logging.error(f"Meme verification failed: {e}")
        return False # Fail safe if the API call has an error


def meme_generation_job():
    logging.info("Meme generation job started.")

    current_lecture_segment = get_last_n_minutes_text(minutes=MEME_GENERATION_INTERVAL_MINUTES)
    if not current_lecture_segment or len(current_lecture_segment.split()) < 10:
        logging.info("Not enough new text to summarize. Using default text for testing.")
        current_lecture_segment = (
            "This is a default paragraph that is long enough to be summarized. "
            "It is being used for testing purposes to ensure that the summarization "
            "and meme generation process works as expected even when there is no "
            "new transcript data available. This helps in demonstrating the "
            "functionality of the system without relying on real-time audio input."
        )

    logging.info(f"Transcript segment for meme generation: {current_lecture_segment}")

    # Dynamically identify topics and combine with pre-defined interests
    lecture_topics = identify_topics_from_text(current_lecture_segment)
    combined_topics = INTERESTED_TOPICS + lecture_topics
    
    # Filter out any not-interested topics
    final_topics = [t for t in combined_topics if t.lower() not in [ni.lower() for ni in NOT_INTERESTED_TOPICS]]
    
    if not final_topics:
        logging.warning("No suitable topics found after filtering. Using default interested topics.")
        final_topics = INTERESTED_TOPICS

    topic = random.choice(final_topics)
    logging.info(f"Selected topic for this run: {topic}")

    verified_meme_text = None
    for attempt in range(3): # Retry up to 3 times
        logging.info(f"Meme generation attempt {attempt + 1}...")
        
        summary = summarize_for_meme(current_lecture_segment, topic)
        if not summary:
            logging.warning("Summarization failed for this attempt.")
            continue

        if verify_meme_relevance(current_lecture_segment, summary, topic):
            logging.info("Meme caption passed verification.")
            verified_meme_text = summary
            break
        else:
            logging.warning(f"Meme caption '{summary}' failed verification. Retrying...")

    if not verified_meme_text:
        logging.error("Failed to generate a verified meme caption after 3 attempts. Skipping this cycle.")
        return

    web_search_results = perform_web_search_google_scrape([verified_meme_text], num_results=1)
    meme_text = formulate_meme_prompt(verified_meme_text, web_search_results)
    logging.info(f"Final meme text: {meme_text}")

    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    output_meme_filename = f"memes/generated_meme_{timestamp_str}.jpg"
    
    meme_image_path = create_meme_with_imgflip(meme_text, output_meme_filename)
    
    if meme_image_path:
        logging.info(f"Successfully generated meme: {meme_image_path}")
        display_meme(meme_image_path)
    else:
        logging.error("Meme generation with Imgflip failed.")
        
    logging.info("Meme generation job complete.")


def display_meme(image_path):
    """
    Opens the generated meme image in the default image viewer.
    """
    logging.info(f"Displaying meme: {image_path}")
    try:
        webbrowser.open(image_path)
    except Exception as e:
        logging.error(f"Failed to display meme: {e}")


def main():
    """
    Main function to run the application.
    """
    logging.info("Starting Lecture Meme Generator Application...")

    try:
        logging.info("Pre-loading Whisper model...")
        load_whisper_model()
    except Exception as e:
        logging.critical(f"Fatal Error: Could not load Whisper model. {e}")
        return

    transcription_thread = threading.Thread(
        target=continuous_transcription_loop, args=(stop_event,), daemon=True
    )
    transcription_thread.start()
    logging.info("Transcription thread started.")

    # --- Main Loop for Testing (runs once) ---
    logging.info("Running in single-test mode. Will run for 20 seconds to capture audio.")
    time.sleep(20) # Let transcription run for a bit

    logging.info("Triggering meme generation job manually for test.")
    meme_generation_job()

    # --- Shutdown ---
    logging.info("Test cycle complete. Shutting down...")
    stop_event.set()
    if transcription_thread.is_alive():
        logging.info("Waiting for transcription thread to finish...")
        transcription_thread.join(timeout=10)
        if transcription_thread.is_alive():
            logging.warning("Transcription thread did not stop in time.")
    logging.info("Application shut down.")


if __name__ == "__main__":
    main()