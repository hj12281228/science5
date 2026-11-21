"""
LABMATCH 비교 화면 (첫 화면에서 '비교 시작'을 누른 뒤)

- 확인(동명이인): 후보를 학교 배지가 달린 카드로 보여주고 한 번에 고르기
- 비교: 상단 A vs B 바 → 한눈에 보기(질문 5줄) → 내 기준 → 지표 상세 → 3줄 브리프
- 지표 상세의 그래프와 계산은 팀원 파일(practice1~5)의 render_* 함수를 그대로 씁니다.
  '한눈에 보기' 숫자는 같은 파일의 compute_* 함수에서 가져옵니다.
"""

import html

import streamlit as st

from home_page import load_logos
from practice1 import compute_toptier, render_toptier
from practice2 import compute_industry_collab, render_industry_collab
from practice3 import summarize as summarize_fields, render_interdisciplinarity
from practice4 import compute_lab_size, render_lab_size
from practice5 import compute_continuity, render_continuity

A_COLOR, B_COLOR = "#3D5A80", "#5E8C83"

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

# 다섯 가지 질문. key는 내 기준 칩과 지표 상세를 잇는 이름
QUESTIONS = [
    {"key": "top", "chip": "좋은 학회·저널", "q": "주요 학회·저널에 자주 싣나요?", "name": "① 우수 학회·저널 비중"},
    {"key": "ind", "chip": "학교 밖 협업", "q": "기업·다른 기관과 함께 연구하나요?", "name": "② 산학·외부 협업 비율"},
    {"key": "mix", "chip": "여러 분야 융합", "q": "다른 전공 출신도 어울릴 만큼 분야가 넓나요?", "name": "③ 학제 간 융합도"},
    {"key": "size", "chip": "질문할 선배", "q": "함께 연구하는 사람이 많나요?", "name": "④ 연구실 규모·사수"},
    {"key": "cont", "chip": "꾸준한 논문", "q": "논문이 끊기지 않고 꾸준히 나오나요?", "name": "⑤ 연구 산출 연속성"},
]

