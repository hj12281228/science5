"""
LABMATCH 비교 화면 (첫 화면에서 '비교 시작'을 누른 뒤)

- 확인(동명이인): 후보를 학교 배지가 달린 카드로 보여주고 한 번에 고르기
- 비교: 큰 이름 A vs B → 탭 [요약 | 지표 | 저장]
  · 요약: 다섯 지표 칸(벤토) + 3줄 브리프
  · 지표: 질문 하나당 한 장. 숫자는 팀원 compute_* 결과, 그래프 형식은 팀원 것을 다시 배치 (compare_sheets.py)
          각 장 아래 '원래 그래프와 계산 방법'에서 팀원 render_* 화면을 그대로 볼 수 있음
  · 저장: 면담 질문, TXT 리포트
"""

import html

import streamlit as st

from home_page import load_logos
from practice1 import render_toptier
from practice2 import render_industry_collab
from practice3 import render_interdisciplinarity
from practice4 import render_lab_size
from practice5 import render_continuity
from compare_sheets import CSS as SHEET_CSS, QUESTIONS, collect, headline, brief_line, brief_pick, names_html, summary_html, folders_html, use_palette, css_vars, P

A_COLOR, B_COLOR = "#F24F0B", "#B9C250"

UNI_KO = {
    "Yonsei University": "연세대", "Seoul National University": "서울대", "Korea Advanced Institute of Science and Technology": "KAIST",
    "Pohang University of Science and Technology": "POSTECH", "Korea University": "고려대", "Sungkyunkwan University": "성균관대",
    "Hanyang University": "한양대", "Ulsan National Institute of Science and Technology": "UNIST", "Ewha Womans University": "이화여대",
    "Kyungpook National University": "경북대", "Pusan National University": "부산대", "Gwangju Institute of Science and Technology": "GIST",
    "Daegu Gyeongbuk Institute of Science and Technology": "DGIST", "Kyung Hee University": "경희대", "Chung-Ang University": "중앙대",
    "Sogang University": "서강대", "Chonnam National University": "전남대", "Chungnam National University": "충남대",
    "Inha University": "인하대", "Ajou University": "아주대", "Konkuk University": "건국대", "Dongguk University": "동국대",
    "Hankuk University of Foreign Studies": "한국외대", "University of Seoul": "서울시립대", "Hallym University": "한림대",
}

