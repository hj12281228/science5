import json
from datetime import datetime
from pathlib import Path
import requests
import streamlit as st

# 조원들이 만든 5개의 지표 함수 불러오기
from practice1 import render_toptier
from practice2 import render_industry_collab
from practice3 import render_interdisciplinarity
from practice4 import render_lab_size
from practice5 import render_continuity

# =========================================================
# [데이터베이스] 연세대학교 교수진 DB 자동 생성 및 로드
# =========================================================
def load_professor_db():
    db_path = Path("professors_db.json")
    if not db_path.exists():
        default_db = {
            "인공지능융합대학": {
                "인공지능학과": [
                    {"name": "함범섭", "eng": "Bumsub Ham"},
                    {"name": "황도식", "eng": "Dosik Hwang"}
                ]
            },
            "공과대학": {
                "전기전자공학부": [
                    {"name": "손광훈", "eng": "Kwanghoon Sohn"}
                ]
            },
            "문과대학": {
                "문헌정보학과": [
                    {"name": "송민", "eng": "Min Song"},
                    {"name": "김기영", "eng": "Kiyoung Kim"},
                    {"name": "주영준", "eng": "Youngjoon Joo"},
                    {"name": "이지연", "eng": "Jiyeon Lee"},
                    {"name": "김성언", "eng": "Seongeon Kim"}
                ]
            }
        }
        db_path.write_text(json.dumps(default_db, ensure_ascii=False, indent=4), encoding="utf-8")

    db_tree = json.loads(db_path.read_text(encoding="utf-8"))
    name_map = {
        p["name"]: p["eng"]
        for depts in db_tree.values()
        for profs in depts.values()
        for p in profs
    }
    return db_tree, name_map

PROF_DB_TREE, PROF_NAME_MAP = load_professor_db()

# =========================================================
# [엔진 1, 2] OpenAlex 데이터 수집
# =========================================================
@st.cache_data(show_spinner=False, ttl=3600)
def search_author_candidates(query_name):
    search_url = f"https://api.openalex.org/authors?search={query_name}&per-page=5"
    res = requests.get(search_url).json()
    candidates = []
    for author in res.get("results", []):
        inst = "소속 정보 없음"
        if author.get("last_known_institution"):
            inst = author["last_known_institution"].get("display_name", "소속 정보 없음")
        candidates.append({
            "id": author["id"],
            "name": author["display_name"],
            "institution": inst,
            "works_count": author.get("works_count", 0)
        })
    return candidates

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_openalex_lab_data_by_id(author_id, author_name):
    works_url = f"https://api.openalex.org/works?filter=author.id:{author_id}&sort=publication_year:desc&per-page=100"
    works_res = requests.get(works_url).json()
    raw_works = works_res.get("results", [])

    lab_dict = {
        "lab_name": f"{author_name} 연구실",
        "professor_id": author_id,
        "professor": author_name,
        "total_papers": len(raw_works),
        "collaboration": {"external_papers": 0, "industry_papers": 0, "industry_partners": []},
        "works": [],
        "interdisciplinarity_demo_papers": [],
        "toptier_papers": []
    }
    industry_partners = set()

    for w in raw_works:
        year = w.get("publication_year")
        pub_date = w.get("publication_date")
        authorships = w.get("authorships", [])

        lab_dict["works"].append({
            "id": w["id"],
            "year": year,
            "publication_year": year,
            "publication_date": pub_date,
            "authorships": authorships
        })
        concepts = [c["display_name"] for c in w.get("concepts", []) if c.get("level", 1) == 0]
        lab_dict["interdisciplinarity_demo_papers"].append({
            "id": w["id"],
            "title": w.get("title", ""),
            "year": year,
            "field_ids": concepts
        })

        venue_name = w.get("primary_location", {}).get("source", {})
        venue_name = venue_name.get("display_name", "") if venue_name else ""
        lab_dict["toptier_papers"].append({
            "title": w.get("title", ""),
            "year": year,
            "venue": venue_name,
            "type": w.get("type", ""),
            "url": w.get("id", "")
        })

        is_external, is_industry = False, False
        for auth in authorships:
            if auth["author"]["id"] != author_id:
                for inst in auth.get("institutions", []):
                    if inst.get("id"):
                        is_external = True
                        if inst.get("type") == "company":
                            is_industry = True
                            if inst.get("display_name"):
                                industry_partners.add(inst.get("display_name"))
        if is_external:
            lab_dict["collaboration"]["external_papers"] += 1
        if is_industry:
            lab_dict["collaboration"]["industry_papers"] += 1

    lab_dict["collaboration"]["industry_partners"] = list(industry_partners)
    return lab_dict

