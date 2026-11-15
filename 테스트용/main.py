import streamlit as st
import requests
from pathlib import Path
import time

# 조원들이 보내준 4개의 지표 함수 불러오기
from practice2 import render_industry_collab
from practice3 import render_interdisciplinarity
from practice4 import render_lab_size
from practice5 import render_continuity

# =========================================================
# [핵심 추가] OpenAlex API 실시간 데이터 수집 및 변환 엔진
# =========================================================
@st.cache_data(show_spinner=False, ttl=3600)  # 한 번 검색한 교수는 1시간 동안 캐시(속도 향상)
def fetch_openalex_lab_data(query_name):
    """
    교수님 영문 이름을 검색해 OpenAlex에서 최근 100편의 논문을 가져온 뒤,
    조원들 코드(practice 2~5)가 요구하는 json 구조로 똑같이 조립해주는 함수입니다.
    """
    # 1. 저자 검색 (OpenAlex는 영문 검색이 정확합니다)
    search_url = f"https://api.openalex.org/authors?search={query_name}"
    res = requests.get(search_url).json()
    
    if not res.get("results"):
        return None  # 검색 결과가 없으면 None 반환
    
    author = res["results"][0]  # 가장 관련도 높은 첫 번째 저자 선택
    author_id = author["id"]
    author_name = author["display_name"]

    # 2. 해당 저자의 최근 논문 최대 100편 수집 (속도를 위해 제한)
    works_url = f"https://api.openalex.org/works?filter=author.id:{author_id}&sort=publication_year:desc&per-page=100"
    works_res = requests.get(works_url).json()
    raw_works = works_res.get("results", [])

    # 3. 조원들 코드(practice2~5) 규격에 맞게 빈 데이터 통(dict) 만들기
    lab_dict = {
        "lab_name": f"{author_name} 연구실",
        "professor_id": author_id,
        "professor": author_name,
        "total_papers": len(raw_works),
        "collaboration": {"external_papers": 0, "industry_papers": 0, "industry_partners": []},
        "works": [],
        "interdisciplinarity_demo_papers": []
    }

    industry_partners = set()

    # 4. 수집한 논문을 하나씩 돌면서 지표별 필요 데이터로 분해 및 조립
    for w in raw_works:
        year = w.get("publication_year")
        pub_date = w.get("publication_date")
        authorships = w.get("authorships", [])

        # [지표 4, 5용] 기본 논문 정보
        lab_dict["works"].append({
            "id": w["id"],
            "year": year,
            "publication_year": year,
            "publication_date": pub_date,
            "authorships": authorships
        })

        # [지표 3용] 학제 간 융합도: OpenAlex의 'Concepts(개념)'을 분야(Field)로 사용
        concepts = [c["display_name"] for c in w.get("concepts", []) if c.get("level", 1) == 0]
        lab_dict["interdisciplinarity_demo_papers"].append({
            "id": w["id"],
            "title": w.get("title", ""),
            "year": year,
            "field_ids": concepts
        })

        # [지표 2용] 산학/외부 협업: 나와 다른 기관인지, 기관 타입이 'company'인지 검사
        is_external = False
        is_industry = False
        for auth in authorships:
            if auth["author"]["id"] != author_id:
                for inst in auth.get("institutions", []):
                    if inst.get("id"):
                        is_external = True
                        if inst.get("type") == "company":
                            is_industry = True
                            if inst.get("display_name"):
                                industry_partners.add(inst.get("display_name"))
        
        if is_external: lab_dict["collaboration"]["external_papers"] += 1
        if is_industry: lab_dict["collaboration"]["industry_papers"] += 1

    lab_dict["collaboration"]["industry_partners"] = list(industry_partners)
    
    return lab_dict


# 1. 기본 페이지 설정
st.set_page_config(page_title="LABMATCH", layout="wide")

