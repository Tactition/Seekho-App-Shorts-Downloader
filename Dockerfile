FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Create and set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your project files
COPY . /app

# Expose a port if needed (not always required for a bot)
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]
