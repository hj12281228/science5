"""
연세대 교수 목록(yonsei_profs.json) 만들기

1) 연세대 교원정보시스템(fis.yonsei.ac.kr)의 학과별 교원 목록에서 단과대·학과·한글 이름·영문 이름·직위를 모두 가져옴
2) 교수님마다 OpenAlex 저자 ID를 찾음
   - 영문 이름으로 '연세대 소속 논문'을 찾고, 저자 칸에 적힌 이름과 소속 문자열이 맞는 저자만 셈
   - 소속 문자열에 그 교수님 학과 이름(예: Library and Information Science)이 들어 있는 저자 ID만 채택
     → 같은 학교 안의 동명이인(예: 의과대학 'Jee-Yeon Lee')이 섞이지 않음
3) 카드에 보일 최근 5년 논문 수와 많이 쓴 세부 분야 3개를 계산 (비교 화면과 같은 동명이인 거르기 규칙, aff_filter.py)

실행:  python build_yonsei_db.py          (전체, 몇 분 걸림)
      python build_yonsei_db.py 문헌정보   (학과 이름에 '문헌정보'가 들어간 곳만 다시 계산해서 기존 파일에 덮어씀)
OPENALEX_API_KEY 환경 변수가 있으면 씀. 이름 검색은 요청 한 번에 비용이 커서(0.001달러) 앱용 키의 하루 한도를 넘지 않게
키 없이 돌리는 것을 권장 (OPENALEX_API_KEY= python build_yonsei_db.py).

교원정보시스템에 영문 이름이 없거나 OpenAlex에서 못 찾은 분은 oa_ids가 비어 있고, 비교할 때 이름으로 검색함.
교원정보시스템에 없는 분, 자동으로 찾은 ID가 틀린 분은 아래 MANUAL에 적어 두면 그 값을 씀.
"""
import html
import json
import os
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from aff_filter import COLLEGE_KW, aff_ok, dept_keywords, kw_hit, words
from build_home_snapshot import SUBFIELD_KO

YONSEI = "I193775966"
YEARS = (2021, 2025)
FIS = "https://fis.yonsei.ac.kr"
OUT = Path(__file__).with_name("yonsei_profs.json")

# (단과대, 학과 한글 이름, 한글 이름) → 덮어쓸 값. 학과가 교원정보시스템에 없으면 'dept_en'과 함께 새로 추가됨
MANUAL = {
    # 교원정보시스템 학과 목록에는 없지만 문헌정보학과 수업·연구실을 운영하는 분
    ("문과대학", "문헌정보학", "송민"): {"eng": "Min Song", "pos": "교수", "oa_ids": ["A5045749444"],
                                    "dept_en": "Department of Library and Information Science"},
    # 명예특임교수라 학과 목록에서 빠짐
    ("공과대학", "전기전자공학부", "손광훈"): {"eng": "Kwanghoon Sohn", "pos": "명예특임교수", "oa_ids": ["A5073320959", "A5090874091"],
                                        "dept_en": "School of Electrical and Electronic Engineering"},
    # 자동 매칭이 다른 사람을 고른 분 (진짜 프로필에는 의과대학 동명이인 논문이 섞여 있음 → 비교할 때 학과 소속으로 걸러짐)
    ("문과대학", "문헌정보학", "이지연"): {"oa_ids": ["A5004660653", "A5109185097"]},
    # OpenAlex에서 프로필이 여러 개로 나뉜 분 (같은 ORCID)
    ("인공지능융합대학", "인공지능학과", "황도식"): {"oa_ids": ["A5085519704", "A5108218127", "A5124218721", "A5130556430"]},
}


