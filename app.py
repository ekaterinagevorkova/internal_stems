import streamlit as st
from PIL import Image
import zipfile
import base64
import io
import os

st.set_page_config(page_title="PNG → WebP или HTML5", layout="centered")

st.title("🖼 PNG → WebP или HTML5 (для медийной рекламы)")

st.markdown("""
Загрузите PNG-файлы и выберите, как их обработать:

- **WebP** — без потерь, изображения в формате .webp  
- **HTML5** — чистый .html с base64 PNG внутри (для AdFox, DV360, Adform и т.п.)
""")

st.divider()

# Формат конвертации
format_choice = st.radio("Формат конвертации", ["WebP", "HTML5"], horizontal=True)

# Загрузка PNG-файлов
uploaded_files = st.file_uploader("Загрузите PNG-файлы", type=["png"], accept_multiple_files=True)

if uploaded_files:
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    zip_filename = "converted_files.zip"

    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for file in uploaded_files:
            img = Image.open(file).convert("RGBA")
            base_name = file.name.rsplit(".", 1)[0]

            if format_choice == "WebP":
                webp_path = os.path.join(output_dir, base_name + ".webp")
                img.save(webp_path, "webp", lossless=True)
                zipf.write(webp_path, arcname=os.path.basename(webp_path))

            elif format_choice == "HTML5":
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                buffered = base64.b64encode(buffer.getvalue()).decode()

                html_content = f"""<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8">
    <title>Banner</title>
    <style>
      html, body {{
        margin: 0;
        padding: 0;
        background: transparent;
      }}
      img {{
        width: 100%;
        height: auto;
        display: block;
      }}
    </style>
  </head>
  <body>
    <img src="data:image/png;base64,{buffered}" alt="banner" />
  </body>
</html>
"""
                html_path = os.path.join(output_dir, base_name + ".html")
                with open(html_path, "w") as html_file:
                    html_file.write(html_content)
                zipf.write(html_path, arcname=os.path.basename(html_path))

    # Скачивание архива
    with open(zip_filename, "rb") as f:
        st.download_button("⬇️ Скачать архив", f, file_name=zip_filename, mime="application/zip")

    # Очистка
    for f in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, f))
    os.rmdir(output_dir)
    os.remove(zip_filename)

