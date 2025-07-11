import streamlit as st
from PIL import Image
import zipfile
import base64
import io
import os

st.set_page_config(page_title="PNG → WebP или HTML5", layout="centered")

st.title("🖼 PNG → WebP или HTML5")

st.markdown("""
Загрузите PNG-файлы и выберите, как их обработать:

- **WebP** — без потерь, изображения в формате .webp  
- **HTML5** — каждый PNG встроен в отдельный .html-файл с валидной структурой  
""")

st.divider()

# Выбор формата
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
    <title>{file.name}</title>
    <style>
      body {{
        font-family: sans-serif;
        padding: 2rem;
        text-align: center;
        background-color: #f9f9f9;
      }}
      img {{
        max-width: 100%;
        height: auto;
        border: 1px solid #ccc;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
      }}
    </style>
  </head>
  <body>
    <h1>{file.name}</h1>
    <img src="data:image/png;base64,{buffered}" alt="{file.name}" />
  </body>
</html>
"""
                html_path = os.path.join(output_dir, base_name + ".html")
                with open(html_path, "w") as html_file:
                    html_file.write(html_content)
                zipf.write(html_path, arcname=os.path.basename(html_path))

    # Кнопка скачивания ZIP-архива
    with open(zip_filename, "rb") as f:
        st.download_button("⬇️ Скачать архив", f, file_name=zip_filename, mime="application/zip")

    # Очистка временных файлов
    for f in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, f))
    os.rmdir(output_dir)
    os.remove(zip_filename)
