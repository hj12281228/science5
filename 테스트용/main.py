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
    
    name_map = {}
    for college, depts in db_tree.items():
        for dept, profs in depts.items():
            for p in profs:
                name_map[p["name"]] = p["eng"]
                
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
st.markdown(
    """<style>
    .stTextInput label p { font-size: 18px !important; font-weight: bold !important; }
    .stTextInput input { font-size: 20px !important; height: 55px !important; }
    div.stButton > button, div.stDownloadButton > button { background-color: #F8FAFC !important; height: 58px !important; border-radius: 8px !important; }
    div.stButton > button *, div.stDownloadButton > button * { color: #000000 !important; font-size: 19px !important; font-weight: 800 !important; }
    </style>""", unsafe_allow_html=True
)

# 3. Session State 초기화
if "step" not in st.session_state: st.session_state.step = 1
for k in ["query_a", "query_b", "summary_1", "summary_2"]:
    if k not in st.session_state: st.session_state[k] = ""
for k in ["cands_a", "cands_b"]:
    if k not in st.session_state: st.session_state[k] = []
for k in ["data_a", "data_b"]:
    if k not in st.session_state: st.session_state[k] = None

# =========================================================
# [공통 상단 바] 3개의 팝업 메뉴 
# =========================================================
top_spacer, top_btn1, top_btn2, top_btn3 = st.columns([4.5, 1.9, 1.9, 1.7])
with top_btn1:
    with st.popover("📊 5대 체감 지표 안내", use_container_width=True):
        st.markdown("| 지표명 | 이용자 관점 질문 | 화면 시각화 안내 |\n|---|---|---|\n| **1. 탑티어 비중** | 유명 학회/저널 게재 빈도 | 🏆 도넛형 차트 + 피라미드 |\n| **2. 산학/외부 협업** | 기업 과제 or 학술 연구 중심? | 📊 막대 그래프 + 태그 |\n| **3. 학제 간 융합도** | 타 전공 출신 적응 가능성 | 🔗 생키 다이어그램 |\n| **4. 연구실 규모** | 연구실 사수 인원 수 | 👥 아이콘 그리드 |\n| **5. 산출 연속성** | 논문이 꾸준히 나오는가? | 🚦 신호등 배지 + 꺾은선 |")
