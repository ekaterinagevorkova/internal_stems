
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="PNG ➜ WebP / HTML5 + Генератор ссылок", layout="wide")
st.markdown(
    """
    <style>
        .block-container {{
            padding-top: 2rem;
        }}
        .tool-box {{
            border: 2px solid #28EBA4;
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }}
        .link-row {{
            display: flex;
            align-items: center;
            font-family: monospace;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }}
        .link-label {{
            color: #28EBA4;
            font-weight: bold;
            min-width: 90px;
            display: inline-block;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='tool-box'>", unsafe_allow_html=True)
    st.header("🎯 PNG ➜ WebP или HTML5")
    format_option = st.radio("Формат", ["WebP", "HTML5"])
    uploaded_files = st.file_uploader("Загрузите PNG-файлы", type=["png"], accept_multiple_files=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='tool-box'>", unsafe_allow_html=True)
    st.header("🔗 Генератор ссылок")
    base_url = st.text_input("Основная ссылка")
    link_type = st.radio("Тип параметров", ["ref", "utm"])

    def parse_multi_input(value):
        raw = value.replace(",", "\n").replace(" ", "\n")
        return [line.strip() for line in raw.split("\n") if line.strip()]

    all_results = []

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
                row_params = []
                changing = ""
                for key, values in parsed_fields.items():
                    if values:
                        val = values[i % len(values)]
                        row_params.append(f"{key}={val}")
                        if len(values) > 1:
                            changing = val
                link = base_url + "?" + "&".join(row_params)
                all_results.append({"Формат": changing, "Ссылка": link, "Визуал": ""})

    if link_type == "utm":
        st.markdown("### utm-параметры (можно списки в любом поле)")
        utm_source = st.text_input("utm_source")
        utm_medium = st.text_input("utm_medium")
        utm_campaign = st.text_input("utm_campaign")
        utm_content = st.text_input("utm_content")
        utm_term = st.text_input("utm_term")

        if base_url and utm_source:
            parsed_fields = {
                "utm_source": parse_multi_input(utm_source),
                "utm_medium": parse_multi_input(utm_medium),
                "utm_campaign": parse_multi_input(utm_campaign),
                "utm_content": parse_multi_input(utm_content),
                "utm_term": parse_multi_input(utm_term),
            }

            max_count = max(len(v) for v in parsed_fields.values() if v)
            for i in range(max_count):
                row_params = []
                changing = ""
                for key, values in parsed_fields.items():
                    if values:
                        val = values[i % len(values)]
                        row_params.append(f"{key}={val}")
                        if len(values) > 1:
                            changing = val
                link = base_url + "?" + "&".join(row_params)
                all_results.append({"Формат": changing, "Ссылка": link, "Визуал": ""})

    if all_results:
        st.markdown("---")
        for item in all_results:
            st.markdown(
                f"<div class='link-row'><div class='link-label'>{item['Формат']}</div> {item['Ссылка']}</div>",
                unsafe_allow_html=True
            )

        # ✅ Генерация Excel
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

    st.markdown("</div>", unsafe_allow_html=True)
