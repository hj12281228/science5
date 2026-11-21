"""
첫 화면 '분야별 국내 연구자'에 쓰는 home_fields.json을 만드는 스크립트

실행:  python build_home_snapshot.py            (같은 폴더에 home_fields.json 생성)
       OPENALEX_API_KEY=... python build_home_snapshot.py   (API 키가 있으면 사용)

무엇을 세나 (모두 OpenAlex, 국내 기관 = institutions.country_code:kr)
- 분야(26개): 최근 3년 국내 기관 논문 수와, 그 전 3년 대비 증가율
- 세부 분야: 분야마다 논문이 많은 세부 분야 상위 N개
- 연구자: 세부 분야마다 최근 3년 국내 기관 논문이 많은 연구자 (최근 소속이 국내 기관인 사람만)

OpenAlex 사용량 한도가 있어서, 받아온 응답은 .openalex_cache/ 에 저장해 두고
중간에 멈춰도 다시 실행하면 이어서 진행합니다.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

import requests

HERE = Path(__file__).parent
CACHE = HERE / ".openalex_cache"
BASE = "https://api.openalex.org"

WINDOW = (2023, 2025)
PREV = (2020, 2022)

FIELD_KO = {
    "Agricultural and Biological Sciences": "농업·생물학", "Arts and Humanities": "인문·예술",
    "Biochemistry, Genetics and Molecular Biology": "생화학·분자생물학", "Business, Management and Accounting": "경영·회계",
    "Chemical Engineering": "화학공학", "Chemistry": "화학", "Computer Science": "컴퓨터과학",
    "Decision Sciences": "의사결정과학", "Earth and Planetary Sciences": "지구과학", "Economics, Econometrics and Finance": "경제·금융",
    "Energy": "에너지", "Engineering": "공학", "Environmental Science": "환경과학", "Immunology and Microbiology": "면역·미생물학",
    "Materials Science": "재료과학", "Mathematics": "수학", "Medicine": "의학", "Neuroscience": "신경과학", "Nursing": "간호학",
    "Pharmacology, Toxicology and Pharmaceutics": "약학", "Physics and Astronomy": "물리·천문학", "Psychology": "심리학",
    "Social Sciences": "사회과학", "Veterinary": "수의학", "Dentistry": "치의학", "Health Professions": "보건학",
}
DOMAIN_KO = {"Physical Sciences": "자연·공학", "Life Sciences": "생명과학", "Health Sciences": "보건·의학", "Social Sciences": "인문·사회"}
SUBFIELD_KO = {
    "Artificial Intelligence": "인공지능", "Computer Vision and Pattern Recognition": "컴퓨터비전",
    "Information Systems": "정보시스템", "Computer Networks and Communications": "컴퓨터 네트워크", "Hardware and Architecture": "하드웨어",
    "Software": "소프트웨어", "Signal Processing": "신호처리", "Human-Computer Interaction": "인간-컴퓨터 상호작용",
    "Computational Theory and Mathematics": "계산 이론", "Computer Science Applications": "컴퓨터 응용", "Computer Graphics and Computer-Aided Design": "그래픽스·CAD",
    "Library and Information Sciences": "문헌정보학", "Education": "교육학", "Sociology and Political Science": "사회학·정치학",
    "Communication": "커뮤니케이션", "Geography, Planning and Development": "지리·도시계획", "Public Administration": "행정학",
    "Law": "법학", "Linguistics and Language": "언어학", "Transportation": "교통", "Health (social science)": "보건사회",
    "Electrical and Electronic Engineering": "전기전자공학", "Mechanical Engineering": "기계공학", "Biomedical Engineering": "의공학",
    "Civil and Structural Engineering": "토목·구조공학", "Control and Systems Engineering": "제어·시스템", "Industrial and Manufacturing Engineering": "산업공학",
    "Aerospace Engineering": "항공우주공학", "Ocean Engineering": "해양공학", "Building and Construction": "건축·시공", "Safety, Risk, Reliability and Quality": "안전·신뢰성",
    "Biomaterials": "생체재료", "Electronic, Optical and Magnetic Materials": "전자·광학 소재", "Polymers and Plastics": "고분자",
    "Materials Chemistry": "재료화학", "Surfaces, Coatings and Films": "표면·박막", "Metals and Alloys": "금속·합금", "Ceramics and Composites": "세라믹·복합재",
    "Organic Chemistry": "유기화학", "Inorganic Chemistry": "무기화학", "Physical and Theoretical Chemistry": "물리화학", "Analytical Chemistry": "분석화학",
    "Molecular Biology": "분자생물학", "Cancer Research": "암 연구", "Genetics": "유전학", "Cell Biology": "세포생물학", "Biotechnology": "생명공학",
    "Oncology": "종양학", "Cardiology and Cardiovascular Medicine": "심장내과", "Surgery": "외과", "Radiology, Nuclear Medicine and Imaging": "영상의학",
    "Neurology": "신경과", "Psychiatry and Mental health": "정신건강의학", "Public Health, Environmental and Occupational Health": "보건·환경의학",
    "Endocrinology, Diabetes and Metabolism": "내분비·대사", "Gastroenterology": "소화기내과", "Infectious Diseases": "감염내과",
    "Clinical Psychology": "임상심리", "Social Psychology": "사회심리", "Experimental and Cognitive Psychology": "인지심리", "Developmental and Educational Psychology": "발달·교육심리",
    "Applied Psychology": "응용심리", "Marketing": "마케팅", "Strategy and Management": "경영전략", "Management Information Systems": "경영정보",
    "Finance": "재무", "Economics and Econometrics": "경제학", "Renewable Energy, Sustainability and the Environment": "재생에너지",
    "Energy Engineering and Power Technology": "에너지공학", "Fuel Technology": "연료", "Condensed Matter Physics": "응집물질물리",
    "Atomic and Molecular Physics, and Optics": "원자·광학", "Nuclear and High Energy Physics": "핵·입자물리", "Statistical and Nonlinear Physics": "통계물리",
    "Applied Mathematics": "응용수학", "Statistics and Probability": "통계학", "Pollution": "오염", "Ecology": "생태학",
}


def _params(extra):
    key = os.environ.get("OPENALEX_API_KEY")
    return {**extra, **({"api_key": key} if key else {})}


def get(path, **params):
    """응답을 디스크에 저장해 두고 같은 요청은 다시 보내지 않음 (API 키는 캐시 이름에 넣지 않음)"""
    CACHE.mkdir(exist_ok=True)
    name = hashlib.sha1((path + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    f = CACHE / f"{name}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    for attempt in range(4):
        r = requests.get(BASE + path, params=_params(params), timeout=40)
        if r.status_code == 429:
            print("  OpenAlex 사용량 한도에 걸렸어요. 한도가 풀린 뒤 다시 실행하면 이어서 진행합니다.", file=sys.stderr)
            sys.exit(2)
        if r.ok:
            data = r.json()
            f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            time.sleep(0.12)
            return data
        time.sleep(2 * (attempt + 1))
    r.raise_for_status()


def short(oa_id):
    return (oa_id or "").rsplit("/", 1)[-1]


def kr(years):
    return f"institutions.country_code:kr,publication_year:{years[0]}-{years[1]}"


def group(filter_, by):
    return {short(g["key"]): g for g in get("/works", filter=filter_, group_by=by, **{"per-page": 200}).get("group_by", [])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-subfields", type=int, default=5, help="분야마다 연구자를 뽑을 세부 분야 수")
    ap.add_argument("--per-subfield", type=int, default=14, help="세부 분야마다 남길 연구자 수")
    ap.add_argument("--out", default=str(HERE / "home_fields.json"))
    args = ap.parse_args()

    fields_meta = get("/fields", **{"per-page": 50})["results"]
    now = group(kr(WINDOW), "primary_topic.field.id")
    prev = group(kr(PREV), "primary_topic.field.id")
    total = sum(g["count"] for g in now.values()) or 1

    out_fields = []
    for i, fm in enumerate(sorted(fields_meta, key=lambda x: -now.get(short(x["id"]), {}).get("count", 0))):
        fid = short(fm["id"])
        works = now.get(fid, {}).get("count", 0)
        before = prev.get(fid, {}).get("count", 0)
        growth = (works / before - 1) if before else None
        en = fm["display_name"]
        print(f"[{i + 1}/{len(fields_meta)}] {en}: {works}편")

        subs_now = group(f"{kr(WINDOW)},primary_topic.field.id:{fid}", "primary_topic.subfield.id")
        subs_prev = group(f"{kr(PREV)},primary_topic.field.id:{fid}", "primary_topic.subfield.id")
        subs = []
        for rank, (sid, g) in enumerate(sorted(subs_now.items(), key=lambda kv: -kv[1]["count"])):
            s_en = g.get("key_display_name") or sid
            b = subs_prev.get(sid, {}).get("count", 0)
            sub = {"id": sid, "en": s_en, "ko": SUBFIELD_KO.get(s_en, s_en), "works": g["count"],
                   "growth": (g["count"] / b - 1) if b else None, "researchers": []}
            if rank < args.max_subfields:
                authors = group(f"{kr(WINDOW)},primary_topic.subfield.id:{sid}", "authorships.author.id")
                top = sorted(authors.items(), key=lambda kv: -kv[1]["count"])[:50]
                ids = [aid for aid, _ in top if aid.startswith("A")]
                if ids:
                    info = get("/authors", filter=f"openalex:{'|'.join(ids)},last_known_institutions.country_code:kr",
                               select="id,display_name,last_known_institutions", **{"per-page": 50})["results"]
                    keep = {short(a["id"]): a for a in info}
                    for aid, g2 in top:
                        a = keep.get(aid)
                        if not a:
                            continue
                        inst = next((x.get("display_name") for x in (a.get("last_known_institutions") or []) if x.get("country_code") in ("KR", "kr")), None)
                        sub["researchers"].append({"oa_id": "https://openalex.org/" + aid, "name": a["display_name"], "inst": inst, "works": g2["count"]})
                        if len(sub["researchers"]) >= args.per_subfield:
                            break
            subs.append(sub)

        domain_en = (fm.get("domain") or {}).get("display_name", "")
        out_fields.append({"id": fid, "en": en, "ko": FIELD_KO.get(en, en), "domain": DOMAIN_KO.get(domain_en, domain_en),
                           "works": works, "prev": before, "growth": growth, "subfields": subs})

    # 칩에 먼저 보여줄 분야: 국내 논문 비중 1.5% 이상인 분야 중 증가율 상위 8개
    big = [f for f in out_fields if f["works"] / total >= 0.015 and f["growth"] is not None]
    featured = [f["id"] for f in sorted(big, key=lambda f: -f["growth"])[:8]]

    snap = {"generated": date.today().strftime("%Y년 %m월"), "window": list(WINDOW), "prev": list(PREV),
            "featured": featured, "fields": out_fields}
    Path(args.out).write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    print("저장:", args.out)


if __name__ == "__main__":
    main()
