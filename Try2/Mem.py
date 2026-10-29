# Main application logic will go here.

# Load environment variables from .env file
from dotenv import load_dotenv
import os
import time # Added import time
import schedule # Added import schedule
import string # Added import string
from collections import Counter # Added import Counter
from PIL import Image, ImageDraw, ImageFont # Added Pillow imports
load_dotenv()

# Example of accessing API keys (replace with actual keys needed)
SPEECH_API_KEY = os.getenv("SPEECH_API_KEY")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")
MEME_API_KEY = os.getenv("MEME_API_KEY")

# You can add a print statement for testing, like:
# print(f"Speech API Key: {SPEECH_API_KEY}")
# (though be careful not to print actual keys in production logs)

STOP_WORDS = [
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "should",
    "can", "could", "may", "might", "must", "and", "but", "or", "nor",
    "for", "so", "yet", "in", "on", "at", "by", "from", "to", "with",
    "about", "above", "after", "again", "against", "all", "am", "as",
    "because", "before", "below", "between", "both", "during", "each",
    "few", "further", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "into", "it", "its", "itself",
    "me", "more", "most", "my", "myself", "no", "not", "of", "off",
    "once", "only", "other", "our", "ours", "ourselves", "out", "over",
    "own", "same", "she", "some", "still", "such", "than", "that", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "too", "under", "until", "up", "very",
    "we", "what", "when", "where", "which", "while", "who", "whom",
    "why", "you", "your", "yours", "yourself", "yourselves", "it's",
    "this is", "that is", "could be", "about", "lecture", "segment", # Added project specific
    "simulated", "python", "data", "science", "even", "memes", "themselves" # From placeholder
]

transcript_buffer = [] # Global list for transcript buffer

def prune_transcript_buffer():
    """Removes entries from transcript_buffer older than the time_window."""
    current_time = time.time()
    time_window = 12 * 60  # 12 minutes in seconds
    # Update global transcript_buffer in place
    transcript_buffer[:] = [
        item for item in transcript_buffer if current_time - item[0] < time_window
    ]

def capture_and_transcribe_chunk():
    """Simulates capturing and transcribing a chunk of audio."""
    current_timestamp = time.time()
    simulated_text = "This is a simulated lecture segment. It could be about Python, data science, or even memes themselves!"
    transcript_buffer.append((current_timestamp, simulated_text))
    print(f"Captured: {simulated_text}")
    prune_transcript_buffer()

def generate_meme_job():
    """Generates a meme based on recent lecture content."""
    print("INFO: Generating meme...")
    current_time = time.time()
    time_window_text = 10 * 60  # 10 minutes in seconds

    recent_texts = [
        item[1] for item in transcript_buffer if current_time - item[0] < time_window_text
    ]

    if not recent_texts:
        print("INFO: No recent text to process for meme generation.")
        return

    full_text = " ".join(recent_texts)
    
    # Text Cleaning
    cleaned_text = full_text.lower()
    translator = str.maketrans('', '', string.punctuation)
    cleaned_text = cleaned_text.translate(translator)

    # Stop Word Removal & Keyword Extraction
    words = cleaned_text.split()
    filtered_words = [word for word in words if word not in STOP_WORDS and len(word) > 2]

    if not filtered_words:
        print("INFO: No keywords found after filtering.")
        return

    word_counts = Counter(filtered_words)
    top_keywords = [item[0] for item in word_counts.most_common(3)]

    if top_keywords:
        print(f"INFO: Extracted keywords: {top_keywords}")
        simulated_search_results = search_web_for_keywords(top_keywords)
        print(f"INFO: Simulated web search results: {simulated_search_results}")

        meme_prompt = formulate_meme_prompt(top_keywords, simulated_search_results)
        print(f"INFO: Formulated meme prompt: {meme_prompt}")

        simulated_image_path = generate_image_from_prompt(meme_prompt)
        print(f"INFO: Simulated image path: {simulated_image_path}")

        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        output_meme_filename = f"memes/generated_meme_{timestamp_str}.png"
        text_for_meme = meme_prompt # Using the prompt as text for now

        final_meme_path = add_text_to_image(simulated_image_path, text_for_meme, output_meme_filename)
        if final_meme_path:
            print(f"INFO: Meme assembled and saved to: {final_meme_path}")
        else:
            print("ERROR: Failed to assemble meme.")
    else:
        print("INFO: No keywords extracted, skipping meme generation.")

    # Simulate work
    time.sleep(5) 
    print("INFO: Meme generation cycle complete!")

