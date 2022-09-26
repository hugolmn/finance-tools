import streamlit as st

def load_css():
    return st.markdown(
        """
        <style>
        div[data-testid="metric-container"] {
        background-color: rgba(59, 151, 243, 0.05);
        border: 1px solid rgba(59, 151, 243, 0.25);
        padding: 5% 5% 5% 10%;
        border-radius: 5px;
        }
        div[data-testid="metric-container"] > div[style*="color: rgb(9, 171, 59);"] {
           overflow-wrap: break-word;
           white-space: break-spaces;
            color: #3B97F3 !important;
        }
        div[data-testid="metric-container"] > div[style*="color: rgb(255, 43, 43);"] {
           overflow-wrap: break-word;
           white-space: break-spaces;
            color: #F27716 !important;
        }
        div[data-baseweb="tab-list"] > button[data-baseweb="tab"] {
           overflow-wrap: break-word;
           white-space: break-spaces;
            color: white !important;
        }
        div[data-baseweb="tab-list"] > div[data-baseweb="tab-highlight"] {
           overflow-wrap: break-word;
           white-space: break-spaces;
           background-color: #3B97F3 !important;
        }
        # div[class*="stSelectbox"] > div[aria-expanded="trus"] > div {
        #    overflow-wrap: break-word;
        #    white-space: break-spaces;
        #    background-color: #3B97F3 !important;
        # }
        .st-dr{
            border-color: #3B97F3
        }
        </style>
        """,
        unsafe_allow_html=True
    )