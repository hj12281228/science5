"""
연세대 교수 목록(yonsei_profs.json) 만들기

교수님마다 OpenAlex 저자 ID를 사람이 한 번 확인해서 아래 SRC에 적어 두고, 이 스크립트로 카드용 정보(논문 수·연구 분야)를 채움.
- 이름 검색은 동명이인이 섞이고(예: 송민 교수 프로필에 중국 산둥대 송민 논문이 합쳐져 있음), 영문 표기가 다르면 아예 못 찾음(김기영 = Giyeong Kim)
- 그래서 ID를 고정하고, 논문은 '연세대 소속으로 쓴 것'만 셈
- 한 사람이 OpenAlex에서 여러 프로필로 나뉜 경우(황도식, 이지연 등)는 ID를 여러 개 적으면 합쳐서 셈. 같은 ORCID를 가진 프로필은 자동으로 추가

새 교수님이 오시면: SRC에 이름·영문·ID를 추가하고  `python build_yonsei_db.py`  (OPENALEX_API_KEY가 있으면 함께 씀)
ID 찾기: https://api.openalex.org/authors?search=영문이름&filter=affiliations.institution.id:I193775966
"""
import json
import os
from pathlib import Path

import requests

from build_home_snapshot import SUBFIELD_KO

YONSEI = "I193775966"
OUT = Path(__file__).with_name("yonsei_profs.json")

# 단과대 → 학과 → [이름, 영문, OpenAlex ID들]  (ID가 비어 있으면 OpenAlex에서 아직 못 찾은 분: 비교할 때 이름으로 검색)
SRC = {
    "인공지능융합대학": {
        "인공지능학과": [
            ("함범섭", "Bumsub Ham", ["A5054888241"]),
            ("황도식", "Dosik Hwang", ["A5085519704", "A5108218127"]),
        ]
    },
    "공과대학": {
        "전기전자공학부": [
            ("손광훈", "Kwanghoon Sohn", ["A5073320959", "A5090874091"]),
        ]
    },
    "문과대학": {
        "문헌정보학과": [
            ("송민", "Min Song", ["A5045749444"]),
            ("김기영", "Giyeong Kim", ["A5035791603"]),
            ("주영준", "Youngjun Joo", ["A5065892078"]),
            ("이지연", "Jee-Yeon Lee", ["A5109185097", "A5004660653"]),
            ("김성언", "Seongeon Kim", []),
        ]
    },
}


def _get(url, **params):
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        params["api_key"] = key
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def expand_ids(ids):
    """같은 ORCID를 쓰는 다른 프로필도 함께"""
    out = list(ids)
    for a in list(ids):
        orcid = _get(f"https://api.openalex.org/authors/{a}", select="orcid").get("orcid")
        if not orcid:
            continue
        for r in _get("https://api.openalex.org/authors", filter=f"orcid:{orcid}", select="id", **{"per-page": 25}).get("results", []):
            short = r["id"].rsplit("/", 1)[-1]
            if short not in out:
                out.append(short)
    return out


def profile(ids):
    """연세대 소속으로 쓴 논문 수와 많이 쓴 세부 분야 3개"""
    f = f"authorships.author.id:{'|'.join(ids)},authorships.institutions.id:{YONSEI}"
    total = _get("https://api.openalex.org/works", filter=f, **{"per-page": 1}).get("meta", {}).get("count", 0)
    groups = _get("https://api.openalex.org/works", filter=f, group_by="primary_topic.subfield.id").get("group_by", [])
    tags = [SUBFIELD_KO.get(g["key_display_name"], g["key_display_name"]) for g in groups[:3]]
    return total, tags


def main():
    tree = {}
    for col, depts in SRC.items():
        for dept, profs in depts.items():
            for name, eng, ids in profs:
                item = {"name": name, "eng": eng, "oa_ids": [], "works": None, "tags": []}
                if ids:
                    item["oa_ids"] = expand_ids(ids)
                    item["works"], item["tags"] = profile(item["oa_ids"])
                tree.setdefault(col, {}).setdefault(dept, []).append(item)
                print(name, item["oa_ids"], item["works"], item["tags"])
    OUT.write_text(json.dumps(tree, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
