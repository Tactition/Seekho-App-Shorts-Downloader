FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

EXPOSE 8080

CMD ["python", "bot.py"]
