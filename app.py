import streamlit as st
from PIL import Image
import zipfile
import os

# Заголовок страницы
st.title("🖼 PNG → WebP без потерь")

# Инструкция
st.markdown("""
Загрузите один или несколько PNG-файлов — они будут автоматически конвертированы в формат WebP без потери качества.  
Готовый архив с .webp можно будет скачать в один клик.  
""")

# Загрузка файлов
uploaded_files = st.file_uploader("Загрузите PNG-файлы", type=["png"], accept_multiple_files=True)

if uploaded_files:
    # Создаём папку для временных файлов
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    zip_path = "converted_webp.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in uploaded_files:
            img = Image.open(file).convert("RGBA")
            webp_name = file.name.replace(".png", ".webp")
            webp_path = os.path.join(output_dir, webp_name)
            img.save(webp_path, "webp", lossless=True)
            zipf.write(webp_path, arcname=webp_name)

    # Кнопка для скачивания архива
    with open(zip_path, "rb") as f:
        st.download_button("⬇️ Скачать .webp архив", f, file_name=zip_path, mime="application/zip")

    # Очистка (по желанию)
    for f in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, f))
    os.rmdir(output_dir)
    os.remove(zip_path)
