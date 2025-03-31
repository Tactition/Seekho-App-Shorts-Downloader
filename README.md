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

- **🌐 Web Interface**
  - Browser-based video downloads
  - Simple and intuitive UI
  - Health check endpoints for monitoring

- **⚙️ Technical Capabilities**
  - Extracts m3u8 links from Seekho pages
  - High-quality downloads using FFmpeg
  - Concurrent operation with threading

## 📋 How It Works

1. User provides a Seekho video URL (via Telegram or web)
2. Bot extracts the m3u8 stream link from the page
3. FFmpeg downloads and processes the video
4. Video is delivered to the user
5. Temporary files are automatically cleaned up

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
```

### Running the Bot

```bash
python main.py
```

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with instructions |
| `/download <video_link> [filename]` | Download video from the provided link |

## 🌐 Web Interface

Access the web interface at your deployment URL to download videos through your browser.

- **Health Check**: `/` endpoint returns "OK"
- **Download API**: `/download` endpoint processes download requests
- **User Interface**: Served from static HTML files

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

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<div align="center">
  <p>Created with ❤️ for Seekho learners everywhere</p>
</div>