CSS = """
<style>
.lmc-banner{font-size:12.5px;color:#8a5a00;background:#FFF6E0;border:1px solid #F0DDAE;border-radius:8px;padding:6px 10px;margin-bottom:10px}
.lmc-steps{display:flex;gap:8px;align-items:center;font-size:13px;color:#98A2B0;margin:0 0 10px}
.lmc-steps b{color:#1C2430}
.lmc-steps i{font-style:normal;color:#C9CFD8}
.lmc-bar{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);gap:12px;align-items:center}
.lmc-pc{display:flex;align-items:center;gap:12px;border-radius:14px;padding:10px 14px;color:#141414;min-width:0}
.lmc-pc.A{background:#F24F0B}
.lmc-pc.B{background:#B9C250}
.lmc-pc .slot{font-size:11px;letter-spacing:.12em;opacity:.8}
.lmc-pc b{display:block;font-size:18px;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lmc-pc span.sub{display:block;font-size:12.5px;opacity:.82;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lmc-pc .meta{min-width:0}
.lmc-badge{width:40px;height:40px;flex:none;border-radius:50%;background:#fff;display:grid;place-items:center;overflow:hidden;font-weight:700;font-size:13px;color:#E04608}
.lmc-badge img{width:34px;height:34px;object-fit:contain}
.lmc-vs{width:34px;height:34px;border-radius:50%;border:1px solid #E3E6EB;display:grid;place-items:center;font-weight:700;color:#5F6B7A;font-size:12px;background:#fff}
.lmc-h{font-size:21px;font-weight:700;margin:6px 0 2px;letter-spacing:-.01em}
.lmc-cap{font-size:13.5px;color:#5F6B7A;margin:0 0 10px}
.st-key-lmc_side_B div.stButton > button[kind="primary"]{background:#B9C250;border-color:#B9C250;color:#141414}
.st-key-lmc_side_B div.stButton > button[kind="primary"]:hover{background:#A3AC3C;border-color:#A3AC3C;color:#141414}
.lmc-cand{border:1px solid #DCD8CF;border-radius:18px;padding:12px 14px;display:flex;gap:12px;align-items:center;background:#fff;min-height:82px}
.lmc-cand.on{border:2px solid var(--c);background:var(--soft)}
.lmc-cand .nm{font-weight:700;font-size:16px}
.lmc-cand .af{font-size:13px;color:#5F6B7A}
.lmc-cand .tg{font-size:12px;color:#5F6B7A;margin-top:2px}
/* 상단 A vs B 바: 스크롤해도 위에 붙어 있게 (컨테이너를 감싼 div에 sticky) */
div:has(> .st-key-lmc_bar){position:sticky;top:3.75rem;z-index:20}
.st-key-lmc_bar{background:#FBFBFC;padding:8px 0 16px;border-bottom:1px solid #E3E6EB}
.st-key-lmc_bar div.stButton > button{min-height:30px;height:30px;padding:0 10px;font-size:13px;border-radius:999px;color:#5F6B7A}
.st-key-lmc_bar [data-testid="stHorizontalBlock"]{gap:8px}
@media (max-width:640px){.lmc-pc b{font-size:15px}.lmc-badge{width:32px;height:32px}.lmc-badge img{width:27px;height:27px}}
</style>
"""

esc = html.escape


def uni_ko(name):
    return UNI_KO.get(name or "", name or "소속 정보 없음")


def badge_html(school):
    logos = load_logos()
    if school in logos:
        return f'<span class="lmc-badge"><img src="{logos[school]}" alt="{esc(school)}"></span>'
    short = school[:2] if any("가" <= c <= "힣" for c in school) else "".join(w[0] for w in school.split() if w[:1].isupper())[:4]
    return f'<span class="lmc-badge">{esc(short or "?")}</span>'


def steps_html(now):
    names = ["교수님 고르기", "본인 확인", "비교"]
    parts = [f"<b>{n}</b>" if i == now else n for i, n in enumerate(names)]
    return '<div class="lmc-steps">' + " <i>›</i> ".join(parts) + "</div>"


def person_card(slot, p, sub=None):
    p = p or {}
    school = p.get("school") or p.get("aff") or ""
    sub = sub if sub is not None else (p.get("sub") or "")
    eng = f' <span style="font-weight:400;font-size:13px;opacity:.8">{esc(p.get("eng") or "")}</span>' if p.get("eng") else ""
    return (f'<div class="lmc-pc {slot}">{badge_html(school)}<div class="meta"><div class="slot">LAB {slot}</div>'
            f'<b>{esc(p.get("name") or "")}{eng}</b><span class="sub">{esc(school)}{" · " + esc(sub) if sub else ""}</span></div></div>')


# ---------------------------------------------------------------- 공통 상단 바
def render_bar(slots, step, on_swap):
    dark = is_dark()
    use_palette(dark)
    st.html(CSS + (dark_css() if dark else ""))
    with st.container(key="lmc_bar"):
        st.markdown(steps_html(step), unsafe_allow_html=True)
        st.markdown(f'<div class="lmc-bar">{person_card("A", slots.get("A"))}<div class="lmc-vs">VS</div>{person_card("B", slots.get("B"))}</div>',
                    unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 1])
        if c1.button("A 바꾸기", key=f"swapA{step}", use_container_width=True):
            on_swap("A")
        if c2.button("처음 화면으로", key=f"home{step}", use_container_width=True):
            on_swap(None)
        if c3.button("B 바꾸기", key=f"swapB{step}", use_container_width=True):
            on_swap("B")