def _get(path, **params):
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        params["api_key"] = key
    for i in range(6):
        r = requests.get("https://api.openalex.org" + path, params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(2 * (i + 1))
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()


# ---------- 1) 교원정보시스템 ----------
def fis_departments():
    """학과 목록: [{col, name('한글 / English'), href}]"""
    s = requests.get(FIS + "/faculty/dep_search.do", timeout=60).text
    out = []
    for box in re.findall(r'<div class="belong-box">(.*?)</dl>', s, re.S):
        # 단과대 이름 뒤에 <br/>영문이 오는 곳과, 줄바꿈 없이 바로 영문이 붙는 곳(예: 교육과학대학College of ...)이 섞여 있음
        col = re.search(r"<dt><span>(.*?)</span>", box, re.S)
        col = html.unescape(re.sub(r"<[^>]+>", " ", col.group(1).split("<br")[0])).strip() if col else ""
        col = (re.match(r"[가-힣·/()\s]+", col) or [col])[0].strip()
        for href, name in re.findall(r'<a [^>]*href="(/faculty/depMember\.do\?[^"]+)"[^>]*>(.*?)</a>', box, re.S):
            out.append({"col": col, "href": html.unescape(href), "name": html.unescape(re.sub(r"<[^>]+>", "", name)).strip()})
    return out


def fis_members(href):
    s = requests.get(FIS + href, timeout=60).text
    out = []
    for box in re.findall(r'<div class="pro-info-box">(.*?)(?=<div class="pro-info-box">|$)', s, re.S):
        m = re.search(r"<dt>.*?<a [^>]*>\s*([^<]+?)\s*<span>(.*?)</span>", box, re.S)
        if not m:
            continue
        ko = html.unescape(m.group(1)).strip()
        en = html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"<!--.*?-->", "", m.group(2), flags=re.S))).strip()
        lines = [l.strip() for l in html.unescape(re.sub(r"<[^>]+>", "\n", re.sub(r"<!--.*?-->", "", box, flags=re.S))).split("\n") if l.strip()]
        pos = next((lines[i + 1] for i, l in enumerate(lines) if l == "/" and i + 1 < len(lines)), "")
        out.append({"ko": ko, "en": en, "pos": pos})
    return out


# ---------- 2) OpenAlex ID 찾기 ----------
def match_ids(eng, kw):
    """영문 이름 + 연세대 소속 논문에서, 이름이 맞고 소속에 학과 단어가 들어간 저자 ID (많이 나온 순)"""
    toks = [t for t in words(eng.replace("-", "")) if t]
    if len(toks) < 2 or not kw:
        return []
    data = _get("/works", filter=f"raw_author_name.search:{' '.join(toks)},institutions.id:{YONSEI}",
                select="id,authorships", sort="publication_year:desc", **{"per-page": 100})
    hits = Counter()
    for w in data.get("results", []):
        for a in w.get("authorships") or []:
            raw = a.get("raw_author_name") or ""
            names, joined = set(words(raw)) | set(words(raw.replace("-", ""))), "".join(words(raw.replace("-", "")))
            if not all(t in names or t in joined for t in toks):
                continue
            aff = " ".join(a.get("raw_affiliation_strings") or [])
            aid = ((a.get("author") or {}).get("id") or "").rsplit("/", 1)[-1]
            if not aid or "yonsei" not in aff.lower():
                continue
            if kw_hit(set(words(aff)), kw):
                hits[aid] += 1
    if hits:
        # 가장 많이 나온 ID와, 그 절반 이상 나온 ID만 (한두 번 우연히 맞은 다른 사람 ID는 버림)
        top = hits.most_common(1)[0][1]
        return [a for a, n in hits.most_common() if n >= max(1, top / 2)][:6]
    return match_ids_by_author_search(eng, kw)


def match_ids_by_author_search(eng, kw):
    """논문 저자 칸 검색으로 못 찾은 경우(예: 'Jee-Yeon Lee'처럼 이름을 나눠 쓴 경우): OpenAlex 저자 검색으로 연세대 이력이 있는
    후보를 받고, 후보마다 연세대 논문의 소속 문자열에 학과 단어가 있는지 확인"""
    name = " ".join(reversed([x.strip() for x in eng.split(",")])) if "," in eng else eng
    cands = _get("/authors", search=name, filter=f"affiliations.institution.id:{YONSEI}", select="id", **{"per-page": 25}).get("results", [])
    out = []
    for c in cands:
        aid = c["id"].rsplit("/", 1)[-1]
        works = _get("/works", filter=f"author.id:{aid},institutions.id:{YONSEI}", select="authorships", **{"per-page": 50}).get("results", [])
        n = 0
        for w in works:
            me = next((a for a in w.get("authorships") or [] if (a.get("author") or {}).get("id") == c["id"]), None)
            aw = set(words(" ".join((me or {}).get("raw_affiliation_strings") or [])))
            n += kw_hit(aw, kw)
        if n:
            out.append((n, aid))
    out.sort(reverse=True)
    return [a for n, a in out if n >= max(1, out[0][0] / 2)][:6] if out else []


