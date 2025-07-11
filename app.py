import streamlit as st
from PIL import Image
import zipfile
import base64
import io
import os

st.set_page_config(page_title="PNG → WebP / HTML5 + Генератор ссылок", layout="wide")

st.markdown("""
<style>
    .stRadio > div { gap: 1rem; }
    .stRadio > div > label { color: #28EBA4 !important; }
    .stDownloadButton button {
        background-color: #28EBA4;
        color: black;
        font-weight: 600;
    }
    .block-container > div > div {
        border: 2px solid #28EBA4;
        border-radius: 18px;
        padding: 24px;
        margin-bottom: 24px;
        background-color: #111;
    }
    .link-row {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 0.3rem 0;
        flex-wrap: wrap;
    }
    .link-label {
        min-width: 2rem;
        color: #28EBA4;
        font-weight: bold;
        font-size: 1.2rem;
        word-break: break-word;
        max-width: 100px;
    }
    .link-url {
        font-family: monospace;
        word-break: break-all;
        color: #ffffff;
        flex: 1;
        min-width: 300px;
    }
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.header("🎯 PNG → WebP или HTML5")
    format_choice = st.radio("Формат", ["WebP", "HTML5"], horizontal=True)
    uploaded_files = st.file_uploader("Загрузите PNG-файлы", type=["png"], accept_multiple_files=True)

    if uploaded_files:
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        zip_filename = "converted_files.zip"

        html_template = (
            "<!DOCTYPE html><html lang='ru'><head><meta charset='UTF-8'>"
            "<title>Banner</title><style>"
            "html, body {{margin:0;padding:0;background:transparent;}}"
            "img {{width:100%;height:auto;display:block;}}"
            "</style></head><body>"
            "<img src='data:image/png;base64,{{}}' alt='banner' />"
            "</body></html>"
        )

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
                    html_content = html_template.format(buffered)
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

with col2:
    st.header("🔗 Генератор ссылок")
    base_url = st.text_input("Основная ссылка")
    link_type = st.radio("Тип параметров", ["ref", "utm"], horizontal=True)

    def parse_multi_input(value):
        raw = value.replace(",", "\n").replace(" ", "\n")
        return [line.strip() for line in raw.split("\n") if line.strip()]

    def get_changing_field(parsed_fields):
        lengths = {key: len(v) for key, v in parsed_fields.items() if v}
        max_len = max(lengths.values(), default=0)
        return [k for k, l in lengths.items() if l == max_len and l > 1]

    if base_url:
        if link_type == "ref":
            st.markdown("### ref-параметры (можно списки в любом поле)")
            ref = st.text_input("ref")
            ref1 = st.text_input("ref1")
            ref2 = st.text_input("ref2")
            ref3 = st.text_input("ref3")
            ref4 = st.text_input("ref4")

            parsed_fields = {
                "ref": parse_multi_input(ref),
                "ref1": parse_multi_input(ref1),
                "ref2": parse_multi_input(ref2),
                "ref3": parse_multi_input(ref3),
                "ref4": parse_multi_input(ref4),
            }

        else:
            st.markdown("### utm-параметры (можно списки в любом поле)")
            utm_source = st.text_input("utm_source")
            utm_medium = st.text_input("utm_medium")
            utm_campaign = st.text_input("utm_campaign")
            utm_content = st.text_input("utm_content")
            utm_term = st.text_input("utm_term")

            parsed_fields = {
                "utm_source": parse_multi_input(utm_source),
                "utm_medium": parse_multi_input(utm_medium),
                "utm_campaign": parse_multi_input(utm_campaign),
                "utm_content": parse_multi_input(utm_content),
                "utm_term": parse_multi_input(utm_term),
            }

        max_count = max(len(v) for v in parsed_fields.values() if v)
        changing_fields = get_changing_field(parsed_fields)

        for i in range(max_count):
            params = []
            for key, values in parsed_fields.items():
                if values:
                    val = values[i % len(values)]
                    params.append(f"{key}={val}")
            url = f"{base_url}?" + "&".join(params)

            label = ""
            for key in changing_fields:
                if parsed_fields[key]:
                    label = parsed_fields[key][i % len(parsed_fields[key])]
                    break
            st.markdown(
                '<div class="link-row"><div class="link-label">{}</div><div class="link-url">{}</div></div>'.format(label, url),
                unsafe_allow_html=True
            )



# 👉 Кнопка для скачивания Excel-таблицы с результатами
import pandas as pd

if base_url and any(parsed_fields.values()):
    all_results = []
    for i in range(max_count):
        row_params = []
        row_label = ""
        for key, values in parsed_fields.items():
            if values:
                val = values[i % len(values)]
                row_params.append(f"{key}={val}")
                if key in changing_fields and not row_label:
                    row_label = val
        link = base_url + "?" + "&".join(row_params)
        all_results.append({"Формат": row_label, "Ссылка": link, "Визуал": ""})

    df = pd.DataFrame(all_results)
    excel_out = io.BytesIO()
    with pd.ExcelWriter(excel_out, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
   st.download_button(
    label="📥 Скачать Excel-таблицу",
    data=excel_out.getvalue(),
    file_name="ссылки.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
