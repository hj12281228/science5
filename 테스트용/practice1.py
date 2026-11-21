"""
지표 1. 우수 학회·저널 논문 비중 및 건수

수식 (2021~2025)
- 전체 논문 수 = 정식 게재 논문 수 (프리프린트·워크숍 제외)
- 우수 학회·저널 비중(%) = 우수 학회·저널 논문 수 / 전체 논문 수 * 100
- 연평균 우수 논문 = 우수 학회·저널 논문 수 / 활동 연수 (기간 중 첫 논문 연도부터)

판별 기준 (전 학문 분야 공통 OpenAlex 정량 지표)
- 우수 학회·저널(1): 분야 보정 피인용 상위 10% 백분위(>= 0.90) 또는 저널 2년 평균 피인용(>= 5.0)
- 중위권(2)        : 분야 보정 피인용 상위 25% 백분위(>= 0.75) 또는 저널 2년 평균 피인용(>= 2.5)
- 기타(3)          : 그 외 정식 게재 논문
"""

import json
import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

MOCK_PATH = Path(__file__).with_name("mock-up-data-toptier-demo.json")
START, END = 2021, 2025

TIER_LABEL = {1: "우수 학회·저널", 2: "중위권", 3: "기타"}

# 연구실 색 (A, B) / 연한 색
COLOR = ("#3D5A80", "#5E8C83")
LIGHT = ("#E3E8EF", "#E2ECEA")
TEXT, MUTE, LINE = "#31333F", "#6b7280", "#e6e8ec"

_EXCLUDED_TYPES = {"preprint", "paratext", "erratum", "retraction", "editorial"}
_NOT_MAIN = re.compile(r"workshop|findings|\b\w+W\)", re.IGNORECASE)


def _extract_percentile(p):
    """OpenAlex citation_normalized_percentile 값 추출 (dict 또는 float 모두 대응)"""
    cnp = p.get("citation_normalized_percentile")
    if isinstance(cnp, dict):
        return cnp.get("value")
    if isinstance(cnp, (int, float)):
        return float(cnp)
    return None


def _clean_venue(venue: str) -> str:
    """사전 매핑 없이 모든 학회·저널에 공통 적용되는 범용 표시명 정리"""
    v = (venue or "").strip()
    if not v:
        return "(게재처 없음)"
    # 1) "이름 - 이름" 중복 표기 제거
    if " - " in v:
        parts = [p.strip() for p in v.split(" - ") if p.strip()]
        if len(parts) >= 2 and parts[0].lower() == parts[1].lower():
            v = parts[0]
    # 2) 끝에 공식 약어 괄호가 붙은 경우 약어 추출 (예: "... Computer Vision (ICCV)" -> "ICCV")
    m = re.search(r"\(([A-Z0-9\-]{2,15})\)\s*$", v)
    if m:
        return m.group(1)
    # 3) 전 분야 공통 영문 접두어 간소화
    for pat, rep in [
        (r"^Proceedings of (the )?", ""),
        (r"^IEEE/CVF\s+", ""),
        (r"\bInternational\b", "Int."),
        (r"\bConference\b", "Conf."),
        (r"\bTransactions\b", "Trans."),
        (r"\bJournal\b", "J."),
    ]:
        v = re.sub(pat, rep, v, flags=re.IGNORECASE).strip()
    return v if len(v) <= 28 else v[:26].rstrip() + "…"


def classify_paper(p):
    """사전 등급표 없이 OpenAlex 분야 보정 백분위 및 저널 영향력 지수로 등급 판별"""
    raw_venue = (p.get("venue") or "").strip()
    short_venue = _clean_venue(raw_venue)
    if not raw_venue or _NOT_MAIN.search(raw_venue):
        return 3, short_venue, raw_venue or "(게재처 없음)"

    pct = _extract_percentile(p)
    impact = p.get("2yr_mean_citedness")

    is_top_pct = pct is not None and pct >= 0.90
    is_top_imp = isinstance(impact, (int, float)) and impact >= 5.0
    if is_top_pct or is_top_imp:
        return 1, short_venue, raw_venue

    is_mid_pct = pct is not None and pct >= 0.75
    is_mid_imp = isinstance(impact, (int, float)) and impact >= 2.5
    if is_mid_pct or is_mid_imp:
        return 2, short_venue, raw_venue

    return 3, short_venue, raw_venue


