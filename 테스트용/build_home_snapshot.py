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
    # 이름 검색 결과 태그에도 쓰는 세부 분야 (OpenAlex subfield 이름)
    "Management, Monitoring, Policy and Law": "환경 관리·정책", "Environmental Engineering": "환경공학", "Environmental Chemistry": "환경화학",
    "Global and Planetary Change": "기후·지구 변화", "Nature and Landscape Conservation": "자연 보전", "Water Science and Technology": "수자원",
    "Waste Management and Disposal": "폐기물 관리", "Health, Toxicology and Mutagenesis": "환경독성", "Atmospheric Science": "대기과학",
    "Oceanography": "해양학", "Geology": "지질학", "Geophysics": "지구물리", "Earth-Surface Processes": "지표 환경", "Space and Planetary Science": "우주·행성과학",
    "Astronomy and Astrophysics": "천문학", "Instrumentation": "계측", "Radiation": "방사선", "Acoustics and Ultrasonics": "음향",
    "Mathematical Physics": "수리물리", "Numerical Analysis": "수치해석", "Algebra and Number Theory": "대수·정수론", "Geometry and Topology": "기하·위상",
    "Discrete Mathematics and Combinatorics": "이산수학", "Modeling and Simulation": "모델링·시뮬레이션", "Computational Mathematics": "계산수학",
    "Control and Optimization": "제어·최적화", "Management Science and Operations Research": "경영과학", "Information Systems and Management": "정보시스템 관리",
    "Statistics, Probability and Uncertainty": "통계·불확실성", "Mechanics of Materials": "재료역학", "Computational Mechanics": "계산역학",
    "Fluid Flow and Transfer Processes": "유체·열전달", "Catalysis": "촉매", "Process Chemistry and Technology": "공정화학",
    "Filtration and Separation": "분리공정", "Bioengineering": "생물공학", "Spectroscopy": "분광학", "Electrochemistry": "전기화학",
    "Nuclear Energy and Engineering": "원자력공학", "Automotive Engineering": "자동차공학", "Architecture": "건축학", "Urban Studies": "도시학",
    "Media Technology": "미디어 기술", "Biochemistry": "생화학", "Molecular Medicine": "분자의학",
    "Physiology": "생리학", "Developmental Biology": "발생생물학", "Structural Biology": "구조생물학", "Clinical Biochemistry": "임상생화학",
    "Microbiology": "미생물학", "Immunology": "면역학", "Virology": "바이러스학", "Parasitology": "기생충학", "Applied Microbiology and Biotechnology": "응용미생물",
    "Plant Science": "식물학", "Animal Science and Zoology": "동물학", "Food Science": "식품과학", "Agronomy and Crop Science": "작물학",
    "Aquatic Science": "수생과학", "Forestry": "산림학", "Soil Science": "토양학", "Horticulture": "원예학", "Insect Science": "곤충학",
    "Cellular and Molecular Neuroscience": "세포·분자신경과학", "Cognitive Neuroscience": "인지신경과학", "Behavioral Neuroscience": "행동신경과학",
    "Sensory Systems": "감각신경", "Developmental Neuroscience": "발달신경과학", "Pharmacology": "약리학", "Pharmaceutical Science": "약학",
    "Drug Discovery": "신약 개발", "Toxicology": "독성학", "Pulmonary and Respiratory Medicine": "호흡기내과", "Nephrology": "신장내과",
    "Hematology": "혈액내과", "Rheumatology": "류마티스내과", "Dermatology": "피부과", "Ophthalmology": "안과", "Otorhinolaryngology": "이비인후과",
    "Obstetrics and Gynecology": "산부인과", "Pediatrics, Perinatology and Child Health": "소아청소년과", "Orthopedics and Sports Medicine": "정형외과·스포츠의학",
    "Urology": "비뇨의학", "Anesthesiology and Pain Medicine": "마취통증의학", "Emergency Medicine": "응급의학", "Epidemiology": "역학",
    "Pathology and Forensic Medicine": "병리학", "Rehabilitation": "재활의학", "Geriatrics and Gerontology": "노인의학", "Hepatology": "간질환",
    "Health Policy": "보건정책", "Health Informatics": "의료정보학", "Genetics (clinical)": "임상유전학", "Internal Medicine": "내과", "General Health Professions": "보건의료",
    "Nutrition and Dietetics": "영양학", "Physical Therapy, Sports Therapy and Rehabilitation": "물리치료·재활", "Pharmacy": "약학", "Oral Surgery": "구강외과",
    "Orthodontics": "치과교정", "Periodontics": "치주과", "General Dentistry": "치의학", "Small Animals": "소동물", "Food Animals": "농장동물",
    "Accounting": "회계", "Business and International Management": "국제경영", "Organizational Behavior and Human Resource Management": "조직·인사",
    "Tourism, Leisure and Hospitality Management": "관광·여가", "Management of Technology and Innovation": "기술경영", "General Economics, Econometrics and Finance": "경제·금융",
    "Political Science and International Relations": "정치·국제관계", "Anthropology": "인류학", "Cultural Studies": "문화연구", "Gender Studies": "젠더연구",
    "Demography": "인구학", "Development": "개발학", "Safety Research": "안전 연구", "Archeology": "고고학", "History": "역사학", "Philosophy": "철학",
    "Literature and Literary Theory": "문학", "Music": "음악", "Visual Arts and Performing Arts": "시각·공연예술", "Religious studies": "종교학",
    "Language and Linguistics": "언어학", "Museology": "박물관학", "Neuropsychology and Physiological Psychology": "신경심리", "Psychology (miscellaneous)": "심리학",
    "Nanoscience and Nanotechnology": "나노과학", 
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
