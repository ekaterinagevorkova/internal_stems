import streamlit as st
import pandas as pd
import io
from PIL import Image

# Настройки страницы
st.set_page_config(page_title="PNG → WebP / HTML5 + Генератор ссылок", layout="wide")

# Вставка логотипа по центру
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("зубы.png", width=80)

st.markdown("## 🎯 PNG → WebP или HTML5 / 🔗 Генератор ссылок")

# Вспомогательная функция: разбор ввода на список
def parse_multi_input(value):
    raw = value.replace(",", "\n").replace(" ", "\n")
    return [line.strip() for line in raw.split("\n") if line.strip()]

# Контейнер для двух колонок
left, right = st.columns(2)

with left:
    st.markdown("### 🖼 Конвертер изображений")
    fmt = st.radio("Формат", ["WebP", "HTML5"], horizontal=True)
    files = st.file_uploader("Загрузите PNG-файлы", type=["png"], accept_multiple_files=True)

    output_files = []
    if files:
        for file in files:
            im = Image.open(file)
            buf = io.BytesIO()

            if fmt == "WebP":
                im.save(buf, format="WebP", lossless=True)
                ext = "webp"
                filename = file.name.replace(".png", ".webp")
                output_files.append((filename, buf.getvalue()))
            else:
                b64 = io.BytesIO()
                im.save(b64, format="PNG")
                b64_str = b64.getvalue().hex()
                html = f"<html><body><h1>{file.name}</h1><img src='data:image/png;base64,{b64.getvalue().decode(errors="ignore")}'></body></html>"
                filename = file.name.replace(".png", ".html")
                output_files.append((filename, html.encode("utf-8")))

        zip_buf = io.BytesIO()
        import zipfile
        with zipfile.ZipFile(zip_buf, "w") as zf:
            for name, data in output_files:
                zf.writestr(name, data)
        st.download_button("📥 Скачать архив", data=zip_buf.getvalue(), file_name="converted.zip")

with right:
    st.markdown("### 🔗 Генератор ссылок")
    base_url = st.text_input("Основная ссылка")
    link_type = st.radio("Тип параметров", ["ref", "utm"], horizontal=True)

    def generate_links(base, inputs):
        from itertools import product
        keys = list(inputs.keys())
        values = [parse_multi_input(inputs[k]) for k in keys]
        combos = list(product(*values))
        results = []
        for combo in combos:
            full_url = base + "?" + "&".join(f"{k}={v}" for k, v in zip(keys, combo))
            changing_value = next((v for v in combo if len(values[keys.index(k)]) > 1 for k in keys), "")
            results.append((changing_value, full_url))
        return results

    inputs = {}
    if link_type == "ref":
        st.markdown("##### ref-параметры (можно списки в любом поле)")
        for i in range(5):
            key = f"ref{i if i > 0 else ''}"
            inputs[key] = st.text_input(key)
    else:
        for k in ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]:
            inputs[k] = st.text_input(k)

    if base_url and any(inputs.values()):
        results = generate_links(base_url, inputs)
        all_results = []
        for val, url in results:
            st.markdown(f"<div style='display: flex; gap: 12px; align-items: center;'><span style='color:#28EBA4;font-weight:bold;font-size:20px'>{val}</span><code>{url}</code></div>", unsafe_allow_html=True)
            all_results.append({"Формат": val, "Ссылка": url, "Визуал": ""})

        if all_results:
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