def compute_toptier(lab, start=START, end=END):
    base = {"lab_name": lab.get("lab_name", ""), "professor": lab.get("professor", "")}
    papers = lab.get("toptier_papers")

    if papers is None:
        n_all, n_top = lab.get("total_papers") or 0, lab.get("top_tier_papers") or 0
        years = [w["year"] for w in lab.get("yearly_works", []) if w.get("count")]
        active = end - max(min(years), start) + 1 if years else 0
        return {**base, "has_papers": False, "n_all": n_all, "n_top": n_top,
                "n_mid": None, "n_oth": None, "active": active, "df": pd.DataFrame()}

    rows = []
    for p in papers:
        y = p.get("year")
        if y is None or not start <= int(y) <= end:
            continue
        if (p.get("type") or "").lower() in _EXCLUDED_TYPES or p.get("venue_type") == "repository":
            continue
        if _NOT_MAIN.search(p.get("venue") or ""):
            continue
        tier, short_key, full_venue = classify_paper(p)
        rows.append({"year": int(y), "title": p.get("title", ""), "venue": short_key,
                     "full_venue": full_venue, "tier": tier, "등급": TIER_LABEL[tier], "url": p.get("url")})
    df = pd.DataFrame(rows, columns=["year", "title", "venue", "full_venue", "tier", "등급", "url"])
    count = df["tier"].value_counts()
    active = end - max(int(df["year"].min()), start) + 1 if len(df) else 0
    return {**base, "has_papers": True, "n_all": len(df), "n_top": int(count.get(1, 0)),
            "n_mid": int(count.get(2, 0)), "n_oth": int(count.get(3, 0)),
            "active": active, "df": df}


def _ratio(r):
    return r["n_top"] / r["n_all"] * 100 if r["n_all"] else None


def _per_year(r):
    return r["n_top"] / r["active"] if r["active"] else None


# ---------------- 화면 조각 (HTML) ----------------

def _badge(mine, other, unit):
    if mine is None or other is None or mine <= other:
        return ""
    return (f"<span style='font-size:12px;padding:1px 8px;border-radius:999px;background:#F0F2F6;"
            f"border:1px solid #e1e4ea;color:{TEXT};margin-left:6px'>+{mine - other:.3g}{unit}</span>")


def _ring(r, color, light):
    v = _ratio(r)
    rad, circ = 56, 2 * 3.14159 * 56
    dash = circ * (v or 0) / 100
    label = "정보 없음" if v is None else f"{v:.3g}%"
    return (f"<svg width='140' height='140'>"
            f"<circle cx='70' cy='70' r='{rad}' fill='none' stroke='{light}' stroke-width='15'/>"
            f"<circle cx='70' cy='70' r='{rad}' fill='none' stroke='{color}' stroke-width='15' "
            f"stroke-linecap='round' stroke-dasharray='{dash} {circ}' transform='rotate(-90 70 70)'/>"
            f"<text x='70' y='76' text-anchor='middle' font-size='26' font-weight='800' fill='{color}'>{label}</text>"
            f"<text x='70' y='97' text-anchor='middle' font-size='11' fill='{MUTE}'>{r['n_top']} / {r['n_all']}편</text>"
            f"</svg>")


