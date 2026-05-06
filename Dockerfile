# Використовуємо стабільну версію Python
FROM python:3.11-slim

# Встановлюємо системні залежності для OpenCV та YOLO
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxcb1 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копіюємо залежності та встановлюємо їх
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь проєкт
COPY . .

# Команда для запуску (Railway автоматично підставить $PORT)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]