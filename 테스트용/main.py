import json
import os
from datetime import datetime
from pathlib import Path
import requests
import streamlit as st

from home_page import render_home
from theme import theme_watch
from korean_names import korean_name
from aff_filter import aff_ok
from build_home_snapshot import SUBFIELD_KO

# 조원들이 만든 5개의 지표 화면은 compare_page에서 불러옵니다.
from compare_page import render_confirm, render_compare

# =========================================================
# [데이터베이스] 연세대학교 교수진 목록 (yonsei_profs.json, build_yonsei_db.py로 만듦)
# 교수님마다 OpenAlex ID를 고정해 두어서 이름 검색 때 동명이인·다른 대학 교수가 섞이지 않음
# =========================================================
def load_professor_db():
    db_path = Path(__file__).with_name("yonsei_profs.json")
    try:
        db_tree = json.loads(db_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        db_tree = {}
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


def _has_hangul(text):
    return any("가" <= ch <= "힣" for ch in str(text or ""))


def korean_display_name(query, cand):
    """검색 결과를 한글 이름으로 보여주기 위한 이름 고르기
    1) OpenAlex 이름 표기 중 한글이 검색어와 같으면 그것
    2) 한글로 검색한 경우 검색어
    3) OpenAlex 한글 표기 중 영문 이름과 소리가 맞는 것, 없으면 로마자를 한글로 바꾼 것 (korean_names.py)
    4) 다 아니면 None (영문 그대로 표시)"""
    alts = cand.get("alt_ko") or []
    if query in alts:
        return query
    if _has_hangul(query):
        return query
    return korean_name(cand.get("name") or "", alts)[0]


YONSEI_OA_ID = "I193775966"  # OpenAlex의 연세대학교 기관 ID


@st.cache_data(show_spinner=False, ttl=3600)
def search_author_candidates(query_name, yonsei_only=False):
    """OpenAlex 저자 검색 (yonsei_only=True면 연세대 소속 이력이 있는 사람만)"""
    extra = {"filter": f"affiliations.institution.id:{YONSEI_OA_ID}"} if yonsei_only else {}
    resp = requests.get(
        "https://api.openalex.org/authors",
        params={"search": query_name, "per-page": 5, **extra, **_openalex_params()},
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
        # 카드에 붙일 연구 분야: 저자의 주요 토픽에서 세부 분야(subfield)를 순서대로 최대 3개 (첫 번째가 주 분야)
        tags = []
        for t in author.get("topics") or []:
            sub = (t.get("subfield") or {}).get("display_name")
            if sub and sub not in tags:
                tags.append(sub)
            if len(tags) >= 3:
                break
        candidates.append({
            "id": author["id"],
            "name": author["display_name"],
            "institution": inst,
            "works_count": author.get("works_count", 0),
            "tags": tags,
            # OpenAlex가 따로 모아 둔 이름 표기 중 한글이 들어 있는 것 (예: 김민석)
            "alt_ko": [n for n in author.get("display_name_alternatives") or [] if _has_hangul(n)],
        })
    return candidates

YEARS = (2021, 2025)  # 지표 계산 기간 (최근 완전 연도 5년)


def _short(aid):
    return str(aid).rsplit("/", 1)[-1]


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_openalex_lab_data_by_id(author_id, author_name, yonsei_only=False, kw=None, col_kw=""):
    """교수님의 2021~2025년 논문 전부 (예전에는 최근 100편만 불러와서 논문이 많은 분은 5년치가 잘렸음)
    author_id: OpenAlex ID 하나, 또는 한 사람이 여러 프로필로 나뉜 경우 'A1|A2'
    yonsei_only: 연세대 교수 목록에서 고른 분은 연세대 소속으로 쓴 논문만 (OpenAlex가 동명이인 논문을 합쳐 둔 경우를 걸러냄)"""
    ids = [_short(x) for x in str(author_id).split("|") if x]
    full_ids = {"https://openalex.org/" + x for x in ids}
    author_id = "https://openalex.org/" + ids[0]
    raw_works, cursor = [], "*"
    for _ in range(10):  # 200편씩 최대 2,000편
        resp = requests.get(
            "https://api.openalex.org/works",
            params={"filter": f"author.id:{'|'.join(ids)},publication_year:{YEARS[0]}-{YEARS[1]}",
                    "sort": "publication_year:desc", "per-page": 200, "cursor": cursor, **_openalex_params()},
            timeout=30,
        )
        resp.raise_for_status()
        page = resp.json()
        raw_works += page.get("results", [])
        cursor = (page.get("meta") or {}).get("next_cursor")
        if not cursor or not page.get("results"):
            break

    def mine(w):
        """교수님 본인 저자 칸: 나뉜 프로필 ID를 대표 ID 하나로 맞춤 (팀원 지표 코드가 ID 하나로 교수님을 찾음)"""
        me = None
        for a in w.get("authorships") or []:
            if (a.get("author") or {}).get("id") in full_ids:
                a["author"] = {**a["author"], "id": author_id}
                me = me or a
        return me

    def at_yonsei(w, me):
        insts = [i.get("id") for i in (me or {}).get("institutions") or []]
        if insts:
            return any(_short(i) == YONSEI_OA_ID for i in insts if i)
        # 본인 소속이 비어 있으면 공저자 중 연세대가 있는지로 판단
        return any(_short(i.get("id")) == YONSEI_OA_ID for a in w.get("authorships") or [] for i in a.get("institutions") or [] if i.get("id"))

    kept = []
    for w in raw_works:
        me = mine(w)
        if yonsei_only and not at_yonsei(w, me):
            continue
        if yonsei_only and kw and not aff_ok(me, kw, col_kw):
            continue
        kept.append(w)
    raw_works = kept

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
def _qlines(qs):
    qs = [qs] if isinstance(qs, str) else qs
    return "\n".join(f"  {i}. {q}" for i, q in enumerate(qs, 1))


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
■ 데이터 출처 : OpenAlex 공개 학술 DB (2021~2025년 논문 전체)

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
{_qlines(q_a)}

▶ {prof_b} 교수님 면담 시 추천 질문
{_qlines(q_b)}

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
# 라이트/다크: 브라우저의 실제 테마를 확인해서 색을 고름 (메뉴에서 테마를 바꿔도 바로 따라감)
_DARK = theme_watch()
_BTN = ("#9989F1", "#8A78EE", "#0B0B0D") if _DARK else ("#93BAB5", "#7FA9A3", "#141414")
st.markdown(
    f"""<style>
    /* 비교 화면 버튼: 팀 공통 톤 (라이트 A 세이지 / 다크 A 라벤더) */
    div.stButton > button[kind="primary"] * {{ color:{_BTN[2]}; }}
    div.stButton > button[kind="primary"] {{ background:{_BTN[0]}; border-color:{_BTN[0]}; color:{_BTN[2]}; }}
    div.stButton > button[kind="primary"]:hover {{ background:{_BTN[1]}; border-color:{_BTN[1]}; color:{_BTN[2]}; }}
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
# [STEP 1] 첫 화면: 이름 검색 + A·B 비교함 + 학과·분야 둘러보기
# =========================================================
def _yonsei_first(cands):
    """연세대 DB에서 고른 교수님은 연세대 소속 후보가 맨 위에 오도록 정렬"""
    return sorted(cands, key=lambda c: "Yonsei" not in (c.get("institution") or ""))


def _fill_yonsei_works(person):
    """학과 목록에서 담은 연세대 교수님에게 OpenAlex 전체 논문 수 붙이기 (실패하면 그대로 둠)"""
    if not person or person.get("oa_id") or person.get("works") is not None or not person.get("eng"):
        return person
    try:
        hit = _yonsei_pick(person["eng"], person.get("dept"))
    except Exception:
        return person
    if hit:
        person = {**person, "works": hit.get("works_count") or 0, "works_label": "전체 논문",
                  "tags": person.get("tags") or [SUBFIELD_KO.get(t, t) for t in hit.get("tags", [])]}
    return person


_PROFILE_CACHE = {}  # 영문 이름 → {"works", "tags"} (성공한 것만 저장, 실패하면 다음 접속 때 다시 시도)


def _yonsei_pick(eng, dept=None):
    """연세대 교수님에 가장 맞는 OpenAlex 저자 (본인확인 화면에서 미리 골라 두는 사람과 같음). 없으면 None"""
    cands = _candidates_for({"name": eng, "eng": eng, "school": "연세대", "dept": dept}) if dept else \
        [c for c in search_author_candidates(eng) if "Yonsei" in (c.get("institution") or "")]
    return cands[0] if cands else None


def _yonsei_profile(eng, dept=None):
    """연세대 교수님 한 분의 OpenAlex 전체 논문 수와 주요 연구 분야(세부 분야 최대 3개)"""
    if eng in _PROFILE_CACHE:
        return _PROFILE_CACHE[eng]
    hit = _yonsei_pick(eng, dept)
    prof = {"works": hit.get("works_count") or 0, "tags": [SUBFIELD_KO.get(t, t) for t in hit.get("tags", [])]} if hit else {}
    _PROFILE_CACHE[eng] = prof
    return prof


def yonsei_profiles(db_tree):
    """학과 둘러보기 카드에 붙일 연구 분야·논문 수. 사용량 한도(429)에 걸리면 받은 만큼만 씀"""
    out = {}
    for depts in db_tree.values():
        for dept, profs in depts.items():
            for p in profs:
                if not p.get("eng"):
                    continue
                try:
                    out[p["name"]] = _yonsei_profile(p["eng"], dept)
                except Exception:
                    return out  # 한도에 걸렸으면 나머지는 다음에
    return out


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
    if person.get("school") != "연세대" or not person.get("dept"):
        return _yonsei_first(search_author_candidates(query))
    # 학과 목록에서 담은 연세대 교수님: 연세대 소속 이력이 있는 사람을 먼저 찾고,
    # 연구 분야가 학과와 맞는 사람 → 최근 소속이 연세대인 사람 → 논문이 많은 사람 순으로 고름
    try:
        yon = search_author_candidates(query, yonsei_only=True)
    except Exception:
        yon = []
    seen = {c["id"] for c in yon}
    pool = yon + [c for c in search_author_candidates(query) if c["id"] not in seen]
    dept = person["dept"].removesuffix("학부").removesuffix("과")
    def score(c):
        tags_ko = [SUBFIELD_KO.get(t, t) for t in c.get("tags", [])]
        fit = any(t and (t in dept or dept in t) for t in tags_ko)
        return (not fit, "Yonsei" not in (c.get("institution") or ""), c["id"] not in seen, -(c.get("works_count") or 0))
    return sorted(pool, key=score)[:5]


if st.session_state.step == 1:
    event = render_home(
        PROF_DB_TREE, st.session_state.home_slots, st.session_state.home_search, st.session_state.home_notice,
    )

    # 같은 이벤트가 다시 실행될 때 두 번 처리하지 않도록 t(시각)로 구분
    if event and event.get("t") != st.session_state.home_last_event:
        st.session_state.home_last_event = event.get("t")
        kind = event.get("type")
        st.session_state.home_notice = None

        if kind == "slots":
            st.session_state.home_slots = {"A": _fill_yonsei_works(event.get("A")), "B": _fill_yonsei_works(event.get("B"))}
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
                         "tags": [SUBFIELD_KO.get(t, t) for t in c.get("tags", [])],
                         "ko": korean_display_name(q, c)}
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
                        st.session_state.data_a = fetch_openalex_lab_data_by_id(pa["oa_id"], pa["name"], bool(pa.get("yonsei")), pa.get("kw"), pa.get("ckw", ""))
                        st.session_state.data_b = fetch_openalex_lab_data_by_id(pb["oa_id"], pb["name"], bool(pb.get("yonsei")), pb.get("kw"), pb.get("ckw", ""))
                        st.session_state.step = 3
                    else:
                        st.session_state.step = 2
                st.rerun()
            except Exception:
                st.session_state.home_notice = "OpenAlex에서 정보를 불러오지 못했습니다. 잠시 후 다시 시도하세요."
                st.rerun()

# =========================================================
# [STEP 2] 본인 확인 (동명이인)  /  [STEP 3] 비교
# =========================================================
def _go_home(slot):
    """상단 바의 '바꾸기': 그 칸만 비우고 첫 화면으로 (None이면 둘 다 유지)"""
    if slot:
        slots = dict(st.session_state.home_slots)
        slots[slot] = None
        st.session_state.home_slots = slots
    st.session_state.home_notice = None
    st.session_state.step = 1
    st.rerun()


def _with_tags_ko(cands):
    return [{**c, "tags_ko": [SUBFIELD_KO.get(t, t) for t in c.get("tags", [])]} for c in cands]


def _research(slot, query):
    query = (query or "").strip()
    if not query:
        return
    try:
        st.session_state["cands_" + slot.lower()] = _yonsei_first(search_author_candidates(query))
    except Exception:
        st.warning("지금은 OpenAlex 검색이 되지 않아요. 잠시 후 다시 시도하세요.")
        return
    st.rerun()


if st.session_state.step == 2:
    slots = st.session_state.home_slots
    picked = render_confirm(
        slots,
        {"A": _with_tags_ko(st.session_state.cands_a), "B": _with_tags_ko(st.session_state.cands_b)},
        _go_home, _research,
    )
    st.write("")
    ready = picked.get("A") and picked.get("B")
    if st.button("이 두 분으로 비교하기", type="primary", use_container_width=True, disabled=not ready):
        try:
            with st.status("연구실 논문을 모으고 있어요", expanded=True) as status:
                new_slots = dict(slots)
                for slot, cands, key in (("A", st.session_state.cands_a, "data_a"), ("B", st.session_state.cands_b, "data_b")):
                    c = next(x for x in cands if x["id"] == picked[slot])
                    person = slots.get(slot) or {}
                    name = person.get("name") or c["name"]
                    st.write(f"LAB {slot} {name} 교수님 2021~2025년 논문 불러오는 중")
                    yon = bool(person.get("yonsei")) and c["id"] == person.get("oa_id")
                    st.session_state[key] = fetch_openalex_lab_data_by_id(c["id"], name, yon, person.get("kw") if yon else None, person.get("ckw", ""))
                    new_slots[slot] = {**person, "oa_id": c["id"], "inst": c.get("institution")}
                st.write("다섯 가지 지표 계산 중")
                status.update(label="준비됐어요", state="complete")
            st.session_state.home_slots = new_slots
            st.session_state.step = 3
            st.rerun()
        except Exception:
            st.error("OpenAlex에서 논문을 불러오지 못했어요. 잠시 후 다시 시도하세요.")

elif st.session_state.step >= 3:
    if not (st.session_state.data_a and st.session_state.data_b):
        st.session_state.step = 1
        st.rerun()
    render_compare(
        st.session_state.home_slots, st.session_state.data_a, st.session_state.data_b,
        _go_home, build_txt_report, demo=st.session_state.get("lmc_demo", False),
    )
