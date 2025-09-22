import streamlit as st
import zipfile
from PIL import Image
import io
import base64
import pandas as pd
import re
from itertools import product, permutations

col1, col2 = st.columns(2)
st.set_page_config(page_title="Internal tools", layout="wide")

st.markdown(
    "<div style='text-align: center; margin-bottom: 20px;'>"
    "<img src='https://dumpster.cdn.sports.ru/7/f5/0180499259d7b11aaceee78e2b91e.png' width='80'>"
    "</div>",
    unsafe_allow_html=True
)

# Цвет фона
# Цвет фона
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color:#0E1117 !important; color:#FAFAFA !important; }
[data-testid="stHeader"]{ background:transparent !important; }
[data-testid="stSidebar"]{ background-color:#0E1117 !important; color:#FAFAFA !important; }

/* общий текст */
label, p, span { color:#FAFAFA !important; }

/* заголовки мятные */
h1, h2, h3, h4, h5, h6 { color:#28EBA4 !important; }

input, textarea { color:#FAFAFA !important; background-color:#11151c !important; border-color:#2a2f3a !important; }
.stDownloadButton > button, button[kind="primary"], button[kind="secondary"] { background-color:#28EBA4 !important; color:#0E1117 !important; border-color:#28EBA4 !important; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* инпуты и выпадающие списки */
input, textarea, select, .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
    background-color: #1E222A !important;  /* тёмно-серый фон */
    color: #FAFAFA !important;             /* белый текст */
    border: 1px solid #444 !important;
}

/* placeholder тоже белый */
input::placeholder, textarea::placeholder {
    color: #AAAAAA !important;
}

/* file uploader */
[data-testid="stFileUploader"] section {
    background-color: #1E222A !important;
    color: #FAFAFA !important;
    border: 1px dashed #444 !important;
}

/* select (выпадающий список) текст */
.stSelectbox div[data-baseweb="select"] span {
    color: #FAFAFA !important;
}
</style>
""", unsafe_allow_html=True)



# ==================== ЛЕВАЯ КОЛОНКА ==================== #
with col1:
    # -------------------- КОНВЕРТОР (PNG -> WebP) -------------------- #
    st.markdown("<h1 style='color:#28EBA4;'>КОНВЕРТАЦИЯ (PNG → WebP)</h1>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Загрузите PNG-файлы", type=["png"], accept_multiple_files=True)
    archive_name = st.text_input("опционально: название файла", placeholder="converted_images")

    if uploaded_files:
        converted_files = []
        converted_filenames = []

        for file in uploaded_files:
            image = Image.open(file).convert("RGBA")
            filename = file.name.rsplit(".", 1)[0]
            buffer = io.BytesIO()
            # lossless=True можно заменить на quality=90/method=6 при желании
            image.save(buffer, format="WEBP", lossless=True)
            converted_files.append(buffer.getvalue())
            converted_filenames.append(filename + ".webp")

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

    # -------------------- КОНВЕРТАЦИЯ В HTML -------------------- #
    st.markdown("<h1 style='color:#28EBA4;'>КОНВЕРТАЦИЯ В HTML</h1>", unsafe_allow_html=True)

    # Шаблоны HTML с плейсхолдером
    templates = {
        "FullScreen (320x480)": """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="ad.size" content="width=320px,height=480px">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AdFox Banner</title>
  <link rel="stylesheet" href="https://dumpster.cdn.sports.ru/0/52/558ad552e5e0256fae54ff7fc6d8c.css">
</head>
<body>
  <a href="%banner.reference_mrc_user1%" target="%banner.target%" style="display:block;width:100%;height:100%;text-decoration:none;cursor:pointer;">
    <div class="banner" style="width:100%;height:100%;">
      <img src="ССЫЛКА НА ИЗОБРАЖЕНИЕ" alt="баннер" style="width:100%;height:100%;display:block;">
    </div>
  </a>
</body>
</html>""",
        "Mobile Branding (100%x200px)": """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="ad.size" content="width=100%,height=200px">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AdFox Banner</title>
  <link rel="stylesheet" href="https://dumpster.cdn.sports.ru/e/4d/85f288418a95f555eb5035aebed92.css">
</head>
<body>
  <a href="%banner.reference_mrc_user1%" target="%banner.target%" style="display:block;width:100%;height:100%;text-decoration:none;cursor:pointer;">
    <div class="banner" style="width:100%;height:100%;">
      <img src="ССЫЛКА НА ИЗОБРАЖЕНИЕ" alt="баннер" style="width:100%;height:100%;display:block;">
    </div>
  </a>
</body>
</html>""",
        "1Right (300x600)": """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="ad.size" content="width=300px,height=600px">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AdFox Banner</title>
  <link rel="stylesheet" href="https://dumpster.cdn.sports.ru/2/96/4af4f5dcdeb75f36b9197556810c8.css">
</head>
<body>
  <a href="%banner.reference_mrc_user1%" target="%banner.target%" style="display:block;width:100%;height:100%;text-decoration:none;cursor:pointer;">
    <div class="banner" style="width:100%;height:100%;">
      <img src="ССЫЛКА НА ИЗОБРАЖЕНИЕ" alt="баннер" style="width:100%;height:100%;display:block;">
    </div>
  </a>
</body>
</html>""",
        "Desktop Branding (1920x1080)": """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="ad.size" content="width=1920,height=1080">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AdFox Banner</title>
  <link rel="stylesheet" href="https://dumpster.cdn.sports.ru/f/a3/a35026ae42d4e609a322ffb220623.css">
</head>
<body>
  <a href="%banner.reference_mrc_user1%" target="%banner.target%" style="display:block;width:100%;height:100%;text-decoration:none;cursor:pointer;">
    <div class="banner" style="width:100%;height:100%;">
      <img src="ССЫЛКА НА ИЗОБРАЖЕНИЕ" alt="баннер" style="width:100%;height:100%;display:block;">
    </div>
  </a>
</body>
</html>""",
        "Mobile_top (100%x250px)": """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="ad.size" content="width=100%,height=250px">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AdFox Banner</title>
  <link rel="stylesheet" href="https://dumpster.cdn.sports.ru/9/58/782b7c244f327056е145d297c6f4b.css">
</head>
<body>
  <a href="%banner.reference_mrc_user1%" target="%banner.target%" style="display:block;width:100%;height:100%;text-decoration:none;cursor:pointer;">
    <div class="banner" style="width:100%;height:100%;">
      <img src="ССЫЛКА НА ИЗОБРАЖЕНИЕ" alt="баннер" style="width:100%;height:100%;display:block;">
    </div>
  </a>
</body>
</html>"""
    }

    format_choice = st.selectbox("Выберите формат баннера", list(templates.keys()))
    image_url = st.text_input("Ссылка на визуал")

    if image_url and format_choice:
        html_code = templates[format_choice].replace("ССЫЛКА НА ИЗОБРАЖЕНИЕ", image_url)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("index.html", html_code)
        st.download_button(
            "📦 Скачать ZIP с index.html",
            data=zip_buffer.getvalue(),
            file_name=f"{format_choice.replace(' ', '_')}.zip",
            mime="application/zip"
        )

# ==================== ПРАВАЯ КОЛОНКА ==================== #
with col2:
    # -------------------- ГЕНЕРАТОР ССЫЛОК -------------------- #
    st.markdown("<h1 style='color:#28EBA4;'>ГЕНЕРАЦИЯ ССЫЛОК</h1>", unsafe_allow_html=True)
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

        # чекбокс ref1: если включён — поле ref1 показывается; если выключён — вместо него появится ref5 внизу
        show_ref1 = st.checkbox("ref1", value=True, key="toggle_ref1")

        # Базовый порядок полей: ref, (ref1?), ref2, ref3, ref4
        ref_order = ["ref"] + (["ref1"] if show_ref1 else []) + ["ref2", "ref3", "ref4"]

        inputs = {}
        for name in ref_order:
            inputs[name] = st.text_input(name)

        # Если ref1 отключён — добавляем ref5 в самом низу
        if not show_ref1:
            inputs["ref5"] = st.text_input("ref5")

        # Под последним полем — подсказка
        st.caption("можно вводить неограниченное значение параметров, отделяя через пробел")

        # Преобразуем поля в списки значений
        parsed = {k: parse_multi(v) for k, v in inputs.items()}

    else:
        st.markdown("utm-параметры")
        keys = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]
        ref_inputs = [st.text_input(key) for key in keys]
        parsed = {key: parse_multi(val) for key, val in zip(keys, ref_inputs)}

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
        keys_list = list(parsed.keys())

        for combo in combined:
            params = "&".join([f"{k}={v}" for k, v in zip(keys_list, combo) if v])
            full_url = f"{base_url}?{params}" if params else base_url
            value = combo[keys_list.index(varying_key)] if varying_key in keys_list else ""
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

    # -------------------- ГЕНЕРАТОР СЛАГОВ -------------------- #
    st.markdown("<h1 style='color:#28EBA4;'>СЛАГИ ДЛЯ ССЫЛОК</h1>", unsafe_allow_html=True)
    words_raw = st.text_input("2–3 слова через пробел или запятую", key="slug_words", placeholder="")

    if words_raw:
        # разбираем вход, приводим к нижнему регистру
        words = [w.lower() for w in re.split(r"[\s,]+", words_raw.strip()) if w]
        if 2 <= len(words) <= 3:
            seps = ['-', '_', '.']
            combos = set()
            for p in permutations(words):
                for sep in seps:
                    combos.add(sep.join(p))
            slugs = sorted(combos, key=lambda s: (len(s), s))
            text_blob = "\n".join(slugs)
            st.text_area("Варианты слагов", value=text_blob, height=200)
        else:
            st.caption("Введите от 2 до 3 слов.")