def _pyramid(r, color):
    if r["n_mid"] is None:
        return f"<div style='font-size:13px;color:{MUTE}'>등급별 정보 없음 · 수집 예정</div>"
    levels = [(1, r["n_top"], color, "#fff"), (2, r["n_mid"], "#D5D9E0", TEXT),
              (3, r["n_oth"], "#EEF0F3", "#4b5563")]
    edges = [40, 60, 80, 100]
    html = []
    for i, (tier, n, bg, fg) in enumerate(levels):
        top, bottom = (100 - edges[i]) / 2, (100 - edges[i + 1]) / 2
        pct = round(n / r["n_all"] * 100) if r["n_all"] else 0
        star = "★ " if tier == 1 else ""
        html.append(
            "<div style='margin-bottom:4px'>"
            f"<div style='height:40px;display:flex;align-items:center;justify-content:center;"
            f"background:{bg};color:{fg};font-weight:800;font-size:15px;"
            f"clip-path:polygon({top}% 0,{100 - top}% 0,{100 - bottom}% 100%,{bottom}% 100%)'>"
            f"{star}{TIER_LABEL[tier]} {n}편<span style='font-weight:500;font-size:12px;margin-left:4px'>({pct}%)</span></div>"
            "</div>"
        )
    return "".join(html)


def _stickers(r, top_n=6):
    if not r["has_papers"]:
        return ""
    top_df = r["df"][r["df"]["tier"] == 1]
    if top_df.empty:
        return f"<div style='font-size:13px;color:{MUTE}'>우수 학회·저널 게재 이력 없음</div>"
    vc = top_df["venue"].value_counts().head(top_n)
    full_map = top_df.groupby("venue")["full_venue"].first().to_dict()
    return "".join(
        f"<span title='{full_map.get(v, v)}' style='display:inline-flex;align-items:center;gap:6px;font-weight:700;border-radius:8px;"
        f"padding:4px 10px;margin:4px 3px;color:{TEXT};background:#fff;border:1px solid #d5d9e0;"
        f"box-shadow:0 1px 0 {LINE};font-size:13px'>"
        f"<span style='font-size:.7em;color:#9aa3af'>★</span>{v}"
        f"<b style='background:#F0F2F6;border-radius:999px;font-size:11px;padding:1px 6px;font-weight:600'>{n}</b></span>"
        for v, n in vc.items()
    )


def _panel(r, other, idx, max_top):
    color, light = COLOR[idx], LIGHT[idx]
    title = "font-size:13px;color:#6b7280;font-weight:700;margin-bottom:6px"
    per_year = _per_year(r)
    per_year_txt = "-" if per_year is None else f"{per_year:.1f}편"
    width = r["n_top"] / max_top * 100 if max_top else 0
    return (
        f"<div style='border:1px solid {LINE};border-radius:12px;overflow:hidden;background:#fff;"
        f"border-top:4px solid {color};padding-bottom:16px'>"
        f"<div style='padding:12px 20px 10px;border-bottom:1px solid #eef0f3'>"
        f"<div style='font-size:20px;font-weight:800;color:{color}'>{r['lab_name']}</div>"
        f"<div style='font-size:13px;color:{MUTE}'>{r['professor']} 교수 · 정식 논문 {r['n_all']}편</div></div>"
        f"<div style='padding:4px 20px 0'>"
        f"<div style='display:grid;grid-template-columns:165px 1fr;gap:14px;margin-top:14px'>"
        f"<div><div style='{title}'>우수 학회·저널 비중{_badge(_ratio(r), _ratio(other), '%p')}</div>"
        f"{_ring(r, color, light)}</div>"
        f"<div><div style='{title}'>우수 학회·저널 건수 (5년){_badge(r['n_top'], other['n_top'], '편')}</div>"
        f"<div style='font-size:34px;font-weight:800;line-height:1;color:{color}'>{r['n_top']}"
        f"<span style='font-size:16px'>편</span></div>"
        f"<div style='height:12px;background:#f3f4f6;border-radius:999px;overflow:hidden;margin:10px 0 6px'>"
        f"<div style='height:100%;width:{width:.0f}%;background:{color};border-radius:999px'></div></div>"
        f"<div style='font-size:12px;color:{MUTE}'>연평균 {per_year_txt} · 막대는 두 연구실 같은 기준</div>"
        f"</div></div>"
        f"<div style='margin-top:16px'><div style='{title}'>영향력 등급별 논문 수</div>{_pyramid(r, color)}</div>"
        f"<div style='margin-top:14px'><div style='{title}'>★ 주요 우수 학회·저널 TOP</div>{_stickers(r)}</div>"
        f"</div></div>"
    )


