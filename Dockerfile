FROM python:3.11-slim

# Tizimga ffmpeg va boshqa kerakli paketlarni o'rnatish
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot kodini ko'chirish
COPY . .

# Botni ishga tushirish
CMD ["python", "main.py"]
