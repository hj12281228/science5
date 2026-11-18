import streamlit as st
import requests
import json
from pathlib import Path

# 조원들이 보내준 5개의 지표 함수 모두 불러오기
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
            "인공지능융합대학": {"인공지능학과": [{"name": "함범섭", "eng": "Bumsub Ham"}, {"name": "황도식", "eng": "Dosik Hwang"}]},
            "공과대학": {"전기전자공학부": [{"name": "손광훈", "eng": "Kwanghoon Sohn"}]},
            "문과대학": {"문헌정보학과": [{"name": "송민", "eng": "Min Song"}, {"name": "김기영", "eng": "Kiyoung Kim"}, {"name": "주영준", "eng": "Youngjoon Joo"}, {"name": "이지연", "eng": "Jiyeon Lee"}, {"name": "김성언", "eng": "Seongeon Kim"}]}
        }
        db_path.write_text(json.dumps(default_db, ensure_ascii=False, indent=4), encoding="utf-8")
    
    db_tree = json.loads(db_path.read_text(encoding="utf-8"))
    name_map = {p["name"]: p["eng"] for college, depts in db_tree.items() for dept, profs in depts.items() for p in profs}
    return db_tree, name_map

PROF_DB_TREE, PROF_NAME_MAP = load_professor_db()

# =========================================================
# [엔진 1, 2] OpenAlex 데이터 수집 (생략 없이 유지)
# =========================================================
@st.cache_data(show_spinner=False, ttl=3600)
def search_author_candidates(query_name):
    search_url = f"https://api.openalex.org/authors?search={query_name}&per-page=5"
    res = requests.get(search_url).json()
    candidates = []
    for author in res.get("results", []):
        inst = "소속 정보 없음"
        if author.get("last_known_institution"): inst = author["last_known_institution"].get("display_name", "소속 정보 없음")
        candidates.append({"id": author["id"], "name": author["display_name"], "institution": inst, "works_count": author.get("works_count", 0)})
    return candidates

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_openalex_lab_data_by_id(author_id, author_name):
    works_url = f"https://api.openalex.org/works?filter=author.id:{author_id}&sort=publication_year:desc&per-page=100"
    works_res = requests.get(works_url).json()
    raw_works = works_res.get("results", [])

    lab_dict = {
        "lab_name": f"{author_name} 연구실", "professor_id": author_id, "professor": author_name,
        "total_papers": len(raw_works), "collaboration": {"external_papers": 0, "industry_papers": 0, "industry_partners": []},
        "works": [], "interdisciplinarity_demo_papers": [], "toptier_papers": []
    }
    industry_partners = set()

    for w in raw_works:
        year = w.get("publication_year")
        pub_date = w.get("publication_date")
        authorships = w.get("authorships", [])

        lab_dict["works"].append({"id": w["id"], "year": year, "publication_year": year, "publication_date": pub_date, "authorships": authorships})
        concepts = [c["display_name"] for c in w.get("concepts", []) if c.get("level", 1) == 0]
        lab_dict["interdisciplinarity_demo_papers"].append({"id": w["id"], "title": w.get("title", ""), "year": year, "field_ids": concepts})

        venue_name = w.get("primary_location", {}).get("source", {})
        venue_name = venue_name.get("display_name", "") if venue_name else ""
        lab_dict["toptier_papers"].append({"title": w.get("title", ""), "year": year, "venue": venue_name, "type": w.get("type", ""), "url": w.get("id", "")})

        is_external, is_industry = False, False
        for auth in authorships:
            if auth["author"]["id"] != author_id:
                for inst in auth.get("institutions", []):
                    if inst.get("id"):
                        is_external = True
                        if inst.get("type") == "company":
                            is_industry = True
                            if inst.get("display_name"): industry_partners.add(inst.get("display_name"))
        if is_external: lab_dict["collaboration"]["external_papers"] += 1
        if is_industry: lab_dict["collaboration"]["industry_papers"] += 1

    lab_dict["collaboration"]["industry_partners"] = list(industry_partners)
    return lab_dict

# 1. 기본 페이지 설정
st.set_page_config(page_title="LABMATCH", layout="wide")
st.markdown("""<style>.stTextInput label p { font-size: 18px !important; font-weight: bold !important; } .stTextInput input { font-size: 20px !important; height: 55px !important; } div.stButton > button, div.stDownloadButton > button { background-color: #F8FAFC !important; height: 58px !important; border-radius: 8px !important; } div.stButton > button *, div.stDownloadButton > button * { color: #000000 !important; font-size: 19px !important; font-weight: 800 !important; }</style>""", unsafe_allow_html=True)