# ---------- 3) 카드용 논문 수 · 분야 ----------
def profile(ids, kw, col_kw):
    full = {"https://openalex.org/" + x for x in ids}
    n, tags = 0, Counter()
    for pg in range(1, 11):  # 키 없이는 cursor 넘김이 막혀서 page 번호로
        page = _get("/works", filter=f"author.id:{'|'.join(ids)},publication_year:{YEARS[0]}-{YEARS[1]},institutions.id:{YONSEI}",
                    select="id,authorships,primary_topic", page=pg, **{"per-page": 200})
        for w in page.get("results", []):
            me = next((a for a in w.get("authorships") or [] if (a.get("author") or {}).get("id") in full), None)
            if not aff_ok(me, kw, col_kw):
                continue
            n += 1
            sub = ((w.get("primary_topic") or {}).get("subfield") or {}).get("display_name")
            if sub:
                tags[sub] += 1
        if len(page.get("results", [])) < 200:
            break
    return n, [SUBFIELD_KO.get(k, k) for k, _ in tags.most_common(3)]


def build_person(col, dept_ko, dept_en, m):
    over = MANUAL.get((col, dept_ko, m["ko"]), {})
    eng = over.get("eng") or m["en"]
    col_kw = COLLEGE_KW.get(col, "")
    kw = dept_keywords(dept_en, col_kw)
    item = {"name": m["ko"], "eng": eng, "pos": over.get("pos") or m.get("pos", ""), "oa_ids": [], "works": None, "tags": [],
            "kw": kw, "ckw": col_kw}
    try:
        ids = over.get("oa_ids") or match_ids(eng, kw)
        if ids:
            item["oa_ids"] = ids
            item["works"], item["tags"] = profile(ids, kw, col_kw)
    except Exception as e:  # 한 분이 실패해도 나머지는 계속
        print("실패:", m["ko"], e)
    return col, dept_ko, item


def main(only=None):
    depts = fis_departments()
    jobs = []
    seen = set()
    for d in depts:
        ko, _, en = d["name"].partition("/")
        ko, en = ko.strip(), (en or ko).strip()
        if only and only not in ko:
            continue
        for m in fis_members(d["href"]):
            jobs.append((d["col"], ko, en, m)); seen.add((d["col"], ko, m["ko"]))
    for (col, ko, name), over in MANUAL.items():
        if (col, ko, name) not in seen and "dept_en" in over and (not only or only in ko):
            jobs.append((col, ko, over["dept_en"], {"ko": name, "en": over.get("eng", ""), "pos": over.get("pos", "")}))
    print(len(jobs), "명")
    tree = json.loads(OUT.read_text(encoding="utf-8")) if only and OUT.exists() else {}
    if only:
        for col in tree:
            for k in [k for k in tree[col] if only in k]:
                del tree[col][k]
    with ThreadPoolExecutor(6) as ex:
        for i, (col, ko, item) in enumerate(ex.map(lambda j: build_person(*j), jobs)):
            tree.setdefault(col, {}).setdefault(ko, []).append(item)
            if i % 100 == 0:
                print(i, item["name"], item["oa_ids"], item["works"], item["tags"])
    for col in tree:
        for ko in tree[col]:
            tree[col][ko].sort(key=lambda p: p["name"])
    OUT.write_text(json.dumps(tree, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    found = sum(1 for c in tree.values() for ps in c.values() for p in ps if p["oa_ids"])
    print("저장:", OUT.name, sum(len(ps) for c in tree.values() for ps in c.values()), "명 중 OpenAlex ID 확인", found, "명")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
