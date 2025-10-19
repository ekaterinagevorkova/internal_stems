# app.py
import io, zipfile, re
from itertools import product, permutations
from urllib.parse import urlparse
from typing import Optional, List, Dict

import streamlit as st
import pandas as pd
from PIL import Image
import requests

# ───────────────────────── НАСТРОЙКИ СТРАНИЦЫ ─────────────────────────
# ВАЖНО: только один вызов set_page_config за всё приложение
st.set_page_config(page_title="Internal tools", layout="wide")

# Защита от повторного редиректа
if "redirected_once" not in st.session_state:
    st.session_state.redirected_once = False

# Временно выключаем редирект
should_redirect = False

if should_redirect and not st.session_state.redirected_once:
    st.session_state.redirected_once = True
    # st.switch_page есть не во всех версиях — защищаемся
    try:
        st.switch_page("pages/login.py")
    except Exception:
        st.experimental_rerun()

# Обновление query_params (без бесконечных перерисовок)
new_qp = {"tab": "stats"}
try:
    # API менялся: в новых версиях есть to_dict()/from_dict(), в старых — нет
    if st.query_params.to_dict() != new_qp:
        st.query_params.from_dict(new_qp)
except Exception:
    pass  # на старых версиях просто не трогаем

# Пароль
FALLBACK_PASSWORD = "SportsTeam"
PASSWORD = st.secrets.get("password", FALLBACK_PASSWORD)

# ───────────────────────── SHORT.IO ПРЕСЕТЫ ───────────────────────────
SHORTIO_PRESETS: Dict[str, Dict[str, object]] = {
    "sirena.world": {
        "api_key":   "sk_ROGCu7fwKkYVRz5V",
        "domain":    "sirena.world",
        "domain_id": 628828,
    },
    "sprts.cc": {
        "api_key":   "sk_ROGCu7fwKkYVRz5V",
        "domain":    "sprts.cc",
        "domain_id": 216771,
    },
}
DEFAULT_DOMAIN = "sprts.cc"

# ───────────────────────── ВСПОМОГАТЕЛЬНОЕ ────────────────────────────
def shortio_create_link(
    original_url: str,
    title: Optional[str],
    path: Optional[str],
    preset: Dict[str, object],
):
    api_key   = str(preset["api_key"]).strip()
    domain_id = int(preset["domain_id"])
    domain    = str(preset["domain"]).strip()

    if not api_key.startswith("sk_"):
        return {"error": "Нужен Secret API Key (sk_...)."}

    if not (original_url.startswith("http://") or original_url.startswith("https://")):
        return {"error": "originalURL должен начинаться с http:// или https://."}

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": api_key,
    }
    payload = {
        "originalURL": original_url,
        "domainId": domain_id,
        "domain": domain,
    }
    if title:
        payload["title"] = title.strip()
    if path:
        payload["path"] = path.strip()

    try:
        r = requests.post("https://api.short.io/links", json=payload, headers=headers, timeout=20)
        try:
            data = r.json()
        except Exception:
            data = {"raw_text": r.text}
        if r.status_code >= 400:
            return {"error": f"HTTP {r.status_code}", "details": data}
        return data
    except requests.RequestException as e:
        return {"error": "Network/Request error", "details": str(e)}

def generate_custom_slugs(words_str: str, need: int) -> List[str]:
    """Из 2–3 слов собрать уникальные слаги с разделителями . - _; выдаём до need штук."""
    words = [w.lower() for w in re.split(r"[\s,]+", words_str.strip()) if w]
    if not (2 <= len(words) <= 3):
        return []
    seps = ['.', '-', '_']
    combos = []
    for p in permutations(words):
        for sep in seps:
            combos.append(sep.join(p))
    combos = sorted(set(combos), key=lambda s: (len(s), s))
    return combos[:need]

