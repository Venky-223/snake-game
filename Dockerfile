FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libsdl2-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-ttf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY snake-game-v3.py .

CMD ["python", "snake_game_v3.py"]
