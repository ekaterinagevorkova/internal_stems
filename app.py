# Установка Pillow
!pip install -q pillow

from PIL import Image
import os
import zipfile
from google.colab import files

# Создаём папку для webp
output_folder = "webp_output"
os.makedirs(output_folder, exist_ok=True)

# Поиск PNG-файлов
png_files = [f for f in os.listdir() if f.lower().endswith(".png")]

if not png_files:
    print("❌ PNG-файлы не найдены. Перетащи их в левую панель 'Файлы' и перезапусти ячейку.")
else:
    # Конвертация с максимальным качеством (lossless)
    for filename in png_files:
        try:
            img = Image.open(filename).convert("RGBA")
            webp_path = os.path.join(output_folder, filename.replace(".png", ".webp"))
            img.save(webp_path, "webp", lossless=True)  # <--- БЕЗ потерь
            print(f"✅ {filename} → {webp_path}")
        except Exception as e:
            print(f"⚠️ Ошибка при обработке {filename}: {e}")

    # Упаковываем все webp в zip
    zip_filename = "converted_webp_lossless.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for f in os.listdir(output_folder):
            zipf.write(os.path.join(output_folder, f), arcname=f)

    # Скачиваем zip-архив
    print("\n⬇️ Скачиваем ZIP с .webp-файлами (lossless)...")
    files.download(zip_filename)

    print("🎉 Готово! Все файлы конвертированы без потерь и скачаны в архиве.")
