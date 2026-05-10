# shared/theme.py

import streamlit as st

def apply_theme():
    """
    Inject global Soft Dark theme styles.
    """

    st.markdown(
        """
        <style>

        /* ============================
           GLOBAL SMALL THEME
        ============================ */

        html, body {
            background-color: #0f0f0f !important;
            color: #e6e6e6 !important;
            font-family: "Inter", sans-serif;
            font-size: 0.85rem !important;
        }

        .block-container {
            padding-top: 0.8rem !important;
            padding-bottom: 1.6rem !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #151515 !important;
            border-right: 1px solid #2d2d2d !important;
        }
        section[data-testid="stSidebar"] * {
            color: #dcdcdc !important;
        }

        /* CARD SYSTEM */
        .card {
            background-color: #1a1a1a !important;
            border: 1px solid #292929 !important;
            border-radius: 10px !important;
            padding: 0.8rem 1rem !important;
            margin-bottom: 1rem !important;
        }

        .lyrics-card { background-color: #1c1a17 !important; border-color: #3b2f1a !important; }
        .song-card   { background-color: #171a1c !important; border-color: #263038 !important; }

        .xs-text { font-size: 0.75rem !important; }

        .card h2, .card h3 {
            margin-top: 0 !important;
            margin-bottom: 0.4rem !important;
        }

        /* Streamlit widget scaling */
        .stButton > button { padding: 0.35rem 0.8rem !important; font-size: 0.8rem !important; }
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            font-size: 0.85rem !important;
            padding: 0.35rem 0.5rem !important;
        }

        /* Scrollbars */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
        ::-webkit-scrollbar-track { background: #1a1a1a; }

        /* SONGS HISTORY COMPACT LIST */
        .song-row {
            background: #1a1a1a;
            border: 1px solid #2b2b2b;
            padding: 0.55rem 0.85rem;
            border-radius: 8px;
            margin-bottom: 0.55rem;
            cursor: pointer;
            transition: background 0.15s ease-out, border-color 0.15s ease-out;
        }
        .song-row:hover { background: #222; border-color: #444; }

        .song-row-title { font-size: 0.90rem !important; font-weight: 600; color: #f2f2f2 !important; }
        .song-row-meta  { font-size: 0.70rem !important; color: #b8b8b8 !important; }

        .song-row-status { font-size: 0.68rem !important; padding: 0.15rem 0.35rem; border-radius: 5px; }

        .song-ok     { background: #0d4020; color: #a1e6b2; }
        .song-pending{ background: #2f2f12; color: #f2e79a; }
        .song-failed { background: #402020; color: #f2a1a1; }

        .song-expanded {
            background: #111;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1.2rem;
        }
        .song-expanded audio,
        .song-expanded video {
            transform: scale(0.95);
            transform-origin: left;
        }

        /* LOGIN PAGE NORMAL SIZE */
        body:not(.authenticated) * { font-size: 1rem !important; }
        body:not(.authenticated) h1,
        body:not(.authenticated) h2,
        body:not(.authenticated) h3 {
            font-size: 1.6rem !important;
        }

        </style>
        """,
        unsafe_allow_html=True
    )
