import numpy as np
import cv2

DEFAULT_STYLE = "Modern"

# ── Вагова таблиця об'єктів ──────────────────────────────────────────────────
# Кожен COCO-об'єкт → (стиль, вага)
# Чим більша вага — тим сильніший сигнал
OBJECT_STYLE_MAP = {

    # ── BOHO ──────────────────────────────────────────────────────────────────
    # Багато рослин = головний маркер бохо
    "potted plant":  ("Boho", 5),   # кожна рослина дає +5
    "vase":          ("Boho", 3),   # вазони характерні для бохо
    "teddy bear":    ("Boho", 3),   # м'які іграшки, декор
    "backpack":      ("Boho", 2),   # богемний стиль життя
    "umbrella":      ("Boho", 2),   # декоративні парасолі
    "frisbee":       ("Boho", 1),
    "bowl":          ("Boho", 2),   # керамічні миски як декор
    "banana":        ("Boho", 2),   # фрукти як декор
    "orange":        ("Boho", 2),
    "apple":         ("Boho", 2),

    # ── LOFT ──────────────────────────────────────────────────────────────────
    # Барні стільці, пляшки, індустріальні деталі
    "bar stool":     ("Loft", 6),   # найсильніший маркер лофту
    "bottle":        ("Loft", 4),   # пляшки на відкритих полицях
    "wine glass":    ("Loft", 3),
    "cup":           ("Loft", 2),
    "scissors":      ("Loft", 2),   # майстерня, робочий простір
    "knife":         ("Loft", 2),
    "fork":          ("Loft", 1),
    "spoon":         ("Loft", 1),
    "toaster":       ("Loft", 3),   # відкрита кухня — типово для лофту
    "microwave":     ("Loft", 2),
    "refrigerator":  ("Loft", 2),
    "oven":          ("Loft", 2),
    "sink":          ("Loft", 2),

    # ── SCANDI ────────────────────────────────────────────────────────────────
    # Мінімалізм, дерево, світло
    "bed":           ("Scandi", 3),   # прості ліжка без пишного декору
    "book":          ("Scandi", 2),   # книжкові полиці — скандинавська риса
    "laptop":        ("Scandi", 2),   # мінімалістичне робоче місце

    # ── CLASSIC ───────────────────────────────────────────────────────────────
    # Витончені деталі, симетрія, декор
    "clock":         ("Classic", 5),  # настінні годинники = класика
    "tv":            ("Classic", 1),  # телевізор є і в класиці
    "suitcase":      ("Classic", 2),
    "handbag":       ("Classic", 2),
    "tie":           ("Classic", 3),

    # ── MODERN ────────────────────────────────────────────────────────────────
    # Технологічний мінімалізм
    "tv":            ("Modern", 3),
    "monitor":       ("Modern", 4),
    "keyboard":      ("Modern", 3),
    "mouse":         ("Modern", 3),
    "remote":        ("Modern", 2),
    "cell phone":    ("Modern", 2),
    "laptop":        ("Modern", 2),

    # ── НЕЙТРАЛЬНІ меблі (мала вага) ─────────────────────────────────────────
    "chair":         ("Scandi", 1),
    "couch":         ("Modern", 1),
    "dining table":  ("Modern", 1),
    "toilet":        ("Modern", 1),
    "sink":          ("Modern", 1),
    "bench":         ("Scandi", 1),
}


def detect_style(image_bytes: bytes) -> str:
    """
    Головна функція визначення стилю.
    1. Спочатку аналізуємо кольори (швидко, завжди працює)
    2. Потім запускаємо YOLO для детекції об'єктів
    3. Комбінуємо обидва результати з вагами
    """
    color_scores = _color_analysis(image_bytes)
    yolo_scores = _yolo_analysis(image_bytes)

    # Комбінуємо: кольори мають вагу 40%, об'єкти 60%
    final_scores = {}
    all_styles = set(list(color_scores.keys()) + list(yolo_scores.keys()))

    for style in all_styles:
        c = color_scores.get(style, 0)
        y = yolo_scores.get(style, 0)
        final_scores[style] = c * 0.4 + y * 0.6

    print(f"[StyleDetector] Кольори: {color_scores}")
    print(f"[StyleDetector] Об'єкти: {yolo_scores}")
    print(f"[StyleDetector] Фінал:   {final_scores}")

    best = max(final_scores, key=lambda k: final_scores[k])

    # Якщо всі scores = 0 — fallback
    if final_scores[best] == 0:
        return DEFAULT_STYLE

    return best


