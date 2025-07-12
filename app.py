import streamlit as st
import pandas as pd
from PIL import Image
import zipfile
import io
import base64
from io import BytesIO
import os

st.set_page_config(page_title="ИНСТРУМЕНТЫ", layout="wide")

st.markdown("""
    <style>
        .block-style {
            border: 2px solid #28EBA4;
            border-radius: 20px;
            padding: 20px;
            margin: 10px;
        }
        .centered-image {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        .download-button-style {
            background-color: #28EBA4;
            color: black;
            font-weight: bold;
            border-radius: 10px;
        }
        .generated-link {
            display: flex;
            align-items: center;
            gap: 10px;
            font-family: monospace;
            margin-bottom: 5px;
        }
        .param-label {
            color: #28EBA4;
            min-width: 80px;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>ИНСТРУМЕНТЫ</h1>", unsafe_allow_html=True)

# Верхний логотип
with st.container():
    st.markdown('<div class="centered-image"><img src="data:image/png;base64,{}" width="60"></div>'.format(
        base64.b64encode(open("зубы.png", "rb").read()).decode()), unsafe_allow_html=True)

col1, col2 = st.columns(2)

# --- КОНВЕРТОР --- #
with col1:
    with st.container():
        st.markdown("<div class='block-style'><h3 style='text-align:center'>КОНВЕРТОР</h3>", unsafe_allow_html=True)

        format_type = st.radio("Формат", ["WebP", "HTML5"], index=0)
        uploaded_files = st.file_uploader("Загрузите PNG-файлы", type=["png"], accept_multiple_files=True)

        archive_name = st.text_input("Опционально: название файла")
        archive_btn = st.button("СКАЧАТЬ АРХИВ")

        if archive_btn and uploaded_files:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as zip_file:
                for file in uploaded_files:
                    img = Image.open(file)
                    output = io.BytesIO()
                    if format_type == "WebP":
                        img.save(output, format="WEBP", lossless=True)
                        ext = ".webp"
                    else:
                        html = f"<img src='data:image/png;base64,{base64.b64encode(file.read()).decode()}' />"
                        output = io.BytesIO(html.encode())
                        ext = ".html"
                    zip_file.writestr(file.name.replace(".png", ext), output.getvalue())

            st.download_button(
                label="📦 Скачать архив",
                data=buffer.getvalue(),
                file_name=f"{archive_name or 'converted'}.zip",
                mime="application/zip",
                use_container_width=True
            )

        st.markdown("</div>", unsafe_allow_html=True)


# --- ГЕНЕРАЦИЯ ССЫЛОК --- #
with col2:
    with st.container():
        st.markdown("<div class='block-style'><h3 style='text-align:center'>ГЕНЕРАЦИЯ ССЫЛОК</h3>", unsafe_allow_html=True)

        base_url = st.text_input("Основная ссылка")
        link_type = st.radio("Тип параметров", ["ref", "utm"], horizontal=True)

        def parse_input(value):
            if not value:
                return [""]
            value = value.replace(",", "\n").replace(" ", "\n")
            return [v.strip() for v in value.split("\n") if v.strip()]

        inputs = {}
        all_results = []

        if link_type == "ref":
            st.markdown("#### ref-параметры (можно списки в любом поле)")
            for key in ["ref", "ref1", "ref2", "ref3", "ref4"]:
                inputs[key] = st.text_input(key)
        else:
            st.markdown("#### utm-параметры (можно списки в любом поле)")
            for key in ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]:
                inputs[key] = st.text_input(key)

        if base_url:
            parsed_inputs = {k: parse_input(v) for k, v in inputs.items()}
            max_len = max(len(v) for v in parsed_inputs.values())
            for i in range(max_len):
                params = []
                variable_label = ""
                for k, v in parsed_inputs.items():
                    val = v[i % len(v)]
                    params.append(f"{k}={val}")
                    if i < len(v) and val not in parsed_inputs[k][:i]:
                        variable_label = val
                link = base_url + ("&" if "?" in base_url else "?") + "&".join(params)
                all_results.append((variable_label, link))

            for label, link in all_results:
                st.markdown(f"<div class='generated-link'><span class='param-label'>{label}</span>{link}</div>", unsafe_allow_html=True)

        # --- Таблица и скачивание --- #
        if all_results:
            df = pd.DataFrame([{"Формат": label, "Ссылка": url, "Визуал": ""} for label, url in all_results])

            # EXCEL
            excel_out = BytesIO()
            with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            excel_out.seek(0)

            st.download_button(
                label="📥 СКАЧАТЬ EXCEL",
                data=excel_out,
                file_name="ссылки.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            # CSV
            csv_out = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 СКАЧАТЬ CSV",
                data=csv_out,
                file_name="ссылки.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

