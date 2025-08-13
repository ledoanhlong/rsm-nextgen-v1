# app.py
import os
import json
import yaml
import bcrypt
import requests
import streamlit as st
import base64
from pathlib import Path
from typing import Dict, Any, List

# ---------- Settings ----------
CONFIG_PATH = Path("credentials.yaml")
LLM_API_KEY = os.getenv("AZURE_API_KEY", "")
LLM_ENDPOINT = os.getenv("AZURE_API_ENDPOINT", "")

# ---------- Auth helpers ----------
def load_credentials(path: Path) -> Dict[str, Dict[str, str]]:
    """
    Expected config.yaml structure:
    credentials:
      users:
        Chung:
          name: "Chung"
          password: "$2b$12$...bcrypt-hash..."
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing credentials file: {path.resolve()}")
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return (cfg.get("credentials", {}) or {}).get("users", {}) or {}

def verify_user(users: Dict[str, Dict[str, str]], username: str, password: str) -> bool:
    user = users.get(username)
    if not user:
        return False
    hashed = (user.get("password") or "").encode("utf-8")
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed)
    except ValueError:
        # If the stored hash isn't a valid bcrypt hash
        return False

def do_logout():
    for k in ["authenticated", "username", "messages"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

# ---------- LLM call ----------
def get_llm_response(prompt: str, context: str) -> str:
    """
    Adjust if your API returns a different schema.
    Assumes an OpenAI-style /messages endpoint response.
    """
    if not LLM_API_KEY or not LLM_ENDPOINT:
        raise RuntimeError("LLM_API_KEY/LLM_ENDPOINT are not set in environment variables.")

    headers = {
        "Content-Type": "application/json",
        "api-key": LLM_API_KEY,
    }

    system_message = f"You are a helpful assistant. Here is chat context:\n{context}"

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]

    r = requests.post(LLM_ENDPOINT, headers=headers, json={"messages": messages}, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"LLM error {r.status_code}: {r.text}")

    data = r.json()
    # Try a few common shapes; fall back to raw text
    content = (
        data.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
    )
    if not content:
        # If your API returns e.g. {"output":"..."} or {"reply":"..."}
        content = data.get("output") or data.get("reply") or json.dumps(data)
    return content

def inject_custom_css():
    st.markdown("""
        <style>
        @font-face {
            font-family: 'Prelo';
            src: url('assets/fonts/Prelo-Light.woff2') format('woff2'),
                 url('assets/fonts/Prelo-Light.woff2') format('woff2');
            font-weight: normal;
            font-style: normal;
        }
        html, body, [class*="css"]  {
            font-family: 'Prelo', sans-serif !important;
        }
        .main {
            background-color: #009CDE;
        }
        .rsm-logo {
            width: 120px !important;
            max-width: 30vw;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        .login-card {
            background: #009CDE;
            padding: 2.5rem 2rem 2rem 2rem;
            border-radius: 12px;
            box-shadow: 0 2px 16px rgba(0,0,0,0.07);
            max-width: 350px;
            margin: 2rem auto 0 auto;
        }
        .stButton>button {
            width: 100%;
            border-radius: 6px;
            font-weight: 600;
        }
        .chat-bubble-user {
            background: #009CDE;
            border-radius: 12px 12px 0 12px;
            padding: 0.8em 1em;
            margin-bottom: 0.5em;
            margin-left: 30%;
        }
        .chat-bubble-assistant {
            background: #3F9C35;
            border-radius: 12px 12px 12px 0;
            padding: 0.8em 1em;
            margin-bottom: 0.5em;
            margin-right: 30%;
        }
        .stChatInput {
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

def show_logo():
    logo_path = ".streamlit/rsm logo.png"
    if Path(logo_path).exists():
        with open(logo_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f'<img src="data:image/png;base64,{encoded}" width="120" style="margin-top:2rem;margin-bottom:1rem;" />',
            unsafe_allow_html=True,
        )
    else:
        st.write("<!-- Logo not found -->")

# ---------- UI: Login ----------
def login_ui():
    inject_custom_css()
    show_logo()
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center; margin-bottom:1.5rem;">🔐 Login</h2>', unsafe_allow_html=True)

    users = load_credentials(CONFIG_PATH)
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        if verify_user(users, username, password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state.setdefault("messages", [{"role": "assistant", "content": "Hi! How can I help today?"}])
            st.success("Login successful. Redirecting…")
            st.rerun()
        else:
            st.error("Invalid username or password")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- UI: Chat ----------
def chat_ui():
    inject_custom_css()
    st.set_page_config(page_title="Chat", page_icon="💬", layout="wide")
    show_logo()
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <span style="color:#888;">Logged in as <b>{st.session_state.get('username')}</b></span>
            <form action="#" method="post" style="margin:0;">
                <button type="submit" name="logout" style="background:#fff; color:#005596; border:1px solid #005596; border-radius:6px; padding:0.3em 1em; font-weight:600; cursor:pointer;" onclick="window.location.reload();">Logout</button>
            </form>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<h2 style="margin-bottom:1.5rem;">💬 Chat</h2>', unsafe_allow_html=True)

    st.session_state.setdefault("messages", [])

    # Display history with styled bubbles
    for msg in st.session_state["messages"]:
        bubble_class = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-assistant"
        st.markdown(
            f'<div class="{bubble_class}">{msg["content"]}</div>',
            unsafe_allow_html=True,
        )

    user_input = st.chat_input("Type your message…")
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.markdown(
            f'<div class="chat-bubble-user">{user_input}</div>',
            unsafe_allow_html=True,
        )

        recent: List[Dict[str, str]] = st.session_state["messages"][-10:]
        context_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)

        with st.spinner("Thinking…"):
            try:
                reply = get_llm_response(user_input, context_text)
            except Exception as e:
                reply = f"Sorry, I hit an error calling the model: `{e}`"

        st.markdown(
            f'<div class="chat-bubble-assistant">{reply}</div>',
            unsafe_allow_html=True,
        )
        st.session_state["messages"].append({"role": "assistant", "content": reply})

# ---------- App entry ----------
def main():
    # If not logged in, show login; otherwise show chat
    if not st.session_state.get("authenticated"):
        login_ui()
    else:
        chat_ui()

if __name__ == "__main__":
    main()