# =========================================================
# [리포트 빌더] A4 1페이지 분량 알찬 TXT 리포트 생성
# =========================================================
def build_txt_report(data_a, data_b, summaries, q_a, q_b):
    prof_a = data_a["professor"]
    prof_b = data_b["professor"]
    partners_a = ", ".join(data_a["collaboration"]["industry_partners"][:5]) or "확인된 기업 파트너 없음"
    partners_b = ", ".join(data_b["collaboration"]["industry_partners"][:5]) or "확인된 기업 파트너 없음"
    today = datetime.now().strftime("%Y-%m-%d")

    return f"""====================================================================
                [LABMATCH] 연구실 1:1 비교 분석 리포트
====================================================================
■ 생성 일자   : {today}
■ 분석 대상   : {prof_a} 연구실  vs  {prof_b} 연구실
■ 데이터 출처 : OpenAlex 공개 학술 DB (최근 100편 / 핵심 지표 2021~2025년)

--------------------------------------------------------------------
1. 연구실 기본 데이터 요약 (실시간 수집 기준)
--------------------------------------------------------------------
[A] {prof_a} 연구실
  - 분석 대상 논문 수 : {data_a['total_papers']}편
  - 외부 협업 논문 수 : {data_a['collaboration']['external_papers']}편
  - 기업 공저 논문 수 : {data_a['collaboration']['industry_papers']}편
  - 주요 파트너 기업  : {partners_a}

[B] {prof_b} 연구실
  - 분석 대상 논문 수 : {data_b['total_papers']}편
  - 외부 협업 논문 수 : {data_b['collaboration']['external_papers']}편
  - 기업 공저 논문 수 : {data_b['collaboration']['industry_papers']}편
  - 주요 파트너 기업  : {partners_b}

--------------------------------------------------------------------
2. 5대 핵심 체감 지표 한 줄 요약
--------------------------------------------------------------------
① 우수 학회·저널 비중 : {summaries[0]}
② 산학·외부 협업 비율 : {summaries[1]}
③ 학제 간 융합도      : {summaries[2]}
④ 연구실 규모·사수    : {summaries[3]}
⑤ 연구 산출 연속성    : {summaries[4]}

--------------------------------------------------------------------
3. 향후 액션 플랜: 교수님 면담 및 컨택 가이드
--------------------------------------------------------------------
▶ {prof_a} 교수님 면담 시 추천 질문
  "{q_a}"

▶ {prof_b} 교수님 면담 시 추천 질문
  "{q_b}"

▶ 컨택 전 예비 대학원생 체크리스트
  [ ] 두 연구실의 최근 2년 대표 논문 1~2편 초록 읽어보기
  [ ] 연구실 공식 홈페이지에서 모집 공고 및 랩미팅 일정 확인하기
  [ ] 위 추천 질문을 바탕으로 교수님/재학생 컨택 메일 초안 작성하기

--------------------------------------------------------------------
4. 데이터 해석 시 유의사항
--------------------------------------------------------------------
- 본 리포트는 OpenAlex 공개 논문 메타데이터를 기반으로 자동 산출되었습니다.
- 논문으로 이어지지 않은 비공개 산학 과제나 홈페이지에만 기재된 구성원 정보는
  반영되지 않을 수 있으므로 반드시 공식 홈페이지 및 면담을 통해 교차 확인하세요.
====================================================================
* Generated by LABMATCH (예비 대학원생을 위한 연구실 1:1 비교 플랫폼)
"""