# ---------------------------------------------------------------- 확인(동명이인)
def render_confirm(slots, cands, on_swap, on_research):
    """cands = {"A": [...], "B": [...]} → 고른 후보 id를 {"A": id, "B": id}로 돌려줌 (아직 다 못 고르면 None 포함)"""
    render_bar(slots, 1, on_swap)
    st.markdown('<div class="lmc-h">어느 분인지 확인해 주세요</div>'
                '<p class="lmc-cap">같은 이름이 여러 명 있어요. 소속과 논문 수를 보고 맞는 분을 눌러 주세요. 소속이 같은 분을 먼저 골라 두었어요.</p>',
                unsafe_allow_html=True)
    picked = {}
    cols = st.columns(2, gap="large")
    for col, slot, color, soft in ((cols[0], "A", P["A"], "#FDE4D9"), (cols[1], "B", P["B"], "#F1F3DC")):
        with col, st.container(key=f"lmc_side_{slot}"):
            p = slots.get(slot) or {}
            st.markdown(f"**LAB {slot} · '{esc(p.get('name', ''))}' 검색 결과**")
            lst = cands.get(slot) or []
            key = f"pick_{slot}"
            if not lst:
                st.info("OpenAlex에서 찾지 못했어요. 영문 이름으로 다시 찾아볼게요.")
                q = st.text_input("영문 이름", value=p.get("eng") or "", key=f"re_{slot}", placeholder="예: Min Song")
                if st.button("다시 찾기", key=f"rebtn_{slot}"):
                    on_research(slot, q)
                picked[slot] = None
                continue
            if st.session_state.get(key) not in [c["id"] for c in lst]:
                st.session_state[key] = lst[0]["id"]
            for i, c in enumerate(lst):
                on = st.session_state[key] == c["id"]
                school = uni_ko(c.get("institution"))
                tags = ", ".join(c.get("tags_ko") or [])
                st.markdown(
                    f'<div class="lmc-cand {"on" if on else ""}" style="--c:{color};--soft:{soft}">{badge_html(school)}'
                    f'<div style="min-width:0"><div class="nm">{esc(c["name"])}</div><div class="af">{esc(c.get("institution") or "")} · 논문 {c.get("works_count", 0)}편</div>'
                    f'{f"<div class=tg>{esc(tags)}</div>" if tags else ""}</div></div>', unsafe_allow_html=True)
                if st.button("✓ 이 분이에요" if on else "이 분으로 고르기", key=f"c_{slot}_{i}", use_container_width=True, type="primary" if on else "secondary"):
                    st.session_state[key] = c["id"]
                    st.rerun()
            picked[slot] = st.session_state[key]
    return picked



