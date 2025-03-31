# 📥 Seekho Video Downloader Bot

<div align="center">
  
<img src="/api/placeholder/400/200" alt="Seekho Video Downloader Logo">

**Download Seekho videos easily via Telegram or web interface**
</div>

## 🚀 Features

- **🤖 Telegram Bot Interface**
  - Instant download via simple commands
  - Support for custom output filenames
  - Automatic file cleanup after download
  - **User tracking and broadcasting** (NEW)

- **🌐 Web Interface**
  - Browser-based video downloads
  - Simple and intuitive UI
  - Health check endpoints for monitoring
  - **Admin panel to view registered users** (NEW)

- **⚙️ Technical Capabilities**
  - Extracts m3u8 links from Seekho pages
  - High-quality downloads using FFmpeg
  - Concurrent operation with threading
  - **Persistent user storage in JSON file** (NEW)

## 📋 How It Works

1. User provides a Seekho video URL (via Telegram or web)
2. Bot extracts the m3u8 stream link from the page
3. FFmpeg downloads and processes the video
4. Video is delivered to the user
5. Temporary files are automatically cleaned up
6. **User IDs are stored for future broadcasting** (NEW)

## 🛠️ Prerequisites

- Python 3.7 or higher
- FFmpeg installed and in system PATH
- Telegram Bot API token
- Required Python packages

## ⚡ Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/seekho_downloader_bot.git
cd seekho_downloader_bot

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with the following variables:
```
BOT_TOKEN=your_telegram_bot_token
KOYEB_URL=your_public_facing_url
ADMIN_USER_ID=your_telegram_user_id
```

### Running the Bot

```bash
python bot.py
```

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with instructions; saves user ID (NEW) |
| `/download <video_link> [filename]` | Download video from the provided link |
| `/broadcast <message>` | Sends a message to all registered users (NEW) |
| `/stats` | Shows total number of registered users (NEW) |

## 🌐 Web Interface

Access the web interface at your deployment URL to download videos through your browser.

- **Health Check**: `/` endpoint returns "OK"
- **Download API**: `/download` endpoint processes download requests
- **User Interface**: Served from static HTML files
- **Admin User List**: `/admin/users` to view registered users (NEW)

## 📊 System Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Telegram Bot   │◄────►│  Core Service   │◄────►│   Web Server    │
│   (Pyrogram)    │      │  (FFmpeg/m3u8)  │      │     (Flask)     │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                  ▲
                                  │
                                  ▼
                         ┌─────────────────┐
                         │                 │
                         │   Seekho API    │
                         │                 │
                         └─────────────────┘
```

## 🔒 Security Considerations

- The bot only processes public Seekho video links
- No user credentials are required or stored
- Temporary downloaded files are deleted after processing
- **User data is stored in a local JSON file and is not shared externally** (NEW)

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<div align="center">
  <p>Created with ❤️ for Seekho learners everywhere.. We are not Responsible if you will use the script illegally .. its just for educational purpose and to download the videos and put them into your Social media Statuses to Showcase the learnings</p>
</div>

