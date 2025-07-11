import streamlit as st

st.set_page_config(page_title="PNG → WebP / HTML5 + Генератор ссылок", layout="centered")

st.title("🖼 PNG → WebP / HTML5 + Генератор ссылки")

st.markdown("## 🔗 Генератор ссылок")

base_url = st.text_input("Основная ссылка")

link_type = st.radio("Тип параметров", ["ref", "utm"])

def parse_multi_input(value):
    raw = value.replace(",", "\n").replace(" ", "\n")
    return [line.strip() for line in raw.split("\n") if line.strip()]

# REF-режим
if link_type == "ref":
    st.markdown("### Параметры для внутренних выносов (можно вводить списки)")

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

        # Находим максимальное количество комбинаций
        max_count = max(len(v) for v in parsed_fields.values() if v)

        st.markdown("### 🔗 Сгенерированные ссылки:")
        for i in range(max_count):
            params = []
            for key, values in parsed_fields.items():
                if values:
                    val = values[i % len(values)]
                    params.append(f"{key}={val}")
            result = f"{base_url}?" + "&".join(params)
            st.code(result, language="html")

# UTM-режим
elif link_type == "utm":
    st.markdown("### Параметры UTM (можно вводить списки)")

    utm_source = st.text_input("utm_source")
    utm_medium = st.text_input("utm_medium")
    utm_campaign = st.text_input("utm_campaign")
    utm_content = st.text_input("utm_content")
    utm_term = st.text_input("utm_term")

    if base_url and utm_source and utm_medium and utm_campaign:
        parsed_fields = {
            "utm_source": parse_multi_input(utm_source),
            "utm_medium": parse_multi_input(utm_medium),
            "utm_campaign": parse_multi_input(utm_campaign),
            "utm_content": parse_multi_input(utm_content),
            "utm_term": parse_multi_input(utm_term),
        }

        max_count = max(len(v) for v in parsed_fields.values() if v)

        st.markdown("### 🔗 Сгенерированные ссылки:")
        for i in range(max_count):
            params = []
            for key, values in parsed_fields.items():
                if values:
                    val = values[i % len(values)]
                    params.append(f"{key}={val}")
            result = f"{base_url}?" + "&".join(params)
            st.code(result, language="html")