# =========================================================
# 기본 페이지 설정 및 Session State 초기화
# =========================================================
st.set_page_config(page_title="LABMATCH", layout="wide")
st.markdown(
    """<style>
    .stTextInput label p { font-size: 18px !important; font-weight: bold !important; }
    .stTextInput input { font-size: 20px !important; height: 55px !important; }
    div.stButton > button, div.stDownloadButton > button { background-color: #F8FAFC !important; height: 54px !important; border-radius: 8px !important; }
    div.stButton > button *, div.stDownloadButton > button * { color: #000000 !important; font-size: 17px !important; font-weight: 800 !important; }
    </style>""",
    unsafe_allow_html=True
)

if "step" not in st.session_state:
    st.session_state.step = 1
for k in ["query_a", "query_b", "summary_1", "summary_2", "summary_3", "summary_4", "summary_5"]:
    if k not in st.session_state:
        st.session_state[k] = ""
for k in ["cands_a", "cands_b"]:
    if k not in st.session_state:
        st.session_state[k] = []
for k in ["data_a", "data_b"]:
    if k not in st.session_state:
        st.session_state[k] = None

# =========================================================
# [공통 상단 바] 3개의 팝업 메뉴 (11/25 수정 사항 반영)
# =========================================================
top_spacer, top_btn1, top_btn2, top_btn3 = st.columns([4.5, 1.9, 1.9, 1.7])
with top_btn1:
    with st.popover("📊 5대 체감 지표 안내", use_container_width=True):
        st.markdown(
            "| 지표명 | 이용자 관점 질문 | 기준 및 시각화 안내 |\n"
            "|---|---|---|\n"
            "| **1. 우수 학회·저널 비중** | 주요 학회·저널 게재 빈도 | 2021~2025년 · 도넛 차트 + 피라미드 |\n"
            "| **2. 산학·외부 협업 비율** | 기업 과제 or 학술 연구 중심? | 2021~2025년 · 타 기관·기업 공저 및 랩 주도 비율 |\n"
            "| **3. 학제 간 융합도** | 타 전공 출신 적응 가능성 |2021-2023 vs 2024-2025 · 생키 다이어그램 |\n"
            "| **4. 연구실 규모·사수** | 질문할 사수·동료 규모 | 진한 아이콘(사수 후보) + 연한 아이콘(일반 구성원) |\n"
            "| **5. 연구 산출 연속성** | 논문이 꾸준히 나오는가? | 2021~2025년 · 신호등 배지 + 월별 잔디 달력 |"
        )
with top_btn2:
    with st.popover("⚠️ 분석 시 주의 사항", use_container_width=True):
        st.markdown(
            "- **저자 식별:** 글로벌 DB 특성상 동명이인이 혼재하여 소속 기관 교차 검증 단계를 거칩니다.\n"
            "- **영문 원칙:** 영문 검색이 원칙이나, 연세대 DB에 등록된 교수진은 한글 자동 매핑을 지원합니다.\n"
            "- **분석 범위:** 쾌적한 시연을 위해 최근 논문 100편(핵심 지표는 2021~2025년 기준)으로 제한했습니다."
        )
with top_btn3:
    with st.popover("🦅 연세대 연구자 리스트", use_container_width=True):
        st.markdown("**[📌 단과대 및 학과별 명단 검색]**")
        col_c, col_d = st.columns(2)
        with col_c:
            selected_college = st.selectbox("단과대학 선택", list(PROF_DB_TREE.keys()))
        with col_d:
            selected_dept = st.selectbox("학과 선택", list(PROF_DB_TREE[selected_college].keys()))
        st.divider()
        st.markdown(f"**💡 {selected_dept} 교수진** (클릭 시 이름 복사 가능)")
        for prof in PROF_DB_TREE[selected_college][selected_dept]:
            st.code(f"{prof['name']} ({prof['eng']})", language="text")