# 2. 최소 CSS 스타일 (다크모드 환경 기준)
st.markdown(
    """
    <style>
    .stTextInput label p { font-size: 18px !important; font-weight: bold !important; }
    .stTextInput input { font-size: 20px !important; height: 55px !important; }
    div.stButton > button, div.stDownloadButton > button {
        background-color: #F8FAFC !important; height: 58px !important; border-radius: 8px !important;
    }
    div.stButton > button *, div.stDownloadButton > button * {
        color: #000000 !important; font-size: 19px !important; font-weight: 800 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. Session State 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "query_a" not in st.session_state:
    st.session_state.query_a = "Kwanghoon Sohn"  # 영문 검색 유도
if "query_b" not in st.session_state:
    st.session_state.query_b = "Bumsub Ham"
if "data_a" not in st.session_state:
    st.session_state.data_a = None
if "data_b" not in st.session_state:
    st.session_state.data_b = None
if "summary_2" not in st.session_state:
    st.session_state.summary_2 = ""

# =========================================================
# [공통 상단 바]
# =========================================================
top_spacer, top_btn1, top_btn2 = st.columns([6.5, 1.7, 1.8])
with top_btn1:
    with st.popover("📊 체감 지표 안내", use_container_width=True):
        st.write("1. **탑티어 논문 비중**\n2. **산학/외부 협업 비율**\n3. **학제 간 융합도**\n4. **연구실 규모**\n5. **연구 산출 연속성**")
with top_btn2:
    with st.popover("⚠️ 주의 사항", use_container_width=True):
        st.write("• **검색 주의:** OpenAlex는 글로벌 DB이므로 **반드시 교수님의 영문 성함(예: Kwanghoon Sohn)**으로 검색해야 정확합니다.\n• **동명이인:** 영문 이름이 같은 타 연구자의 논문이 섞일 수 있습니다.")

# =========================================================
# [첫 번째 화면] 입력창 및 라이브 데이터 로딩
# =========================================================
if st.session_state.step == 1:
    st.write("\n\n")
    _, center_col, _ = st.columns([1.5, 5, 1.5])
    
    with center_col:
        st.markdown("<h1 style='text-align: center; font-size: 60px; margin-bottom: 0px;'>🔬 LABMATCH</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 18px; color: #94A3B8; margin-bottom: 35px;'>예비 대학원생을 위한 연구실 1:1 체감 지표 비교 플랫폼 (Live OpenAlex)</p>", unsafe_allow_html=True)

        lab_a_input = st.text_input("첫 번째 교수님 영문 성함 입력", value=st.session_state.query_a, placeholder="예: Kwanghoon Sohn")
        lab_b_input = st.text_input("두 번째 교수님 영문 성함 입력", value=st.session_state.query_b, placeholder="예: Bumsub Ham")
        st.write("\n\n")

        if st.button("🚀 5대 핵심 체감 지표 분석 시작하기", use_container_width=True):
            if not lab_a_input.strip() or not lab_b_input.strip():
                st.error("⚠️ 교수님 성함을 모두 입력해 주세요!")
            else:
                st.session_state.query_a = lab_a_input.strip()
                st.session_state.query_b = lab_b_input.strip()
                
                # 로딩 애니메이션 띄우며 API 호출
                with st.spinner("🌐 OpenAlex 글로벌 데이터베이스에서 논문을 실시간으로 수집 및 분석 중입니다. (약 3~5초 소요)..."):
                    data_a = fetch_openalex_lab_data(st.session_state.query_a)
                    data_b = fetch_openalex_lab_data(st.session_state.query_b)
                
                if not data_a:
                    st.error(f"❌ '{st.session_state.query_a}' 교수님을 찾을 수 없습니다. 영문 스펠링을 확인해 주세요.")
                elif not data_b:
                    st.error(f"❌ '{st.session_state.query_b}' 교수님을 찾을 수 없습니다. 영문 스펠링을 확인해 주세요.")
                else:
                    st.session_state.data_a = data_a
                    st.session_state.data_b = data_b
                    st.session_state.step = 2
                    st.rerun()

# =========================================================
# [두 번째 화면] 5대 핵심 체감 지표 탭 (Live 데이터 주입)
# =========================================================
elif st.session_state.step == 2:
    data_a = st.session_state.data_a
    data_b = st.session_state.data_b

    st.title("📊 5대 핵심 체감 지표 비교")
    st.caption(f"비교 대상: **{data_a['professor']}** vs **{data_b['professor']}**")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["① 탑티어 비중", "② 산학/외부 협업", "③ 학제 간 융합도", "④ 연구실 규모·사수", "⑤ 연구 산출 연속성"])

    with tab1:
        st.info("🔧 1번 지표 조원 코드 연결 예정")
    with tab2:
        try:
            res_2 = render_industry_collab(data_a, data_b)
            st.session_state.summary_2 = res_2.get("summary", "")
        except Exception as e:
            st.error(f"지표 2 렌더링 오류: {e}")
    with tab3:
        try:
            render_interdisciplinarity({"lab_A": data_a, "lab_B": data_b})
        except Exception as e:
            st.error(f"지표 3 렌더링 오류: {e}")
    with tab4:
        try:
            render_lab_size(data_a, data_b)
        except Exception as e:
            st.error(f"지표 4 렌더링 오류: {e}")
    with tab5:
        try:
            render_continuity([data_a, data_b])
        except Exception as e:
            st.error(f"지표 5 렌더링 오류: {e}")

    st.divider()
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ 연구실 다시 검색하기", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("📌 최종 Visual Brief 및 면담 질문 보기 ➡️", use_container_width=True):
            st.session_state.step = 3
            st.rerun()

# =========================================================
# [세 번째 화면] Visual Brief 및 리포트 다운로드
# =========================================================
elif st.session_state.step == 3:
    st.title("📌 최종 비교 리포트 & 면담 질문 가이드")
    st.divider()

    st.subheader("💡 맞춤형 Visual Brief")
    st.success(
        "1. **연구실 규모:** 두 연구실의 구성원 수와 사수 환경을 통해 밀착 지도 여부를 파악할 수 있습니다.\n"
        f"2. **산학/외부 협업:** {st.session_state.summary_2 if st.session_state.summary_2 else '데이터 산출 중'}\n"
        "3. **선택 가이드:** 선배와의 폭넓은 협업 vs 1:1 밀착 지도를 실제 데이터를 기반으로 비교해 보세요."
    )

    st.divider()
    col_fmt, col_dl = st.columns([1, 2])
    with col_fmt:
        file_format = st.selectbox("저장할 파일 형식", ["TXT (.txt)", "PDF (.pdf)", "DOCX (.docx)", "HWP (.hwp)"])

    ext_map = {"TXT (.txt)": "txt", "PDF (.pdf)": "pdf", "DOCX (.docx)": "docx", "HWP (.hwp)": "hwp"}
    ext = ext_map[file_format]

    report_content = f"LABMATCH 최종 리포트\n- 요약: {st.session_state.summary_2}"
    
    with col_dl:
        st.write("")
        st.download_button(label=f"📄 {file_format} 형식 다운로드", data=report_content.encode("utf-8"), file_name=f"report.{ext}", use_container_width=True)

    st.divider()
    if st.button("⬅️ 지표 화면으로 돌아가기", use_container_width=True):
        st.session_state.step = 2
        st.rerun()
