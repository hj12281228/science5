"""
화면 테마(라이트/다크) 알아내기

Streamlit 메뉴에서 Light/Dark를 바꾸면 화면 색은 바로 바뀌지만, 파이썬 코드는 다시 실행되지 않아서
st.context.theme 값이 예전 테마로 남아 있을 수 있습니다. (그래서 다크모드에서 라이트용 색이 섞여 보였음)

theme_watch()는 보이지 않는 작은 컴포넌트를 붙여서, 브라우저의 실제 배경색으로 테마를 확인하고
파이썬이 알고 있는 테마와 다르면 화면을 한 번 다시 그리게 합니다.
"""

import streamlit as st

_JS = """
export default function ({ data, setStateValue, parentElement }) {
  const host = parentElement instanceof Element ? parentElement : parentElement.host;
  const isDark = () => {
    const v = (getComputedStyle(host).getPropertyValue('--st-background-color') || '').trim();
    const m = v.match(/^#?([0-9a-f]{6})$/i);
    if (!m) return null;
    const n = parseInt(m[1], 16), r = n >> 16 & 255, g = n >> 8 & 255, b = n & 255;
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 < 0.5;
  };
  const check = () => {
    const d = isDark();
    if (d !== null && d !== data.dark) setStateValue('dark', d);
  };
  check();
  const id = setInterval(check, 500);
  return () => clearInterval(id);
}
"""


@st.cache_resource(show_spinner=False)
def _watcher():
    return st.components.v2.component("lm_theme_watch", js=_JS)


def _context_dark():
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


def theme_watch():
    """페이지마다 맨 처음에 한 번 부르기. 브라우저 테마가 바뀌면 자동으로 다시 그려짐"""
    st.html('<style>.st-key-lm_theme_watch{display:none!important}</style>')
    current = st.session_state.get("lm_dark")
    if current is None:
        current = _context_dark()
    res = _watcher()(data={"dark": current}, key="lm_theme_watch", default={"dark": None}, on_dark_change=lambda: None)
    seen = getattr(res, "dark", None)
    st.session_state.lm_dark = current if seen is None else bool(seen)
    return st.session_state.lm_dark


def is_dark():
    """지금 화면이 다크모드인지 (theme_watch를 먼저 불렀으면 브라우저 기준, 아니면 st.context 기준)"""
    v = st.session_state.get("lm_dark")
    return _context_dark() if v is None else v
