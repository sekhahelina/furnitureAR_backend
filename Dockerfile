# Використовуємо стабільну версію Python на базі Debian Bookworm
FROM python:3.11-slim

# Встановлюємо сучасні системні залежності для OpenCV та YOLO
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копіюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь проєкт
COPY . .

# Railway автоматично підхопить порт із вашої команди запуску або налаштувань
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]