FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

# Install Chromium, ChromeDriver dependencies, and FFmpeg
RUN apt-get update && apt-get install -y \
    chromium chromium-driver ffmpeg wget unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

# Set environment variables for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

EXPOSE 8080

CMD ["python", "bot.py"]