# ---------------------------------------------------------------- 비교 화면
TOP_CSS = """
<style>
/* 비교 화면 상단 버튼: 테두리만 있는 알약 */
.st-key-lm_top div.stButton > button{min-height:32px;height:32px;padding:0 14px;font-size:13px;border-radius:999px;background:transparent;border:1px solid #141414;color:#141414}
.st-key-lm_top div.stButton > button:hover{background:#141414;color:#FBFAF7}
.st-key-lm_top .st-key-lm_swapA button{border-color:#F24F0B;color:#E04608}
.st-key-lm_top .st-key-lm_swapB button{border-color:#B9C250;color:#7F8724}
.lm-logo-word{font-family:"Space Grotesk",sans-serif;font-weight:700;font-size:20px;letter-spacing:.04em;padding-top:4px}
.st-key-lm_top{border-bottom:1px solid #141414;padding-bottom:10px}
/* 탭: 작은 대문자 라벨 */
.st-key-lm_tabs [data-baseweb="tab-list"]{gap:22px;border-bottom:1px solid #141414}
.st-key-lm_tabs [data-baseweb="tab"] p{font-family:"IBM Plex Mono",monospace;font-size:13px;letter-spacing:.06em}
.st-key-lm_tabs [data-baseweb="tab-highlight"]{background:#141414;height:3px}
/* 지표 장 아래 '원래 그래프' 펼치기 */
.st-key-lm_tabs [data-testid="stExpander"] details{border-radius:18px;border-color:#DCD8CF}
.lm-gap{height:28px}
.st-key-lm_tabs [data-testid="stTab"] p{font-family:"IBM Plex Mono",monospace;font-size:13px;letter-spacing:.04em}
.st-key-lm_tabs [data-testid="stTab"][aria-selected="true"],.st-key-lm_tabs [data-testid="stTab"][aria-selected="true"] p,.st-key-lm_tabs [data-testid="stTab"]:hover p{color:#141414}
.st-key-lm_tabs [data-testid="stTab"][aria-selected="true"] p{font-weight:600}
.st-key-lm_tabs .react-aria-SelectionIndicator{background:#141414!important}
.st-key-lmc_pref button[aria-pressed="true"]{background:#141414!important;border-color:#141414!important;color:#FBFAF7!important}
.st-key-lmc_pref button[aria-pressed="true"] *{color:#FBFAF7!important}
.st-key-lm_tabs .stDownloadButton button[kind="primary"]{background:#141414;border-color:#141414}
@media (max-width:640px){
 .st-key-lm_top [data-testid="stHorizontalBlock"]{flex-direction:row;flex-wrap:wrap;gap:6px}
 .st-key-lm_top [data-testid="stColumn"]{min-width:0!important;width:auto!important;flex:1 1 0!important}
 .st-key-lm_top [data-testid="stColumn"]:first-child{flex:1 0 100%!important;margin-bottom:6px}
}
</style>
"""


def is_dark():
    """Streamlit 테마(설정의 Light/Dark 또는 시스템 설정)가 다크인지"""
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


def dark_css():
    """다크모드: 처음부터 다크로 디자인한 것처럼 바탕·카드·버튼 색을 바꿈 (A·B 색은 다크용 조합)"""
    a, b, ona, onb = P["A"], P["B"], P["ON_A"], P["ON_B"]
    return f"""<style>
.stApp,[data-testid="stHeader"]{{background:#0C0C0F}}
.lmc-pc.A{{background:{a};color:{ona}}}.lmc-pc.B{{background:{b};color:{onb}}}
.lmc-vs{{background:#141418;border-color:#2B2B33;color:#B7B6BE}}
.lmc-steps{{color:#6B6A73}}.lmc-steps b{{color:#F3F2EE}}.lmc-steps i{{color:#3A3A42}}
.st-key-lmc_bar{{background:#0C0C0F;border-bottom-color:#2B2B33}}
.st-key-lmc_bar div.stButton > button{{color:#B7B6BE;background:transparent;border-color:#2B2B33}}
.lmc-h{{color:#F3F2EE}}.lmc-cap{{color:#A5A4AD}}
.lmc-cand{{background:#141418;border-color:#2B2B33;color:#F3F2EE}}
.lmc-cand .af,.lmc-cand .tg{{color:#A5A4AD}}
.lmc-cand.on{{border:2px solid var(--c);background:color-mix(in srgb,var(--c) 14%,#141418)}}
.lmc-badge{{background:#fff}}
.st-key-lmc_side_A div.stButton > button[kind="primary"]{{background:{a};border-color:{a};color:{ona}}}
.st-key-lmc_side_B div.stButton > button[kind="primary"]{{background:{b};border-color:{b};color:{onb}}}
.st-key-lmc_side_A div.stButton > button[kind="primary"] *{{color:{ona}}}
.st-key-lmc_side_B div.stButton > button[kind="primary"] *{{color:{onb}}}
div.stButton > button[kind="secondary"]{{background:transparent;border-color:#2B2B33;color:#F3F2EE}}
div.stButton > button[kind="primary"]{{background:#F3F2EE;border-color:#F3F2EE;color:#0C0C0F}}
div.stButton > button[kind="primary"] *{{color:#0C0C0F}}
.st-key-lm_top{{border-bottom-color:#F3F2EE}}
.st-key-lm_top div.stButton > button{{border-color:#F3F2EE;color:#F3F2EE;background:transparent}}
.st-key-lm_top div.stButton > button:hover{{background:#F3F2EE;color:#0C0C0F}}
.st-key-lm_top .st-key-lm_swapA button{{border-color:{a};color:{a}}}
.st-key-lm_top .st-key-lm_swapB button{{border-color:{b};color:{b}}}
.lm-logo-word{{color:#F3F2EE}}
.st-key-lm_tabs [data-baseweb="tab-list"]{{border-bottom-color:#F3F2EE}}
.st-key-lm_tabs [data-testid="stTab"] p{{color:#8E8D96}}
.st-key-lm_tabs [data-testid="stTab"][aria-selected="true"] p,.st-key-lm_tabs [data-testid="stTab"]:hover p{{color:#F3F2EE}}
.st-key-lm_tabs .react-aria-SelectionIndicator{{background:#F3F2EE!important}}
.st-key-lmc_pref button{{background:transparent;border-color:#3A3A42;color:#F3F2EE}}
.st-key-lmc_pref button[aria-pressed="true"]{{background:#F3F2EE!important;border-color:#F3F2EE!important;color:#0C0C0F!important}}
.st-key-lmc_pref button[aria-pressed="true"] *{{color:#0C0C0F!important}}
.st-key-lm_tabs [data-testid="stExpander"] details{{border-color:#2B2B33;background:#141418}}
.st-key-lm_tabs .stDownloadButton button[kind="primary"]{{background:#F3F2EE;border-color:#F3F2EE;color:#0C0C0F}}
.st-key-lm_tabs .stDownloadButton button[kind="primary"] *{{color:#0C0C0F}}
</style>"""


