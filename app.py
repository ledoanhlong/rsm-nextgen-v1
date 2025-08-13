# app.py
import os
import json
import yaml
import bcrypt
import requests
import streamlit as st
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

# ---------- UI: Login ----------
def login_ui():
    st.title("🔐 Login")

    users = load_credentials(CONFIG_PATH)
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        if verify_user(users, username, password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            # Initialize chat history if first login this session
            st.session_state.setdefault("messages", [{"role": "assistant", "content": "Hi! How can I help today?"}])
            st.success("Login successful. Redirecting…")
            st.rerun()
        else:
            st.error("Invalid username or password")

# ---------- UI: Chat ----------
def chat_ui():
    st.set_page_config(page_title="Chat", page_icon="💬", layout="wide")
    col_left, col_right = st.columns([1, 5])
    with col_left:
        st.caption(f"Logged in as **{st.session_state.get('username')}**")
    with col_right:
        st.button("Logout", on_click=do_logout, type="secondary")

    st.title("💬 Chat")

    # Ensure messages is present
    st.session_state.setdefault("messages", [])

    # Display history
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    user_input = st.chat_input("Type your message…")
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Build a simple textual context from recent turns
        recent: List[Dict[str, str]] = st.session_state["messages"][-10:]
        context_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    reply = get_llm_response(user_input, context_text)
                except Exception as e:
                    reply = f"Sorry, I hit an error calling the model: `{e}`"

            st.markdown(reply)
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