# 3. Session State 초기화 (5개 지표 요약본 모두 추가)
if "step" not in st.session_state: st.session_state.step = 1
for k in ["query_a", "query_b", "summary_1", "summary_2", "summary_3", "summary_4", "summary_5"]:
    if k not in st.session_state: st.session_state[k] = ""
for k in ["cands_a", "cands_b"]:
    if k not in st.session_state: st.session_state[k] = []
for k in ["data_a", "data_b"]:
    if k not in st.session_state: st.session_state[k] = None

# =========================================================
# [STEP 1 & 2] 검색어 입력 및 동명이인 처리 (기존과 동일하여 생략 없이 전체 코드 유지)
# =========================================================
if st.session_state.step == 1:
    st.write("\n\n")
    _, center_col, _ = st.columns([1.5, 5, 1.5])
    with center_col:
        st.markdown("<h1 style='text-align: center; font-size: 60px; margin-bottom: 0px;'>🔬 LABMATCH</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 18px; color: #94A3B8; margin-bottom: 35px;'>예비 대학원생을 위한 연구실 1:1 체감 지표 비교 플랫폼</p>", unsafe_allow_html=True)

        lab_a_input = st.text_input("첫 번째 교수님 성함 입력", value=st.session_state.query_a, placeholder="예: 손광훈")
        lab_b_input = st.text_input("두 번째 교수님 성함 입력", value=st.session_state.query_b, placeholder="예: 함범섭")
        st.write("\n")

        if st.button("🔍 동명이인 확인 및 교수님 검색", use_container_width=True):
            if not lab_a_input.strip() or not lab_b_input.strip():
                st.error("⚠️ 교수님 성함을 모두 입력해 주세요!")
            else:
                query_a_eng = PROF_NAME_MAP.get(lab_a_input.strip(), lab_a_input.strip())
                query_b_eng = PROF_NAME_MAP.get(lab_b_input.strip(), lab_b_input.strip())
                st.session_state.query_a, st.session_state.query_b = query_a_eng, query_b_eng
                with st.spinner("글로벌 DB에서 검색 중..."):
                    st.session_state.cands_a = search_author_candidates(query_a_eng)
                    st.session_state.cands_b = search_author_candidates(query_b_eng)
                st.session_state.step = 2
                st.rerun()
                
elif st.session_state.step == 2:
    st.title("🔎 정확한 교수님을 선택해 주세요")
    col1, col2 = st.columns(2)
    with col1:
        options_a = {c["id"]: f"{c['name']} ({c['institution']})" for c in st.session_state.cands_a}
        sel_a = st.radio("1️⃣ 첫 번째 교수님:", options=list(options_a.keys()), format_func=lambda x: options_a[x]) if st.session_state.cands_a else None
    with col2:
        options_b = {c["id"]: f"{c['name']} ({c['institution']})" for c in st.session_state.cands_b}
        sel_b = st.radio("2️⃣ 두 번째 교수님:", options=list(options_b.keys()), format_func=lambda x: options_b[x], key="rad_b") if st.session_state.cands_b else None

    st.divider()
    btn_prev, btn_next = st.columns(2)
    with btn_prev:
        if st.button("⬅️ 다시 검색"): st.session_state.step = 1; st.rerun()
    with btn_next:
        if st.button("🚀 지표 분석 시작", use_container_width=True):
            if sel_a and sel_b:
                name_a = [c["name"] for c in st.session_state.cands_a if c["id"] == sel_a][0]
                name_b = [c["name"] for c in st.session_state.cands_b if c["id"] == sel_b][0]
                with st.spinner("논문 수집 및 분석 중..."):
                    st.session_state.data_a = fetch_openalex_lab_data_by_id(sel_a, name_a)
                    st.session_state.data_b = fetch_openalex_lab_data_by_id(sel_b, name_b)
                st.session_state.step = 3
                st.rerun()

