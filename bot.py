import os
import re
import subprocess
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask, request, jsonify, send_from_directory
from threading import Thread

# Replace with your actual credentials
API_ID = 26205215  # Your App API ID
API_HASH = "d4d9b7bce6d76bec759e404ecf2c3ebf"  # Your App API Hash
BOT_TOKEN = "7858262825:AAE1GT1qdWl6XRRJ0R-2LTwvQliTAIvpD4w"  # Your Bot Token

# Dynamically get the Koyeb public URL from environment variable; default provided if not set.
KOYEB_URL = os.environ.get("KOYEB_URL", "https://example.koyeb.app")

# Folder to store downloaded videos temporarily
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def extract_m3u8_links(html_content):
    links = re.findall(r"(https?://[^\s'\"<>]+\.m3u8)", html_content)
    return links

def download_with_ffmpeg(m3u8_url, output_path):
    try:
        command = [
            "ffmpeg", "-i", m3u8_url, "-c", "copy", "-bsf:a", "aac_adtstoasc", "-y", output_path
        ]
        print("Running ffmpeg command:", " ".join(command))
        subprocess.run(command, check=True)
        print(f"Download complete! Video saved as: {output_path}")
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg error: {e}")

# Telegram bot setup
app = Client("seekho_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
@app.on_message(filters.command("start"))
def start_handler(client, message: Message):
    welcome_text = (
        "Welcome to the Seekho Video Downloader Bot!\n\n"
        "To download a video, use the command:\n"
        "/download <video_link>\n\n"
        "Example:\n"
        "/download https://seekho.in/video/sample-video\n\n"
        "The bot will fetch the video page, extract m3u8 links, download the video, and send it to you.\n\n"
        "Alternatively, you can also visit our web interface at: " + KOYEB_URL
    )
    message.reply_text(welcome_text)

@app.on_message(filters.command("download"))
def download_handler(client, message: Message):
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

# Flask app setup
health_app = Flask(__name__, static_folder=os.getcwd(), static_url_path='/')

@health_app.route("/")
def serve_index():
    return send_from_directory(os.getcwd(), "index.html")

@health_app.route("/download", methods=["POST"])
def process_download():
    data = request.json
    video_link = data.get("video_link")
    output_file = data.get("output_file", "output_video.mp4")

    if not video_link:
        return jsonify({"success": False, "error": "No video link provided."}), 400

    output_path = os.path.join(DOWNLOAD_FOLDER, output_file)
    try:
        response = requests.get(video_link, timeout=10)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        return jsonify({"success": False, "error": f"Error fetching video: {e}"}), 500

    m3u8_links = extract_m3u8_links(html_content)
    if not m3u8_links:
        return jsonify({"success": False, "error": "No m3u8 links found in the provided URL."}), 400

    selected_link = m3u8_links[0]
    try:
        download_with_ffmpeg(selected_link, output_path)
    except Exception as e:
        return jsonify({"success": False, "error": f"Download error: {e}"}), 500

    return jsonify({"success": True, "download_url": f"/downloads/{output_file}"})

@health_app.route("/downloads/<filename>")
def serve_download(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

def run_health_app():
    port = int(os.environ.get("PORT", 8080))
    health_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    health_thread = Thread(target=run_health_app)
    health_thread.daemon = True
    health_thread.start()
    app.run()