# ── АНАЛІЗ КОЛЬОРІВ ──────────────────────────────────────────────────────────

def _color_analysis(image_bytes: bytes) -> dict:
    """
    Аналізує кольори зображення і повертає scores для кожного стилю.

    Логіка:
    - Дуже темне зображення → Loft (темні стіни, метал)
    - Холодні сині/сірі відтінки → Loft або Modern
    - Дуже світле і нейтральне → Scandi (білі стіни, дерево)
    - Тепле і яскраве → Boho (оранжевий, жовтий, теракота)
    - Нейтрально-тепле → Classic (бежевий, кремовий)
    - Холодно-нейтральне → Modern (сірий, білий, чорний)
    """
    scores = {"Modern": 0, "Scandi": 0, "Loft": 0, "Classic": 0, "Boho": 0, "Industrial": 0}

    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return scores

        img_small = cv2.resize(img, (200, 200))
        img_rgb = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)
        img_hsv = cv2.cvtColor(img_small, cv2.COLOR_BGR2HSV)

        pixels_rgb = img_rgb.reshape(-1, 3).astype(np.float32)
        pixels_hsv = img_hsv.reshape(-1, 3).astype(np.float32)

        # Основні метрики
        avg_r = np.mean(pixels_rgb[:, 0])
        avg_g = np.mean(pixels_rgb[:, 1])
        avg_b = np.mean(pixels_rgb[:, 2])
        brightness = (avg_r + avg_g + avg_b) / 3

        avg_h = np.mean(pixels_hsv[:, 0])   # hue 0-180
        avg_s = np.mean(pixels_hsv[:, 1])   # saturation 0-255
        avg_v = np.mean(pixels_hsv[:, 2])   # value 0-255

        # Теплота: різниця між червоним і синім каналом
        warmth = avg_r - avg_b

        # Кількість пікселів різних кольорів
        total = len(pixels_rgb)

        # Підраховуємо частки кольорів у HSV
        # Цегляний/теракотовий: hue 0-15 або 165-180, насиченість > 80
        brick_mask = (
            ((pixels_hsv[:, 0] < 15) | (pixels_hsv[:, 0] > 165)) &
            (pixels_hsv[:, 1] > 80) &
            (pixels_hsv[:, 2] > 60)
        )
        brick_ratio = np.sum(brick_mask) / total

        # Сірий/металічний: насиченість < 40
        gray_mask = pixels_hsv[:, 1] < 40
        gray_ratio = np.sum(gray_mask) / total

        # Зелений (рослини): hue 35-85, насиченість > 60
        green_mask = (
            (pixels_hsv[:, 0] > 35) &
            (pixels_hsv[:, 0] < 85) &
            (pixels_hsv[:, 1] > 60)
        )
        green_ratio = np.sum(green_mask) / total

        # Дуже світлий (білі стіни): яскравість > 200
        white_mask = pixels_hsv[:, 2] > 200
        white_ratio = np.sum(white_mask) / total

        # Теплий бежевий/кремовий: hue 15-35, насиченість 20-100
        beige_mask = (
            (pixels_hsv[:, 0] > 15) &
            (pixels_hsv[:, 0] < 35) &
            (pixels_hsv[:, 1] > 20) &
            (pixels_hsv[:, 1] < 120)
        )
        beige_ratio = np.sum(beige_mask) / total

        print(f"[ColorAnalysis] brightness={brightness:.1f}, warmth={warmth:.1f}, "
              f"gray={gray_ratio:.2f}, brick={brick_ratio:.2f}, "
              f"green={green_ratio:.2f}, white={white_ratio:.2f}, beige={beige_ratio:.2f}")

        # ── LOFT: темно + багато сірого АБО цегляні відтінки ─────────────────
        if brightness < 90:
            scores["Loft"] += 8
        elif brightness < 120:
            scores["Loft"] += 4

        if gray_ratio > 0.5:        # більше 50% сірих пікселів = метал/бетон
            scores["Loft"] += 6
        elif gray_ratio > 0.35:
            scores["Loft"] += 3

        if brick_ratio > 0.1:       # цегляний відтінок = лофт
            scores["Loft"] += 8
        elif brick_ratio > 0.05:
            scores["Loft"] += 4

        if warmth < -20:            # холодні синьо-сірі тони
            scores["Loft"] += 4
            scores["Modern"] += 2

        # ── BOHO: зелений (рослини) + теплі відтінки ─────────────────────────
        if green_ratio > 0.15:      # багато зеленого = рослини
            scores["Boho"] += 10
        elif green_ratio > 0.08:
            scores["Boho"] += 5
        elif green_ratio > 0.04:
            scores["Boho"] += 2

        if warmth > 30 and avg_s > 60:   # яскраво-тепле = богемно
            scores["Boho"] += 5
        elif warmth > 20:
            scores["Boho"] += 2

        if beige_ratio > 0.3:       # бежевий + теплий = Boho або Classic
            scores["Boho"] += 3
            scores["Classic"] += 3

        # ── SCANDI: світле + нейтральне + мінімальна насиченість ─────────────
        if white_ratio > 0.4:       # багато білого = скандинавські стіни
            scores["Scandi"] += 7
        elif white_ratio > 0.25:
            scores["Scandi"] += 4

        if brightness > 160 and avg_s < 60:   # світле і ненасичене
            scores["Scandi"] += 5
        elif brightness > 140 and avg_s < 80:
            scores["Scandi"] += 2

        # ── CLASSIC: теплий бежевий, середня яскравість ───────────────────────
        if beige_ratio > 0.25 and brightness > 100 and brightness < 180:
            scores["Classic"] += 6
        elif beige_ratio > 0.15:
            scores["Classic"] += 3

        if warmth > 15 and brightness > 120 and avg_s < 80:
            scores["Classic"] += 3

        # ── MODERN: нейтрально-холодне, сіре, середня яскравість ─────────────
        if gray_ratio > 0.3 and brightness > 100:
            scores["Modern"] += 5
        if warmth < 10 and warmth > -20 and brightness > 120:
            scores["Modern"] += 3

    except Exception as e:
        print(f"[ColorAnalysis] Помилка: {e}")

    return scores