with top_btn2:
    with st.popover("⚠️ 분석 시 주의 사항", use_container_width=True):
        st.markdown("- **저자 식별:** 글로벌 DB 특성상 동명이인이 혼재하여 소속 기관 교차 검증 단계를 거칩니다.\n- **영문 원칙:** 기계 번역 오차를 막고자 영문 검색이 원칙이나, 연세대 DB는 자동 매핑을 지원합니다.\n- **속도 제한:** 쾌적한 분석을 위해 최근 논문 100편으로 범위를 제한했습니다.")
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

        # 💡 예시(Placeholder)에서 문헌정보학과 교수님 제외하고 가장 안전한 두 분으로 교체
        lab_a_input = st.text_input("첫 번째 교수님 성함 입력", value=st.session_state.query_a, placeholder="예: 손광훈 (한글/영문 모두 가능)")
        lab_b_input = st.text_input("두 번째 교수님 성함 입력", value=st.session_state.query_b, placeholder="예: 함범섭 (한글/영문 모두 가능)")
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
        .dashboard-box {
            background-color: #F8FAFC;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            padding: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            overflow: hidden;
        }
        .ticker-wrap, .ticker-wrap-tall {
            overflow: hidden;
            position: relative;
            cursor: pointer;
            -webkit-mask-image: linear-gradient(to bottom, transparent, black 15%, black 85%, transparent);
            mask-image: linear-gradient(to bottom, transparent, black 15%, black 85%, transparent);
        }
        .ticker-wrap { height: 90px; }
        .ticker-wrap-tall { height: 220px; }
        
        .ticker-content {
            text-align: center;
            color: #334155;
            font-size: 14.5px;
            font-weight: 600;
            line-height: 2.0;
            position: absolute;
            width: 100%;
        }
        
        .anim-y { animation: scrollUpY 12s linear infinite; }
        .ticker-wrap:hover .anim-y { animation-play-state: paused; }
        @keyframes scrollUpY {
            0% { top: 100%; transform: translateY(0); }
            100% { top: 0; transform: translateY(-100%); }
        }
        
        .anim-ai { animation: scrollUpAI 20s linear infinite; }
        .ticker-wrap-tall:hover .anim-ai { animation-play-state: paused; }
        @keyframes scrollUpAI {
            0% { top: 100%; transform: translateY(0); }
            100% { top: 0; transform: translateY(-100%); }
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="dashboard-box">
            <h4 style="margin-top:0px; margin-bottom: 10px; color:#1F2937; text-align:center;">🦅 연세대학교 연구자 리스트 기반 추천 명단</h4>
            <div class="ticker-wrap">
                <div class="ticker-content anim-y">
                    🚀 [OpenAlex 실시간 연동] DB 매핑 현황 (마우스를 올리면 멈춥니다)<br>
                    ⭐️ 공과대학: 손광훈 (전기전자공학부)<br>
                    ⭐️ 인공지능융합대학: 함범섭 (인공지능학과) / 황도식 (인공지능학과)<br>
                    ⭐️ 문과대학 (문헌정보학): 송민 / 김기영 / 주영준 / 이지연 / 김성언<br>
                    💡 상단 '연세대 연구자 리스트'에서 이름을 복사하여 검색창에 붙여넣으세요!
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        hot_col1, hot_col2 = st.columns(2)
        with hot_col1:
            st.markdown("""
            <div class="dashboard-box" style="height: 290px;">
                <h4 style="margin-top:0px; margin-bottom: 10px; color:#1F2937; text-align:center;">🔥 글로벌 AI 트렌드 리서치</h4>
                <div class="ticker-wrap-tall">
                    <div class="ticker-content anim-ai">
                        요즘 가장 핫한 글로벌 AI 연구자들을 비교해 보세요!<br><br>
                        🤖 <strong>Sam Altman</strong> (OpenAI)<br>AGI & LLM 생태계<br><br>
                        🧬 <strong>Demis Hassabis</strong> (Google DeepMind)<br>AlphaFold & AI for Science<br><br>
                        🧠 <strong>Geoffrey Hinton</strong> (Univ. of Toronto)<br>Neural Networks & AI 안전성<br><br>
                        👁️ <strong>Fei-Fei Li</strong> (Stanford Univ)<br>Computer Vision & 인간 중심 AI<br><br>
                        ⚙️ <strong>Yann LeCun</strong> (Meta AI)<br>Self-Supervised Learning<br><br>
                        🚀 <strong>Andrej Karpathy</strong> (Eureka Labs)<br>AI Education & 자율주행<br><br>
                        💡 영어 이름을 그대로 검색창에 입력해 보세요!
                    </div>
                </div>
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
# [STEP 2] 동명이인 걸러내기 및 에러 친절 피드백
# =========================================================
elif st.session_state.step == 2:
    st.title("🔎 정확한 교수님을 선택해 주세요 (동명이인 방지)")
    st.caption("OpenAlex DB에서 검색된 학자들입니다. 소속 대학을 확인하고 올바른 교수님을 선택하세요.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"1️⃣ '{st.session_state.query_a}' 검색 결과")
        if not st.session_state.cands_a:
            st.error("💡 **검색 결과가 없습니다.**\n\n- 논문에 기재된 공식 영문 스펠링과 다를 수 있습니다.\n- 구글 스칼라 등에서 정확한 영문 성함을 확인 후 다시 입력해 보세요.")
            sel_a = None
        else:
            options_a = {c["id"]: f"{c['name']} (소속: {c['institution']} / 논문 {c['works_count']}편)" for c in st.session_state.cands_a}
            sel_a = st.radio("교수님을 선택하세요:", options=list(options_a.keys()), format_func=lambda x: options_a[x])

    with col2:
        st.subheader(f"2️⃣ '{st.session_state.query_b}' 검색 결과")
        if not st.session_state.cands_b:
            st.error("💡 **검색 결과가 없습니다.**\n\n- 논문에 기재된 공식 영문 스펠링과 다를 수 있습니다.\n- 구글 스칼라 등에서 정확한 영문 성함을 확인 후 다시 입력해 보세요.")
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
# [STEP 3] 5대 핵심 체감 지표 분석
# =========================================================
elif st.session_state.step == 3:
    data_a, data_b = st.session_state.data_a, st.session_state.data_b
    st.title("📊 5대 핵심 체감 지표 비교")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["① 탑티어 비중", "② 산학/외부 협업", "③ 학제 간 융합도", "④ 연구실 규모·사수", "⑤ 연구 산출 연속성"])
    
    with tab1: 
        try:
            res_1 = render_toptier(data_a, data_b)
            n_top_a = res_1["lab_a"]["n_top"]
            n_top_b = res_1["lab_b"]["n_top"]
            st.session_state.summary_1 = f"{data_a['professor']} 연구실은 최근 {n_top_a}편, {data_b['professor']} 연구실은 {n_top_b}편의 탑티어 논문을 게재했습니다."
        except Exception as e: st.error(f"지표 1 오류: {e}")
    with tab2:
        try:
            res_2 = render_industry_collab(data_a, data_b)
            st.session_state.summary_2 = res_2.get("summary", "")
        except Exception as e: st.error(f"지표 2 오류: {e}")
    with tab3:
        try: render_interdisciplinarity({"lab_A": data_a, "lab_B": data_b})
        except Exception as e: st.error(f"지표 3 오류: {e}")
    with tab4:
        try: render_lab_size(data_a, data_b)
        except Exception as e: st.error(f"지표 4 오류: {e}")
    with tab5:
        try: render_continuity([data_a, data_b])
        except Exception as e: st.error(f"지표 5 오류: {e}")

    st.divider()
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ 동명이인 선택으로 돌아가기", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_next:
        if st.button("📌 최종 Visual Brief 리포트 다운로드 ➡️", use_container_width=True):
            st.session_state.step = 4
            st.rerun()

# =========================================================
# [STEP 4] 리포트 다운로드 (PDF 오류 해결)
# =========================================================
elif st.session_state.step == 4:
    st.title("📌 최종 비교 리포트 다운로드")
    st.divider()

    st.subheader("💡 맞춤형 Visual Brief")
    st.success(
        f"1. **연구 역량:** {st.session_state.summary_1}\n"
        "2. **연구실 규모:** 구체적인 인원과 협업 방식을 데이터로 확인했습니다.\n"
        f"3. **산학/외부 협업:** {st.session_state.summary_2 if st.session_state.summary_2 else '데이터 산출 완료'}\n"
    )

    st.divider()
    st.markdown("**📂 다운로드 파일 포맷 안내**")
    st.caption("기존에 PDF나 HWP 형식을 선택했을 때 파일이 깨지거나 열리지 않던 현상을 해결하기 위해, 텍스트가 완벽하게 호환되는 순수 텍스트(TXT)와 마크다운(MD) 형식으로 지원 포맷을 최적화했습니다.")
    
    col_fmt, col_dl = st.columns([1, 2])
    with col_fmt: 
        file_format = st.selectbox("파일 형식", ["TXT (일반 텍스트)", "MD (마크다운 포맷)"])
    
    ext = "txt" if "TXT" in file_format else "md"
    report_content = f"# LABMATCH 최종 리포트\n\n## 1. 요약 결과\n- {st.session_state.summary_1}\n- {st.session_state.summary_2}\n\n## 2. 면담 질문 가이드\n- 사수 배정 및 프로젝트 진행 방식 확인\n- 신입생 연구 주제 선정 자율성 확인"
    
    with col_dl:
        st.write("")
        st.download_button(f"📄 {ext.upper()} 리포트 다운로드", data=report_content.encode("utf-8"), file_name=f"labmatch_report.{ext}", use_container_width=True)

    st.divider()
    if st.button("⬅️ 지표 화면으로 돌아가기", use_container_width=True):
        st.session_state.step = 3
        st.rerun()
