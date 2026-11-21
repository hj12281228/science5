import json
import os
from datetime import datetime
from pathlib import Path
import requests
import streamlit as st

from home_page import render_home
from build_home_snapshot import SUBFIELD_KO

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
        try:
            db_path.write_text(json.dumps(default_db, ensure_ascii=False, indent=4), encoding="utf-8")
        except OSError:
            pass
    else:
        default_db = None

    # 여러 사용자가 동시에 접속하면 파일을 쓰는 도중에 읽을 수 있어서, 읽기 실패 시 기본값을 씁니다.
    try:
        db_tree = json.loads(db_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        db_tree = default_db or {}
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
def _openalex_params():
    """Streamlit secrets나 환경 변수에 OPENALEX_API_KEY가 있으면 함께 보냅니다 (없어도 동작)."""
    key = os.environ.get("OPENALEX_API_KEY")
    try:
        key = st.secrets.get("OPENALEX_API_KEY", key)
    except Exception:
        pass
    return {"api_key": key} if key else {}


@st.cache_data(show_spinner=False, ttl=3600)
def search_author_candidates(query_name):
    resp = requests.get(
        "https://api.openalex.org/authors",
        params={"search": query_name, "per-page": 5, **_openalex_params()},
        timeout=20,
    )
    resp.raise_for_status()  # 사용량 한도(429) 등 실패한 응답은 캐시에 남기지 않음
    res = resp.json()
    candidates = []
    for author in res.get("results", []):
        inst = "소속 정보 없음"
        insts = author.get("last_known_institutions") or []
        if insts:
            inst = insts[0].get("display_name") or inst
        elif author.get("last_known_institution"):
            inst = author["last_known_institution"].get("display_name", "소속 정보 없음")
        # 카드에 붙일 연구 분야 태그: 저자의 주요 토픽에서 세부 분야(subfield)를 순서대로 최대 2개
        tags = []
        for t in author.get("topics") or []:
            sub = (t.get("subfield") or {}).get("display_name")
            if sub and sub not in tags:
                tags.append(sub)
            if len(tags) >= 2:
                break
        candidates.append({
            "id": author["id"],
            "name": author["display_name"],
            "institution": inst,
            "works_count": author.get("works_count", 0),
            "tags": tags,
        })
    return candidates

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_openalex_lab_data_by_id(author_id, author_name):
    resp = requests.get(
        "https://api.openalex.org/works",
        params={"filter": f"author.id:{author_id}", "sort": "publication_year:desc", "per-page": 100, **_openalex_params()},
        timeout=30,
    )
    resp.raise_for_status()
    works_res = resp.json()
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

        loc = w.get("primary_location") or {}
        src = loc.get("source") or {}
        venue_name = src.get("display_name", "")
        venue_type = src.get("type", "")
        source_impact = (src.get("summary_stats") or {}).get("2yr_mean_citedness")

        lab_dict["toptier_papers"].append({
            "title": w.get("title", ""),
            "year": year,
            "venue": venue_name,
            "venue_type": venue_type,
            "type": w.get("type", ""),
            "url": w.get("id", ""),
            "citation_normalized_percentile": w.get("citation_normalized_percentile"),
            "2yr_mean_citedness": source_impact
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
if "home_slots" not in st.session_state:
    st.session_state.home_slots = {"A": None, "B": None}
if "home_search" not in st.session_state:
    st.session_state.home_search = None
if "home_last_event" not in st.session_state:
    st.session_state.home_last_event = None
if "home_notice" not in st.session_state:
    st.session_state.home_notice = None

# =========================================================
# [공통 상단 바] 3개의 팝업 메뉴 (11/25 수정 사항 반영)
# =========================================================
# 첫 화면에서는 컴포넌트 안의 '이용 안내' 팝업으로 대신합니다.
if st.session_state.step != 1:
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
# [STEP 1] 첫 화면: 이름 검색 + A·B 비교함 + 학과·분야 둘러보기
# =========================================================
def _yonsei_first(cands):
    """연세대 DB에서 고른 교수님은 연세대 소속 후보가 맨 위에 오도록 정렬"""
    return sorted(cands, key=lambda c: "Yonsei" not in (c.get("institution") or ""))


def _candidates_for(person):
    """비교함에 담긴 사람을 동명이인 확인용 후보 목록으로 바꾸기"""
    if person.get("oa_id"):
        return [{
            "id": person["oa_id"],
            "name": person["name"],
            "institution": person.get("aff") or "소속 정보 없음",
            "works_count": person.get("works") or 0,
        }]
    query = person.get("eng") or PROF_NAME_MAP.get(person["name"], person["name"])
    return _yonsei_first(search_author_candidates(query))


if st.session_state.step == 1:
    event = render_home(
        PROF_DB_TREE, st.session_state.home_slots, st.session_state.home_search, st.session_state.home_notice
    )

    # 같은 이벤트가 다시 실행될 때 두 번 처리하지 않도록 t(시각)로 구분
    if event and event.get("t") != st.session_state.home_last_event:
        st.session_state.home_last_event = event.get("t")
        kind = event.get("type")
        st.session_state.home_notice = None

        if kind == "slots":
            st.session_state.home_slots = {"A": event.get("A"), "B": event.get("B")}
            st.rerun()  # 바뀐 비교함을 화면에 바로 반영

        elif kind == "search":
            q = (event.get("q") or "").strip()
            query = PROF_NAME_MAP.get(q, q)
            try:
                cands = search_author_candidates(query)
                st.session_state.home_search = {
                    "q": q,
                    "results": [
                        {"oa_id": c["id"], "name": c["name"], "inst": c["institution"], "works": c["works_count"],
                         "tags": [SUBFIELD_KO.get(t, t) for t in c.get("tags", [])]}
                        for c in cands
                    ],
                }
            except Exception:
                st.session_state.home_search = {
                    "q": q,
                    "results": [],
                    "error": "지금은 OpenAlex 검색이 되지 않아요. 잠시 후 다시 검색하세요.",
                }
            st.rerun()

        elif kind == "compare" and event.get("A") and event.get("B"):
            pa, pb = event["A"], event["B"]
            st.session_state.home_slots = {"A": pa, "B": pb}
            st.session_state.query_a, st.session_state.query_b = pa["name"], pb["name"]
            try:
                with st.spinner("교수님 정보를 확인하고 있습니다..."):
                    st.session_state.cands_a = _candidates_for(pa)
                    st.session_state.cands_b = _candidates_for(pb)
                    # 두 분 모두 OpenAlex에서 정확히 고른 경우에는 동명이인 확인을 건너뜁니다.
                    if pa.get("oa_id") and pb.get("oa_id"):
                        st.session_state.data_a = fetch_openalex_lab_data_by_id(pa["oa_id"], pa["name"])
                        st.session_state.data_b = fetch_openalex_lab_data_by_id(pb["oa_id"], pb["name"])
                        st.session_state.step = 3
                    else:
                        st.session_state.step = 2
                st.rerun()
            except Exception:
                st.session_state.home_notice = "OpenAlex에서 정보를 불러오지 못했습니다. 잠시 후 다시 시도하세요."
                st.rerun()

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
                try:
                    with st.spinner("선택하신 교수님의 최근 100편 논문을 수집해 분석 중입니다..."):
                        st.session_state.data_a = fetch_openalex_lab_data_by_id(sel_a, name_a)
                        st.session_state.data_b = fetch_openalex_lab_data_by_id(sel_b, name_b)
                except Exception:
                    st.error("OpenAlex에서 논문을 불러오지 못했습니다. 잠시 후 다시 시도하세요.")
                else:
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