# ── АНАЛІЗ ОБ'ЄКТІВ (YOLO) ───────────────────────────────────────────────────

def _yolo_analysis(image_bytes: bytes) -> dict:
    """
    Запускає YOLOv8 і повертає scores на основі знайдених об'єктів.
    """
    scores = {"Modern": 0, "Scandi": 0, "Loft": 0, "Classic": 0, "Boho": 0, "Industrial": 0}

    try:
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return scores

        results = model(img, verbose=False)

        detected = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id].lower()
                conf = float(box.conf[0])
                if conf > 0.25:   # поріг впевненості
                    detected.append((class_name, conf))

        print(f"[YOLO] Знайдено: {detected}")

        # Рахуємо рослини окремо — ключовий маркер Boho
        plant_count = sum(1 for name, _ in detected if name == "potted plant")
        if plant_count >= 3:
            scores["Boho"] += 15   # 3+ рослини = явно Boho
        elif plant_count == 2:
            scores["Boho"] += 8
        elif plant_count == 1:
            scores["Boho"] += 5

        # Рахуємо решту об'єктів
        for name, conf in detected:
            if name in OBJECT_STYLE_MAP:
                style, weight = OBJECT_STYLE_MAP[name]
                # Множимо на confidence щоб невпевнені детекції мали менше впливу
                scores[style] += weight * conf

    except Exception as e:
        print(f"[YOLO] Помилка: {e}")

    return scores