# app.py

import streamlit as st

from backend.db import run_migrations
from backend.services.auth_service import login_user, register_user
from constants import APP_NAME
from shared.layout import render_sidebar, app_header, require_login
from shared.session import get_current_user, set_current_user
from shared.theme import apply_theme


# ---------------------------------------------
# Authentication UI
# ---------------------------------------------
def _show_auth():

    # Apply theme AFTER page_config to avoid duplicate injection
    apply_theme()

    st.markdown("<script>document.body.classList.remove('authenticated');</script>",
                unsafe_allow_html=True)

    # Wrap login UI in full-size container
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)

    st.title(APP_NAME)
    tab_login, tab_register = st.tabs(["🔐 Login", "🆕 Register"])

    # LOGIN TAB
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            user = login_user(email, password)
            if user:
                set_current_user(user)
                st.query_params.clear()
                st.rerun()
            else:
                st.error("Invalid email or password.")

    # REGISTER TAB
    with tab_register:
        with st.form("register_form"):
            email = st.text_input("Email")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            password2 = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account")

        if submitted:
            if password != password2:
                st.error("Passwords do not match.")
            else:
                ok, msg = register_user(email, username, password)
                if ok:
                    st.success("Account created.")
                else:
                    st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------
# Dynamic page loader
# ---------------------------------------------
def _load_page_module(name: str):
    pages = {
        "Dashboard": "dashboard",
        "Lyrics Generate": "lyrics_generate",
        "Lyrics History": "lyrics_history",
        "Songs Generate": "songs_generate",
        "Songs History": "songs_history",
        "Settings": "settings",
        "Debug Tools": "debug_tools",
    }
    module_name = pages.get(name, "dashboard")
    return __import__(f"app_pages.{module_name}", fromlist=["run"])


# ---------------------------------------------
# MAIN ENTRYPOINT
# ---------------------------------------------
def main():

    # IMPORTANT: page_config MUST run before ANY rendering
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="🎵",
        layout="wide",
    )

    # Apply theme ONCE after page_config
    apply_theme()

    run_migrations()

    user = get_current_user()
    if not user:
        _show_auth()
        return

    # Mark body as authenticated
    st.markdown(
        "<script>document.body.classList.add('authenticated');</script>",
        unsafe_allow_html=True
    )

    # Init navigation state
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Dashboard"

    # Sidebar navigation
    chosen_page = render_sidebar(st.session_state["current_page"])

    if chosen_page != st.session_state["current_page"]:
        st.session_state["current_page"] = chosen_page
        st.rerun()

    current_page = st.session_state["current_page"]

    # Update browser tab title
    st.markdown(
        f"<script>document.title = '{APP_NAME} — {current_page}';</script>",
        unsafe_allow_html=True,
    )

    app_header(current_page)

    # Render page
    page_module = _load_page_module(current_page)
    require_login()
    page_module.run()


if __name__ == "__main__":
    main()
