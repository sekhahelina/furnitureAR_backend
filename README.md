# 🛋️ Furniture AR — Backend

FastAPI бекенд для системи рекомендацій меблів з AR-візуалізацією.

---

## 📋 Вимоги

- Python **3.11+**
- PostgreSQL **15+**
- pip або conda

---

## 🚀 Запуск крок за кроком

### 1. Розпакуй ZIP та перейди у папку

```bash
cd backend
```

### 2. Створи та активуй віртуальне середовище

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Встанови всі залежності

```bash
pip install -r requirements.txt
```

> ⚠️ Перший запуск може зайняти 3-5 хвилин — завантажується YOLOv8 та OpenCV.

### 4. Створи базу даних у PostgreSQL

```bash
# Підключись до PostgreSQL
psql -U postgres

# Виконай у psql:
CREATE DATABASE furniture_ar;
\q
```

### 5. Налаштуй змінні середовища

```bash
cp .env.example .env
```

Відкрий `.env` та заміни значення:

```env
DATABASE_URL=postgresql+asyncpg://postgres:ТВІй_ПАРОЛЬ@localhost:5432/furniture_ar
SECRET_KEY=будь-яка-довга-рандомна-строка-тут
```

### 6. Застосуй міграції (створення таблиць)

```bash
# Ініціалізуємо Alembic (якщо перший раз)
alembic revision --autogenerate -m "init"

# Застосовуємо міграцію
alembic upgrade head
```

### 7. Заповни БД тестовими товарами

```bash
python seed_products.py
```

### 8. Запусти сервер

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Сервер доступний на: **http://localhost:8000**

---

## 📖 Документація API

Після запуску відкрий у браузері:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔌 Ендпоінти

| Метод | URL | Опис |
|-------|-----|------|
| POST | `/auth/register` | Реєстрація |
| POST | `/auth/login` | Логін → JWT токен |
| GET | `/auth/me` | Профіль поточного користувача |
| POST | `/analyze/` | 🔑 Аналіз фото кімнати |
| GET | `/analyze/status/{id}` | 🔑 Статус аналізу |
| GET | `/products/` | Каталог товарів |
| GET | `/products/?style=Modern` | Фільтр за стилем |
| GET | `/cabinet/history` | 🔑 Історія сканів |
| GET | `/cabinet/saved` | 🔑 Збережені товари |
| POST | `/cabinet/saved/{id}` | 🔑 Зберегти товар |
| DELETE | `/cabinet/saved/{id}` | 🔑 Видалити зі збережених |

> 🔑 — потрібен JWT токен у заголовку: `Authorization: Bearer <token>`

---

## 📦 Структура бібліотек

| Бібліотека | Для чого |
|------------|----------|
| `fastapi` | Веб-фреймворк |
| `uvicorn` | ASGI сервер |
| `sqlalchemy` | ORM для PostgreSQL |
| `asyncpg` | Async PostgreSQL драйвер |
| `alembic` | Міграції БД |
| `psycopg2-binary` | Синхронний PostgreSQL (для Alembic) |
| `python-jose` | JWT токени |
| `passlib[bcrypt]` | Хешування паролів |
| `python-multipart` | Підтримка file upload |
| `opencv-python-headless` | Аналіз зображень (K-Means кольори) |
| `numpy` | Математика для CV |
| `scikit-learn` | K-Means кластеризація |
| `ultralytics` | YOLOv8 детекція об'єктів |
| `Pillow` | Робота з зображеннями |
| `pydantic-settings` | Конфігурація через .env |
| `aiofiles` | Асинхронний запис файлів |

---

## 🗂️ Додавання 3D-моделей

Помісти `.glb` та `.usdz` файли у папку `models_3d/`:

```
models_3d/
├── sofa_mono.glb
├── sofa_mono.usdz
├── chair_arc.glb
└── chair_arc.usdz
```

Потім при створенні товару вкажи шляхи:
```json
{
  "model_glb_path": "models_3d/sofa_mono.glb",
  "model_usdz_path": "models_3d/sofa_mono.usdz"
}
```

Файли доступні через: `http://localhost:8000/models/sofa_mono.glb`
