import json
import streamlit as st

# 조원들이 보내준 4개의 지표 함수 불러오기
from practice2 import render_industry_collab
from practice3 import render_interdisciplinarity
from practice4 import render_lab_size
from practice5 import render_continuity

# 1. 기본 페이지 설정
st.set_page_config(page_title="LABMATCH", layout="wide")

# 2. 최소한의 필수 스타일만 적용 (공식 다크모드 적용 상태 기준)
st.markdown(
    """
    <style>
    .stTextInput label p { font-size: 18px !important; font-weight: bold !important; }
    .stTextInput input { font-size: 20px !important; height: 55px !important; }
    div.stButton > button, div.stDownloadButton > button {
        background-color: #F8FAFC !important;
        height: 58px !important;
        border-radius: 8px !important;
    }
    div.stButton > button *, div.stDownloadButton > button * {
        color: #000000 !important;
        font-size: 19px !important;
        font-weight: 800 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. 화면 단계 및 동적 요약 데이터 기억 장치
if "step" not in st.session_state:
    st.session_state.step = 1
if "lab_a_name" not in st.session_state:
    st.session_state.lab_a_name = "손광훈 (연세대 DIML)"
if "lab_b_name" not in st.session_state:
    st.session_state.lab_b_name = "함범섭 (연세대 CV Lab)"
if "summary_2" not in st.session_state:
    st.session_state.summary_2 = ""

# 목업 데이터 로드 (모든 조원 코드가 이 데이터를 가져다 씀)
with open("mock_lab_data.json", encoding="utf-8") as f:
    data = json.load(f)

# =========================================================
# [공통 상단 바]
# =========================================================
top_spacer, top_btn1, top_btn2 = st.columns([6.5, 1.7, 1.8])
with top_btn1:
    with st.popover("📊 체감 지표 안내", use_container_width=True):
        st.markdown("### 📌 5대 핵심 체감 지표 선정 및 산정 근거")
        st.write("1. **탑티어 논문 비중:** 질적 연구 역량\n2. **산학/외부 협업 비율:** 기업 및 외부 기관 실무\n3. **학제 간 융합도:** 다양한 분야 융합\n4. **연구실 규모:** 사수 및 지도 환경\n5. **연구 산출 연속성:** 5년간 공백기 유무")
with top_btn2:
    with st.popover("⚠️ 주의 사항", use_container_width=True):
        st.markdown("### ⚠️ 데이터 한계점")
        st.write("OpenAlex 데이터 기반이므로 최신 논문 누락이나 동명이인 혼합 문제가 있을 수 있습니다. 실제 진학 전 교차 확인 바랍니다.")

# =========================================================
# [첫 번째 화면] 검색 및 입력창
# =========================================================
if st.session_state.step == 1:
    st.write("\n\n")
    left_margin, center_col, right_margin = st.columns([1.5, 5, 1.5])
    
    with center_col:
        st.markdown("<h1 style='text-align: center; font-size: 60px; margin-bottom: 0px;'>🔬 LABMATCH</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 18px; color: #94A3B8; margin-bottom: 35px;'>예비 대학원생을 위한 연구실 1:1 체감 지표 비교 플랫폼</p>", unsafe_allow_html=True)

        lab_a_input = st.text_input("첫 번째 연구실 / 교수님 입력", value=st.session_state.lab_a_name)
        lab_b_input = st.text_input("두 번째 연구실 / 교수님 입력", value=st.session_state.lab_b_name)
        st.write("\n\n")

        if st.button("🚀 5대 핵심 체감 지표 분석 시작하기", use_container_width=True):
            if not lab_a_input.strip() or not lab_b_input.strip():
                st.error("⚠️ 비교할 두 연구실 또는 교수님 성함을 모두 입력해 주세요!")
            else:
                st.session_state.lab_a_name = lab_a_input.strip()
                st.session_state.lab_b_name = lab_b_input.strip()
                st.session_state.step = 2
                st.rerun()

# =========================================================
# [두 번째 화면] 5대 핵심 체감 지표 탭 (조원들 코드 통합 구역)
# =========================================================
elif st.session_state.step == 2:
    st.title("📊 5대 핵심 체감 지표 비교")
    st.caption(f"비교 대상: **{st.session_state.lab_a_name}** vs **{st.session_state.lab_b_name}**")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "① 탑티어 비중", "② 산학/외부 협업", "③ 학제 간 융합도", "④ 연구실 규모·사수", "⑤ 연구 산출 연속성"
    ])

    with tab1:
        st.info("🔧 1번 지표 조원 코드 연결 예정 (아직 파일이 없습니다.)")
        
    with tab2:
        try:
            # 2번 지표 (practice2): 두 연구실 dict를 각각 받음
            res_2 = render_industry_collab(data["lab_a"], data["lab_b"])
            # 조원이 짜둔 3줄 요약 문장을 3단계 리포트용으로 빼돌려 저장!
            st.session_state.summary_2 = res_2.get("summary", "")
        except Exception as e:
            st.error(f"지표 2 렌더링 오류: {e}")

    with tab3:
        try:
            # 3번 지표 (practice3): "lab_A", "lab_B" 대문자 키를 요구하는 전체 dict 구조
            render_interdisciplinarity({"lab_A": data["lab_a"], "lab_B": data["lab_b"]})
        except Exception as e:
            st.error(f"지표 3 렌더링 오류: {e}")

    with tab4:
        try:
            # 4번 지표 (practice4): 두 연구실 dict를 각각 받음
            render_lab_size(data["lab_a"], data["lab_b"])
        except Exception as e:
            st.error(f"지표 4 렌더링 오류: {e}")

    with tab5:
        try:
            # 5번 지표 (practice5): dict들을 list로 묶어서 받음
            render_continuity([data["lab_a"], data["lab_b"]])
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
        "1. **연구실 규모:** DIML은 다수의 인원이 협업하며, CV Lab은 소규모 밀착 연구가 두드러집니다.\n"
        f"2. **산학/외부 협업:** {st.session_state.summary_2 if st.session_state.summary_2 else '외부 협업 지표 산출 중입니다.'}\n"
        "3. **선택 가이드:** 선배·동료와의 폭넓은 협업이 중요하다면 DIML을, 1:1 밀착 지도가 우선이라면 CV Lab이 적합합니다."
    )

    st.subheader("💬 내가 고민해 볼 포인트 & 면담 확인 질문")
    st.info(
        "• **규모 측면:** 신입생 입학 시 사수 선배와의 팀 단위 프로젝트 비중 vs 교수님 1:1 지도 비중\n"
        "• **협업 측면:** 기업 과제 참여 기회가 학생의 실무 경험에 어느 정도 연결되는지"
    )

    st.divider()
    st.subheader("📥 비교 리포트 파일 다운로드")

    report_content = (
        f"[LABMATCH 최종 비교 리포트]\n비교 대상: {st.session_state.lab_a_name} vs {st.session_state.lab_b_name}\n\n"
        f"- 요약: {st.session_state.summary_2}\n\n- 면담 추천 질문:\n"
        "1) 사수 배정 및 프로젝트 진행 방식 확인\n2) 신입생 연구 주제 선정 자율성 확인\n"
    )

    col_fmt, col_dl = st.columns([1, 2])
    with col_fmt:
        file_format = st.selectbox("저장할 파일 형식을 선택하세요", ["TXT (.txt)", "PDF (.pdf)", "DOCX (.docx)", "HWP (.hwp)"])

    ext_map = {"TXT (.txt)": ("txt", "text/plain"), "PDF (.pdf)": ("pdf", "application/pdf"), "DOCX (.docx)": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"), "HWP (.hwp)": ("hwp", "application/x-hwp")}
    ext, mime_type = ext_map[file_format]

    with col_dl:
        st.write("")
        st.download_button(
            label=f"📄 {file_format} 형식으로 리포트 다운로드",
            data=report_content.encode("utf-8"), file_name=f"labmatch_report.{ext}", mime=mime_type, use_container_width=True,
        )

    st.divider()
    if st.button("⬅️ 지표 화면으로 돌아가기", use_container_width=True):
        st.session_state.step = 2
        st.rerun()