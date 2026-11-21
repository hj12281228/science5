"""
LABMATCH 첫 화면 (검색 + A·B 비교함 + 연세대 학과 둘러보기 + 분야별 국내 연구자)

- 화면은 home_component/ 폴더의 HTML·CSS·JS로 그리고, st.components.v2로 붙입니다.
- 분야 데이터는 build_home_snapshot.py가 미리 만든 home_fields.json을 읽습니다.
  (OpenAlex 사용량 한도 때문에 첫 화면에서 실시간으로 부르지 않습니다.)
"""

import json
from pathlib import Path

import streamlit as st

HERE = Path(__file__).parent
COMP_DIR = HERE / "home_component"
SNAPSHOT_PATH = HERE / "home_fields.json"


@st.cache_resource(show_spinner=False)
def _home_component():
    return st.components.v2.component(
        "labmatch_home",
        css=(COMP_DIR / "home.css").read_text(encoding="utf-8"),
        js=(COMP_DIR / "home.js").read_text(encoding="utf-8"),
    )


@st.cache_data(show_spinner=False)
def load_field_snapshot():
    """home_fields.json이 없거나 깨져 있으면 None (분야 구역에 안내 문구만 표시)"""
    try:
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def yonsei_list(db_tree):
    """professors_db.json 트리를 화면용 목록으로 펼치기"""
    return [
        {"name": p["name"], "eng": p.get("eng", ""), "col": col, "dept": dept}
        for col, depts in db_tree.items()
        for dept, profs in depts.items()
        for p in profs
    ]


def render_home(db_tree, slots, search, notice=None):
    """첫 화면을 그리고, 사용자가 방금 한 행동(event)을 돌려줍니다. 없으면 None."""
    comp = _home_component()
    result = comp(
        data={
            "slots": slots,
            "yonsei": yonsei_list(db_tree),
            "fields": load_field_snapshot(),
            "search": search,
            "notice": notice,
        },
        key="labmatch_home",
        on_event_change=lambda: None,
    )
    return getattr(result, "event", None)
