import streamlit as st, sys, platform, pandas as pd
st.set_page_config(page_title="Healthcheck", layout="wide")
st.set_option("client.showErrorDetails", True)

st.write({
    "python": sys.version,
    "platform": platform.platform(),
    "streamlit": st.__version__,
    "pandas": pd.__version__,
})

st.success("Базовая страница отрисована — среда ок. Можно возвращать основной код.")











