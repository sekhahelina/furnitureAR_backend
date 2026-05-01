import cv2
import numpy as np
from sklearn.cluster import KMeans
from PIL import Image
import io


def extract_palette(image_bytes: bytes, n_colors: int = 5) -> list[str]:
    """
    Приймає байти зображення, повертає список з n_colors HEX-кольорів
    (домінантна палітра через K-Means clustering).
    """
    # Декодуємо зображення
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Не вдалось декодувати зображення")

    # Конвертуємо BGR → RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Зменшуємо розмір для швидкості
    img_small = cv2.resize(img_rgb, (150, 150))

    # Перетворюємо у масив пікселів (N, 3)
    pixels = img_small.reshape(-1, 3).astype(np.float32)

    # K-Means кластеризація
    kmeans = KMeans(n_clusters=n_colors, n_init=10, random_state=42)
    kmeans.fit(pixels)

    # Сортуємо кольори за частотою появи
    labels = kmeans.labels_
    counts = np.bincount(labels)
    sorted_indices = np.argsort(-counts)
    centers = kmeans.cluster_centers_[sorted_indices]

    # Конвертуємо RGB → HEX
    palette = []
    for color in centers:
        r, g, b = int(color[0]), int(color[1]), int(color[2])
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        palette.append(hex_color)

    return palette
