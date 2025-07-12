import streamlit as st
import zipfile
import io
import os
from PIL import Image
import base64
import pandas as pd

st.set_page_config(page_title="ИНСТРУМЕНТЫ", layout="wide")

st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
    }
    .tool-block {
        border: 2px solid #28EBA4;
        border-radius: 20px;
        padding: 20px;
        margin: 10px;
        background-color: #0E0E10;
    }
    .tool-title {
        color: #28EBA4;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    .download-buttons button {
        background-color: #28EBA4 !important;
        color: black !important;
        font-weight: bold;
        width: 100%%;
    }
    .link-label {
        font-weight: bold;
        color: #28EBA4;
        min-width: 120px;
        display: inline-block;
    }
    .link-row {
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>ИНСТРУМЕНТЫ</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

# ========== Конвертор ==========
with col1:
    st.markdown("<div class='tool-block'>", unsafe_allow_html=True)
    st.markdown("<div class='tool-title'>КОНВЕРТОР</div>", unsafe_allow_html=True)

    format_option = st.radio("Формат", ["WebP", "HTML5"], horizontal=True)
    uploaded_files = st.file_uploader("Загрузите PNG-файлы", type="png", accept_multiple_files=True)

    archive_name = st.text_input("опционально: название файла")

    if format_option and uploaded_files:
        archive_buffer = io.BytesIO()
        with zipfile.ZipFile(archive_buffer, "w") as zipf:
            for uploaded_file in uploaded_files:
                image = Image.open(uploaded_file).convert("RGBA")
                filename = os.path.splitext(uploaded_file.name)[0]
                if format_option == "WebP":
                    buffer = io.BytesIO()
                    image.save(buffer, format="WEBP", lossless=True)
                    zipf.writestr(f"{filename}.webp", buffer.getvalue())
                elif format_option == "HTML5":
                    html_str = f"""<html><body><img src='data:image/png;base64,{base64.b64encode(uploaded_file.read()).decode()}'></body></html>"""
                    zipf.writestr(f"{filename}.html", html_str)

        archive_buffer.seek(0)
        btn_name = "📦 СКАЧАТЬ АРХИВ"
        archive_filename = archive_name.strip() + ".zip" if archive_name else "converted_images.zip"
        st.download_button(btn_name, data=archive_buffer, file_name=archive_filename)

    st.markdown("</div>", unsafe_allow_html=True)

# ========== Генерация ссылок ==========
with col2:
    st.markdown("<div class='tool-block'>", unsafe_allow_html=True)
    st.markdown("<div class='tool-title'>ГЕНЕРАЦИЯ ССЫЛОК</div>", unsafe_allow_html=True)

    base_url = st.text_input("Основная ссылка")
    link_type = st.radio("Тип параметров", ["ref", "utm"], horizontal=True)

    def parse_multi_input(value):
        raw = value.replace(",", "\n").replace(" ", "\n")
        return [line.strip() for line in raw.split("\n") if line.strip()]

    fields = {}
    if link_type == "ref":
        st.markdown("### ref-параметры (можно списки в любом поле)")
        for name in ["ref", "ref1", "ref2", "ref3", "ref4"]:
            fields[name] = parse_multi_input(st.text_input(name))
    else:
        st.markdown("### utm-параметры (можно списки в любом поле)")
        for name in ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]:
            fields[name] = parse_multi_input(st.text_input(name))

    max_len = max((len(v) for v in fields.values()), default=0)
    all_results = []

    if base_url and any(fields.values()):
        for i in range(max_len):
            url = base_url + "?"
            label = ""
            for key, val_list in fields.items():
                value = val_list[i] if i < len(val_list) else val_list[-1] if val_list else ""
                url += f"{key}={value}&"
                if i < len(val_list):
                    label = value  # последняя изменяемая переменная
            st.markdown(f"<div class='link-row'><div class='link-label'>{label}</div> {url[:-1]}</div>", unsafe_allow_html=True)
            all_results.append({"Формат": label, "Ссылка": url[:-1], "Визуал": ""})

    if all_results:
        df = pd.DataFrame(all_results)
        excel_out = io.BytesIO()
        df.to_excel(excel_out, index=False)
        st.download_button("📥 СКАЧАТЬ EXCEL", data=excel_out.getvalue(), file_name="ссылки.xlsx")

        csv_out = df.to_csv(index=False).encode("utf-8")
        st.download_button("📄 СКАЧАТЬ CSV", data=csv_out, file_name="ссылки.csv")

    st.markdown("</div>", unsafe_allow_html=True)


