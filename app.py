import streamlit as st
from PIL import Image
import zipfile
import base64
import io
import os

# 🎨 ВСТРОЕННЫЙ ФОН (градиент Спортс)
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

st.set_page_config(page_title="PNG → WebP / HTML5 + Генератор ссылок", layout="wide")

col1, col2 = st.columns(2)

# 👈 Конвертер PNG → WebP / HTML5
with col1:
    st.header("🎯 PNG → WebP или HTML5")
    format_choice = st.radio("Формат", ["WebP", "HTML5"], horizontal=True)
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
</html>"""
                    html_path = os.path.join(output_dir, base_name + ".html")
                    with open(html_path, "w") as html_file:
                        html_file.write(html_content)
                    zipf.write(html_path, arcname=os.path.basename(html_path))

        with open(zip_filename, "rb") as f:
            st.download_button("⬇️ Скачать архив", f, file_name=zip_filename, mime="application/zip")

        for f in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, f))
        os.rmdir(output_dir)
        os.remove(zip_filename)

# 👉 Генератор ссылок (ref или utm)
with col2:
    st.header("🔗 Генератор ссылок")
    base_url = st.text_input("Основная ссылка")
    link_type = st.radio("Тип параметров", ["ref", "utm"], horizontal=True)

    def parse_multi_input(value):
        raw = value.replace(",", "\n").replace(" ", "\n")
        return [line.strip() for line in raw.split("\n") if line.strip()]

    if link_type == "ref":
        st.markdown("### ref-параметры (можно списки в любом поле)")
        ref = st.text_input("ref")
        ref1 = st.text_input("ref1")
        ref2 = st.text_input("ref2")
        ref3 = st.text_input("ref3")
        ref4 = st.text_input("ref4")

        if base_url and ref:
            parsed_fields = {
                "ref": parse_multi_input(ref),
                "ref1": parse_multi_input(ref1),
                "ref2": parse_multi_input(ref2),
                "ref3": parse_multi_input(ref3),
                "ref4": parse_multi_input(ref4),
            }
            max_count = max(len(v) for v in parsed_fields.values() if v)
            for i in range(max_count):
                params = []
                for key, values in parsed_fields.items():
                    if values:
                        val = values[i % len(values)]
                        params.append(f"{key}={val}")
                result = f"{base_url}?" + "&".join(params)
                st.code(result, language="html")

    elif link_type == "utm":
        st.markdown("### utm-параметры (можно списки в любом поле)")
        utm_source = st.text_input("utm_source")
        utm_medium = st.text_input("utm_medium")
        utm_campaign = st.text_input("utm_campaign")
        utm_content = st.text_input("utm_content")
        utm_term = st.text_input("utm_term")

        if base_url and utm_source and utm_medium and utm_campaign:
            parsed_fields = {
                "utm_source": parse_multi_input(utm_source),
                "utm_medium": parse_multi_input(utm_medium),
                "utm_campaign": parse_multi_input(utm_campaign),
                "utm_content": parse_multi_input(utm_content),
                "utm_term": parse_multi_input(utm_term),
            }
            max_count = max(len(v) for v in parsed_fields.values() if v)
            for i in range(max_count):
                params = []
                for key, values in parsed_fields.items():
                    if values:
                        val = values[i % len(values)]
                        params.append(f"{key}={val}")
                result = f"{base_url}?" + "&".join(params)
                st.code(result, language="html")
