import os
import re
import subprocess
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask, request, jsonify, send_from_directory
from threading import Thread
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Telegram Bot Credentials
API_ID = 26205215  # Replace with your API ID
API_HASH = "d4d9b7bce6d76bec759e404ecf2c3ebf"  # Replace with your API Hash
BOT_TOKEN = "7858262825:AAE1GT1qdWl6XRRJ0R-2LTwvQliTAIvpD4w"  # Replace with your Bot Token

# Koyeb URL (for web access)
KOYEB_URL = os.environ.get("KOYEB_URL", "https://example.koyeb.app")

# Download folder
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Function to extract .m3u8 links
def extract_m3u8_links(html_content):
    return re.findall(r"(https?://[^\s'\"<>]+\.m3u8)", html_content)

# Function to download video using FFmpeg
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

# Function to resolve deep links using Selenium
def resolve_final_url_selenium(short_url):
    try:
        options = Options()
        options.add_argument("--headless")  # Run without UI
        options.add_argument("--no-sandbox")  # Required for containerized environments
        options.add_argument("--disable-dev-shm-usage")  # Prevent crashes due to limited memory
        
        service = Service(ChromeDriverManager().install())  # Install ChromeDriver
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get(short_url)
        final_url = driver.current_url
        driver.quit()
        
        return final_url
    except Exception as e:
        print(f"Error resolving URL with Selenium: {e}")
        return None

# Telegram bot setup
app = Client("seekho_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
def start_handler(client, message: Message):
    welcome_text = (
        "🎉 Welcome to the **Seekho Video Downloader Bot**!\n\n"
        "To download a video, use:\n"
        "📥 `/download <video_link>`\n\n"
        "**Example:**\n"
        "`/download https://seekho.in/video/sample-video`\n\n"
        "Visit our web interface: " + KOYEB_URL
    )
    message.reply_text(welcome_text)

@app.on_message(filters.command("download"))
def download_handler(client, message: Message):
    if len(message.command) < 2:
        message.reply_text("⚠️ Usage: `/download <video link>`")
        return

    video_link = message.command[1].strip()

    # Resolve Seekho deep links
    if "seekho.page.link" in video_link:
        resolved_url = resolve_final_url_selenium(video_link)
        if not resolved_url:
            message.reply_text("❌ Failed to resolve the short link.")
            return
        video_link = resolved_url  # Use actual link

    output_file = "output_video.mp4"
    output_path = os.path.join(DOWNLOAD_FOLDER, output_file)

    message.reply_text("🔄 Fetching video... Please wait.")

    try:
        response = requests.get(video_link, timeout=10)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        message.reply_text(f"❌ Error fetching video page: {e}")
        return

    m3u8_links = extract_m3u8_links(html_content)
    if not m3u8_links:
        message.reply_text("❌ No video link found.")
        return

    selected_link = m3u8_links[0]
    
    try:
        download_with_ffmpeg(selected_link, output_path)
    except Exception as e:
        message.reply_text(f"❌ Error downloading video: {e}")
        return

    try:
        message.reply_document(output_path, caption="✅ Here is your downloaded video!")
    except Exception as e:
        message.reply_text(f"❌ Error sending video: {e}")
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

# Flask Web Interface
health_app = Flask(__name__, static_folder=os.getcwd(), static_url_path='/')

@health_app.route("/")
def serve_index():
    return send_from_directory(os.getcwd(), "index.html")

@health_app.route("/download", methods=["POST"])
def process_download():
    data = request.json
    video_link = data.get("video_link")

    if not video_link:
        return jsonify({"success": False, "error": "No video link provided."}), 400

    output_path = os.path.join(DOWNLOAD_FOLDER, "output_video.mp4")
    
    # Process download request
    try:
        resolved_url = resolve_final_url_selenium(video_link) if "seekho.page.link" in video_link else video_link
        response = requests.get(resolved_url, timeout=10)
        response.raise_for_status()
        html_content = response.text
        m3u8_links = extract_m3u8_links(html_content)
        if not m3u8_links:
            return jsonify({"success": False, "error": "No video found."}), 400

        download_with_ffmpeg(m3u8_links[0], output_path)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": True, "download_url": f"/downloads/output_video.mp4"})

def run_health_app():
    port = int(os.environ.get("PORT", 8080))
    health_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    health_thread = Thread(target=run_health_app)
    health_thread.daemon = True
    health_thread.start()
    app.run()
