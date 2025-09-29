# app.py
import io
import zipfile
import re
from itertools import product, permutations

import pandas as pd
from PIL import Image
import streamlit as st
import requests

# ───────────────────────── НАСТРОЙКИ СТРАНИЦЫ ─────────────────────────
st.set_page_config(page_title="Internal tools", layout="wide")

# Пароль
FALLBACK_PASSWORD = "12345"
PASSWORD = st.secrets.get("password", FALLBACK_PASSWORD)

# ───────────────────────── SHORT.IO ПРЕСЕТЫ ───────────────────────────
SHORTIO_PRESETS = {
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
def shortio_create_link(original_url: str, title: str | None, path: str | None, preset: dict):
    api_key   = preset["api_key"].strip()
    domain_id = preset["domain_id"]
    domain    = preset["domain"].strip()

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

def generate_custom_slugs(words_str: str, need: int) -> list[str]:
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
    col1, col2 = st.columns(2)

    # ─── ЛЕВАЯ КОЛОНКА ──────────────────────────────────────────────────
    with col1:
        # КОНВЕРТОР (PNG -> WebP)
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

        # КОНВЕРТАЦИЯ В HTML (шаблоны — без изменений)
        st.markdown("<h1 style='color:#28EBA4;'>КОНВЕРТАЦИЯ В HTML</h1>", unsafe_allow_html=True)
        templates = {
            "FullScreen (320x480)": """<!DOCTYPE html>...""",
            "Mobile Branding (100%x200px)": """<!DOCTYPE html>...""",
            "1Right (300x600)": """<!DOCTYPE html>...""",
            "Desktop Branding (1920x1080)": """<!DOCTYPE html>...""",
            "Mobile_top (100%x250px)": """<!DOCTYPE html>...""",
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

    # ─── ПРАВАЯ КОЛОНКА ─────────────────────────────────────────────────
    with col2:
        # ======= ГЕНЕРАЦИЯ ССЫЛОК + СОКРАЩЕНИЕ =======
        st.markdown("<h1 style='color:#28EBA4;'>ГЕНЕРАЦИЯ ССЫЛОК</h1>", unsafe_allow_html=True)

        # поля генератора
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
            show_ref1 = st.checkbox("ref1", value=True, key="toggle_ref1")
            ref_order = ["ref"] + (["ref1"] if show_ref1 else []) + ["ref2", "ref3", "ref4"]
            inputs = {name: st.text_input(name) for name in ref_order}
            if not show_ref1:
                inputs["ref5"] = st.text_input("ref5")
            st.caption("можно вводить неограниченное значение параметров, отделяя через пробел")
            parsed = {k: parse_multi(v) for k, v in inputs.items()}
        else:
            st.markdown("utm-параметры")
            keys = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]
            parsed = {key: parse_multi(st.text_input(key)) for key in keys}

        # генерация ссылок (Title + исходная ссылка)
        generated = []  # [{'title': ..., 'url': ...}, ...]
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

        # вывод генерации: ТАБЛИЦА из двух колонок
        if generated:
            df_gen = pd.DataFrame([{"Title": g["title"], "исходная ссылка": g["url"]} for g in generated])
            st.dataframe(df_gen, use_container_width=True)

        st.divider()

        # ======= СОКРАЩАТЕЛЬ (всегда на экране) =======
        st.markdown("<h1 style='color:#28EBA4;'>СОКРАЩЕНИЕ ССЫЛОК: Short</h1>", unsafe_allow_html=True)

        use_custom_slugs = st.checkbox("Кастомные слаги")
        custom_words = ""
        if use_custom_slugs:
            custom_words = st.text_input("2–3 слова (для генерации слагов)")

        # домен Short.io — внизу блока
        domain_label_list = list(SHORTIO_PRESETS.keys())
        default_index = domain_label_list.index(DEFAULT_DOMAIN) if DEFAULT_DOMAIN in domain_label_list else 0
        selected_domain_label = st.selectbox("Домен Short.io", domain_label_list, index=default_index)
        active_preset = SHORTIO_PRESETS[selected_domain_label]

        # состояние для fallback-сценария (поля без заголовка)
        if "manual_shorten_active" not in st.session_state:
            st.session_state.manual_shorten_active = False

        # Кнопка сократить
        shorten_clicked = st.button("🔗 Сократить ссылки")
        # подсказка под кнопкой
        st.caption("сократить ref/utm-ссылки ИЛИ ввести новую")

        # Ветвление по сценариям
        if shorten_clicked:
            if generated:
                # обычный сценарий — сокращаем то, что сгенерировано
                slugs = generate_custom_slugs(custom_words, need=len(generated)) if use_custom_slugs else []
                results = []
                for idx, g in enumerate(generated):
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
                # FALLBACK: показать поля для ручного ввода (без заголовка)
                st.session_state.manual_shorten_active = True

        # Ручной режим (без заголовка)
        if st.session_state.manual_shorten_active and not generated:
            manual_url = st.text_input("Ссылка", key="manual_url")
            manual_count = st.number_input("Количество", min_value=1, max_value=1000, value=1, step=1, key="manual_count")

            # кнопка запуска ручного сокращения
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

        # История — три колонки, Excel, без CSV
        if st.session_state.get("shortio_history"):
            st.markdown("#### История Short.io (текущая сессия)")
            hist_df = pd.DataFrame(st.session_state.shortio_history)[["Title", "исходная ссылка", "сокращенная ссылка"]]
            st.dataframe(hist_df, use_container_width=True)
            excel_buf2 = io.BytesIO()
            hist_df.to_excel(excel_buf2, index=False)
            st.download_button("⬇️ Скачать историю (Excel)", data=excel_buf2.getvalue(), file_name="shortio_history.xlsx")

    # кнопка «Выйти»
    st.divider()
    if st.button("Выйти"):
        st.session_state.clear()
        st.rerun()

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
            st.rerun()
        else:
            st.error("Неверный пароль")
    st.stop()

# Авторизован — рисуем инструменты
render_tools()











