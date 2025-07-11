import streamlit as st
from PIL import Image
import zipfile
import base64
import io
import os

# 🎨 Фон-картинка Спортс в base64
st.markdown("""
<style>
.stApp {
    background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAB4AAAAQ4CAYAAADo08FDAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAEBndSURBVHgB7L1rYjM5rzRW0CKynqwh+1+LkNduAlUFUJ457/nyK+KMH0ndJG7EnS07/q//5//OwDMyE4j/fMrfT//5qTvPuxzvn9f8zyvn/cIYI/4D8+d6vdo9gQu5x7lN3Zkf51325d+5dTU3PT/3G34Aylfj/OX7wffwdLAFeYpz7/lf4cJozEOT3JDrftk5JO05ZHEFlDXvP+ter9/rukcL70UmyttAIuuiP/MTRwy481XxFK7E1hO9ZHL/gfV+9u53be/jJOTZQ9Wzfp/Umui9BgWTm5ClLrZvh7cLGz2n+L/YBJQETD2lLlAnU...");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    background-position: center;
}
</style>
""", unsafe_allow_html=True)

# 🧱 Настройки страницы
st.set_page_config(page_title="PNG → WebP или HTML5", layout="centered")

# 🏷 Заголовок и описание
st.title("🖼 PNG → WebP или HTML5 (для медийной рекламы)")

st.markdown("""
Загрузите PNG-файлы и выберите, как их обработать:

- **WebP** — без потерь, изображения в формате `.webp`  
- **HTML5** — каждый PNG встроен в чистый `.html` (подходит для AdFox, DV360 и др.)
""")

st.divider()

# 🔘 Формат конвертации
format_choice = st.radio("Формат конвертации", ["WebP", "HTML5"], horizontal=True)

# 📁 Загрузка файлов
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

    # ⬇️ Кнопка скачивания архива
    with open(zip_filename, "rb") as f:
        st.download_button("⬇️ Скачать архив", f, file_name=zip_filename, mime="application/zip")

    # 🧹 Очистка временных файлов
    for f in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, f))
    os.rmdir(output_dir)
    os.remove(zip_filename)
