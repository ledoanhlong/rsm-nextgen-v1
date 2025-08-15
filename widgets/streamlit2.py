# widgets/Value_Chain_Analysis/streamlit2.py
import streamlit as st
import streamlit.components.v1 as components

DEFAULT_FORM_URL = "https://rsmnl-trial.app.n8n.cloud/form/0afc21e5-8997-481d-aea3-669658fcd72c"

def inject_css():
    """Injects fonts + component styles on every run (no guard)."""
    st.markdown(
        """
        <style>
          /* ====== Fonts ====== */
          @font-face {
            font-family: "Prelo";
            src: url("/static/fonts/Prelo-Regular.woff2") format("woff2"),
                 url("/static/fonts/Prelo-Regular.woff") format("woff");
            font-weight: 400;
            font-style: normal;
            font-display: swap;
          }
          @font-face {
            font-family: "Prelo";
            src: url("/static/fonts/Prelo-Light.woff2") format("woff2"),
                 url("/static/fonts/Prelo-Light.woff") format("woff");
            font-weight: 300;
            font-style: normal;
            font-display: swap;
          }
          html, body, [class^="css"] {
            font-family: "Prelo", system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial;
          }

          .page-wrap { max-width: 1100px; margin: 0 auto; }

          /* ====== Intro (auto light/dark) ====== */
          .intro {
            margin-bottom: 40px;
            padding: 24px;
            border-radius: 16px;
            border: 1px solid rgba(0,0,0,0.08);
            background: #f6f8fa;
            color: #0f172a;
          }
          .intro h2 { font-size: 28px; margin-bottom: 10px; }
          .intro p  { font-size: 16px; line-height: 1.6; margin: 0; }

          @media (prefers-color-scheme: dark) {
            .intro {
              background: rgba(255,255,255,0.06);
              border: 1px solid rgba(255,255,255,0.12);
              color: #ffffff;
            }
            .intro p { color: #dddddd; }
          }

          /* ====== CTA card ====== */
          .cta-card {
            background: linear-gradient(135deg, #0b1020 0%, #131b36 100%);
            color: #fff;
            border-radius: 20px;
            padding: 32px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.25);
            border: 1px solid rgba(255,255,255,0.06);
          }
          .cta-header { display:flex; align-items:center; gap:14px; margin-bottom:8px; font-size: 26px; font-weight: 600; }
          .cta-sub { opacity: 0.9; margin-bottom: 18px; font-weight: 300; }
          .cta-badges { display:flex; gap:10px; flex-wrap:wrap; margin-bottom: 20px; }
          .badge {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            padding: 6px 10px; border-radius: 999px; font-size: 13px;
          }
          .cta-btn {
            display:inline-flex; align-items:center; justify-content:center;
            width: 100%; max-width: 320px; height: 48px;
            border-radius: 12px; font-size: 16px; text-decoration:none;
            background: #009CDE; color: #fff !important; border: 0;
            box-shadow: 0 6px 18px rgba(0,156,222,0.35);
            transition: transform .05s ease, box-shadow .2s ease;
          }
          .cta-btn:hover { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(0,156,222,0.45); }
          .cta-btn:active { transform: translateY(0); }
          .secondary-row {
            display:flex; gap:14px; align-items:center; margin-top: 14px;
            color: rgba(255,255,255,0.8); font-size: 13px;
          }
          .tiny-link a { color: #8ad0ff !important; text-decoration: none; }
          .tiny-link a:hover { text-decoration: underline; }
          .copybox {
            display:flex; gap:8px; align-items:center; margin-left:auto;
            background: rgba(255,255,255,0.06);
            border:1px solid rgba(255,255,255,0.12);
            border-radius: 10px; padding: 6px 8px;
          }
          .copybox input { width: 340px; border:0; background:transparent; color:#fff; outline:none; font-size: 12px; }
          .copybtn {
            background: rgba(255,255,255,0.12); border:0; color:#fff;
            padding: 6px 10px; border-radius: 8px; cursor:pointer; font-size: 12px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render(form_url: str = DEFAULT_FORM_URL, title: str | None = "Value Chain Analysis Agent"):
    inject_css()

    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    if title:
        st.title(title)

    # Intro
    st.markdown(
        """
        <div class="intro">
          <h2>Introduction</h2>
          <p>
            Our Value Chain Analysis Agent helps consultants analyze red flags across Tax, ESG, Trade, and VAT.
            It uses interview transcripts and an AI-generated client profile; outputs include a structured
            business report and a synthesis video.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # CTA card
    st.markdown(
        f"""
        <div class="cta-card">
          <div class="cta-header">📝 Submit your request</div>
          <div class="cta-sub">
            Use our secure form to send details and attachments. Your submission is routed to our n8n workflow instantly.
          </div>
          <div class="cta-badges">
            <div class="badge">Secure</div>
            <div class="badge">Analytical</div>
            <div class="badge">Works on mobile</div>
          </div>

          <a class="cta-btn" href="{form_url}" target="_blank" rel="noopener">Open Form</a>

          <div class="secondary-row">
            <div class="tiny-link">Having trouble? <a href="{form_url}" target="_blank" rel="noopener">Open in a new tab</a></div>
            <div class="copybox">
              <input id="formurl" value="{form_url}" readonly />
              <button class="copybtn" onclick="navigator.clipboard.writeText('{form_url}').then(()=>{{this.textContent='Copied!'; setTimeout(()=>this.textContent='Copy link',1500);}})">Copy link</button>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Popup enhancement
    components.html(
        f"""
        <script>
          const btns = Array.from(parent.document.querySelectorAll('.cta-btn'));
          btns.forEach(btn => {{
            btn.addEventListener('click', function(e) {{
              const w = 980, h = 900;
              const y = window.top.outerHeight/2 + window.top.screenY - ( h/2);
              const x = window.top.outerWidth/2  + window.top.screenX - ( w/2);
              const newWin = window.open("{form_url}", "_blank",
                "toolbar=no,location=no,status=no,menubar=no,scrollbars=yes,resizable=yes" +
                ",width="+w+",height="+h+",top="+y+",left="+x);
              if (newWin) e.preventDefault();
            }});
          }});
        </script>
        """,
        height=0,
    )

    st.markdown("</div>", unsafe_allow_html=True)
