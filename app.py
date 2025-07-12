import streamlit as st
import base64
import zipfile
from PIL import Image
import io
import pandas as pd

st.set_page_config(page_title="ИНСТРУМЕНТЫ", layout="wide")

st.markdown("<h1 style='text-align: center;'>ИНСТРУМЕНТЫ</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

# -------------------- КОНВЕРТОР -------------------- #
with col1:
    st.markdown("<h3 style='color:#28EBA4;'>КОНВЕРТОР</h3>", unsafe_allow_html=True)
    format_type = st.radio("Формат", ["WebP", "HTML5"], horizontal=True)
    uploaded_files = st.file_uploader("Загрузите PNG-файлы", type=["png"], accept_multiple_files=True)
    archive_name = st.text_input("опционально: название файла", placeholder="converted_images")

    if uploaded_files:
        converted_files = []
        converted_filenames = []
        for file in uploaded_files:
            image = Image.open(file).convert("RGBA")
            filename = file.name.rsplit(".", 1)[0]
            if format_type == "WebP":
                buffer = io.BytesIO()
                image.save(buffer, format="WEBP", lossless=True)
                converted_files.append(buffer.getvalue())
                converted_filenames.append(filename + ".webp")
            elif format_type == "HTML5":
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                b64_img = base64.b64encode(buffer.getvalue()).decode()
                html_content = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'></head><body><img src='data:image/png;base64,{b64_img}'></body></html>"""
                converted_files.append(html_content.encode("utf-8"))
                converted_filenames.append(filename + ".html")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for name, data in zip(converted_filenames, converted_files):
                zip_file.writestr(name, data)

        final_name = (archive_name.strip() or "converted_images").replace(" ", "_") + ".zip"
        st.download_button(
            "📦 СКАЧАТЬ АРХИВ",
            data=zip_buffer.getvalue(),
            file_name=final_name,
            mime="application/zip"
        )

# -------------------- ГЕНЕРАТОР ССЫЛОК -------------------- #
with col2:
    st.markdown("<h3 style='color:#28EBA4;'>ГЕНЕРАЦИЯ ССЫЛОК</h3>", unsafe_allow_html=True)
    base_url = st.text_input("Основная ссылка")
    link_type = st.radio("Тип параметров", ["ref", "utm"], horizontal=True)

    def parse_multi(value):
        if not value:
            return [""]
        if "," in value:
            return [v.strip() for v in value.split(",") if v.strip()]
        if "\n" in value:
            return [v.strip() for v in value.split("\n") if v.strip()]
        if " " in value:
            return [v.strip() for v in value.split(" ") if v.strip()]
        return [value.strip()]

    if link_type == "ref":
        st.markdown("ref-параметры")
        ref_inputs = [st.text_input(f"ref{i if i > 0 else ''}") for i in range(5)]
        parsed = {f"ref{i if i > 0 else ''}": parse_multi(val) for i, val in enumerate(ref_inputs)}
    else:
        st.markdown("utm-параметры")
        keys = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]
        ref_inputs = [st.text_input(key) for key in keys]
        parsed = {key: parse_multi(val) for key, val in zip(keys, ref_inputs)}

    from itertools import product
    all_results = []
    varying_key = ""

    if base_url:
        lens = {k: len(v) for k, v in parsed.items() if v}
        max_len = max(lens.values()) if lens else 1
        for k in parsed:
            if len(parsed[k]) == max_len:
                varying_key = k
                break

        combined = list(product(*[parsed[k] if parsed[k] else [""] for k in parsed]))
        keys = list(parsed.keys())

        for combo in combined:
            params = "&".join([f"{k}={v}" for k, v in zip(keys, combo) if v])
            full_url = f"{base_url}?{params}"
            value = combo[keys.index(varying_key)] if varying_key in keys else ""
            st.markdown(
                f"<div style='display: flex; align-items: center; gap: 10px;'>"
                f"<span style='color: #28EBA4; font-weight: bold; min-width: 60px'>{value}</span>"
                f"<code style='word-break: break-all'>{full_url}</code>"
                f"</div>",
                unsafe_allow_html=True
            )
            all_results.append({"Формат": value, "Ссылка": full_url, "Визуал": ""})

    if all_results:
        df = pd.DataFrame(all_results)
        excel_buf = io.BytesIO()
        csv_buf = io.StringIO()
        df.to_excel(excel_buf, index=False)
        df.to_csv(csv_buf, index=False)

        st.download_button("Скачать Excel", data=excel_buf.getvalue(), file_name="ссылки.xlsx")
        st.download_button("Скачать CSV", data=csv_buf.getvalue(), file_name="ссылки.csv")