# ───────────────────────── UI ─────────────────────────────────────────
def render_tools():
    st.markdown(
        "<div style='text-align: center; margin-bottom: 20px;'>"
        "<img src='https://dumpster.cdn.sports.ru/5/93/bf20303bae2833f0d522d4418ae64.png' width='80'>"
        "</div>",
        unsafe_allow_html=True
    )

    # ───────────────────────── ВЕРХНЯЯ ЛИНИЯ ───────────────────────────
    top_left, top_right = st.columns(2)

    with top_left:
        # КОНВЕРТОР (PNG -> WebP)
        st.markdown("<h1 style='color:#28EBA4;'>КОНВЕРТАЦИЯ (PNG → WebP)</h1>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Загрузите PNG-файлы", type=["png"], accept_multiple_files=True, key="png_uploader")
        archive_name = st.text_input("опционально: название файла", placeholder="converted_images", key="zip_name")

        if uploaded_files:
            converted_files, converted_filenames = [], []
            for file in uploaded_files:
                image = Image.open(file).convert("RGBA")
                filename = file.name.rsplit(".", 1)[0]
                buffer = io.BytesIO()
                # Если в окружении Pillow без WEBP — тут бы упало.
                # Streamlit Cloud обычно собирает с WEBP, но на всякий — try/except.
                try:
                    image.save(buffer, format="WEBP", lossless=True)
                except Exception as e:
                    st.error(f"Не удалось сохранить в WEBP: {e}")
                    return
                converted_files.append(buffer.getvalue())
                converted_filenames.append(filename + ".webp")

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for name, data in zip(converted_filenames, converted_files):
                    zip_file.writestr(name, data)

            final_name = (archive_name.strip() or "converted_images").replace(" ", "_") + ".zip"
            st.download_button("📦 СКАЧАТЬ АРХИВ", data=zip_buffer.getvalue(), file_name=final_name, mime="application/zip")

    with top_right:
        # КОНВЕРТАЦИЯ В HTML
        st.markdown("<h1 style='color:#28EBA4;'>КОНВЕРТАЦИЯ В HTML</h1>", unsafe_allow_html=True)
        templates = {
            "FullScreen (320x480)": """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="ad.size" content="width=320px,height=480px">
  <meta name="viewport" content="width=320, initial-scale=1.0">
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
  <!-- Обратите внимание: в исходной ссылке есть кириллические символы.
       Если файл не существует, баннер просто загрузится без стилей. -->
  <link rel="stylesheet" href="https://dumpster.cdn.sports.ru/9/58/782b7c244f327056е145д297c6ф4б.css">
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

    st.divider()

    # ───────────────────────── НИЖНЯЯ ЛИНИЯ ────────────────────────────
    bottom_left, bottom_right = st.columns(2)

    # ======= ЛЕВО: ГЕНЕРАЦИЯ ССЫЛОК =======
    with bottom_left:
        st.markdown("<h1 style='color:#28EBA4;'>ГЕНЕРАЦИЯ ССЫЛОК</h1>", unsafe_allow_html=True)

        base_url = st.text_input("Основная ссылка", key="gen_base_url")
        link_type = st.radio("Тип параметров", ["ref", "utm"], horizontal=True, key="gen_type")

        def parse_multi(value: Optional[str]) -> List[str]:
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
            show_ref1 = st.checkbox("ref1", value=True, key="toggle_ref1")
            ref_order = ["ref"] + (["ref1"] if show_ref1 else []) + ["ref2", "ref3", "ref4"]
            inputs = {name: st.text_input(name, key=f"ref_{name}") for name in ref_order}
            if not show_ref1:
                inputs["ref5"] = st.text_input("ref5", key="ref_ref5")
            st.caption("можно вводить неограниченное значение параметров, отделяя через пробел")
            parsed = {k: parse_multi(v) for k, v in inputs.items()}
        else:
            st.markdown("utm-параметры")
            keys = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]
            parsed = {key: parse_multi(st.text_input(key, key=f"utm_{key}")) for key in keys}

        generated = []
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
                title_val = combo[keys_list.index(varying_key)] if varying_key in keys_list else ""
                generated.append({"title": str(title_val), "url": full_url})

        # сохраняем генерацию в сессию для блока сокращателя
        if generated:
            st.session_state.generated_links = generated
        elif "generated_links" not in st.session_state:
            st.session_state.generated_links = []

        # отображаем таблицу генерации
        if st.session_state.generated_links:
            df_gen = pd.DataFrame(
                [{"Title": g["title"], "исходная ссылка": g["url"]} for g in st.session_state.generated_links]
            )
            st.dataframe(df_gen, use_container_width=True)

        # выгрузка Excel (фолбэк на CSV при отсутствии движка Excel)
        if st.session_state.generated_links:
            try:
                excel_buf = io.BytesIO()
                pd.DataFrame(
                    [{"Title": g["title"], "исходная ссылка": g["url"]} for g in st.session_state.generated_links]
                ).to_excel(excel_buf, index=False)
                st.download_button("Скачать Excel сгенерированных ссылок", data=excel_buf.getvalue(), file_name="ссылки.xlsx")
            except Exception as e:
                csv_buf = io.StringIO()
                pd.DataFrame(
                    [{"Title": g["title"], "исходная ссылка": g["url"]} for g in st.session_state.generated_links]
                ).to_csv(csv_buf, index=False, encoding="utf-8")
                st.warning("Не удалось собрать Excel (нужен openpyxl или xlsxwriter). Отдаю CSV.")
                st.download_button("Скачать CSV сгенерированных ссылок", data=csv_buf.getvalue(), file_name="ссылки.csv")

    # ======= ПРАВО: СОКРАЩЕНИЕ ССЫЛОК: Short =======
    with bottom_right:
        st.markdown("<h1 style='color:#28EBA4;'>СОКРАЩЕНИЕ ССЫЛОК: Short</h1>", unsafe_allow_html=True)

        use_custom_slugs = st.checkbox("Кастомные слаги")
        custom_words = ""
        if use_custom_slugs:
            custom_words = st.text_input("2–3 слова (для генерации слагов)")

        # домен внизу блока
        domain_label_list = list(SHORTIO_PRESETS.keys())
        default_index = domain_label_list.index(DEFAULT_DOMAIN) if DEFAULT_DOMAIN in domain_label_list else 0
        selected_domain_label = st.selectbox("Домен Short.io", domain_label_list, index=default_index, key="short_domain")
        active_preset = SHORTIO_PRESETS[selected_domain_label]

        if "manual_shorten_active" not in st.session_state:
            st.session_state.manual_shorten_active = False

        shorten_clicked = st.button("🔗 Сократить ссылки")
        st.caption("сократить ref/utm-ссылки ИЛИ ввести новую")

        if shorten_clicked:
            generated_links = st.session_state.get("generated_links", [])
            if generated_links:
                slugs = generate_custom_slugs(custom_words, need=len(generated_links)) if use_custom_slugs else []
                results = []
                for idx, g in enumerate(generated_links):
                    path = slugs[idx] if idx < len(slugs) else None
                    title = g["title"] or ""
                    res = shortio_create_link(original_url=g["url"], title=title, path=path, preset=active_preset)
                    if "error" in res:
                        st.error(f"Ошибка Short.io при «{g['url']}»: {res.get('error')}")
                        continue
                    short_url = res.get("shortURL") or res.get("shortUrl") or res.get("secureShortURL")
                    if not short_url:
                        st.warning(f"Ссылка сокращена, но поле shortURL не вернулось для «{g['url']}».")
                        continue
                    results.append({"Title": title, "исходная ссылка": g["url"], "сокращенная ссылка": short_url})
                if results:
                    if "shortio_history" not in st.session_state:
                        st.session_state.shortio_history = []
                    st.session_state.shortio_history.extend(results)
            else:
                st.session_state.manual_shorten_active = True

        # ручной режим (когда генерации нет)
        if st.session_state.manual_shorten_active and not st.session_state.get("generated_links"):
            manual_url = st.text_input("Ссылка", key="manual_url")
            manual_count = st.number_input("Количество", min_value=1, max_value=1000, value=1, step=1, key="manual_count")

            if st.button("Создать сокращённые ссылки"):
                if not manual_url:
                    st.error("Укажите ссылку.")
                else:
                    virtual = [{"title": "", "url": manual_url.strip()} for _ in range(int(manual_count))]
                    slugs = generate_custom_slugs(custom_words, need=len(virtual)) if use_custom_slugs else []
                    results = []
                    for idx, g in enumerate(virtual):
                        slug = slugs[idx] if idx < len(slugs) else None
                        title = slug or ""
                        res = shortio_create_link(original_url=g["url"], title=title, path=slug, preset=active_preset)
                        if "error" in res:
                            st.error(f"Ошибка Short.io при «{g['url']}»: {res.get('error')}")
                            continue
                        short_url = res.get("shortURL") or res.get("shortUrl") or res.get("secureShortURL")
                        if not short_url:
                            st.warning(f"Ссылка сокращена, но поле shortURL не вернулось для «{g['url']}».")
                            continue
                        results.append({"Title": title, "исходная ссылка": g["url"], "сокращенная ссылка": short_url})
                    if results:
                        if "shortio_history" not in st.session_state:
                            st.session_state.shortio_history = []
                        st.session_state.shortio_history.extend(results)
                        st.session_state.manual_shorten_active = False

        # История — три колонки, Excel с фолбэком
        if st.session_state.get("shortio_history"):
            st.markdown("#### История Short.io (текущая сессия)")
            hist_df = pd.DataFrame(st.session_state.shortio_history)[["Title", "исходная ссылка", "сокращенная ссылка"]]
            st.dataframe(hist_df, use_container_width=True)
            try:
                excel_buf2 = io.BytesIO()
                hist_df.to_excel(excel_buf2, index=False)
                st.download_button("⬇️ Скачать историю (Excel)", data=excel_buf2.getvalue(), file_name="shortio_history.xlsx")
            except Exception:
                csv_buf2 = io.StringIO()
                hist_df.to_csv(csv_buf2, index=False, encoding="utf-8")
                st.warning("Не удалось собрать Excel (нужен openpyxl или xlsxwriter). Отдаю CSV.")
                st.download_button("⬇️ Скачать историю (CSV)", data=csv_buf2.getvalue(), file_name="shortio_history.csv")

    # кнопка «Выйти»
    st.divider()
    if st.button("Выйти"):
        st.session_state.clear()
        st.experimental_rerun()

# ───────────────────────── ЭКРАН ЛОГИНА / РОУТИНГ ─────────────────────
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
            st.experimental_rerun()
        else:
            st.error("Неверный пароль")
    st.stop()

# Авторизован — рисуем инструменты
render_tools()