# =========================================================
# [STEP 3] 5대 핵심 체감 지표 분석 (가상의 요약본 생성 포함)
# =========================================================
elif st.session_state.step == 3:
    data_a, data_b = st.session_state.data_a, st.session_state.data_b
    prof_a, prof_b = data_a['professor'], data_b['professor']
    st.title("📊 5대 핵심 체감 지표 비교")
    
    # 💡 조원들이 만들어줄 요약본을 시뮬레이션(가정)하는 코드
    st.session_state.summary_1 = f"최근 5년간 {prof_a} 연구실은 15편, {prof_b} 연구실은 12편의 탑티어 논문을 게재하여 두 곳 모두 우수합니다."
    st.session_state.summary_2 = f"{prof_a} 연구실은 기업 과제 비중(45%)이 높아 실무 지향적이며, {prof_b} 연구실은 학술 연구(80%)에 집중합니다."
    st.session_state.summary_3 = f"{prof_a} 연구실은 타 학문 융합 논문이 30%로 융합 성향이 강하며, {prof_b} 연구실은 정통 전공에 깊게 파고듭니다."
    st.session_state.summary_4 = f"{prof_a} 연구실은 15명 내외로 대형 랩에 속하며, {prof_b} 연구실은 7명 내외의 소수 정예로 운영됩니다."
    st.session_state.summary_5 = f"두 연구실 모두 매년 3편 이상의 논문을 꾸준히 산출하여 연구 단절 위험(Red Light)이 없는 안전한 연구실입니다."
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["① 탑티어 비중", "② 산학/외부 협업", "③ 학제 간 융합도", "④ 연구실 규모·사수", "⑤ 연구 산출 연속성"])
    with tab1: render_toptier(data_a, data_b)
    with tab2: render_industry_collab(data_a, data_b)
    with tab3: render_interdisciplinarity({"lab_A": data_a, "lab_B": data_b})
    with tab4: render_lab_size(data_a, data_b)
    with tab5: render_continuity([data_a, data_b])

    st.divider()
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ 동명이인 선택으로 돌아가기", use_container_width=True): st.session_state.step = 2; st.rerun()
    with col_next:
        if st.button("📌 최종 요약 리포트 내보내기 ➡️", use_container_width=True): st.session_state.step = 4; st.rerun()

# =========================================================
# [STEP 4] 리포트 다운로드 (5대 지표 요약본 A4 출력)
# =========================================================
elif st.session_state.step == 4:
    st.title("📌 랩매치 종합 분석 리포트")
    st.divider()

    prof_a = st.session_state.data_a['professor']
    prof_b = st.session_state.data_b['professor']

    # 화면에 A4 요약본 미리보기 제공
    st.subheader(f"📊 핵심 지표 요약 (A4 한눈에 보기)")
    st.caption(f"분석 대상: 🔵 {prof_a} 연구실 vs 🔴 {prof_b} 연구실")
    
    with st.container(border=True):
        st.markdown(f"**1️⃣ 연구 역량 (탑티어 비중)**\n> {st.session_state.summary_1}")
        st.markdown(f"**2️⃣ 협업 생태계 (산학/외부 협업)**\n> {st.session_state.summary_2}")
        st.markdown(f"**3️⃣ 학제 간 융합도**\n> {st.session_state.summary_3}")
        st.markdown(f"**4️⃣ 연구실 규모 및 사수**\n> {st.session_state.summary_4}")
        st.markdown(f"**5️⃣ 연구 산출 연속성**\n> {st.session_state.summary_5}")

    st.divider()
    
    st.subheader("💾 맞춤형 리포트 내보내기")
    file_format = st.radio("다운로드 포맷 선택", ["TXT (일반 텍스트)", "MD (마크다운 포맷)"], horizontal=True)
    ext = "txt" if "TXT" in file_format else "md"
    
    # 📝 다운로드될 텍스트 파일 내용 조립
    report_content = f"""# LABMATCH 최종 비교 분석 리포트
분석 일자: 2026년 기준 실시간 OpenAlex 연동 데이터
분석 대상: {prof_a} 교수님 vs {prof_b} 교수님

## 1. 5대 핵심 지표 요약 (Executive Summary)
- [탑티어 비중] {st.session_state.summary_1}
- [산학 협력] {st.session_state.summary_2}
- [학제 간 융합도] {st.session_state.summary_3}
- [연구실 규모] {st.session_state.summary_4}
- [산출 연속성] {st.session_state.summary_5}

## 2. 데이터 기반 맞춤형 면담 질문 가이드
- [{prof_a} 교수님 면담 시]: "대형 랩의 특성상 신입생 과제 배정 방식과 주저자(1저자) 논문 작성 기회가 어떻게 주어지는지 궁금합니다."
- [{prof_b} 교수님 면담 시]: "소수 정예로 운영되는데, 내부에서 사수(선배)와 신입생 간의 멘토링이나 논문 지도가 어떤 체계로 이루어지는지 여쭤보고 싶습니다."

* 본 리포트는 랩매치(LABMATCH) 시스템에 의해 자동 생성되었습니다.
"""

    st.write("")
    st.download_button(
        label=f"📥 {ext.upper()} 형식으로 리포트 다운로드", 
        data=report_content.encode("utf-8"), 
        file_name=f"labmatch_summary_report.{ext}", 
        use_container_width=True
    )

    st.divider()
    if st.button("⬅️ 지표 화면으로 돌아가기", use_container_width=True):
        st.session_state.step = 3
        st.rerun()
