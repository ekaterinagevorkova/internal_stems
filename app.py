# app.py
import io
import zipfile
import re
from itertools import product, permutations

import pandas as pd
from PIL import Image
import streamlit as st
import requests

# НАСТРОЙКИ СТРАНИЦЫ
st.set_page_config(page_title="Internal tools", layout="wide")

# ПАРОЛЬ
FALLBACK_PASSWORD = "12345"
PASSWORD = st.secrets.get("password", FALLBACK_PASSWORD)

# === SHORT.IO СЕКРЕТЫ ===
# Базовые дефолты
SHORTIO_DEFAULT_API_KEY = st.secrets.get("shortio_api_key", "PUT_YOUR_SHORTIO_API_KEY")
SHORTIO_DOMAIN_ID = st.secrets.get("216771", "PUT_YOUR_DOMAIN_ID")

# Маппинг "email -> персональный API key", чтобы отправлять запросы от лица конкретных пользователей
# Пример в .streamlit/secrets.toml:
# [shortio_user_keys]
# "e.gevorkova@sports.ru" = "SECRET_KEY_FOR_ELENA"
# "other@sports.ru" = "SECRET_KEY_FOR_OTHER"
SHORTIO_USER_KEYS = st.secrets.get("shortio_user_keys", {})  # dict

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
        # КОНВЕРТОР PNG→WebP
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

        # КОНВЕРТАЦИЯ В HTML (шаблоны)
        st.markdown("<h1 style='color:#28EBA4;'>КОНВЕРТАЦИЯ В HTML</h1>", unsafe_allow_html=True)
        templates = {
            "FullScreen (320x480)": """<!DOCTYPE html>...""",
            "Mobile Branding (100%x200px)": """<!DOCTYPE html>...""",
            "1Right (300x600)": """<!DOCTYPE html>...""",
            "Desktop Branding (1920x1080)": """<!DOCTYPE html>...""",
            "Mobile_top (100%x250px)": """<!DOCTYPE html>..."""
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
        # ГЕНЕРАЦИЯ ССЫЛОК
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

        all_results, varying_key = [], ""
        if base_url:
            lens = {k: len(v) for k, v in parsed.items() if v}
            max_len = max(lens.values()) if lens else 1
            for k in parsed:
                if len(parsed[k]) == max_len:
                    varying_key = k
                    break

            from itertools import product
            combined = list(product(*[parsed[k] if parsed[k] else [""] for k in parsed]))
            keys_list = list(parsed.keys())
            for combo in combined:
                params = "&".join([f"{k}={v}" for k, v in zip(keys_list, combo) if v])
                full_url = f"{base_url}?{params}" if params else base_url
                value = combo[keys_list.index(varying_key)] if varying_key in keys_list else ""
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:10px;'>"
                    f"<span style='color:#28EBA4;font-weight:bold;min-width:60px'>{value}</span>"
                    f"<code style='word-break:break-all'>{full_url}</code>"
                    f"</div>", unsafe_allow_html=True
                )
                all_results.append({"Формат": value, "Ссылка": full_url, "Визуал": ""})

        if all_results:
            df = pd.DataFrame(all_results)
            excel_buf, csv_buf = io.BytesIO(), io.StringIO()
            df.to_excel(excel_buf, index=False)
            df.to_csv(csv_buf, index=False)
            st.download_button("Скачать Excel", data=excel_buf.getvalue(), file_name="ссылки.xlsx")
            st.download_button("Скачать CSV", data=csv_buf.getvalue(), file_name="ссылки.csv")

        # === SHORT.IO — СОКРАЩЕНИЕ "ОТ ИМЕНИ" ПОЛЬЗОВАТЕЛЯ ===
        st.markdown("<h1 style='color:#28EBA4;'>SHORT.IO — СОКРАЩЕНИЕ</h1>", unsafe_allow_html=True)

        with st.expander("🔐 Настройки доступа", expanded=False):
            st.caption("Запросы в Short.io выполняются от владельца указанного API-ключа.")
            # Кого считаем «автором» запроса
            user_emails = sorted(set(list(SHORTIO_USER_KEYS.keys()) + ["e.gevorkova@sports.ru"]))
            acting_email = st.selectbox("От имени пользователя", user_emails, index=user_emails.index("e.gevorkova@sports.ru") if "e.gevorkova@sports.ru" in user_emails else 0)
            # Ключ, который реально пойдёт в Authorization
            effective_api_key = st.text_input(
                "API Key для выбранного пользователя",
                value=SHORTIO_USER_KEYS.get(acting_email, SHORTIO_DEFAULT_API_KEY),
                type="password",
                help="Если оставить пустым — будет использован общий дефолтный ключ."
            )
            domain_id_input = st.text_input("Short.io Domain ID", value=SHORTIO_DOMAIN_ID)

            st.markdown("—")
            with st.expander("Как выдать права на созданную ссылку конкретному юзеру?"):
                st.caption("Можно сразу добавить разрешение на ссылку для нужного пользователя (нужен userIdString). "
                           "Где взять ID: откройте профиль пользователя/URL в админке и скопируйте идентификатор из адресной строки. "
                           "Гид по ID: Help → *How to retrieve domain, link and folder identifiers…*")
                grant_permission = st.checkbox("После создания выдать права пользователю", value=True)
                target_user_id = st.text_input("userIdString пользователя (опционально)", placeholder="например: abCDefGhijkLMNO77")

        st.caption("Введите длинную ссылку и (опционально) слаг/заголовок.")
        long_url_shortio = st.text_input("Длинная ссылка для Short.io", key="shortio_long_url")
        custom_path = st.text_input("Кастомный слаг (path), опционально", key="shortio_path", placeholder="naprimer-akciya-001")
        link_title = st.text_input("Заголовок (title), опционально", key="shortio_title")

        if "shortio_history" not in st.session_state:
            st.session_state.shortio_history = []

        def create_short_link(original_url, path=None, title=None, api_key=None, domain_id=None):
            if not api_key or not domain_id:
                return {"error": "API Key или Domain ID пусты."}
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": api_key  # ← Запрос выполняется от владельца этого ключа
            }
            payload = {"originalURL": original_url, "domainId": domain_id}
            if path:
                payload["path"] = path.strip()
            if title:
                payload["title"] = title.strip()
            try:
                r = requests.post("https://api.short.io/links", json=payload, headers=headers, timeout=20)
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

        def add_link_permission(domain_id, link_id, user_id, api_key):
            """Выдаёт права пользователю на ссылку (если знаете userIdString)."""
            if not (domain_id and link_id and user_id and api_key):
                return {"error": "Не хватает domainId/linkId/userId/api_key"}
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": api_key
            }
            url = f"https://api.short.io/links/permissions/{domain_id}/{link_id}/{user_id}"
            try:
                r = requests.post(url, headers=headers, timeout=20)
                try:
                    data = r.json()
                except Exception:
                    data = {"raw_text": r.text}
                if r.status_code >= 400:
                    return {"error": f"HTTP {r.status_code}", "details": data}
                return data
            except requests.RequestException as e:
                return {"error": "Network/Request error", "details": str(e)}

        if st.button("🔗 Сократить через Short.io (от выбранного пользователя)"):
            if not long_url_shortio:
                st.error("Укажите длинную ссылку.")
            else:
                # 1) Создаём ссылку ключом пользователя
                result = create_short_link(
                    original_url=long_url_shortio.strip(),
                    path=custom_path.strip() if custom_path else None,
                    title=link_title.strip() if link_title else None,
                    api_key=effective_api_key.strip(),
                    domain_id=domain_id_input.strip()
                )
                if "error" in result:
                    st.error(f"Ошибка Short.io: {result.get('error')}")
                    if "details" in result:
                        st.code(result["details"])
                else:
                    short_url = result.get("shortURL") or result.get("shortUrl") or result.get("secureShortURL")
                    link_id = result.get("idString") or result.get("id")  # idString — актуальное поле
                    if short_url:
                        st.success(f"Короткая ссылка: {short_url}")
                        st.write("Ответ API:")
                        st.json(result)
                        st.session_state.shortio_history.append({
                            "Длинная": long_url_shortio.strip(),
                            "Короткая": short_url,
                            "Path": custom_path or result.get("path", ""),
                            "Title": link_title or result.get("title", ""),
                            "Автор (ключ)": acting_email
                        })

                        # 2) (опционально) добавим права пользователю
                        if grant_permission and target_user_id and link_id:
                            perm_res = add_link_permission(domain_id_input.strip(), link_id, target_user_id.strip(), effective_api_key.strip())
                            if "error" in perm_res:
                                st.warning(f"Не удалось выдать права: {perm_res.get('error')}")
                                if "details" in perm_res:
                                    st.code(perm_res["details"])
                            else:
                                st.info("Права на ссылку выданы указанному пользователю.")
                    else:
                        st.warning("Успех, но поле shortURL не найдено. См. RAW JSON ниже.")
                        st.json(result)

        if st.session_state.shortio_history:
            st.markdown("#### История Short.io (текущая сессия)")
            hist_df = pd.DataFrame(st.session_state.shortio_history)
            st.dataframe(hist_df, use_container_width=True)
            excel_buf2, csv_buf2 = io.BytesIO(), io.StringIO()
            hist_df.to_excel(excel_buf2, index=False)
            hist_df.to_csv(csv_buf2, index=False)
            st.download_button("⬇️ Скачать историю (Excel)", data=excel_buf2.getvalue(), file_name="shortio_history.xlsx")
            st.download_button("⬇️ Скачать историю (CSV)", data=csv_buf2.getvalue(), file_name="shortio_history.csv")

        # ГЕНЕРАТОР СЛАГОВ
        st.markdown("<h1 style='color:#28EBA4;'>СЛАГИ ДЛЯ ССЫЛОК</h1>", unsafe_allow_html=True)
        words_raw = st.text_input("2–3 слова через пробел или запятую", key="slug_words", placeholder="")
        if words_raw:
            words = [w.lower() for w in re.split(r"[\s,]+", words_raw.strip()) if w]
            if 2 <= len(words) <= 3:
                from itertools import permutations as _perms
                seps = ['-', '_', '.']
                combos = {sep.join(p) for p in _perms(words) for sep in seps}
                slugs = sorted(combos, key=lambda s: (len(s), s))
                st.text_area("Варианты слагов", value="\n".join(slugs), height=200)
            else:
                st.caption("Введите от 2 до 3 слов.")

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

render_tools()








