import os
import re
import subprocess
import requests
import socket
import ssl
import urllib.parse
import json
import asyncio
import aiohttp
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from flask import Flask, request, jsonify, send_from_directory
from threading import Thread

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your actual credentials
API_ID = 26205215
API_HASH = "d4d9b7bce6d76bec759e404ecf2c3ebf"
BOT_TOKEN = "7858262825:AAE1GT1qdWl6XRRJ0R-2LTwvQliTAIvpD4w"

# Koyeb settings
KOYEB_URL = os.environ.get("KOYEB_URL", "https://example.koyeb.app")
PING_INTERVAL = 30  # Ping every 30 seconds

# Folder to store downloaded videos temporarily
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# File to store user IDs
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Error reading users file. Creating new one.")
            return {"users": []}
    return {"users": []}

def save_user(user_id, username=None, first_name=None):
    data = load_users()
    user_exists = False
    for user in data["users"]:
        if user["id"] == user_id:
            user_exists = True
            if username and user.get("username") != username:
                user["username"] = username
            if first_name and user.get("first_name") != first_name:
                user["first_name"] = first_name
            break
    
    if not user_exists:
        data["users"].append({
            "id": user_id,
            "username": username,
            "first_name": first_name,
            "joined_at": str(os.path.getmtime(USERS_FILE)) if os.path.exists(USERS_FILE) else str(os.path.getctime(__file__))
        })
    
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    
    return not user_exists

def resolve_shortened_url(url):
    print(f"Resolving shortened URL: {url}")
    max_redirects = 10
    redirect_count = 0
    
    while redirect_count < max_redirects:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        
        port = 443 if parsed.scheme == 'https' else 80
        use_ssl = parsed.scheme == 'https'
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            if use_ssl:
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=host)
            
            sock.connect((host, port))
            
            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\nUser-Agent: Python URL Resolver\r\n\r\n"
            sock.sendall(request.encode())
            
            response = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
            
            sock.close()
            
            response_text = response.decode('utf-8', errors='ignore')
            headers, body = response_text.split('\r\n\r\n', 1)
            
            if re.search(r'HTTP/[\d.]+\s+30[12378]', headers):
                location_match = re.search(r'Location:\s*(.+?)\r\n', headers)
                if location_match:
                    new_url = location_match.group(1).strip()
                    if new_url.startswith('/'):
                        new_url = f"{parsed.scheme}://{host}{new_url}"
                    print(f"Redirecting to: {new_url}")
                    url = new_url
                    redirect_count += 1
                else:
                    print("Redirect header found but no Location specified.")
                    break
            else:
                print(f"Final URL reached: {url}")
                return url
        
        except Exception as e:
            print(f"Error resolving URL: {e}")
            return url
    
    print(f"Maximum redirects ({max_redirects}) reached. Last URL: {url}")
    return url

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

def process_video_link(video_link):
    if "seekho.page.link" in video_link:
        print(f"Detected seekho.page.link in URL, resolving: {video_link}")
        resolved_url = resolve_shortened_url(video_link)
        print(f"Resolved to: {resolved_url}")
        return resolved_url
    return video_link

app = Client("seekho_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def ping_server():
    """Keep-alive function to prevent Koyeb idle"""
    while True:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(KOYEB_URL) as resp:
                    logger.info(f"Keep-alive ping successful (Status: {resp.status})")
        except Exception as e:
            logger.error(f"Keep-alive ping failed: {e}")
        await asyncio.sleep(PING_INTERVAL)

@app.on_start()
async def start_ping_task(client):
    """Start the keep-alive task when bot starts"""
    logger.info("Starting keep-alive background task")
    client.ping_task = asyncio.create_task(ping_server())

@app.on_message(filters.command("start"))
def start_handler(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    is_new_user = save_user(user_id, username, first_name)
    
    welcome_text = (
        f"Welcome {first_name} to the Seekho Video Downloader Bot!\n\n"
        "To download a video, use the command:\n"
        "/download <video_link>\n\n"
        "Example:\n"
        "/download https://seekho.in/videlink/example-video\n\n"
        "Or use a shortened link:\n"
        "/download https://seekho.page.link/example\n\n"
        "The bot will automatically extract the Video And download the video, and send it to you.\n\n"
        "Alternatively, you can also visit our web interface at: " + KOYEB_URL
    )
    
    message.reply_text(welcome_text)
    
    if is_new_user:
        print(f"New user registered: {username} ({user_id})")

@app.on_message(filters.command("broadcast") & filters.user([1178233430]))
def broadcast_handler(client, message: Message):
    if len(message.command) < 2:
        message.reply_text("Usage: /broadcast Your message here")
        return
    
    broadcast_text = message.text.split("/broadcast ", 1)[1]
    
    data = load_users()
    user_count = len(data["users"])
    successful = 0
    failed = 0
    
    status_msg = message.reply_text(f"Broadcasting message to {user_count} users...")
    
    for user in data["users"]:
        try:
            client.send_message(user["id"], broadcast_text)
            successful += 1
        except Exception as e:
            print(f"Failed to send message to {user['id']}: {e}")
            failed += 1
    
    client.edit_message_text(
        message.chat.id,
        status_msg.id,
        f"Broadcast completed!\n• Total users: {user_count}\n• Successful: {successful}\n• Failed: {failed}"
    )

@app.on_message(filters.command("stats") & filters.user([1178233430]))
def stats_handler(client, message: Message):
    data = load_users()
    user_count = len(data["users"])
    message.reply_text(f"📊 Bot Statistics 📊\n\nTotal registered users: {user_count}")

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
    video_link = process_video_link(video_link)
    message.reply_text("Processing URL: Downloading video...Till then Join @Self_Improvement_Audiobooks for Premium Audiobooks!")

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

    video_link = process_video_link(video_link)
    print(f"Processing URL in web app: {video_link}")

    output_path = os.path.join(DOWNLOAD_FOLDER, output_file)
    try:
        response = requests.get(video_link, timeout=10)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        return jsonify({"success": False, "error": f"Error fetching video: {e}"}), 500

    m3u8_links = extract_m3u8_links(html_content)
    if not m3u8_links:
        return jsonify({"success": False, "error": "No m3u8 links found."}), 400

    try:
        download_with_ffmpeg(m3u8_links[0], output_path)
        return jsonify({"success": True, "download_url": f"/downloads/{output_file}"})
    except Exception as e:
        return jsonify({"success": False, "error": f"Download error: {e}"}), 500

@health_app.route("/admin/users", methods=["GET"])
def get_users():
    data = load_users()
    return jsonify(data)

@health_app.route("/downloads/<filename>")
def serve_download(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

def run_health_app():
    port = int(os.environ.get("PORT", 8080))
    health_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({"users": []}, f)
            
    health_thread = Thread(target=run_health_app)
    health_thread.daemon = True
    health_thread.start()
    app.run()