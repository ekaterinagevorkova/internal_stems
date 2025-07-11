import streamlit as st
from PIL import Image
import zipfile
import base64
import os

st.set_page_config(page_title="PNG → WebP/HTML", layout="centered")

st.title("🖼 PNG → WebP или HTML")

st.markdown("""
Загрузите PNG-файлы и выберите, как их обработать:  
- **WebP**: без потерь, упакованные в ZIP  
- **HTML**: каждый PNG встраивается в отдельный `.html` файл (base64)  
""")

# Выбор формата
format_choice = st.radio("Выберите формат конвертации:", ["WebP", "HTML"])

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

            elif format_choice == "HTML":
                buffered = base64.b64encode(file.read()).decode()
                html_content = f"""
                <html>
                <body>
                <h3>{file.name}</h3>
                <img src="data:image/png;base64,{buffered}" />
                </body>
                </html>
                """
                html_path = os.path.join(output_dir, base_name + ".html")
                with open(html_path, "w") as html_file:
                    html_file.write(html_content)
                zipf.write(html_path, arcname=os.path.basename(html_path))

    # Кнопка для скачивания архива
    with open(zip_filename, "rb") as f:
        st.download_button("⬇️ Скачать архив", f, file_name=zip_filename, mime="application/zip")

    # Очистка
    for f in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, f))
    os.rmdir(output_dir)
    os.remove(zip_filename)
