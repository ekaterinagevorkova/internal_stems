# app.py
import io
import zipfile
import re
from itertools import product, permutations

import pandas as pd
from PIL import Image
import streamlit as st
import requests  # === SHORT.IO ===

# НАСТРОЙКИ СТРАНИЦЫ
st.set_page_config(page_title="Internal tools", layout="wide")

# ПАРОЛЬ: сначала из st.secrets["password"], иначе fallback
FALLBACK_PASSWORD = "12345"
PASSWORD = st.secrets.get("password", FALLBACK_PASSWORD)

# === SHORT.IO ===
# Используем секретный ключ (sk_), а не публичный pk_
SHORTIO_API_KEY = st.secrets.get("shortio_api_key", "sk_ROGCu7fwKkYVRz5V")
SHORTIO_DOMAIN_ID = st.secrets.get("shortio_domain_id", "216771")

# СТРАНИЦА ИНСТРУМЕНТОВ
def render_tools():
    st.markdown(
        "<div style='text-align: center; margin-bottom: 20px;'>"
        "<img src='https://dumpster.cdn.sports.ru/5/93/bf20303bae2833f0d522d4418ae64.png' width='80'>"
        "</div>",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns(2)

    # ─── ЛЕВАЯ КОЛОНКА ──────────────────────────────────────────────────────────
    with col1:
        st.markdown("<h1 style='color:#28EBA4;'>КОНВЕРТАЦИЯ (PNG → WebP)</h1>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Загрузите PNG-файлы", type=["png"], accept_multiple_files=True)
        archive_name = st.text_input("опционально: название файла", placeholder="converted_images")

        if uploaded_files:
            converted_files, converted_filenames = [], []
            for file in uploaded_files:
                image = Image.open(file).convert("RGBA")
                filename = file.name.rsplit(".", 1)[0]
                buffer = io.BytesIO()
                image.save(buffer, format="WEBP", lossless=True)
                converted_files.append(buffer.getvalue())
                converted_filenames.append(filename + ".webp")

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for name, data in zip(converted_filenames, converted_files):
                    zip_file.writestr(name, data)

            final_name = (archive_name.strip() or "converted_images").replace(" ", "_") + ".zip"
            st.download_button("📦 СКАЧАТЬ АРХИВ", data=zip_buffer.getvalue(), file_name=final_name, mime="application/zip")

        # Конвертация в HTML (оставил без изменений — шаблоны баннеров)
        st.markdown("<h1 style='color:#28EBA4;'>КОНВЕРТАЦИЯ В HTML</h1>", unsafe_allow_html=True)
        templates = {
            "FullScreen (320x480)": "<!DOCTYPE html>...",
            "Mobile Branding (100%x200px)": "<!DOCTYPE html>...",
            "1Right (300x600)": "<!DOCTYPE html>...",
            "Desktop Branding (1920x1080)": "<!DOCTYPE html>...",
            "Mobile_top (100%x250px)": "<!DOCTYPE html>..."
        }
        format_choice = st.selectbox("Выберите формат баннера", list(templates.keys()))
        image_url = st.text_input("Ссылка на визуал")
        if image_url and format_choice:
            html_code = templates[format_choice].replace("ССЫЛКА НА ИЗОБРАЖЕНИЕ", image_url)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                zf.writestr("index.html", html_code)
            st.download_button("📦 Скачать ZIP с index.html", data=zip_buffer.getvalue(),
                               file_name=f"{format_choice.replace(' ', '_')}.zip", mime="application/zip")

    # ─── ПРАВАЯ КОЛОНКА ─────────────────────────────────────────────────────────
    with col2:
        # Генерация ссылок (оставил как было)
        st.markdown("<h1 style='color:#28EBA4;'>ГЕНЕРАЦИЯ ССЫЛОК</h1>", unsafe_allow_html=True)
        base_url = st.text_input("Основная ссылка")
        link_type = st.radio("Тип параметров", ["ref", "utm"], horizontal=True)

        def parse_multi(value):
            if not value:
                return [""]
            for sep in (",", "\n", " "):
                if sep in value:
                    return [v.strip() for v in value.split(sep) if v.strip()]
            return [value.strip()]

        parsed = {}
        if link_type == "ref":
            show_ref1 = st.checkbox("ref1", value=True, key="toggle_ref1")
            ref_order = ["ref"] + (["ref1"] if show_ref1 else []) + ["ref2", "ref3", "ref4"]
            inputs = {name: st.text_input(name) for name in ref_order}
            if not show_ref1:
                inputs["ref5"] = st.text_input("ref5")
            parsed = {k: parse_multi(v) for k, v in inputs.items()}
        else:
            keys = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]
            parsed = {key: parse_multi(st.text_input(key)) for key in keys}

        all_results, varying_key = [], ""
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
                    f"<div style='display:flex;align-items:center;gap:10px;'>"
                    f"<span style='color:#28EBA4;font-weight:bold;min-width:60px'>{value}</span>"
                    f"<code style='word-break:break-all'>{full_url}</code></div>",
                    unsafe_allow_html=True
                )
                all_results.append({"Формат": value, "Ссылка": full_url, "Визуал": ""})
        if all_results:
            df = pd.DataFrame(all_results)
            excel_buf, csv_buf = io.BytesIO(), io.StringIO()
            df.to_excel(excel_buf, index=False)
            df.to_csv(csv_buf, index=False)
            st.download_button("Скачать Excel", data=excel_buf.getvalue(), file_name="ссылки.xlsx")
            st.download_button("Скачать CSV", data=csv_buf.getvalue(), file_name="ссылки.csv")

        # === SHORT.IO ===
        st.markdown("<h1 style='color:#28EBA4;'>SHORT.IO — СОКРАЩЕНИЕ</h1>", unsafe_allow_html=True)

        long_url_shortio = st.text_input("Длинная ссылка для Short.io", key="shortio_long_url")
        custom_path = st.text_input("Кастомный слаг (path), опционально", key="shortio_path")
        link_title = st.text_input("Заголовок (title), опционально", key="shortio_title")

        if "shortio_history" not in st.session_state:
            st.session_state.shortio_history = []

        def create_short_link(original_url, path=None, title=None):
            api_key = SHORTIO_API_KEY.strip()
            domain_id = int(str(SHORTIO_DOMAIN_ID).strip())
            if not api_key.startswith("sk_"):
                return {"error": "Нужен Secret API Key (sk_...), сейчас pk_..."}
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": api_key
            }
            payload = {"originalURL": original_url, "domainId": domain_id}
            if path:
                payload["path"] = path.strip()
            if title:
                payload["title"] = title.strip()
            try:
                r = requests.post("https://api.short.io/links", json=payload, headers=headers, timeout=20)
                data = r.json()
                if r.status_code >= 400:
                    return {"error": f"HTTP {r.status_code}", "details": data}
                return data
            except Exception as e:
                return {"error": "Network/Request error", "details": str(e)}

        if st.button("🔗 Сократить через Short.io"):
            if not long_url_shortio:
                st.error("Укажите длинную ссылку.")
            else:
                result = create_short_link(long_url_shortio, custom_path, link_title)
                if "error" in result:
                    st.error(f"Ошибка Short.io: {result.get('error')}")
                    if "details" in result:
                        st.code(result["details"])
                else:
                    short_url = result.get("shortURL") or result.get("secureShortURL")
                    if short_url:
                        st.success(f"Короткая ссылка: {short_url}")
                        st.json(result)
                        st.session_state.shortio_history.append({
                            "Длинная": long_url_shortio.strip(),
                            "Короткая": short_url,
                            "Path": custom_path or result.get("path", ""),
                            "Title": link_title or result.get("title", ""),
                        })
                    else:
                        st.warning("Запрос успешен, но поле shortURL не найдено.")
                        st.json(result)

        if st.session_state.shortio_history:
            st.markdown("#### История Short.io (текущая сессия)")
            hist_df = pd.DataFrame(st.session_state.shortio_history)
            st.dataframe(hist_df, use_container_width=True)

    st.divider()
    if st.button("Выйти"):
        st.session_state.clear()
        st.rerun()

# ЭКРАН ЛОГИНА
if not st.session_state.get("authenticated"):
    st.markdown(
        "<div style='text-align:center;margin:40px 0 20px;'>"
        "<img src='https://dumpster.cdn.sports.ru/5/93/bf20303bae2833f0d522d4418ae64.png' width='96'>"
        "</div>", unsafe_allow_html=True
    )
    st.markdown("<h2 style='text-align:center;color:#28EBA4;'>Internal tools. Entrance</h2>", unsafe_allow_html=True)
    pwd = st.text_input("Введите пароль", type="password")
    if st.button("Войти"):
        if pwd == PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Неверный пароль")
    st.stop()

render_tools()









