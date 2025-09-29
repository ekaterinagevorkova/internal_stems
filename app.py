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
# Дефолты: берем из secrets, иначе — жестко заданные значения
SHORTIO_API_KEY = st.secrets.get("shortio_api_key", "pk_7MeATLI4vJg1ZyYS")
SHORTIO_DOMAIN_ID = st.secrets.get("shortio_domain_id", "216771")  # строкой, ниже приведем к int

# СТРАНИЦА ИНСТРУМЕНТОВ (без set_page_config)
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
        # КОНВЕРТОР (PNG -> WebP)
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

        # КОНВЕРТАЦИЯ В HTML
        st.markdown("<h1 style='color:#28EBA4;'>КОНВЕРТАЦИЯ В HTML</h1>", unsafe_allow_html=True)

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

    # ─── ПРАВАЯ КОЛОНКА ─────────────────────────────────────────────────────────
    with col2:
        # ГЕНЕРАЦИЯ ССЫЛОК
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

            # чекбокс ref1
            show_ref1 = st.checkbox("ref1", value=True, key="toggle_ref1")

            # Базовый порядок полей:
            ref_order = ["ref"] + (["ref1"] if show_ref1 else []) + ["ref2", "ref3", "ref4"]

            inputs = {}
            for name in ref_order:
                inputs[name] = st.text_input(name)

            # Если ref1 отключён
            if not show_ref1:
                inputs["ref5"] = st.text_input("ref5")

            # подсказка
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

        # === SHORT.IO === БЛОК: создание коротких ссылок + локальная история
        st.markdown("<h1 style='color:#28EBA4;'>SHORT.IO — СОКРАЩЕНИЕ</h1>", unsafe_allow_html=True)

        # Значения по умолчанию уже предзаполнены вашим ключом и доменом
        with st.expander("🔐 Настройки доступа (по умолчанию берутся из st.secrets)", expanded=False):
            api_key_input = st.text_input(
                "Short.io API Key (опционально переопределить)",
                value=SHORTIO_API_KEY,
                type="password"
            )
            domain_id_input = st.text_input(
                "Short.io Domain ID (опционально переопределить)",
                value=str(SHORTIO_DOMAIN_ID)
            )

        st.caption("Введите длинную ссылку и (опционально) собственный слаг/заголовок. Если слаг оставить пустым — Short.io сгенерирует его сам.")

        long_url_shortio = st.text_input("Длинная ссылка для Short.io", key="shortio_long_url")
        custom_path = st.text_input("Кастомный слаг (path), опционально", key="shortio_path", placeholder="naprimer-akciya-001")
        link_title = st.text_input("Заголовок (title), опционально", key="shortio_title")

        # Инициализируем историю в сессии
        if "shortio_history" not in st.session_state:
            st.session_state.shortio_history = []

        def _coerce_domain_id(domain_id_str: str):
            try:
                return int(str(domain_id_str).strip())
            except Exception:
                return str(domain_id_str).strip()

        def create_short_link(original_url, path=None, title=None, api_key=None, domain_id=None):
            api_key = (api_key or "").strip()
            domain_id = _coerce_domain_id(domain_id or "")

            if not api_key or not domain_id:
                return {"error": "API Key или Domain ID пусты. Проверьте настройки."}

            url = "https://api.short.io/links"
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": api_key
            }
            payload = {
                "originalURL": original_url,
                "domainId": domain_id  # int, если получилось преобразовать
            }
            if path:
                payload["path"] = path.strip()
            if title:
                payload["title"] = title.strip()

            try:
                r = requests.post(url, json=payload, headers=headers, timeout=20)
                data = {}
                try:
                    data = r.json()
                except Exception:
                    data = {"raw_text": r.text}

                if r.status_code >= 400:
                    return {"error": f"HTTP {r.status_code}", "details": data}

                return data
            except requests.RequestException as e:
                return {"error": "Network/Request error", "details": str(e)}

        # Кнопка создания
        if st.button("🔗 Сократить через Short.io"):
            if not long_url_shortio:
                st.error("Укажите длинную ссылку.")
            else:
                result = create_short_link(
                    original_url=long_url_shortio.strip(),
                    path=custom_path.strip() if custom_path else None,
                    title=link_title.strip() if link_title else None,
                    api_key=api_key_input,
                    domain_id=domain_id_input
                )
                if "error" in result:
                    st.error(f"Ошибка Short.io: {result.get('error')}")
                    if "details" in result:
                        st.code(result["details"])
                else:
                    short_url = result.get("shortURL") or result.get("shortUrl") or result.get("secureShortURL")
                    if short_url:
                        st.success(f"Короткая ссылка: {short_url}")
                        st.write("Ответ API:")
                        st.json(result)

                        # Добавим в историю
                        st.session_state.shortio_history.append({
                            "Длинная": long_url_shortio.strip(),
                            "Короткая": short_url,
                            "Path": custom_path or result.get("path", ""),
                            "Title": link_title or result.get("title", ""),
                        })
                    else:
                        st.warning("Запрос успешен, но не нашли поле shortURL в ответе. Смотрите RAW JSON.")
                        st.json(result)

        # История
        if st.session_state.shortio_history:
            st.markdown("#### История Short.io (текущая сессия)")
            hist_df = pd.DataFrame(st.session_state.shortio_history)
            st.dataframe(hist_df, use_container_width=True)

            excel_buf = io.BytesIO()
            csv_buf = io.StringIO()
            hist_df.to_excel(excel_buf, index=False)
            hist_df.to_csv(csv_buf, index=False)

            st.download_button("⬇️ Скачать историю (Excel)", data=excel_buf.getvalue(), file_name="shortio_history.xlsx")
            st.download_button("⬇️ Скачать историю (CSV)", data=csv_buf.getvalue(), file_name="shortio_history.csv")

        # ГЕНЕРАТОР СЛАГОВ
        st.markdown("<h1 style='color:#28EBA4;'>СЛАГИ ДЛЯ ССЫЛОК</h1>", unsafe_allow_html=True)
        words_raw = st.text_input("2–3 слова через пробел или запятую", key="slug_words", placeholder="")

        if words_raw:
            # разбираем вход + нижний регистр
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

    # Кнопка «Выйти» (сбросить авторизацию)
    st.divider()
    if st.button("Выйти"):
        st.session_state.clear()
        st.rerun()

# ЭКРАН ЛОГИНА И РОУТИНГ
if not st.session_state.get("authenticated"):
    st.markdown(
        "<div style='text-align:center;margin:40px 0 20px;'>"
        "<img src='https://dumpster.cdn.sports.ru/5/93/bf20303bae2833f0d522d4418ae64.png' width='96'>"
        "</div>",
        unsafe_allow_html=True
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

# Авторизован — рисуем инструменты
render_tools()









