"""
별자리 선 = 실제 공저 관계 (home_fields.json에 field별 "links" 추가)

분야마다 별자리에 오른 연구자들끼리 최근 3년(home_fields.json의 window) 함께 쓴 논문이 있으면 선으로 잇고, 함께 쓴 편수를 적어 둠.
세부 분야가 달라도 함께 쓴 논문이 있으면 이어짐 (예: 경영전략 ↔ 조직인사).
실행: python build_coauthor_links.py   (build_home_snapshot.py로 home_fields.json을 만든 뒤)
"""
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from build_home_snapshot import get, short

SNAP = Path(__file__).with_name("home_fields.json")


def coauthors(aid, years):
    """이 연구자의 최근 논문에 함께 이름을 올린 저자 ID → 편수"""
    c = Counter()
    data = get("/works", filter=f"author.id:{aid},publication_year:{years[0]}-{years[1]}", select="authorships", **{"per-page": 200})
    for w in data.get("results", []):
        ids = {short((a.get("author") or {}).get("id")) for a in w.get("authorships") or []}
        ids.discard(aid)
        c.update(ids)
    return c


def main():
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    years = snap.get("window") or [2023, 2025]
    for f in snap["fields"]:
        ids = sorted({short(r["oa_id"]) for s in f.get("subfields", []) for r in s.get("researchers", [])})
        idset = set(ids)
        with ThreadPoolExecutor(6) as ex:
            res = dict(zip(ids, ex.map(lambda a: coauthors(a, years), ids)))
        links = {}
        for a, cnt in res.items():
            for b, n in cnt.items():
                if b in idset and a != b:
                    k = tuple(sorted((a, b)))
                    links[k] = max(links.get(k, 0), n)
        f["links"] = [[a, b, n] for (a, b), n in sorted(links.items(), key=lambda kv: -kv[1])]
        print(f.get("name") or f.get("id"), len(ids), "명,", len(f["links"]), "개 공저 선")
    SNAP.write_text(json.dumps(snap, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()
