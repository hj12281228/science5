"""
LABMATCH 첫 화면 (검색 + A·B 비교함 + 연세대 학과 둘러보기 + 분야별 국내 연구자)

- 화면은 home_component/ 폴더의 HTML·CSS·JS로 그리고, st.components.v2로 붙입니다.
- 분야 데이터는 build_home_snapshot.py가 미리 만든 home_fields.json을 읽습니다.
  (OpenAlex 사용량 한도 때문에 첫 화면에서 실시간으로 부르지 않습니다.)
"""

import base64
import json
from pathlib import Path

import streamlit as st

HERE = Path(__file__).parent
COMP_DIR = HERE / "home_component"
SNAPSHOT_PATH = HERE / "home_fields.json"
LOGO_DIR = COMP_DIR / "logos"


@st.cache_resource(show_spinner=False)
def _make_component(css, js):
    return st.components.v2.component("labmatch_home", css=css, js=js)


def _home_component():
    # CSS/JS 내용을 캐시 키로 넘겨서, 파일이 바뀌어 배포되면 서버를 재시작하지 않아도 새 화면이 나오게 함
    return _make_component(
        (COMP_DIR / "home.css").read_text(encoding="utf-8"),
        (COMP_DIR / "home.js").read_text(encoding="utf-8"),
    )


@st.cache_data(show_spinner=False)
def load_field_snapshot():
    """home_fields.json이 없거나 깨져 있으면 None (분야 구역에 안내 문구만 표시)"""
    try:
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def load_logos():
    """home_component/logos/학교이름.webp → {"연세대": "data:image/webp;base64,..."} (파일이 없는 학교는 글자 배지로 표시)"""
    out = {}
    for f in sorted(LOGO_DIR.glob("*.webp")):
        out[f.stem] = "data:image/webp;base64," + base64.b64encode(f.read_bytes()).decode()
    return out


def yonsei_list(db_tree, profiles=None):
    """yonsei_profs.json 트리를 화면용 목록으로 펼치기.
    OpenAlex ID가 확인된 분은 oa_id('A1|A2')와 yonsei=True를 붙여서, 비교할 때 동명이인 확인 없이 그 ID의 연세대 논문만 불러옴"""
    out = []
    for col, depts in db_tree.items():
        for dept, profs in depts.items():
            for p in profs:
                item = {"name": p["name"], "eng": p.get("eng", ""), "col": col, "dept": dept,
                        "tags": p.get("tags") or [], "works": p.get("works")}
                if p.get("oa_ids"):
                    item.update(oa_id="|".join(p["oa_ids"]), yonsei=True, inst="Yonsei University")
                out.append(item)
    return out


def render_home(db_tree, slots, search, notice=None, profiles=None):
    """첫 화면을 그리고, 사용자가 방금 한 행동(event)을 돌려줍니다. 없으면 None."""
    from compare_sheets import LIGHT, DARK
    from theme import is_dark
    dark = is_dark()
    pal = lambda c: {"A": c["A"], "B": c["B"], "tA": c["TA"], "tB": c["TB"], "onA": c["ON_A"], "onB": c["ON_B"]}
    comp = _home_component()
    result = comp(
        data={
            "slots": slots,
            "yonsei": yonsei_list(db_tree, profiles),
            "fields": load_field_snapshot(),
            "search": search,
            "notice": notice,
            "logos": load_logos(),
            # 처음 그릴 때의 테마. 화면에서 테마를 바꾸면 컴포넌트가 직접 알아채고 아래 두 색 조합 중에서 고름
            "theme": "dark" if dark else "light",
            "palettes": {"light": pal(LIGHT), "dark": pal({**LIGHT, **DARK})},
        },
        key="labmatch_home",
        on_event_change=lambda: None,
    )
    return getattr(result, "event", None)
