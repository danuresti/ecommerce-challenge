import streamlit as st


def show_flash():
    if "flash" in st.session_state:
        st.toast(st.session_state.pop("flash"), icon="✅")