# ---------------- 그래프 ----------------

def _yearly_chart(ra, rb):
    frames = []
    for r in (ra, rb):
        g = r["df"].groupby("year")
        y = pd.DataFrame({"전체": g.size(), "우수": g["tier"].apply(lambda s: int((s == 1).sum()))})
        y = y.reindex(range(START, END + 1), fill_value=0).reset_index(names="year")
        y["연구실"] = r["lab_name"]
        frames.append(y)
    data = pd.concat(frames)
    labs = [ra["lab_name"], rb["lab_name"]]
    base = alt.Chart(data).encode(
        x=alt.X("year:O", title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("연구실:N", sort=labs),
        tooltip=["연구실", alt.Tooltip("year:O", title="연도"), "우수", "전체"])
    total = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        y=alt.Y("전체:Q", title="논문 수 (편)"),
        color=alt.Color("연구실:N", scale=alt.Scale(domain=labs, range=list(LIGHT)), legend=None))
    top = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        y="우수:Q",
        color=alt.Color("연구실:N", scale=alt.Scale(domain=labs, range=list(COLOR)),
                        legend=alt.Legend(orient="top", title=None)))
    text = base.mark_text(dy=10, fontSize=11, color="white", fontWeight="bold").encode(
        y="우수:Q", text="우수:Q")
    return alt.layer(total, top, text).resolve_scale(color="independent").properties(height=280)


def _venue_chart(ra, rb):
    rows = []
    for r, sign in ((ra, -1), (rb, 1)):
        for v, n in r["df"][r["df"]["tier"] == 1]["venue"].value_counts().items():
            rows.append({"학회/저널": v, "연구실": r["lab_name"], "편수": int(n), "x": sign * int(n)})
    if not rows:
        return None
    data = pd.DataFrame(rows)
    order = data.groupby("학회/저널")["편수"].sum().sort_values(ascending=False).index.tolist()
    labs = [ra["lab_name"], rb["lab_name"]]
    mx = data["편수"].max() + 1
    base = alt.Chart(data).encode(
        y=alt.Y("학회/저널:N", sort=order, title=None, axis=alt.Axis(labelOverlap=False)),
        tooltip=["학회/저널", "연구실", "편수"])
    bars = base.mark_bar(cornerRadius=3).encode(
        x=alt.X("x:Q", title=f"← {labs[0]}   |   {labs[1]} →", scale=alt.Scale(domain=[-mx, mx]),
                axis=alt.Axis(labelExpr="abs(datum.value)", tickMinStep=1)),
        color=alt.Color("연구실:N", scale=alt.Scale(domain=labs, range=list(COLOR)),
                        legend=alt.Legend(orient="top", title=None)))
    left = base.transform_filter("datum.x < 0").mark_text(align="right", dx=-4, fontSize=11).encode(
        x="x:Q", text="편수:Q")
    right = base.transform_filter("datum.x > 0").mark_text(align="left", dx=4, fontSize=11).encode(
        x="x:Q", text="편수:Q")
    rule = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#9ca3af").encode(x="x:Q")
    return (bars + left + right + rule).properties(height=34 * len(order) + 20)


def _paper_table(ra, rb):
    c1, c2 = st.columns([1, 2])
    who = c1.radio("연구실", [ra["lab_name"], rb["lab_name"], "둘 다"], horizontal=True,
                   key="toptier_list_lab")
    tiers = c2.multiselect("등급", list(TIER_LABEL.values()), default=["우수 학회·저널"],
                           key="toptier_list_tier")
    frames = [r["df"].assign(연구실=r["lab_name"]) for r in (ra, rb) if who in (r["lab_name"], "둘 다")]
    df = pd.concat(frames)
    df = df[df["등급"].isin(tiers)].sort_values(["year", "venue"], ascending=[False, True])
    st.caption(f"{len(df)}편")
    st.dataframe(
        df[["연구실", "year", "등급", "venue", "title", "url"]].rename(
            columns={"year": "연도", "venue": "학회/저널", "title": "제목", "url": "링크"}),
        hide_index=True, use_container_width=True,
        column_config={"링크": st.column_config.LinkColumn("링크", display_text="원문"),
                       "연도": st.column_config.NumberColumn("연도", format="%d")})


