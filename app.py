import streamlit as st

st.set_page_config(page_title="PNG → WebP / HTML5 + Ссылка", layout="centered")

st.title("🖼 PNG → WebP / HTML5 + Генератор ссылки")

st.markdown("## 🔗 Генератор ссылок")

# Поле: основная ссылка
base_url = st.text_input("Основная ссылка")

# Выбор типа: ref или utm
link_type = st.radio("Тип параметров", ["ref", "utm"])

# Если ref
if link_type == "ref":
    ref_value = st.selectbox("Выберите ref", ["ref", "ref1", "ref2"])
    if base_url:
        result = f"{base_url}?{ref_value}"
        st.code(result, language="html")

# Если utm
elif link_type == "utm":
    st.markdown("### Обязательные параметры")
    utm_source = st.text_input("utm_source", help="google, yandex, vk")
    utm_medium = st.text_input("utm_medium", help="cpc, email, banner, article")
    utm_campaign = st.text_input("utm_campaign", help="promo, discount, sale")

    st.markdown("### Необязательные параметры")
    utm_content = st.text_input("utm_content", help="link, landing page")
    utm_term = st.text_input("utm_term", help="free, -30%, registration")

    if base_url and utm_source and utm_medium and utm_campaign:
        params = [
            f"utm_source={utm_source}",
            f"utm_medium={utm_medium}",
            f"utm_campaign={utm_campaign}",
        ]
        if utm_content:
            params.append(f"utm_content={utm_content}")
        if utm_term:
            params.append(f"utm_term={utm_term}")
        full_url = f"{base_url}?" + "&".join(params)
        st.code(full_url, language="html")

