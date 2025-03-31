import os
import re
import subprocess
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask
from threading import Thread

# Replace with your actual credentials
API_ID = 26205215  # Your App API ID
API_HASH = "d4d9b7bce6d76bec759e404ecf2c3ebf"  # Your App API Hash
BOT_TOKEN = "7858262825:AAE1GT1qdWl6XRRJ0R-2LTwvQliTAIvpD4w"  # Your Bot Token

# Folder to store downloaded videos temporarily
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def extract_m3u8_links(html_content):
    """
    Extracts all m3u8 links from the provided HTML content using regex.
    """
    links = re.findall(r"(https?://[^\s'\"<>]+\.m3u8)", html_content)
    return links

def download_with_ffmpeg(m3u8_url, output_path):
    """
    Uses ffmpeg to download a video from the provided m3u8 URL.
    """
    try:
        command = [
            "ffmpeg",
            "-i", m3u8_url,
            "-c", "copy",
            "-bsf:a", "aac_adtstoasc",
            "-y",  # Overwrite file if exists
            output_path
        ]
        print("Running ffmpeg command:", " ".join(command))
        subprocess.run(command, check=True)
        print(f"Download complete! Video saved as: {output_path}")
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg error: {e}")

# Initialize the Telegram bot client with API credentials
app = Client("seekho_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
def start_handler(client, message: Message):
    """
    Sends a welcome message with instructions on how to use the bot.
    """
    welcome_text = (
        "Welcome to the Seekho Video Downloader Bot!\n\n"
        "To download a video, use the command:\n"
        "/download <video_link> [optional_output_file_name]\n\n"
        "Example:\n"
        "/download https://seekho.in/video/sample-video my_video.mp4\n\n"
        "The bot will fetch the video page, extract m3u8 links, download the video using FFmpeg, "
        "and send you the file. Enjoy!"
    )
    message.reply_text(welcome_text)

@app.on_message(filters.command("download"))
def download_handler(client, message: Message):
    """
    Handles the /download command.
    Usage: /download <video_link> [optional_output_file_name]
    """
    if len(message.command) < 2:
        message.reply_text("Usage: /download <video link> [output file name]")
        return

    video_link = message.command[1].strip()
    output_file = message.command[2].strip() if len(message.command) > 2 else "output_video.mp4"
    if not output_file.lower().endswith(".mp4"):
        output_file += ".mp4"
    output_path = os.path.join(DOWNLOAD_FOLDER, output_file)

    message.reply_text("Processing your request. Please wait...")

    try:
        response = requests.get(video_link, timeout=10)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        message.reply_text(f"Error fetching video link: {e}")
        return

    m3u8_links = extract_m3u8_links(html_content)
    if not m3u8_links:
        message.reply_text("No m3u8 links found in the provided URL.")
        return

    selected_link = m3u8_links[0]
    try:
        download_with_ffmpeg(selected_link, output_path)
    except Exception as e:
        message.reply_text(f"Error downloading video: {e}")
        return

    try:
        message.reply_document(output_path, caption="Here is your downloaded video!")
    except Exception as e:
        message.reply_text(f"Error sending video: {e}")
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"Deleted temporary file: {output_path}")

# Minimal Flask app for health checks
health_app = Flask("health")

@health_app.route("/")
def health():
    return "OK", 200

def run_health_app():
    # Use PORT from environment variable or default to 8080
    port = int(os.environ.get("PORT", 8080))
    health_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start the health check server in a separate thread.
    health_thread = Thread(target=run_health_app)
    health_thread.daemon = True
    health_thread.start()
    
    # Start the Telegram bot
    app.run()