def _logo(school):
    logos = load_logos()
    if school in logos:
        return f'<img src="{logos[school]}" alt="{esc(school)}">'
    return esc(school[:2] if school else "?")


def _person(slot, slots, data):
    p = dict(slots.get(slot) or {})
    p.setdefault("name", data.get("professor") or f"LAB {slot}")
    if not p.get("school"):
        p["school"] = uni_ko(p.get("inst") or "")
    return p


def _detail(key, data_a, data_b):
    """팀원 render_* 화면 (계산 방법·표·원래 그래프). 요약 한 줄을 돌려받으면 리포트에 씀"""
    if key == "top":
        return render_toptier(data_a, data_b)
    if key == "ind":
        return render_industry_collab(data_a, data_b)
    if key == "mix":
        return render_interdisciplinarity({"lab_A": data_a, "lab_B": data_b})
    if key == "size":
        return render_lab_size(data_a, data_b)
    return render_continuity([data_a, data_b])


def render_compare(slots, data_a, data_b, on_swap, build_txt_report, demo=False):
    dark = is_dark()
    use_palette(dark)
    st.html(CSS + SHEET_CSS + TOP_CSS + css_vars() + (dark_css() if dark else ""))
    m = collect(data_a, data_b)
    pa, pb = _person("A", slots, data_a), _person("B", slots, data_b)

    # 상단: 로고 · 바꾸기 버튼
    with st.container(key="lm_top"):
        c0, c1, c2, c3 = st.columns([5, 1.2, 1.2, 1.2], vertical_alignment="center")
        c0.markdown('<div class="lm-logo-word">LABMATCH</div>', unsafe_allow_html=True)
        if c1.button("A 바꾸기", key="lm_swapA", use_container_width=True):
            on_swap("A")
        if c2.button("처음 화면", key="lm_home", use_container_width=True):
            on_swap(None)
        if c3.button("B 바꾸기", key="lm_swapB", use_container_width=True):
            on_swap("B")

    # 큰 이름 A vs B
    st.markdown(names_html(pa, pb, _logo(pa["school"]), _logo(pb["school"])), unsafe_allow_html=True)

    # 나에게 중요한 것 → 요약 칸 색칠, 브리프·지표 순서
    st.pills("나에게 중요한 것", [q["key"] for q in QUESTIONS], selection_mode="multi", key="lmc_pref",
             format_func=lambda k: next(q["chip"] for q in QUESTIONS if q["key"] == k))
    chosen = st.session_state.get("lmc_pref") or []
    order = sorted(QUESTIONS, key=lambda q: (q["key"] not in chosen, QUESTIONS.index(q)))

    summaries = {}
    title = f"{pa['name']} vs {pb['name']}"
    with st.container(key="lm_tabs"):
        t1, t2, t3 = st.tabs(["01  요약", "02  지표", "03  저장"])

        with t1:
            st.markdown(summary_html(m, chosen, demo, title), unsafe_allow_html=True)

        with t2:
            st.markdown(folders_html(order, m, chosen, title), unsafe_allow_html=True)
            st.html('<div class="lm-gap"></div>')
            with st.expander("ⓘ 계산 방법 · 원래 그래프와 표 자세히 (팀원 화면)"):
                tabs = st.tabs([f"{q['no']} {q['chip']}" for q in QUESTIONS])
                for tab, q in zip(tabs, QUESTIONS):
                    with tab:
                        try:
                            res = _detail(q["key"], data_a, data_b)
                        except Exception as e:  # 한 지표가 실패해도 나머지는 보여줌
                            st.error(f"이 지표를 그리지 못했어요: {e}")
                            res = None
                    summaries[q["key"]] = res.get("summary") if isinstance(res, dict) else None

        for q in QUESTIONS:
            if not summaries.get(q["key"]):
                a, b, unit, _ = headline(m, q["key"])
                summaries[q["key"]] = f"{brief_line(q['key'], a, b, unit)} (A {a:g}{unit}, B {b:g}{unit})"

        with t3:
            pick = brief_pick(m, chosen)
            prof_a, prof_b = pa["name"], pb["name"]
            weak = pick[0]["chip"]
            q_a = f"최근 논문을 보니 '{weak}' 쪽이 눈에 띄었습니다. 신입생이 합류하면 어떤 과제부터 맡게 되고, 1저자 연구 기회는 어떻게 주어지나요?"
            q_b = f"'{weak}' 측면에서 연구실 운영 방식이 궁금합니다. 신입생이 적응할 때 선배 멘토링이나 세미나는 어떻게 진행되나요?"
            st.markdown("**면담에서 물어볼 질문**")
            c1, c2 = st.columns(2)
            c1.caption(f"{prof_a} 교수님께")
            c1.code(q_a, language=None, wrap_lines=True)
            c2.caption(f"{prof_b} 교수님께")
            c2.code(q_b, language=None, wrap_lines=True)

            txt = build_txt_report(data_a, data_b, [summaries[q["key"]] for q in QUESTIONS], q_a, q_b)
            c1, c2 = st.columns(2)
            c1.download_button("리포트 저장 (TXT)", data=txt.encode("utf-8"), file_name=f"LABMATCH_{prof_a}_vs_{prof_b}.txt",
                               mime="text/plain", use_container_width=True, type="primary")
            if c2.button("A는 두고 B만 바꿔 비교하기", use_container_width=True, key="keepA"):
                on_swap("B")

            with st.expander("데이터를 읽을 때 주의할 점"):
                st.markdown(
                    "- **저자 식별:** OpenAlex는 전 세계 DB라 동명이인이 섞일 수 있어요. 본인 확인 단계에서 소속을 꼭 확인하세요.\n"
                    "- **분석 범위:** 최근 논문 100편을 불러오고, 핵심 지표는 2021~2025년 논문으로 계산해요.\n"
                    "- **논문에 없는 정보:** 연구실 분위기, 인건비, 비공개 과제는 반영되지 않아요. 면담에서 확인하세요."
                )