# =========================================================
# [STEP 1] 검색어 입력 및 핫 트렌드 대시보드
# =========================================================
if st.session_state.step == 1:
    st.write("\n\n")
    _, center_col, _ = st.columns([1.5, 5, 1.5])
    with center_col:
        st.markdown("<h1 style='text-align: center; font-size: 60px; margin-bottom: 0px;'>🔬 LABMATCH</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 18px; color: #94A3B8; margin-bottom: 35px;'>예비 대학원생을 위한 연구실 1:1 체감 지표 비교 플랫폼</p>", unsafe_allow_html=True)

        lab_a_input = st.text_input("첫 번째 교수님 성함 입력", value=st.session_state.query_a, placeholder="예: 황도식 또는 Fei-Fei Li (한글/영문 가능)")
        lab_b_input = st.text_input("두 번째 교수님 성함 입력", value=st.session_state.query_b, placeholder="예: Yann LeCun (한글/영문 가능)")
        st.write("\n")

        if st.button("🔍 동명이인 확인 및 교수님 검색", use_container_width=True):
            if not lab_a_input.strip() or not lab_b_input.strip():
                st.error("⚠️ 교수님 성함을 모두 입력해 주세요!")
            else:
                query_a_eng = PROF_NAME_MAP.get(lab_a_input.strip(), lab_a_input.strip())
                query_b_eng = PROF_NAME_MAP.get(lab_b_input.strip(), lab_b_input.strip())
                st.session_state.query_a = query_a_eng
                st.session_state.query_b = query_b_eng
                with st.spinner("글로벌 DB에서 해당하는 학자들을 찾고 있습니다..."):
                    st.session_state.cands_a = search_author_candidates(query_a_eng)
                    st.session_state.cands_b = search_author_candidates(query_b_eng)
                st.session_state.step = 2
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <style>
        .dashboard-box { background-color: #F8FAFC; border-radius: 10px; border: 1px solid #e2e8f0; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px; overflow: hidden; }
        .ticker-wrap, .ticker-wrap-tall { overflow: hidden; position: relative; cursor: pointer; -webkit-mask-image: linear-gradient(to bottom, transparent, black 15%, black 85%, transparent); mask-image: linear-gradient(to bottom, transparent, black 15%, black 85%, transparent); }
        .ticker-wrap { height: 90px; }
        .ticker-wrap-tall { height: 220px; }
        .ticker-content { text-align: center; color: #334155; font-size: 14.5px; font-weight: 600; line-height: 2.0; position: absolute; width: 100%; }
        .anim-y { animation: scrollUpY 12s linear infinite; }
        .ticker-wrap:hover .anim-y { animation-play-state: paused; }
        @keyframes scrollUpY { 0% { top: 100%; transform: translateY(0); } 100% { top: 0; transform: translateY(-100%); } }
        .anim-ai { animation: scrollUpAI 20s linear infinite; }
        .ticker-wrap-tall:hover .anim-ai { animation-play-state: paused; }
        @keyframes scrollUpAI { 0% { top: 100%; transform: translateY(0); } 100% { top: 0; transform: translateY(-100%); } }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="dashboard-box">
            <h4 style="margin-top:0px; margin-bottom: 10px; color:#1F2937; text-align:center;">🦅 연세대학교 연구자 리스트 기반 추천 명단</h4>
            <div class="ticker-wrap"><div class="ticker-content anim-y">
                🚀 [OpenAlex 실시간 연동] DB 매핑 현황 (마우스를 올리면 멈춥니다)<br>
                ⭐️ 공과대학: 손광훈 (전기전자공학부)<br>
                ⭐️ 인공지능융합대학: 함범섭 (인공지능학과) / 황도식 (인공지능학과)<br>
                ⭐️ 문과대학 (문헌정보학): 송민 / 김기영 / 주영준 / 이지연 / 김성언<br>
                💡 상단 '연세대 연구자 리스트'에서 이름을 복사하여 검색창에 붙여넣으세요!
            </div></div>
        </div>
        """, unsafe_allow_html=True)

        hot_col1, hot_col2 = st.columns(2)
        with hot_col1:
            st.markdown("""
            <div class="dashboard-box" style="height: 290px;">
                <h4 style="margin-top:0px; margin-bottom: 10px; color:#1F2937; text-align:center;">🔥 글로벌 AI 트렌드 리서치</h4>
                <div class="ticker-wrap-tall"><div class="ticker-content anim-ai">
                    요즘 가장 핫한 글로벌 AI 연구자들을 비교해 보세요!<br><br>
                    🤖 <strong>Sam Altman</strong> (OpenAI)<br>AGI & LLM 생태계<br><br>
                    🧬 <strong>Demis Hassabis</strong> (Google DeepMind)<br>AlphaFold & AI for Science<br><br>
                    🧠 <strong>Geoffrey Hinton</strong> (Univ. of Toronto)<br>Neural Networks & AI 안전성<br><br>
                    👁️ <strong>Fei-Fei Li</strong> (Stanford Univ)<br>Computer Vision & 인간 중심 AI<br><br>
                    ⚙️ <strong>Yann LeCun</strong> (Meta AI)<br>Self-Supervised Learning<br><br>
                    🚀 <strong>Andrej Karpathy</strong> (Eureka Labs)<br>AI Education & 자율주행<br><br>
                    💡 영어 이름을 그대로 검색창에 입력해 보세요!
                </div></div>
            </div>
            """, unsafe_allow_html=True)

        with hot_col2:
            st.markdown("""
            <div class="dashboard-box" style="height: 290px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h4 style="margin-top:0px; color:#1F2937;">🌐 OpenAlex 인기 학문 분야</h4>
                    <p style="font-size:13px; color:#4B5563; margin-bottom:5px;">글로벌 논문 DB에서 가장 활발히 인용되는 최상위 분야입니다.</p>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;">
                        <span style="background:#E5E7EB; padding: 4px 8px; border-radius: 4px; font-size:12px; font-weight:bold; color:#374151;">Computer Science</span>
                        <span style="background:#E5E7EB; padding: 4px 8px; border-radius: 4px; font-size:12px; font-weight:bold; color:#374151;">Medicine</span>
                        <span style="background:#E5E7EB; padding: 4px 8px; border-radius: 4px; font-size:12px; font-weight:bold; color:#374151;">Materials Science</span>
                    </div>
                </div>
                <hr style="margin: 15px 0; border-top: 1px dashed #CBD5E1;">
                <div>
                    <h4 style="margin-top:0px; color:#1F2937;">🚀 2026 급부상 융합 연구 키워드</h4>
                    <p style="font-size:13px; color:#4B5563; margin-bottom:5px;">랩매치가 주목하는 차세대 학제 간 융합 테마입니다.</p>
                    <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px;">
                        <span style="color:#2563EB; font-size:13px; font-weight:bold;">#Bio_Informatics</span>
                        <span style="color:#059669; font-size:13px; font-weight:bold;">#Climate_Tech</span>
                        <span style="color:#D97706; font-size:13px; font-weight:bold;">#Quantum_AI</span>
                        <span style="color:#7C3AED; font-size:13px; font-weight:bold;">#Neuro_Symbolic</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# [STEP 2] 동명이인 걸러내기
# =========================================================
elif st.session_state.step == 2:
    st.title("🔎 정확한 교수님을 선택해 주세요 (동명이인 방지)")
    st.caption("OpenAlex DB에서 검색된 학자들입니다. 소속 대학을 확인하고 올바른 교수님을 선택하세요.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"1️⃣ '{st.session_state.query_a}' 검색 결과")
        if not st.session_state.cands_a:
            st.error("💡 **검색 결과가 없습니다.** 영문 스펠링을 확인 후 다시 입력해 보세요.")
            sel_a = None
        else:
            options_a = {c["id"]: f"{c['name']} (소속: {c['institution']} / 논문 {c['works_count']}편)" for c in st.session_state.cands_a}
            sel_a = st.radio("교수님을 선택하세요:", options=list(options_a.keys()), format_func=lambda x: options_a[x])

    with col2:
        st.subheader(f"2️⃣ '{st.session_state.query_b}' 검색 결과")
        if not st.session_state.cands_b:
            st.error("💡 **검색 결과가 없습니다.** 영문 스펠링을 확인 후 다시 입력해 보세요.")
            sel_b = None
        else:
            options_b = {c["id"]: f"{c['name']} (소속: {c['institution']} / 논문 {c['works_count']}편)" for c in st.session_state.cands_b}
            sel_b = st.radio("교수님을 선택하세요:", options=list(options_b.keys()), format_func=lambda x: options_b[x], key="radio_b")

    st.divider()
    btn_prev, btn_next = st.columns(2)
    with btn_prev:
        if st.button("⬅️ 다시 검색하기", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with btn_next:
        if st.button("🚀 선택한 교수님으로 지표 분석 시작", use_container_width=True):
            if sel_a and sel_b:
                name_a = [c["name"] for c in st.session_state.cands_a if c["id"] == sel_a][0]
                name_b = [c["name"] for c in st.session_state.cands_b if c["id"] == sel_b][0]
                with st.spinner("선택하신 교수님의 최근 100편 논문을 수집해 분석 중입니다..."):
                    st.session_state.data_a = fetch_openalex_lab_data_by_id(sel_a, name_a)
                    st.session_state.data_b = fetch_openalex_lab_data_by_id(sel_b, name_b)
                st.session_state.step = 3
                st.rerun()

# =========================================================
# [STEP 3] 5대 핵심 체감 지표 분석 (한 줄 요약 자동 수집)
# =========================================================
elif st.session_state.step == 3:
    data_a, data_b = st.session_state.data_a, st.session_state.data_b
    st.title("📊 5대 핵심 체감 지표 비교")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "① 우수 학회·저널 비중",
        "② 산학·외부 협업 비율",
        "③ 학제 간 융합도",
        "④ 연구실 규모·사수",
        "⑤ 연구 산출 연속성"
    ])

    with tab1:
        try:
            res_1 = render_toptier(data_a, data_b)
            if isinstance(res_1, dict) and res_1.get("summary"):
                st.session_state.summary_1 = res_1["summary"]
            elif isinstance(res_1, dict) and "lab_a" in res_1:
                st.session_state.summary_1 = (
                    f"{data_a['professor']} 연구실 {res_1['lab_a']['n_top']}편 vs "
                    f"{data_b['professor']} 연구실 {res_1['lab_b']['n_top']}편 게재 (2021~2025년 기준)."
                )
        except Exception as e:
            st.error(f"지표 1 오류: {e}")

    with tab2:
        try:
            res_2 = render_industry_collab(data_a, data_b)
            if isinstance(res_2, dict) and res_2.get("summary"):
                st.session_state.summary_2 = res_2["summary"]
            else:
                st.session_state.summary_2 = "2021~2025년 기준 타 기관·기업 공저 및 연구실 주도 산학 비율 비교 완료."
        except Exception as e:
            st.error(f"지표 2 오류: {e}")

    with tab3:
        try:
            res_3 = render_interdisciplinarity({"lab_A": data_a, "lab_B": data_b})
            if isinstance(res_3, dict) and res_3.get("summary"):
                st.session_state.summary_3 = res_3["summary"]
            else:
                st.session_state.summary_3 = "초기 3년(2021-2023) 대비 최근 2년(2024-2025) 연구 분야 비중 변화 분석 완료."
        except Exception as e:
            st.error(f"지표 3 오류: {e}")

    with tab4:
        try:
            res_4 = render_lab_size(data_a, data_b)
            if isinstance(res_4, dict) and res_4.get("summary"):
                st.session_state.summary_4 = res_4["summary"]
            else:
                st.session_state.summary_4 = "교수와 2편 이상 공저한 사수 후보 및 일반 구성원 규모·협업 스타일 비교 완료."
        except Exception as e:
            st.error(f"지표 4 오류: {e}")

    with tab5:
        try:
            res_5 = render_continuity([data_a, data_b])
            if isinstance(res_5, dict) and res_5.get("summary"):
                st.session_state.summary_5 = res_5["summary"]
            else:
                st.session_state.summary_5 = "2021~2025년 공백 연도 유무 및 최근 2년 산출 추세 신호등 판정 완료."
        except Exception as e:
            st.error(f"지표 5 오류: {e}")

    st.divider()
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ 동명이인 선택으로 돌아가기", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_next:
        if st.button("📌 최종 A4 요약 리포트 다운로드 ➡️", use_container_width=True):
            st.session_state.step = 4
            st.rerun()

# =========================================================
# [STEP 4] A4 1페이지 요약 리포트 다운로드 (TXT 전용)
# =========================================================
elif st.session_state.step == 4:
    st.title("📌 랩매치 최종 비교 리포트")
    data_a, data_b = st.session_state.data_a, st.session_state.data_b
    prof_a, prof_b = data_a["professor"], data_b["professor"]
    st.caption(f"분석 대상: **{prof_a} 연구실** vs **{prof_b} 연구실** (OpenAlex 2021~2025년 기준)")
    st.divider()

    summaries = [
        st.session_state.summary_1 or "우수 학회·저널 비중 데이터 산출 완료.",
        st.session_state.summary_2 or "산학·외부 협업 비율 데이터 산출 완료.",
        st.session_state.summary_3 or "초기 3년(2021~2023) 대비 최근 2년(2024~2025) 분야 비중 변화 분석 완료.",
        st.session_state.summary_4 or "사수 후보(2편 이상 공저) 및 일반 구성원 규모 비교 완료.",
        st.session_state.summary_5 or "2021~2025년 공백 연도 및 산출 추세 판정 완료."
    ]

    # 1. 5대 핵심 지표 한 줄 요약
    st.subheader("📊 1. 5대 핵심 지표 한 줄 요약")
    with st.container(border=True):
        st.markdown(f"- **① 우수 학회·저널 비중:** {summaries[0]}")
        st.markdown(f"- **② 산학·외부 협업 비율:** {summaries[1]}")
        st.markdown(f"- **③ 학제 간 융합도:** {summaries[2]}")
        st.markdown(f"- **④ 연구실 규모·사수:** {summaries[3]}")
        st.markdown(f"- **⑤ 연구 산출 연속성:** {summaries[4]}")

    # 2. 면담 가이드 (접기/펼치기 + 원클릭 복사 UI)
    q_a = "최근 발표된 논문과 협업 실적이 인상적입니다. 신입생 합류 시 기존 과제 배정과 1저자 연구 기회가 어떻게 주어지는지 궁금합니다."
    q_b = "연구실의 산출 흐름과 구성원 협업 구조가 궁금합니다. 신입생이 적응할 때 사수(선배) 멘토링이나 세미나가 어떻게 운영되는지 여쭤보고 싶습니다."

    with st.expander("🗣️ 교수님 면담 시 활용할 추천 질문 보기 (클릭 시 원클릭 복사)", expanded=False):
        q_col1, q_col2 = st.columns(2)
        with q_col1:
            st.markdown(f"**{prof_a} 교수님께**")
            st.code(q_a, language=None)
        with q_col2:
            st.markdown(f"**{prof_b} 교수님께**")
            st.code(q_b, language=None)

    st.divider()

    # 3. A4 1페이지 TXT 리포트 미리보기 및 다운로드
    st.subheader("💾 2. 최종 비교 리포트 내보내기 (TXT)")
    st.caption("실시간 수집 통계, 5대 지표 한 줄 요약, 면담 가이드 및 컨택 전 체크리스트를 A4 1페이지 분량의 TXT 파일로 저장합니다.")

    txt_data = build_txt_report(data_a, data_b, summaries, q_a, q_b)

    with st.expander("📄 다운로드될 TXT 리포트 내용 미리보기", expanded=False):
        st.text(txt_data)

    st.download_button(
        label="📥 TXT 종합 분석 리포트 다운로드",
        data=txt_data.encode("utf-8"),
        file_name=f"LABMATCH_{prof_a}_vs_{prof_b}.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.divider()
    if st.button("⬅️ 지표 화면으로 돌아가기", use_container_width=True):
        st.session_state.step = 3
        st.rerun()
