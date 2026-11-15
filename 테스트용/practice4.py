"""
지표 4. 연구실 규모 및 사수 환경 — "질문할 사람이 몇 명이나 있는가?"

[입력] 연구실 1곳 = dict
  {
    "lab_name": "A 연구실",
    "professor_id": "A1",            # OpenAlex 교수 author id
    "works": [ OpenAlex works 리스트 (title, publication_year, authorships 포함) ]
  }

[수식] 최근 N년(기본 5년) 논문 기준
  1) 활동 연구자 수   = 교수와 같은 기관 소속 공저자(교수 제외) 중 중복 없는 인원 수
  2) 논문당 평균 저자 수 = Σ(논문별 저자 수) / 논문 수
  3) 사수 후보 수     = 교수와 2편 이상 함께 쓴 같은 기관 소속 공저자 수
  4) 협업 스타일 라벨  = 평균 저자 수 ≤3 소규모 밀착형 / ≤5 중규모 팀형 / >5 대형 협업형
  5) 팀 크기 분포     = 논문별 저자 수를 1~2명 / 3~5명 / 6명 이상으로 나눈 논문 수

※ OpenAlex에는 석사·박사 직위 정보가 없으므로 '교수와 같은 기관 소속 공저자'를 연구실 구성원으로 간주함.
"""

from collections import Counter

import streamlit as st

MIN_COWORK = 2  # 사수 후보로 볼 최소 공저 논문 수


# ---------- 1. 계산 ----------
def _inst_names(authorship):
    return {i.get("display_name") for i in authorship.get("institutions", []) if i.get("display_name")}


def compute_lab_size(lab, years=5, current_year=2026):
    prof_id = lab["professor_id"]
    works = [w for w in lab.get("works", []) if w.get("publication_year", 0) > current_year - years]

    # 교수 소속 기관 (논문들에 등장한 교수 소속 전체)
    prof_insts = set()
    for w in works:
        for a in w.get("authorships", []):
            if a["author"]["id"] == prof_id:
                prof_insts |= _inst_names(a)

    member_count = Counter()   # 같은 기관 공저자별 등장 논문 수
    names = {}
    team_sizes = []

    for w in works:
        auths = w.get("authorships", [])
        team_sizes.append(len(auths))
        for a in auths:
            aid = a["author"]["id"]
            if aid == prof_id:
                continue
            if _inst_names(a) & prof_insts:
                member_count[aid] += 1
                names[aid] = a["author"].get("display_name", aid)

    n_works = len(works)
    avg_authors = round(sum(team_sizes) / n_works, 1) if n_works else 0.0

    if avg_authors <= 3:
        style = "🤝 소규모 밀착형"
    elif avg_authors <= 5:
        style = "👥 중규모 팀형"
    else:
        style = "🏢 대형 협업형"

    distribution = {
        "1~2명": sum(1 for s in team_sizes if s <= 2),
        "3~5명": sum(1 for s in team_sizes if 3 <= s <= 5),
        "6명 이상": sum(1 for s in team_sizes if s >= 6),
    }

    seniors = [(names[a], c) for a, c in member_count.most_common() if c >= MIN_COWORK]

    return {
        "lab_name": lab.get("lab_name", ""),
        "n_works": n_works,
        "active_members": len(member_count),
        "avg_authors": avg_authors,
        "senior_count": len(seniors),
        "seniors": seniors,
        "style": style,
        "distribution": distribution,
    }


# ---------- 2. 화면: 사람 아이콘 그리드 ----------
def _icon_grid(r):
    """사수 후보는 진한 색, 나머지 구성원은 연한 색 아이콘으로 표시"""
    n_senior = r["senior_count"]
    n_other = r["active_members"] - n_senior
    icons = (
        '<span style="font-size:34px;filter:none">👤</span>' * n_senior
        + '<span style="font-size:34px;opacity:0.3">👤</span>' * n_other
    )
    return f'<div style="display:flex;flex-wrap:wrap;gap:4px;min-height:48px">{icons}</div>'


def _render_one(r):
    st.markdown(f"#### {r['lab_name']}")
    if r["active_members"] == 0:
        st.caption("공저 구성원 정보 없음")
        return
    st.markdown(_icon_grid(r), unsafe_allow_html=True)
    st.markdown(
        f"**{r['active_members']}명** 활동 · 그중 사수 후보 **{r['senior_count']}명** · {r['style']}"
    )


def render_lab_size(lab_a, lab_b, years=5):
    """메인 대시보드에서 호출: render_lab_size(lab_a_dict, lab_b_dict)"""
    st.subheader("④ 연구실 규모 및 사수 환경")
    st.caption(
        f"최근 {years}년 논문 기준 · 교수와 같은 기관 소속 공저자 = 구성원 · "
        f"진한 아이콘 = 교수와 {MIN_COWORK}편 이상 함께 쓴 사수 후보"
    )

    ra, rb = compute_lab_size(lab_a, years), compute_lab_size(lab_b, years)

    left, right = st.columns(2)
    with left:
        _render_one(ra)
    with right:
        _render_one(rb)

    if ra["active_members"] != rb["active_members"]:
        bigger = ra if ra["active_members"] > rb["active_members"] else rb
        st.info(f"💡 {bigger['lab_name']}에 함께 연구하는 사람이 더 많아 질문할 선배를 찾기 쉬울 가능성이 높습니다.")


# ---------- 3. 단독 테스트: streamlit run indicator4_lab_size.py ----------
if __name__ == "__main__":
    import json

    with open("mock_lab_data.json", encoding="utf-8") as f:
        data = json.load(f)
    st.set_page_config(page_title="지표 4 테스트", layout="wide")
    render_lab_size(data["lab_a"], data["lab_b"])
