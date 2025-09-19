import streamlit as st
import zipfile
from PIL import Image
import io
import base64
import pandas as pd

st.set_page_config(page_title="ИНСТРУМЕНТЫ", layout="wide")

col1, col2 = st.columns(2)

# -------------------- КОНВЕРТОР (PNG -> WebP) -------------------- #
with col1:
    st.markdown("<h1 style='color:#28EBA4;'>КОНВЕРТОР (PNG → WebP)</h3>", unsafe_allow_html=True)
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

# -------------------- ГЕНЕРАТОР ССЫЛОК -------------------- #
with col2:
    st.markdown("<h1 style='color:#28EBA4;'>ГЕНЕРАЦИЯ ССЫЛОК</h3>", unsafe_allow_html=True)
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
            full_url = f"{base_url}?{params}" if params else base_url
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
import streamlit as st
import io
import zipfile

st.set_page_config(page_title="HTML Banner Generator", layout="wide")

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
  <link rel="stylesheet" href="https://dumpster.cdn.sports.ru/9/58/782b7c244f327056e145d297c6f4b.css">
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
# -------------------- DATA URL (PNG/JPEG/WebP → data:) -------------------- #
st.markdown("<h3 style='color:#28EBA4;'>DATA URL</h3>", unsafe_allow_html=True)
img_file = st.file_uploader(
    "Загрузите изображение (PNG/JPEG/WebP)",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=False,
    key="data_url_uploader",
)

def _detect_mime(uploaded) -> str:
    # 1) пробуем по mime-типу, который отдаёт браузер
    if getattr(uploaded, "type", None):
        return uploaded.type
    # 2) иначе — по расширению
    suffix = uploaded.name.split(".")[-1].lower()
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    }.get(suffix, "application/octet-stream")

if img_file is not None:
    raw = img_file.read()
    mime = _detect_mime(img_file)
    data_url = f"data:{mime};base64,{base64.b64encode(raw).decode('utf-8')}"
    st.image(raw, caption="Превью", use_container_width=True)
    st.markdown("**Ссылка (data URL):**")
    st.text_area("",
                 value=data_url,
                 height=160,
                 label_visibility="collapsed")
    st.download_button(
        "📄 Скачать как .txt",
        data=data_url.encode("utf-8"),
        file_name="image_data_url.txt",
        mime="text/plain",
    )


# UI
format_choice = st.selectbox("Выберите формат баннера", list(templates.keys()))
image_url = st.text_input("Ссылка на визуал")

if image_url and format_choice:
    # Подставляем ссылку
    html_code = templates[format_choice].replace("ССЫЛКА НА ИЗОБРАЖЕНИЕ", image_url)

    # Создаём ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("index.html", html_code)

    # Кнопка для скачивания
    st.download_button(
        "📦 Скачать ZIP с index.html",
        data=zip_buffer.getvalue(),
        file_name=f"{format_choice.replace(' ', '_')}.zip",
        mime="application/zip"
    )


