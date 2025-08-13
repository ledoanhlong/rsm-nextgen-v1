# app.py
import os, json, yaml, bcrypt, requests, streamlit as st
from pathlib import Path
from typing import Dict, Any, List

# ---------- Settings ----------
CONFIG_PATH = Path("credentials.yaml")
LLM_API_KEY = os.getenv("AZURE_API_KEY", "")
LLM_ENDPOINT = os.getenv("AZURE_API_ENDPOINT", "")

# ---------- Auth helpers ----------
def load_credentials(path: Path) -> Dict[str, Dict[str, str]]:
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
        return False

def do_logout():
    # ✅ No st.rerun() here. Just mutate state; the button click will rerun automatically.
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["messages"] = []
    # st.session_state.clear()       # wipe everything
    # st.stop()                      # stop execution right here



# ---------- LLM call ----------
def get_llm_response(prompt: str, context: str) -> str:
    if not LLM_API_KEY or not LLM_ENDPOINT:
        raise RuntimeError("LLM_API_KEY/LLM_ENDPOINT are not set in environment variables.")
    headers = {"Content-Type": "application/json", "api-key": LLM_API_KEY}
    system_message = f"You are a helpful assistant. Here is chat context:\n{context}"
    messages = [{"role": "system", "content": system_message}, {"role": "user", "content": prompt}]
    r = requests.post(LLM_ENDPOINT, headers=headers, json={"messages": messages}, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"LLM error {r.status_code}: {r.text}")
    data = r.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content")
    if not content:
        content = data.get("output") or data.get("reply") or json.dumps(data)
    return content

# ---------- PAGE CONFIG & sidebar visibility ----------
AUTH = st.session_state.get("authenticated", False)
st.set_page_config(
    page_title="Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded" if AUTH else "collapsed",
)
if not AUTH:
    # Hide sidebar and hamburger on login page
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"] { display: none; }
          [data-testid="collapsedControl"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
            st.session_state.setdefault("messages", [{"role": "assistant", "content": "Hi! How can I help today?"}])
            st.success("Login successful.")
            # ❌ No st.rerun() needed; form submit triggers a rerun automatically.
        else:
            st.error("Invalid username or password")

# ---------- UI: Chat ----------
def chat_ui():
    col_left, col_right = st.columns([1, 5])
    with col_left:
        st.caption(f"Logged in as **{st.session_state.get('username')}**")
    with col_right:
        # ✅ Avoid on_click callback; handle logout inline
        if st.button("Logout", type="secondary"):
            do_logout()
            st.success("Logged out.")

    # # Sidebar navigation (visible only after login)
    # st.sidebar.header("Navigation")
    # if hasattr(st.sidebar, "page_link"):
    #     st.sidebar.page_link("app.py", label="Chat", icon="💬")                 # renamed link label
    #     st.sidebar.page_link("pages/VAT_Checker.py", label="VAT Checker", icon="🧾")

    st.title("💬 Chat")

    st.session_state.setdefault("messages", [])
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Type your message…")
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
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
    if not st.session_state.get("authenticated"):
        login_ui()
    else:
        chat_ui()

if __name__ == "__main__":
    main()