def formulate_meme_prompt(keywords: list[str], search_results: list[dict]) -> str:
    """Formulates a prompt for meme generation based on keywords and search snippets."""
    if not keywords:
        return "A generic funny meme."
    
    base_prompt = f"A meme about {' and '.join(keywords)}."
    
    if search_results:
        first_snippet = search_results[0].get('snippet', '')
        if first_snippet: # Append only if snippet is not empty
            return f"{base_prompt} Context from web: {first_snippet}"
            
    return base_prompt

def generate_image_from_prompt(prompt: str) -> str:
    """Simulates image generation based on a prompt and returns a placeholder path."""
    print(f"INFO: Simulating image generation for prompt: {prompt}")
    # In a real scenario, this would call an image generation API.
    # For now, it returns the path to a pre-generated placeholder.
    return "memes/placeholder_meme.png"

def add_text_to_image(base_image_path: str, text_to_add: str, output_image_path: str) -> str:
    """Adds text to an image and saves it."""
    try:
        img = Image.open(base_image_path)
        draw = ImageDraw.Draw(img)

        # Attempt to load a common font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 20) # Worker might need to adjust font size/name if arial isn't there
        except IOError:
            font = ImageFont.load_default()

        # Basic text positioning (e.g., top-left corner with some padding)
        text_position = (10, 10)
        text_color = (255, 255, 255) # White

        # Simple text wrapping (very basic)
        if len(text_to_add) > 50: # Arbitrary length for wrapping
            text_to_add = text_to_add[:47] + "..."

        draw.text(text_position, text_to_add, font=font, fill=text_color)
        
        # Ensure the output directory exists (it should, but good practice)
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        img.save(output_image_path)
        return output_image_path
    except FileNotFoundError:
        print(f"ERROR: Base image not found at {base_image_path}")
        return ""
    except Exception as e:
        print(f"ERROR: Could not add text to image: {e}")
        return ""

MOCK_SEARCH_DATA = {
    "python": {"image_url": "https://via.placeholder.com/300/0000FF/FFFFFF?Text=Python+Meme+Idea", "snippet": "Python: versatile, readable, and great for scripting."},
    "data": {"image_url": "https://via.placeholder.com/300/00FF00/FFFFFF?Text=Data+Science+Visual", "snippet": "Data science involves extracting knowledge from data."},
    "science": {"image_url": "https://via.placeholder.com/300/FF0000/FFFFFF?Text=Science+Concept", "snippet": "Science is the pursuit of knowledge."},
    "meme": {"image_url": "https://via.placeholder.com/300/FFFF00/000000?Text=Funny+Meme+Template", "snippet": "Memes are cultural touchstones, often humorous."},
    "simulated": {"image_url": "https://via.placeholder.com/300/CCCCCC/000000?Text=Simulated+Concept", "snippet": "Simulation is the imitation of a real-world process."},
    "lecture": {"image_url": "https://via.placeholder.com/300/9900CC/FFFFFF?Text=Lecture+Notes", "snippet": "A lecture is an oral presentation of information."},
}

def search_web_for_keywords(keywords: list[str]) -> list[dict]:
    """Simulates web search for keywords and returns mock image URLs and snippets."""
    search_results = []
    for keyword in keywords:
        if keyword in MOCK_SEARCH_DATA:
            search_results.append({
                "term": keyword,
                "image_url": MOCK_SEARCH_DATA[keyword]["image_url"],
                "snippet": MOCK_SEARCH_DATA[keyword]["snippet"]
            })
    return search_results

# Schedule the job
# For testing, you might use schedule.every(1).minutes.do(generate_meme_job) or even schedule.every(30).seconds.do(generate_meme_job)
schedule.every(10).minutes.do(generate_meme_job)

if __name__ == "__main__":
    print("Lecture Meme Generator Started. Press Ctrl+C to stop.")
    print(f"INFO: Search API Key Loaded: {'Yes' if SEARCH_API_KEY else 'No'}")
    print(f"INFO: Meme API Key Loaded: {'Yes' if MEME_API_KEY else 'No'}")
    # Uncomment for one immediate run for testing purposes
    # generate_meme_job() 

    try:
        while True:
            capture_and_transcribe_chunk() # Simulates continuous transcription
            schedule.run_pending()
            time.sleep(5)  # Simulate capturing audio chunks every 5 seconds
    except KeyboardInterrupt:
        print("\nStopping generator...")