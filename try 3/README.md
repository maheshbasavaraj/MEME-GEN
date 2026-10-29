# Lecture Meme Generator

This project is a Python application that listens to a lecture or any continuous audio stream, transcribes it in real-time, and periodically generates memes based on the spoken content.

## Features

- **Continuous Audio Transcription:** Uses the OpenAI Whisper model to transcribe audio from a microphone in real-time.
- **Automatic Meme Generation:** Periodically analyzes the transcribed text to generate relevant memes.
- **Multi-API Summarization:** Leverages Hugging Face, local transformers, OpenAI GPT, and Google Gemini to summarize the lecture content.
- **Web Context:** Uses Google search to find contextually relevant information based on the lecture content to enrich the memes.
- **Extensible and Modular:** The project is divided into several modules for easy understanding and extension.

## Project Structure

```
.
├── .env                  # For storing API keys
├── main.py               # Main application entry point
├── transcription_module.py # Handles continuous audio transcription
├── keyword_module.py     # For extracting keywords from text
├── web_search_module_google_scrape.py # For performing web searches
├── Mem.py                # Contains core logic for meme generation
├── voice_transcriber.py  # An earlier version of the transcription module
├── requirements.txt      # Project dependencies
└── memes/                # Directory for generated memes
    └── placeholder_meme.png
```

### Modules

- **`main.py`**: The main script that orchestrates the entire process. It starts the transcription thread and schedules the meme generation job.
- **`transcription_module.py`**: This module is responsible for capturing audio from the microphone and using the Whisper ASR model to transcribe it. It maintains a buffer of the most recent transcribed text.
- **`keyword_module.py`**: This module uses TF-IDF (Term Frequency-Inverse Document Frequency) to extract relevant keywords from the transcribed text.
- **`web_search_module_google_scrape.py`**: This module performs a Google search based on the extracted keywords to gather more context for meme generation.
- **`Mem.py`**: This module contains the core logic for creating memes. It takes keywords and web search results, formulates a meme prompt, and adds text to a placeholder image.
- **`voice_transcriber.py`**: This is an older version of the transcription module and is not used in the current implementation.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory of the project and add your API keys. You can use the following as a template:

    ```
    HUGGINGFACE_API_KEY="your_huggingface_api_key"
    OPENAI_API_KEY="your_openai_api_key"
    GEMINI_API_KEY="your_gemini_api_key"
    ```

## How to Run

To start the application, run the `main.py` script:

```bash
python main.py
```

The application will start listening for audio from your microphone. It will transcribe the audio in real-time and generate a new meme every 10 minutes (by default). The generated memes will be saved in the `memes/` directory.

## Dependencies

The project uses the following major Python libraries:

- `torch` and `transformers`: For local summarization and for the Whisper model.
- `openai-whisper`: For audio transcription.
- `requests`: For making HTTP requests to APIs.
- `Pillow`: For image manipulation.
- `python-dotenv`: For managing environment variables.
- `schedule`: For scheduling jobs.
- `numpy` and `scipy`: For numerical operations.
- `google-generativeai`: For using the Gemini API.
- `openai`: For using the OpenAI API.
- `beautifulsoup4` and `lxml`: For web scraping.
- `nltk`: For natural language processing tasks.
- `pydantic`: For data validation.
- `googlesearch-python`: For performing Google searches.

You can install all the dependencies using the `requirements.txt` file.
