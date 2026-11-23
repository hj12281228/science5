"""동명이인 거르기: 교수님 본인 저자 칸에 적힌 소속 문자열로 그 논문이 정말 이 교수님 것인지 판단.
OpenAlex는 같은 이름(같은 학교 안에서도)의 논문을 한 프로필에 합쳐 두는 경우가 있음.
예) 문헌정보학과 이지연 교수 프로필에 의과대학 외과 'Jee-Yeon Lee'의 논문이 섞여 있었음.
main.py(비교할 때)와 build_yonsei_db.py(카드의 논문 수·분야)가 같은 규칙을 씀."""
import re

STOP = {"department", "dept", "of", "and", "the", "school", "division", "program", "college", "graduate",
        "interdisciplinary", "major", "in", "for", "studies", "faculty"}
UNIT = ("department", "dept", "division", "school", "college", "graduate", "faculty", "program")
COLLEGE_KW = {"의과대학": "medicine", "치과대학": "dentistry", "간호대학": "nursing", "약학대학": "pharmacy"}


def words(s):
    return re.sub(r"[^a-z0-9 ]", " ", (s or "").lower().replace("&", " and ")).split()


def dept_keywords(dept_en, col_kw=""):
    """영문 학과 이름의 핵심 단어 (예: Department of Library and Information Science → library, information, science)
    의대 'Internal Medicine'처럼 단과대 이름(medicine)이 들어간 경우, 그 단어는 의대 누구에게나 맞으므로 뺌"""
    kw = [w for w in words(dept_en) if w not in STOP and len(w) > 2]
    return [w for w in kw if w != col_kw] or kw


def kw_hit(aff_words, kw):
    """학과 단어가 소속 문자열에 충분히 들어 있는지: 단어가 1~2개면 모두, 3개 이상이면 하나 빼고"""
    need = len(kw) if len(kw) <= 2 else len(kw) - 1
    return bool(kw) and sum(k in aff_words for k in kw) >= need


def aff_ok(me, kw, col_kw=""):
    """me: 교수님 본인 authorship. kw: 학과 핵심 단어들.
    - 소속에 학과 단어가 들어 있으면 본인 논문
    - 의대·치대 등은 단과대 이름만 적은 경우도 본인 논문으로 봄
    - 소속에 '다른' 학과·단과대가 적혀 있으면 동명이인으로 보고 뺌
    - 'Yonsei University'처럼 학교 이름만 있거나 소속이 비어 있으면 그대로 둠"""
    aff = " ".join((me or {}).get("raw_affiliation_strings") or [])
    if not aff.strip() or not kw:
        return True
    w = set(words(aff))
    if kw_hit(w, kw):
        return True
    if col_kw and col_kw in w and not any(u in w for u in ("department", "dept", "division")):
        return True
    return not any(u in w for u in UNIT)
