"""
지표 2. 산학/외부 협업 비율  (담당: 김유하)

학생 질문: "이 랩은 기업 과제 중심인가, 학술 연구 중심인가? 밖과 얼마나 협업하나?"

[분석 기준] 2021~2025년 (완전 연도 5년, ①⑤ 지표와 통일). 이 기간 밖 논문은 제외.

[계산식]  (OpenAlex works 원자료 기준)
- 기업 공저 비율 = (교수 외 공저자 중 type == "company" 기관이 있는 논문 수 ÷ 전체 논문 수) x 100
- 외부 공저 비율 = (교수 외 공저자 중 '교수 소속 기관이 아닌' 기관이 있는 논문 수 ÷ 전체 논문 수) x 100
    · 교수 소속 기관 = 교수 본인 authorship에 찍힌 기관 + 그 상위 기관(lineage)
    · 같은 대학(연세대) 소속 공저자는 외부로 세지 않음  ← 11/18 한계점 보완
    · 소속 정보가 없는 공저자는 판단에서 제외
- 실질 주도 산학 비율 = (기업 공저 논문 중 1저자 또는 마지막(교신) 저자가 교수 본인/교수 소속 기관인 논문 수
                        ÷ 기업 공저 논문 수) x 100   ← 11/18 개선 방안(가중치) 반영
- 논문 구성 3분할 = 기업 협업 / 기타 외부 기관 / 내부 연구
- 연도별 기업 공저 비율, 파트너 기업(기업별 공저 논문 수)
- diff_score = 두 랩의 격차 점수(0~1) = max(|기업 공저 %p 차|, |외부 공저 %p 차|) ÷ 100  → main.py Brief 자동 조립용

[입력 데이터]
lab = {"lab_name": "DIML", "professor": "손광훈", "professor_id": "https://openalex.org/A...",
       "works": [OpenAlex work 객체, ...]}      ← main.py의 fetch_openalex_lab_data_by_id() 결과 그대로
  (professor_id 대신 author_id도 가능, 둘 다 없으면 가장 많이 등장한 저자를 교수로 추정)
* works가 없고 예전 목업처럼 collaboration 집계값만 있으면 그 값으로 계산(호환용).

[한계] 공동 '과제'가 아니라 공동 '논문' 기준. 소속 정보가 빠진 논문은 협업 없음으로 세어질 수 있음.

[사용법]
- 혼자 테스트:   streamlit run industry_collab.py
- 조장 조립용:   from practice2 import render_industry_collab   (레포에서는 practice2.py 이름으로 저장)
                 result = render_industry_collab(lab_a, lab_b)
                 result["summary"], result["diff_score"]  → 3줄 Brief용
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

# 혼자 테스트할 때만 쓰는 목업 경로: 같은 폴더 → 한 칸 위 폴더 순서로 찾음 (main.py 연결과는 무관)
_HERE = Path(__file__).parent
MOCK_PATH = next((p for p in [_HERE / "mock_lab_data.json", _HERE / "mock-up data.json",
                              _HERE.parent / "mock-up data.json"] if p.exists()),
                 _HERE / "mock_lab_data.json")


# ---------- 1. 계산 ----------

def _pct(n, d):
    return round(n / d * 100, 1) if d else 0.0


YEARS = list(range(2021, 2026))  # 2021~2025


def _short_id(x):
    """'https://openalex.org/A123' -> 'A123'"""
    return (x or "").rstrip("/").split("/")[-1]


def _is_professor(authorship, author_id):
    return bool(author_id) and _short_id((authorship.get("author") or {}).get("id")) == _short_id(author_id)


def _inst_ids(inst):
    """기관 ID + 상위 기관(lineage) ID 집합"""
    ids = {_short_id(inst.get("id"))}
    ids.update(_short_id(x) for x in (inst.get("lineage") or []))
    ids = {i for i in ids if i}
    if not ids and inst.get("display_name"):  # ID 없는 목업 데이터용: 기관 이름으로 비교
        ids = {"name:" + inst["display_name"].strip().lower()}
    return ids


def _home_ids(works, author_id):
    """교수 본인 authorship에 나온 기관들 = 교수 소속 기관"""
    home = set()
    for w in works:
        for a in w.get("authorships", []):
            if _is_professor(a, author_id):
                for inst in a.get("institutions") or []:
                    home |= _inst_ids(inst)
    return home


def _guess_professor(works):
    """author_id가 안 넘어오면 가장 많은 논문에 등장한 저자를 교수로 추정"""
    cnt = {}
    for w in works:
        for a in w.get("authorships", []):
            aid = _short_id((a.get("author") or {}).get("id"))
            if aid:
                cnt[aid] = cnt.get(aid, 0) + 1
    return max(cnt, key=cnt.get) if cnt else ""


def _compute_from_works(lab):
    works = [w for w in lab.get("works", []) if w.get("publication_year") in YEARS]
    author_id = lab.get("author_id") or lab.get("professor_id") or _guess_professor(works)
    home = _home_ids(works, author_id)

    total = industry = external = led = 0
    partners = {}
    yearly = {y: [0, 0] for y in YEARS}  # [기업 공저 논문, 전체]

    for w in works:
        total += 1
        auths = w.get("authorships", [])
        others = [a for a in auths if not _is_professor(a, author_id)]
        other_insts = [i for a in others for i in (a.get("institutions") or [])]

        companies = {i.get("display_name") for i in other_insts if i.get("type") == "company"}
        companies.discard(None)
        is_industry = bool(companies)
        is_external = any(not (_inst_ids(i) & home) for i in other_insts) if home else bool(other_insts)

        industry += is_industry
        external += is_external
        yearly[w["publication_year"]][1] += 1
        if is_industry:
            yearly[w["publication_year"]][0] += 1
            for c in companies:
                partners[c] = partners.get(c, 0) + 1
            # 1저자 또는 마지막 저자가 교수 본인이거나 교수 소속 기관 → 우리 랩 주도
            leads = [a for a in auths if a.get("author_position") in ("first", "last")]
            if any(_is_professor(a, author_id) or
                   any(_inst_ids(i) & home for i in (a.get("institutions") or []))
                   for a in leads):
                led += 1

    return total, industry, external, led, partners, {y: _pct(v[0], v[1]) for y, v in yearly.items() if v[1]}


def compute_industry_collab(lab):
    """연구실 1곳의 산학/외부 협업 지표 계산"""
    if lab.get("works"):
        total, industry, external, led, partners, yearly = _compute_from_works(lab)
        partners = [{"name": n, "count": c} for n, c in partners.items()]
    else:  # 예전 목업(집계값) 호환
        collab = lab.get("collaboration", {}) or {}
        total = lab.get("total_papers", 0) or 0
        industry = collab.get("industry_papers", 0) or 0
        external = collab.get("external_papers", 0) or 0
        led = collab.get("industry_led_papers")
        partners = [p for p in (collab.get("industry_partners") or []) if p.get("name")]
        yearly = {y["year"]: _pct(y.get("industry", 0), y.get("total", 0))
                  for y in (collab.get("industry_yearly") or []) if "year" in y}

    return {
        "lab_name": lab.get("lab_name", ""),
        "professor": lab.get("professor", ""),
        "total": total,
        "industry": industry,
        "external": external,
        "industry_ratio": _pct(industry, total),
        "external_ratio": _pct(external, total),
        "led": led,
        "led_ratio": _pct(led, industry) if led is not None else None,
        "split": {
            "기업 협업": _pct(industry, total),
            "기타 외부 기관": _pct(max(external - industry, 0), total),
            "내부 연구": _pct(max(total - external, 0), total),
        },
        "partners": partners,
        "yearly": yearly,
    }


# ---------- 2. 화면 ----------

def _iga(name):
    """이름 뒤 조사 '이/가' 자동 선택 (한글은 받침, 영문은 끝 글자로 판단)"""
    if not name:
        return "이"
    ch = name.strip()[-1]
    if "가" <= ch <= "힣":
        return "이" if (ord(ch) - 0xAC00) % 28 else "가"
    return "가" if ch.lower() in "aeiouy" else "이"


PENDING = ("<span style='display:inline-block;padding:3px 10px;border-radius:999px;"
           "background:#f3f4f6;color:#6b7280;font-size:13px'>정보 없음 · 수집 예정</span>")


def _pills(partners):
    """파트너 기업 이름을 알약 모양 태그로 (논문 수 많은 순 5개)"""
    if not partners:
        return PENDING
    style = ("display:inline-block;padding:3px 10px;margin:2px;border-radius:999px;"
             "background:#eef2ff;color:#3730a3;font-size:13px")
    top = sorted(partners, key=lambda p: -p.get("count", 0))[:5]
    return "".join(f"<span style='{style}'>{p['name']} · {p.get('count', 0)}편</span>" for p in top)


def _trend_chart(ra, rb):
    """연도별 기업 공저 비율 꺾은선"""
    st.markdown("**연도별 기업 공저 비율 추이 (%)**")
    if not ra["yearly"] and not rb["yearly"]:
        st.markdown(PENDING, unsafe_allow_html=True)
        return
    trend = pd.DataFrame({ra["lab_name"]: pd.Series(ra["yearly"]),
                          rb["lab_name"]: pd.Series(rb["yearly"])}).sort_index()
    trend.index = trend.index.astype(str)
    st.line_chart(trend)


def _bubble_chart(ra, rb):
    """파트너 기업 버블: 크기 = 공저 논문 수, 두 랩 공통 기업은 가운데"""
    st.markdown("**파트너 기업 버블 (크기 = 공저 논문 수)**")
    a = {p["name"]: p.get("count", 0) for p in ra["partners"]}
    b = {p["name"]: p.get("count", 0) for p in rb["partners"]}
    if not a and not b:
        st.markdown(PENDING, unsafe_allow_html=True)
        return

    import altair as alt  # streamlit 설치 시 함께 설치됨

    rows = []
    groups = [(ra["lab_name"], -1, [n for n in a if n not in b]),
              ("공통 파트너", 0, [n for n in a if n in b]),
              (rb["lab_name"], 1, [n for n in b if n not in a])]
    for group, pos, names in groups:
        for i, n in enumerate(sorted(names, key=lambda n: -(a.get(n, 0) + b.get(n, 0)))):
            rows.append({"name": n, "group": group, "pos": pos, "row": -i,
                         "count": a.get(n, 0) + b.get(n, 0)})
    df = pd.DataFrame(rows)

    base = alt.Chart(df).encode(
        x=alt.X("pos:Q", scale=alt.Scale(domain=[-1.7, 1.7]), axis=None),
        y=alt.Y("row:Q", scale=alt.Scale(domain=[-max(len(g[2]) for g in groups), 1]), axis=None),
    )
    bubbles = base.mark_circle(opacity=0.6).encode(
        size=alt.Size("count:Q", scale=alt.Scale(range=[400, 4000]), legend=None),
        color=alt.Color("group:N", title="",
                        scale=alt.Scale(domain=[g[0] for g in groups],
                                        range=["#4f46e5", "#10b981", "#f97316"])),
        tooltip=["name", "group", "count"],
    )
    labels = base.mark_text(fontSize=12).encode(text="name:N")
    st.altair_chart((bubbles + labels).properties(height=80 + 70 * max(len(g[2]) for g in groups)))


def _lab_column(r):
    st.markdown(f"#### {r['lab_name']}")
    prof = f"{r['professor']} 교수 · " if r["professor"] else ""
    st.caption(f"{prof}2021~2025년 논문 {r['total']}편 기준")
    st.write(f"기업 공저 **{r['industry_ratio']}%** ({r['industry']}편)")
    st.progress(min(r["industry_ratio"] / 100, 1.0))
    if r["led_ratio"] is not None and r["industry"]:
        st.caption(f"└ 그중 우리 랩 주도(1저자·교신) {r['led']}편 ({r['led_ratio']}%)")
    st.write(f"외부 기관 협업 **{r['external_ratio']}%** ({r['external']}편)")
    st.progress(min(r["external_ratio"] / 100, 1.0))
    st.markdown("**주요 파트너 기업**")
    st.markdown(_pills(r["partners"]), unsafe_allow_html=True)


def _preference_sentence(ra, rb, level):
    """이용자 선호(중요도)에 따라 한 줄 해석"""
    if level == "상관없음":
        return "산학 협업은 크게 상관없다고 하셨으니, 다른 지표를 중심으로 비교해 보세요."
    key = "industry_ratio" if level == "매우 중요" else "external_ratio"
    label = "기업 공저" if level == "매우 중요" else "외부 기관 협업"
    if abs(ra[key] - rb[key]) < 5:
        return f"{label} 기준으로는 두 연구실이 비슷해요 ({ra[key]}% vs {rb[key]}%)."
    closer = ra if ra[key] > rb[key] else rb
    return f"내 기준에는 **{closer['lab_name']}**{_iga(closer['lab_name'])} 더 가까워 보여요 ({label} {closer[key]}%)."


def render_industry_collab(lab_a, lab_b):
    """조장이 import해서 부르는 함수: 두 연구실 데이터를 받아 지표 2 화면을 그림"""
    ra, rb = compute_industry_collab(lab_a), compute_industry_collab(lab_b)

    st.subheader("🤝 기업 과제 중심인가, 학술 연구 중심인가?")
    with st.expander("ⓘ 계산 방법과 한계"):
        st.markdown(
            "- 분석 기간: **2021~2025년** (5개 지표 공통)\n"
            "- **기업 공저 비율** = 교수 외 공저자 중 기업 소속이 있는 논문 수 ÷ 전체 논문 수\n"
            "- **외부 기관 협업** = 교수 외 공저자 중 교수 소속 대학이 아닌 기관이 있는 논문 수 ÷ 전체 논문 수 "
            "(같은 대학 공저자는 외부로 세지 않음)\n"
            "- **우리 랩 주도** = 기업 공저 논문 중 1저자 또는 마지막(교신) 저자가 우리 랩인 논문\n"
            "- 출처: OpenAlex 공저자 소속 정보\n"
            "- 한계: 공동 '과제'가 아니라 공동 '논문' 기준이에요. 소속 정보가 빠진 논문은 "
            "협업 없음으로 세어져 실제보다 낮을 수 있어요."
        )

    # (1) 좌우 비교 카드: 게이지 바 + 파트너 태그
    col_a, col_b = st.columns(2)
    with col_a:
        _lab_column(ra)
    with col_b:
        _lab_column(rb)

    # (2) 논문 구성 3분할 막대 (산학 vs 학술 한눈에)
    st.markdown("**논문 구성 비교 (%)**")
    split = pd.DataFrame([ra["split"], rb["split"]], index=[ra["lab_name"], rb["lab_name"]])
    st.bar_chart(split, horizontal=True, color=["#4f46e5", "#a5b4fc", "#e5e7eb"])

    # (3) 연도별 추이 + (4) 기업 버블 (데이터 없으면 '수집 예정')
    _trend_chart(ra, rb)
    _bubble_chart(ra, rb)

    # (5) 이용자 선호 선택 → 해석 문장
    level = st.radio("나에게 기업·외부 협업은 얼마나 중요한가요?",
                     ["매우 중요", "보통", "상관없음"], horizontal=True, key="industry_pref")
    st.info(_preference_sentence(ra, rb, level))

    # 3줄 Brief용: 격차 점수(0~1)와 한 줄 요약 (main.py에서 자동 조립)
    d_ind = abs(ra["industry_ratio"] - rb["industry_ratio"])
    d_ext = abs(ra["external_ratio"] - rb["external_ratio"])
    diff_score = round(max(d_ind, d_ext) / 100, 3)
    if max(d_ind, d_ext) < 5:
        summary = (f"두 연구실 모두 기업 공저 비율이 {min(ra['industry_ratio'], rb['industry_ratio'])}~"
                   f"{max(ra['industry_ratio'], rb['industry_ratio'])}%로 비슷해 산학 협업 성향이 닮았습니다.")
    elif d_ext >= d_ind:
        more, less = (ra, rb) if ra["external_ratio"] > rb["external_ratio"] else (rb, ra)
        summary = (f"외부 협업은 {more['lab_name']}({more['external_ratio']}%){_iga(more['lab_name'])} {less['lab_name']}"
                   f"({less['external_ratio']}%)보다 {d_ext:.1f}%p 높아, 학교 밖 기관과 일할 기회가 많습니다.")
    else:
        more, less = (ra, rb) if ra["industry_ratio"] > rb["industry_ratio"] else (rb, ra)
        summary = (f"기업 공저는 {more['lab_name']}({more['industry_ratio']}%){_iga(more['lab_name'])} {less['lab_name']}"
                   f"({less['industry_ratio']}%)보다 {d_ind:.1f}%p 높아, 산학 과제 경험 기회가 많습니다.")
    return {"lab_a": ra, "lab_b": rb, "summary": summary, "diff_score": diff_score}


# ---------- 3. 혼자 테스트용 ----------

if __name__ == "__main__":
    st.set_page_config(page_title="산학/외부 협업 비율", layout="wide")
    data = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
    lab_a = data.get("lab_a") or data.get("lab_A")
    lab_b = data.get("lab_b") or data.get("lab_B")
    result = render_industry_collab(lab_a, lab_b)
    st.caption("3줄 Brief용 요약: " + result["summary"])
