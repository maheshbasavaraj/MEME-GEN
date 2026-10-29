"""Try3-derived lecture meme generator with OpenRouter captions and Imgflip output."""

from collections import deque
from pathlib import Path
import argparse
import logging
import os
import random
import threading
import time
import webbrowser

import requests
try:
    from dotenv import load_dotenv
except ImportError:  # Environment variables can still be set in the shell.
    def load_dotenv(_path=None):
        return False

from meme_director import create_plan
from transcription_module import (
    RECORD_SECONDS,
    add_transcript,
    capture_loop,
    list_microphones,
    load_transcriber,
    record_audio_chunk,
    recent_text,
    transcribe_audio,
)

load_dotenv(Path(__file__).with_name(".env"))
INTERVAL_MINUTES = int(os.getenv("MEME_INTERVAL_MINUTES", "5"))
OUTPUT_DIR = Path(__file__).parent / "memes"
LOG_FILE = Path(__file__).parent / "app.log"
STOP_EVENT = threading.Event()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)


def _choose_template(templates, hint):
    hint = hint.lower()
    keywords = {
        "drake": ("drake",),
        "distracted": ("distracted",),
        "buttons": ("buttons",),
        "success": ("success", "bunny", "kid"),
        "confused": ("confused", "question", "think"),
    }.get(hint, ())
    matching = [template for template in templates
                if any(word in template.get("name", "").lower() for word in keywords)]
    if matching:
        return matching[0]
    two_box = [template for template in templates if template.get("box_count") == 2]
    return random.choice(two_box or templates)


def create_meme_with_imgflip(plan, output_path):
    username = os.getenv("IMGFLIP_USERNAME")
    password = os.getenv("IMGFLIP_PASSWORD")
    if not username or not password:
        logging.warning("Imgflip credentials missing; using local renderer.")
        return create_local_meme(plan, output_path)

    try:
        response = requests.get("https://api.imgflip.com/get_memes", timeout=20)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise RuntimeError(data.get("error_message", "template request failed"))
        template = _choose_template(data["data"]["memes"], plan.get("template_hint", ""))
        payload = {
            "template_id": template["id"],
            "username": username,
            "password": password,
            "text0": plan["top_text"],
            "text1": plan["bottom_text"],
        }
        response = requests.post("https://api.imgflip.com/caption_image", data=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise RuntimeError(data.get("error_message", "caption request failed"))
        image = requests.get(data["data"]["url"], timeout=30)
        image.raise_for_status()
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_bytes(image.content)
        logging.info("Imgflip template: %s", template["name"])
        return output_path
    except (requests.RequestException, KeyError, RuntimeError) as error:
        logging.error("Imgflip failed: %s; using local renderer.", error)
        return create_local_meme(plan, output_path)


def create_local_meme(plan, output_path):
    """Offline fallback so a missing Imgflip key never loses a generated meme."""
    from PIL import Image, ImageDraw, ImageFont

    output_path = output_path.with_suffix(".png")
    image = Image.new("RGB", (1200, 630), "#202d52")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    lines = [plan["top_text"], plan["bottom_text"]]
    for index, line in enumerate(lines):
        box = draw.textbbox((0, 0), line, font=font)
        draw.text(((1200 - (box[2] - box[0])) / 2, 220 + index * 80), line,
                  fill="white", font=font)
    output_path.parent.mkdir(exist_ok=True)
    image.save(output_path)
    return output_path


def generate_meme(buffer, lock):
    transcript = recent_text(buffer, lock, minutes=INTERVAL_MINUTES)
    if len(transcript.split()) < 10:
        logging.info("Not enough recent speech; skipping this cycle.")
        return None
    plan = create_plan(transcript)
    if not plan:
        return None
    logging.info("Topic: %s | Caption: %s", plan["topic"], plan["caption"])
    filename = OUTPUT_DIR / f"generated_meme_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
    path = create_meme_with_imgflip(plan, filename)
    logging.info("Meme saved: %s", path)
    return path


def transcribe_once(wait_seconds=30):
    """Record and log one local transcript without calling any external service."""
    try:
        model, use_fp16 = load_transcriber()
        duration = max(5, wait_seconds)
        microphone = os.getenv("MIC_DEVICE_INDEX") or "Windows default"
        logging.info("Microphone: %s", microphone)
        logging.info("Recording %s seconds for a local English transcription test.", duration)
        audio_path = record_audio_chunk(duration)
        try:
            text = transcribe_audio(model, audio_path, use_fp16)
        finally:
            audio_path.unlink(missing_ok=True)
        if not text:
            logging.warning("No speech was detected in the recording.")
            return ""
        logging.info("TRANSCRIPT: %s", text)
        return text
    except Exception as error:
        logging.exception("Local transcription failed: %s", error)
        return ""


def run_once(wait_seconds=30, display=True):
    """Make one meme only after a completed recording has been transcribed."""
    lock = threading.Lock()
    buffer = deque(maxlen=64)
    STOP_EVENT.clear()
    try:
        text = transcribe_once(wait_seconds)
        if not text:
            return None
        add_transcript(buffer, lock, text)
        path = generate_meme(buffer, lock)
        if path and display:
            webbrowser.open(path.resolve().as_uri())
        return path
    finally:
        STOP_EVENT.set()


def run_forever(display=True):
    lock = threading.Lock()
    buffer = deque(maxlen=64)
    worker = threading.Thread(target=capture_loop, args=(STOP_EVENT, buffer, lock), daemon=True)
    worker.start()
    logging.info("Running continuously; generating every %s minutes.", INTERVAL_MINUTES)
    try:
        next_run = time.monotonic() + INTERVAL_MINUTES * 60
        while not STOP_EVENT.wait(1):
            if time.monotonic() >= next_run:
                path = generate_meme(buffer, lock)
                if path and display:
                    webbrowser.open(path.resolve().as_uri())
                next_run += INTERVAL_MINUTES * 60
    except KeyboardInterrupt:
        pass
    finally:
        STOP_EVENT.set()
        worker.join(timeout=RECORD_SECONDS + 5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="capture briefly and generate one meme")
    parser.add_argument("--transcribe-only", action="store_true", help="record and log a local transcript only")
    parser.add_argument("--list-mics", action="store_true", help="list microphone device indexes")
    parser.add_argument("--wait", type=int, default=30, help="seconds to record with --once or --transcribe-only")
    parser.add_argument("--no-display", action="store_true")
    args = parser.parse_args()
    if args.list_mics:
        for index, name in list_microphones():
            print(f"{index}: {name}")
    elif args.transcribe_only:
        transcribe_once(args.wait)
    elif args.once:
        run_once(args.wait, not args.no_display)
    else:
        run_forever(not args.no_display)