# ---------------- 메인 ----------------

def render_toptier(lab_a, lab_b):
    ra, rb = compute_toptier(lab_a), compute_toptier(lab_b)

    st.subheader("1. 우수 학회·저널 논문 비중 및 건수")
    st.caption(f"학계에서 영향력을 인정받는 주요 학회·저널에 논문을 자주 내는가? · {START}–{END}")
    with st.expander("ⓘ 계산 방법과 판별 기준"):
        st.markdown(
            "- **우수 학회·저널 비중(%)** = 우수 학회·저널 게재 논문 수 ÷ 전체 정식 논문 수 × 100\n"
            "- **판별 기준 (전 학문 분야 공통):** OpenAlex 분야 보정 피인용 상위 10% 백분위(`>= 0.90`) 또는 저널 2년 평균 피인용 지수(`>= 5.0`) 충족 시 우수 논문으로 분류\n"
            "- **제외 대상:** 프리프린트(arXiv 등), 워크숍·Findings, 편집자 글·정오표 등 비정식 출판물"
        )

    max_top = max(ra["n_top"], rb["n_top"])
    col_a, col_b = st.columns(2, gap="medium")
    col_a.markdown(_panel(ra, rb, 0, max_top), unsafe_allow_html=True)
    col_b.markdown(_panel(rb, ra, 1, max_top), unsafe_allow_html=True)

    st.write("")
    if ra["has_papers"] and rb["has_papers"]:
        t1, t2, t3 = st.tabs(["연도별 추이", "학회·저널별 비교", "논문 목록"])
        with t1:
            st.caption("진한 막대 = 우수 학회·저널 · 연한 막대 = 전체 정식 논문")
            st.altair_chart(_yearly_chart(ra, rb), use_container_width=True)
        with t2:
            chart = _venue_chart(ra, rb)
            if chart is None:
                st.caption("우수 학회·저널 논문이 없어요.")
            else:
                st.caption("우수 학회·저널별 논문 수 (왼쪽 A · 오른쪽 B)")
                st.altair_chart(chart, use_container_width=True)
        with t3:
            _paper_table(ra, rb)
    else:
        st.info("논문 목록이 없어 연도별·학회별 그래프는 수집 예정이에요.")

    # 최종 리포트(STEP 4) 연동용 한 줄 요약 & 격차 점수 반환
    rat_a, rat_b = _ratio(ra) or 0.0, _ratio(rb) or 0.0
    diff_score = round(abs(rat_a - rat_b), 1)
    if diff_score < 5.0:
        summary = f"두 연구실 모두 우수 학회·저널 비중이 {rat_a:.1f}% vs {rat_b:.1f}%로 학술 성과 밀도가 비슷합니다."
    else:
        more, less = (ra, rb) if rat_a > rat_b else (rb, ra)
        more_rat, less_rat = max(rat_a, rat_b), min(rat_a, rat_b)
        summary = (f"{more['lab_name']}은 우수 학회·저널 비중이 {more_rat:.1f}%({more['n_top']}편)로 "
                   f"{less['lab_name']}({less_rat:.1f}%)보다 {diff_score:.1f}%p 높아 고임팩트 성과 밀도가 높습니다.")

    return {"lab_a": ra, "lab_b": rb, "summary": summary, "diff_score": diff_score}


if __name__ == "__main__":
    st.set_page_config(page_title="우수 학회·저널 논문 비중 및 건수", layout="wide")
    data = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
    result = render_toptier(data["lab_A"], data["lab_B"])
    st.caption("최종 리포트용 요약: " + result["summary"])
