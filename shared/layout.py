# shared/layout.py

import streamlit as st
from shared.session import get_current_user, logout
from constants import APP_NAME, ENABLE_DEBUG_TOOLS


# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------
def app_header(title: str = APP_NAME):
    st.markdown(
        f"""
        <div style="padding:0.4rem 0 0.2rem 0;">
            <h1 style="margin:0;font-size:2.1rem;color:#e6e6e6;">{title}</h1>
        </div>
        <hr style="margin-top:0.4rem;margin-bottom:1rem;border-color:#333;">
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Login Requirement
# ---------------------------------------------------------
def require_login():
    if "user" not in st.session_state:
        st.error("You must log in to access this page.")
        st.stop()


# ---------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------
def render_sidebar(current_page: str) -> str:
    user = get_current_user()

    st.sidebar.markdown(
        f"<h2 style='margin-top:0;color:#e6e6e6;'>🎵 {APP_NAME}</h2>",
        unsafe_allow_html=True,
    )

    # FULL list of pages — must include Debug Tools so radio won't crash
    pages = [
        "Dashboard",
        "Lyrics Generate",
        "Lyrics History",
        "Songs Generate",
        "Songs History",
        "Settings",
        "Debug Tools",   # <--- required so Streamlit radio accepts the value
    ]

    # Filter what is actually *visible* in the radio
    visible_pages = pages.copy()
    if not (user and user.get("is_admin") and ENABLE_DEBUG_TOOLS):
        visible_pages.remove("Debug Tools")

    # Initialize nav state
    if "nav_radio" not in st.session_state:
        st.session_state["nav_radio"] = current_page

    # Deferred navigation handler
    if "pending_nav" in st.session_state:
        target = st.session_state["pending_nav"]
        st.session_state["nav_radio"] = target
        st.session_state["current_page"] = target
        del st.session_state["pending_nav"]

    # Radio showing ONLY allowed pages
    choice = st.sidebar.radio(
        "Navigation",
        visible_pages,
        key="nav_radio",
    )

    # Admin Tools section
    if user and user.get("is_admin") and ENABLE_DEBUG_TOOLS:
        st.sidebar.write("---")
        st.sidebar.markdown("🛠 **Admin Tools**")

        if st.sidebar.button("Debug Tools"):
            st.session_state["pending_nav"] = "Debug Tools"
            st.rerun()

    st.sidebar.write("---")

    # User info + logout
    if user:
        st.sidebar.markdown(
            f"**Logged in as:**<br><span style='color:#bbbbbb'>{user['email']}</span>",
            unsafe_allow_html=True,
        )
        if st.sidebar.button("Logout"):
            logout()
            st.rerun()

    return choice