CSS = """
<style>
.lmc-banner{font-size:12.5px;color:#8a5a00;background:#FFF6E0;border:1px solid #F0DDAE;border-radius:8px;padding:6px 10px;margin-bottom:10px}
.lmc-steps{display:flex;gap:8px;align-items:center;font-size:13px;color:#98A2B0;margin:0 0 10px}
.lmc-steps b{color:#1C2430}
.lmc-steps i{font-style:normal;color:#C9CFD8}
.lmc-bar{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);gap:12px;align-items:center}
.lmc-pc{display:flex;align-items:center;gap:12px;border-radius:14px;padding:10px 14px;color:#fff;min-width:0}
.lmc-pc.A{background:linear-gradient(160deg,#4A6A93,#2F4867)}
.lmc-pc.B{background:linear-gradient(160deg,#6E9C93,#466F67)}
.lmc-pc .slot{font-size:11px;letter-spacing:.12em;opacity:.8}
.lmc-pc b{display:block;font-size:18px;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lmc-pc span.sub{display:block;font-size:12.5px;opacity:.82;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lmc-pc .meta{min-width:0}
.lmc-badge{width:40px;height:40px;flex:none;border-radius:50%;background:#fff;display:grid;place-items:center;overflow:hidden;font-weight:700;font-size:13px;color:#3D5A80}
.lmc-badge img{width:34px;height:34px;object-fit:contain}
.lmc-vs{width:34px;height:34px;border-radius:50%;border:1px solid #E3E6EB;display:grid;place-items:center;font-weight:700;color:#5F6B7A;font-size:12px;background:#fff}
.lmc-lean{margin-top:10px;font-size:13px;color:#5F6B7A}
.lmc-lean .track{position:relative;height:8px;border-radius:4px;background:linear-gradient(90deg,#3D5A80 0%,#E3E6EB 50%,#5E8C83 100%);margin:6px 0 2px}
.lmc-lean .knob{position:absolute;top:50%;width:18px;height:18px;border-radius:50%;background:#fff;border:3px solid #1C2430;transform:translate(-50%,-50%);transition:left .4s}
.lmc-lean .ends{display:flex;justify-content:space-between;font-size:11.5px;color:#98A2B0}
.lmc-h{font-size:21px;font-weight:700;margin:6px 0 2px;letter-spacing:-.01em}
.lmc-cap{font-size:13.5px;color:#5F6B7A;margin:0 0 10px}
.lmc-row{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1.3fr);gap:18px;align-items:center;padding:14px 4px;border-top:1px solid #EEF0F3}
.lmc-row .q{font-weight:700;font-size:15.5px}
.lmc-row .q small{display:block;font-weight:500;font-size:12px;color:#98A2B0;margin-top:2px}
.lmc-row .ans{font-size:13.5px;color:#31333F;margin-top:4px}
.lmc-row .star{display:inline-block;font-size:11px;font-weight:600;color:#fff;background:#1C2430;border-radius:999px;padding:1px 8px;margin-left:6px;vertical-align:2px}
.lmc-db{position:relative;height:46px}
.lmc-db .axis{position:absolute;left:0;right:0;top:22px;height:2px;background:#E3E6EB}
.lmc-db .seg{position:absolute;top:21px;height:4px;background:#C9CFD8;border-radius:2px}
.lmc-db .dot{position:absolute;top:23px;width:18px;height:18px;border-radius:50%;transform:translate(-50%,-50%);border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.25)}
.lmc-db .lab{position:absolute;font-size:12px;font-weight:700;transform:translateX(-50%);white-space:nowrap}
.lmc-db .lab.top{top:0}
.lmc-db .lab.bot{top:31px}
.lmc-brief{border:1px solid #E3E6EB;border-radius:18px;padding:18px 20px;background:#fff}
.lmc-brief ol{margin:6px 0 0;padding-left:20px}
.lmc-brief li{margin:6px 0;line-height:1.55}
.st-key-lmc_side_B div.stButton > button[kind="primary"]{background:#5E8C83;border-color:#5E8C83}
.st-key-lmc_side_B div.stButton > button[kind="primary"]:hover{background:#466F67;border-color:#466F67}
.lmc-cand{border:1px solid #E3E6EB;border-radius:14px;padding:12px 14px;display:flex;gap:12px;align-items:center;background:#fff;min-height:82px}
.lmc-cand.on{border:2px solid var(--c);background:var(--soft)}
.lmc-cand .nm{font-weight:700;font-size:16px}
.lmc-cand .af{font-size:13px;color:#5F6B7A}
.lmc-cand .tg{font-size:12px;color:#5F6B7A;margin-top:2px}
/* 상단 A vs B 바: 스크롤해도 위에 붙어 있게 (컨테이너를 감싼 div에 sticky) */
div:has(> .st-key-lmc_bar){position:sticky;top:3.75rem;z-index:20}
.st-key-lmc_bar{background:#FBFBFC;padding:8px 0 16px;border-bottom:1px solid #E3E6EB}
.st-key-lmc_bar div.stButton > button{min-height:30px;height:30px;padding:0 10px;font-size:13px;border-radius:999px;color:#5F6B7A}
.st-key-lmc_bar [data-testid="stHorizontalBlock"]{gap:8px}
@media (max-width:640px){.lmc-row{grid-template-columns:minmax(0,1fr)}.lmc-pc b{font-size:15px}.lmc-badge{width:32px;height:32px}.lmc-badge img{width:27px;height:27px}}
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
def render_bar(slots, step, on_swap, lean=None):
    st.html(CSS)
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
        if lean is not None:
            st.markdown(lean, unsafe_allow_html=True)


# ---------------------------------------------------------------- 확인(동명이인)
def render_confirm(slots, cands, on_swap, on_research):
    """cands = {"A": [...], "B": [...]} → 고른 후보 id를 {"A": id, "B": id}로 돌려줌 (아직 다 못 고르면 None 포함)"""
    render_bar(slots, 1, on_swap)
    st.markdown('<div class="lmc-h">어느 분인지 확인해 주세요</div>'
                '<p class="lmc-cap">같은 이름이 여러 명 있어요. 소속과 논문 수를 보고 맞는 분을 눌러 주세요. 소속이 같은 분을 먼저 골라 두었어요.</p>',
                unsafe_allow_html=True)
    picked = {}
    cols = st.columns(2, gap="large")
    for col, slot, color, soft in ((cols[0], "A", A_COLOR, "#E8EEF5"), (cols[1], "B", B_COLOR, "#E7F0EE")):
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


# ---------------------------------------------------------------- 비교: 숫자 모으기
def _pct(n, d):
    return round(100 * n / d, 1) if d else 0.0


def overview_values(data_a, data_b):
    """한눈에 보기용 값 (팀원 compute_* 함수 결과에서 꺼냄)"""
    out = {}
    ta, tb = compute_toptier(data_a), compute_toptier(data_b)
    out["top"] = (_pct(ta["n_top"], ta["n_all"]), _pct(tb["n_top"], tb["n_all"]), "%", 100,
                  f"우수 학회·저널 논문 {ta['n_top']}편 / {ta['n_all']}편", f"{tb['n_top']}편 / {tb['n_all']}편")
    ia, ib = compute_industry_collab(data_a), compute_industry_collab(data_b)
    out["ind"] = (ia["external_ratio"], ib["external_ratio"], "%", 100,
                  f"기업 공저 {ia['industry_ratio']}%", f"기업 공저 {ib['industry_ratio']}%")

    def mix(d):
        ps = [p for p in d.get("interdisciplinarity_demo_papers") or [] if isinstance(p.get("year"), int) and 2021 <= p["year"] <= 2025]
        s = summarize_fields(ps)
        return round(s["score"], 1) if s["score"] is not None else 0.0, s["classified"]
    ma, mb = mix(data_a), mix(data_b)
    out["mix"] = (ma[0], mb[0], "%", 100, f"분류된 논문 {ma[1]}편 기준", f"{mb[1]}편 기준")
    sa, sb = compute_lab_size(data_a), compute_lab_size(data_b)
    out["size"] = (sa["active_members"], sb["active_members"], "명", max(sa["active_members"], sb["active_members"], 1) * 1.15,
                   f"사수 후보 {sa['senior_count']}명", f"사수 후보 {sb['senior_count']}명")
    ca, cb = compute_continuity(data_a), compute_continuity(data_b)
    out["cont"] = (ca["active_month_ratio"], cb["active_month_ratio"], "%", 100,
                   f"공백 연도 {len(ca['gap_years'])}개", f"공백 연도 {len(cb['gap_years'])}개")
    return out


def _fmt(v, unit):
    return f"{v:g}{unit}" if unit == "%" else f"{int(v)}{unit}"


def answer_sentence(key, a, b, unit):
    gap = abs(a - b)
    close = gap < (5 if unit == "%" else max(2, 0.15 * max(a, b)))
    if close:
        return "두 연구실이 비슷해요."
    who = "A" if a > b else "B"
    diff = f"{gap:.1f}%p" if unit == "%" else f"{int(gap)}명"
    return {
        "top": f"{who} 연구실이 {diff} 더 자주 실어요.",
        "ind": f"{who} 연구실이 학교 밖과 {diff} 더 많이 함께 써요.",
        "mix": f"{who} 연구실 논문이 여러 분야에 더 걸쳐 있어요 ({diff}).",
        "size": f"{who} 연구실에 함께 쓰는 사람이 {diff} 더 많아요.",
        "cont": f"{who} 연구실이 더 꾸준해요 (논문 나온 달 {diff} 더 많음).",
    }[key]


def dumbbell(a, b, unit, mx):
    mx = mx or 1
    pa, pb = min(a / mx, 1) * 100, min(b / mx, 1) * 100
    lo, hi = min(pa, pb), max(pa, pb)
    near = abs(pa - pb) < 9  # 두 점이 가까우면 라벨을 위아래로 나눔
    la = "top" if (not near or pa >= pb) else "bot"
    lb = "bot" if (near and pa >= pb) else "top"
    return (f'<div class="lmc-db"><div class="axis"></div><div class="seg" style="left:{lo}%;width:{hi - lo}%"></div>'
            f'<div class="dot" style="left:{pa}%;background:{A_COLOR}"></div><div class="dot" style="left:{pb}%;background:{B_COLOR}"></div>'
            f'<div class="lab {la}" style="left:{pa}%;color:{A_COLOR}">A {_fmt(a, unit)}</div>'
            f'<div class="lab {lb}" style="left:{pb}%;color:{B_COLOR}">B {_fmt(b, unit)}</div></div>')


def lean_html(vals, chosen):
    """내 기준(고른 칩)에서 어느 쪽으로 기우는지: -1(A) ~ +1(B)"""
    if not chosen:
        return ('<div class="lmc-lean">아래 "나에게 중요한 것"을 고르면, 내 기준으로 어느 연구실 쪽으로 기우는지 여기에 보여드려요.</div>')
    score = 0.0
    for k in chosen:
        a, b = vals[k][0], vals[k][1]
        if a == b:
            continue
        rel = (b - a) / max(a, b)  # 큰 쪽 기준 상대 차이
        score += max(-1.0, min(1.0, rel * 2))
    score /= len(chosen)
    pos = 50 + score * 45
    if abs(score) < 0.12:
        txt = "내 기준으로는 <b>두 연구실이 비슷해요</b>."
    else:
        txt = f"내 기준으로는 <b>{'A' if score < 0 else 'B'} 연구실 쪽으로 기울어요</b>."
    return (f'<div class="lmc-lean">{txt} <span style="color:#98A2B0">(고른 기준 {len(chosen)}개, 좋고 나쁨이 아니라 내 우선순위와의 거리)</span>'
            f'<div class="track"><div class="knob" style="left:{pos}%"></div></div><div class="ends"><span>A 쪽</span><span>비슷함</span><span>B 쪽</span></div></div>')


# ---------------------------------------------------------------- 비교 화면
def render_compare(slots, data_a, data_b, on_swap, build_txt_report, demo=False):
    vals = overview_values(data_a, data_b)
    chosen = st.session_state.get("lmc_pref") or []
    render_bar(slots, 2, on_swap, lean=lean_html(vals, chosen))
    if demo:
        st.markdown('<div class="lmc-banner">화면 확인용 예시 데이터예요. 실제 교수님 데이터가 아닙니다.</div>', unsafe_allow_html=True)

    # 1) 내 기준
    st.markdown('<div class="lmc-h">나에게 중요한 것</div><p class="lmc-cap">고른 것부터 위로 올라오고, 위쪽 막대가 내 기준으로 어느 연구실에 가까운지 보여줘요.</p>',
                unsafe_allow_html=True)
    st.pills("나에게 중요한 것", [q["key"] for q in QUESTIONS], selection_mode="multi", key="lmc_pref",
             format_func=lambda k: next(q["chip"] for q in QUESTIONS if q["key"] == k), label_visibility="collapsed")
    order = sorted(QUESTIONS, key=lambda q: (q["key"] not in chosen, QUESTIONS.index(q)))

    # 2) 한눈에 보기
    st.markdown('<div class="lmc-h" style="margin-top:18px">한눈에 보기</div>'
                '<p class="lmc-cap">최근 논문(2021~2025년)으로 계산했어요. 점이 오른쪽일수록 값이 커요. 자세한 그래프는 아래에서 펼쳐 보세요.</p>',
                unsafe_allow_html=True)
    rows = []
    for q in order:
        a, b, unit, mx, na, nb = vals[q["key"]]
        star = '<span class="star">내 기준</span>' if q["key"] in chosen else ""
        rows.append(f'<div class="lmc-row"><div><div class="q">{esc(q["q"])}{star}<small>{esc(q["name"])} · A {esc(na)} · B {esc(nb)}</small></div>'
                    f'<div class="ans">{esc(answer_sentence(q["key"], a, b, unit))}</div></div>{dumbbell(a, b, unit, mx)}</div>')
    st.markdown("".join(rows), unsafe_allow_html=True)

    # 3) 지표 상세 (팀원 화면 그대로)
    st.markdown('<div class="lmc-h" style="margin-top:22px">지표 자세히 보기</div><p class="lmc-cap">각 지표의 그래프와 계산 방법이에요.</p>',
                unsafe_allow_html=True)
    summaries, diffs = {}, {}
    for q in order:
        with st.expander(f"{q['name']}  ·  {q['q']}", expanded=(q is order[0])):
            try:
                if q["key"] == "top":
                    res = render_toptier(data_a, data_b)
                elif q["key"] == "ind":
                    res = render_industry_collab(data_a, data_b)
                elif q["key"] == "mix":
                    res = render_interdisciplinarity({"lab_A": data_a, "lab_B": data_b})
                elif q["key"] == "size":
                    res = render_lab_size(data_a, data_b)
                else:
                    res = render_continuity([data_a, data_b])
            except Exception as e:  # 한 지표가 실패해도 나머지는 보여줌
                st.error(f"이 지표를 그리지 못했어요: {e}")
                res = None
        a, b, unit, *_ = vals[q["key"]]
        summaries[q["key"]] = (res or {}).get("summary") if isinstance(res, dict) else None
        if not summaries[q["key"]]:
            summaries[q["key"]] = f"{answer_sentence(q['key'], a, b, unit)} (A {_fmt(a, unit)}, B {_fmt(b, unit)})"
        diffs[q["key"]] = abs(a - b) / max(a, b, 1e-9)

    # 4) 3줄 브리프: 내 기준을 먼저, 그다음 차이가 큰 지표 순으로 3개
    pick = sorted(QUESTIONS, key=lambda q: (q["key"] not in chosen, -diffs[q["key"]]))[:3]
    st.markdown('<div class="lmc-h" style="margin-top:22px">3줄 브리프</div>'
                f'<p class="lmc-cap">{"내 기준으로 고른 것과 " if chosen else ""}두 연구실 차이가 큰 지표 3가지예요.</p>', unsafe_allow_html=True)
    st.markdown('<div class="lmc-brief"><ol>' + "".join(f"<li><b>{esc(q['name'][2:])}</b> · {esc(summaries[q['key']])}</li>" for q in pick)
                + "</ol></div>", unsafe_allow_html=True)

    prof_a, prof_b = data_a.get("professor", "A"), data_b.get("professor", "B")
    weak = pick[0]["name"][2:]
    q_a = f"최근 논문을 보니 {weak} 쪽이 눈에 띄었습니다. 신입생이 합류하면 어떤 과제부터 맡게 되고, 1저자 연구 기회는 어떻게 주어지나요?"
    q_b = f"{weak} 측면에서 연구실 운영 방식이 궁금합니다. 신입생이 적응할 때 선배 멘토링이나 세미나는 어떻게 진행되나요?"
    with st.expander("면담에서 물어볼 질문", expanded=False):
        c1, c2 = st.columns(2)
        c1.markdown(f"**{esc(prof_a)} 교수님께**")
        c1.code(q_a, language=None)
        c2.markdown(f"**{esc(prof_b)} 교수님께**")
        c2.code(q_b, language=None)

    order5 = [summaries[q["key"]] for q in QUESTIONS]
    txt = build_txt_report(data_a, data_b, order5, q_a, q_b)
    c1, c2 = st.columns(2)
    c1.download_button("리포트 저장 (TXT)", data=txt.encode("utf-8"), file_name=f"LABMATCH_{prof_a}_vs_{prof_b}.txt",
                       mime="text/plain", use_container_width=True)
    if c2.button("A는 두고 B만 바꿔 비교하기", use_container_width=True, key="keepA"):
        on_swap("B")

    with st.expander("데이터를 읽을 때 주의할 점"):
        st.markdown(
            "- **저자 식별:** OpenAlex는 전 세계 DB라 동명이인이 섞일 수 있어요. 본인 확인 단계에서 소속을 꼭 확인하세요.\n"
            "- **분석 범위:** 최근 논문 100편을 불러오고, 핵심 지표는 2021~2025년 논문으로 계산해요.\n"
            "- **논문에 없는 정보:** 연구실 분위기, 인건비, 비공개 과제는 반영되지 않아요. 면담에서 확인하세요."
        )
