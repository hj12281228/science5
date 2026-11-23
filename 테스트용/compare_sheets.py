"""
LABMATCH 비교 화면의 '요약'과 '지표 장(sheet)' HTML을 만드는 함수들

- 숫자는 모두 팀원 파일(practice1~5)의 compute_* / summarize 함수 결과를 그대로 씁니다.
- 그래프의 형식(도넛·건수 막대·피라미드·연도별 막대·학회 목록 / 게이지·3분할 막대·꺾은선·파트너 버블 /
  생키 / 사람 아이콘 / 신호등·잔디·연도별 꺾은선)은 유지하고, 배치와 표현만 벤토 칸 안에 맞게 다시 그렸습니다.
- Streamlit의 st.html로 넣을 수 있게 스크립트 없이 HTML + SVG 문자열만 만듭니다.
"""

import html
import math

from practice1 import compute_toptier
from practice2 import compute_industry_collab
from practice3 import summarize as summarize_fields
from practice4 import compute_lab_size
from practice5 import compute_continuity

A, B = "#93BAB5", "#F5CB71"
INK, MU, HA = "#141414", "#8A877F", "#9A968D"
YEARS = list(range(2021, 2026))
esc = html.escape

# ---------------------------------------------------------------- 색 (라이트 / 다크)
# 라이트: 세이지 #93BAB5 · 머스터드 #F5CB71 / 다크: 라벤더 #9989F1 · 연두 #B5DC8A (확정)
# TA·TB는 글씨용 색. 라이트 두 색은 흰 바탕 글씨로 쓰기엔 옅어서 진하게 씀.
LIGHT = dict(A="#93BAB5", B="#F5CB71", TA="#3B6862", TB="#946600", INK="#141414", MU="#8A877F", HA="#9A968D",
             ON_A="#141414", ON_B="#141414",
             AT="#E4EEED", BT="#FDF3DD", SAND="#EAE7E0", GRID="#D3CFC5", PAPER="#FFFFFF", ON_BLK="#FFFFFF",
             BUB_A="#AECBC8", BUB_C="#C9C5BC", BUB_B="#F8D894", BUB_TXT="#141414")
DARK = dict(INK="#F3F2EE", MU="#8E8D96", HA="#6B6A73", SAND="#1D1D23", GRID="#34343C", PAPER="#141418", ON_BLK="#F3F2EE",
            BUB_C="#8E8D96", BUB_TXT="#0B0B0D",
            A="#9989F1", B="#B5DC8A", TA="#9989F1", TB="#B5DC8A", ON_A="#0B0B0D", ON_B="#0B0B0D")
P = dict(LIGHT)
DARK_MODE = False


def blend(c1, c2, w):
    """c1을 w만큼, c2를 1-w만큼 섞은 색"""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * w + y * (1 - w)):02X}" for x, y in zip(a, b))


def rgba(c, a):
    return f"rgba({int(c[1:3], 16)},{int(c[3:5], 16)},{int(c[5:7], 16)},{a})"


def use_palette(dark=False, pal=None):
    """화면 테마에 맞춰 색을 고름 (그래프 SVG 색도 함께 바뀜)"""
    global A, B, INK, MU, HA, DARK_MODE
    P.clear()
    P.update(LIGHT)
    if dark:
        P.update(DARK)
        P["AT"], P["BT"] = blend(P["A"], "#141418", .2), blend(P["B"], "#141418", .2)
        P["BUB_A"], P["BUB_B"] = P["A"], P["B"]
    A, B, INK, MU, HA = P["A"], P["B"], P["INK"], P["MU"], P["HA"]
    DARK_MODE = dark


def css_vars():
    """CSS 변수 (.lm 안에서 씀)"""
    p = P
    blk = "#1E1E25" if DARK_MODE else "#141414"
    page = "#0C0C0F" if DARK_MODE else "#FFFFFF"
    return (f"<style>.lm{{--paper:{p['PAPER'] if DARK_MODE else '#FBFAF7'};--ink:{p['INK']};--mute:{p['MU']};--line:{'#2B2B33' if DARK_MODE else '#DCD8CF'};"
            f"--A:{p['A']};--B:{p['B']};--At:{p['AT']};--Bt:{p['BT']};--sand:{p['SAND']};--onA:{p['ON_A']};--onB:{p['ON_B']};"
            f"--blk:{blk};--page:{page};--hatch:{p['HA']};--tA:{p['TA']};--tB:{p['TB']};--bandA:{'transparent' if DARK_MODE else p['A']};--bandB:{'transparent' if DARK_MODE else p['B']};--nmA:{p['A'] if DARK_MODE else p['INK']};--nmB:{p['B'] if DARK_MODE else p['INK']};--tinA:{p['TA'] if not DARK_MODE else blend(p['A'], '#FFFFFF', .85)};"
            f"--tinB:{p['TB'] if not DARK_MODE else blend(p['B'], '#FFFFFF', .85)};"
            f"--lbA:{p['A']};--lbB:{p['B']}}}</style>")

# OpenAlex 최상위 분야(concepts level 0) 한글 이름
FIELD_KO = {
    "Computer science": "컴퓨터과학", "Medicine": "의학", "Biology": "생물학", "Chemistry": "화학", "Physics": "물리학",
    "Mathematics": "수학", "Engineering": "공학", "Materials science": "재료과학", "Psychology": "심리학",
    "Economics": "경제학", "Business": "경영학", "Political science": "정치학", "Sociology": "사회학",
    "Philosophy": "철학", "Art": "예술", "History": "역사학", "Geography": "지리학", "Geology": "지질학",
    "Environmental science": "환경과학",
}

QUESTIONS = [
    {"key": "top", "no": "01", "en": "TOP VENUE", "chip": "좋은 학회·저널", "q": "주요 학회·저널에 자주 싣나요?"},
    {"key": "ind", "no": "02", "en": "COLLAB", "chip": "학교 밖 협업", "q": "기업·다른 기관과 함께 연구하나요?"},
    {"key": "mix", "no": "03", "en": "MIX", "chip": "여러 분야 융합", "q": "다른 전공 출신도 어울릴 만큼 분야가 넓나요?"},
    {"key": "size", "no": "04", "en": "PEOPLE", "chip": "질문할 선배", "q": "함께 연구하는 선배가 많나요?"},
    {"key": "cont", "no": "05", "en": "STEADY", "chip": "꾸준한 논문", "q": "논문이 끊기지 않고 꾸준히 나오나요?"},
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
.lm{--paper:#FBFAF7;--ink:#141414;--mute:#8A877F;--line:#DCD8CF;--A:#93BAB5;--B:#F5CB71;--tA:#3B6862;--tB:#946600;--At:#E4EEED;--Bt:#FDF3DD;--sand:#EAE7E0;
 --disp:"Space Grotesk","IBM Plex Sans KR",sans-serif;--kr:"IBM Plex Sans KR","Apple SD Gothic Neo",sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace;
 font-family:var(--kr);color:var(--ink);line-height:1.35}
.lm *{box-sizing:border-box}
.lm ul,.lm ol{padding:0!important;margin-left:0!important;list-style:none}
.lm li{margin:0!important;padding-left:0}
.lm li::marker{content:""}
.lm p{margin:0}
.lm .tag{font-family:var(--mono);font-size:11px;letter-spacing:.08em;color:var(--mute);display:flex;justify-content:space-between;gap:10px}
.lm .pill{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--ink);border-radius:999px;padding:4px 12px;font-size:13px;white-space:nowrap}
.lm .note{font-size:12px;color:#8a5a00;background:#FFF3D6;border-radius:999px;padding:3px 10px;display:inline-block}
/* 이름 */
.lm-names{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:end;gap:24px;margin:12px 0 26px}
.lm-nm{font-weight:700;font-size:clamp(40px,6.4vw,92px);line-height:.98;letter-spacing:-.04em;min-width:0;overflow-wrap:anywhere;word-break:keep-all}
.lm-nm.A{color:var(--nmA,var(--ink))}.lm-nm.B{color:var(--nmB,var(--ink));text-align:right}
.lm-nm .nm{background:linear-gradient(transparent 60%,var(--bandA) 60%,var(--bandA) 86%,transparent 86%);padding:0 .06em;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.lm-nm.B .nm{background:linear-gradient(transparent 60%,var(--bandB) 60%,var(--bandB) 86%,transparent 86%)}
.lm-nm small{display:flex;align-items:center;gap:10px;font-size:15px;font-weight:500;letter-spacing:0;color:var(--ink);margin-bottom:12px;min-width:0}
.lm-nm small span.t{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lm-nm.B small{justify-content:flex-end}
.lm-nm .eng{display:block;font-size:15px;font-weight:400;letter-spacing:0;color:var(--mute);margin-top:12px}
.lm-logo{width:34px;height:34px;flex:none;border-radius:50%;background:#fff;display:grid;place-items:center;overflow:hidden;border:1px solid var(--line);font-size:12px;font-weight:700;color:var(--tA)}
.lm-logo img{width:29px;height:29px;object-fit:contain}
.lm-vs{font-family:var(--disp);font-weight:300;font-size:40px;color:var(--mute);padding-bottom:10px}
/* 요약 벤토 */
.lm-bento{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px}
.lm-tile{border-radius:22px;background:var(--paper);padding:18px 20px 20px;min-height:212px;display:flex;flex-direction:column;border:1px solid var(--line);min-width:0}
.lm-tile.fillA{background:var(--A);color:var(--onA);border-color:var(--A)}.lm-tile.fillB{background:var(--B);color:var(--onB);border-color:var(--B)}
.lm-tile.fillA .tag,.lm-tile.fillB .tag{color:inherit;opacity:.7}
.lm-tile h4{margin:8px 0 0;font-size:15px;font-weight:600;padding:0}
.lm-big{font-family:var(--disp);line-height:.92;letter-spacing:-.04em;margin-top:auto;padding-top:14px}
.lm-big .r{display:flex;align-items:baseline;gap:8px}
.lm-big .r i{font-style:normal;font-family:var(--mono);font-size:11px;letter-spacing:.06em;width:12px}
.lm-big .lead{font-size:clamp(40px,4.2vw,60px);font-weight:700}
.lm-big .lag{font-size:clamp(28px,2.8vw,40px);font-weight:300;opacity:.45}
.lm-big .even{font-size:clamp(32px,3.3vw,46px);font-weight:500}
.lm-big u{text-decoration:none;font-size:.4em;font-weight:400;margin-left:2px;letter-spacing:0}
.lm-bars{margin-top:14px;display:grid;gap:6px}
.lm-bars span{display:block;height:2px;background:var(--line);position:relative}
.lm-bars span b{position:absolute;left:0;top:-1px;height:4px;border-radius:2px}
.lm-tile.fillA .lm-bars span,.lm-tile.fillB .lm-bars span{background:color-mix(in srgb,currentColor 25%,transparent)}
/* 3줄 브리프 */
.lm-brief{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:end;margin-top:28px;border-top:1px solid var(--ink)}
.lm-brief ol{list-style:none;margin:0;padding:0}
.lm-brief li{display:grid;grid-template-columns:84px minmax(0,1fr) auto;align-items:baseline;border-bottom:1px solid var(--line);padding:10px 0;margin:0}
.lm-brief li .n{font-family:var(--mono);font-size:12px;color:var(--mute)}
.lm-brief li p{margin:0;padding:0;font-size:clamp(19px,2.1vw,30px);font-weight:600;letter-spacing:-.02em;line-height:1.3}
.lm-brief li:nth-child(2) p{opacity:.62}.lm-brief li:nth-child(3) p{opacity:.36}
.lm-brief li em{font-style:normal;font-family:var(--mono);font-size:12px;color:var(--mute)}
.lm-arrow{font-family:var(--disp);font-weight:300;font-size:110px;line-height:.8;padding-left:30px}
.lm-hint{font-size:13px;color:var(--mute);margin-top:10px}
/* 지표 장 */
.lm-sheet{background:var(--paper);border-radius:28px;padding:36px 36px 36px;margin-bottom:12px}
.lm-hd{display:grid;grid-template-columns:44px minmax(0,1fr) auto;align-items:center;gap:8px;margin-bottom:28px}
.lm-hd .no{font-family:var(--mono);font-size:13px;color:var(--mute)}
.lm-hd .q{font-size:clamp(26px,2.8vw,40px);font-weight:700;letter-spacing:-.03em;line-height:1.15}
.lm-hd .star{font-size:12px;font-weight:600;color:var(--paper);background:var(--ink);border-radius:999px;padding:3px 10px;white-space:nowrap}
.lm-g{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:16px}
.lm-t{border-radius:22px;padding:24px 26px;position:relative;overflow:hidden;min-width:0}
.s3{grid-column:span 3}.s4{grid-column:span 4}.s5{grid-column:span 5}.s6{grid-column:span 6}.s7{grid-column:span 7}.s8{grid-column:span 8}.s12{grid-column:span 12}
.solA{background:var(--A);color:var(--onA)}.solA .tag{color:inherit;opacity:.68}
.solB{background:var(--B);color:var(--onB)}.solB .tag{color:inherit;opacity:.7}
.tinA{background:var(--At);color:var(--tinA)}.tinA .tag{color:var(--tinA);opacity:.75}
.tinB{background:var(--Bt);color:var(--tinB)}.tinB .tag{color:var(--tinB);opacity:.75}
.out{background:var(--paper);border:1px solid var(--ink)}
.sand{background:var(--sand)}
.blk{background:var(--blk);color:#F3F2EE;border:1px solid var(--line)}.blk .tag{color:rgba(243,242,238,.55)}
.h300{min-height:310px}.h280{min-height:250px}
.lm-t:has(.lm-foot){padding-bottom:80px}
.lm-ring{position:absolute;right:26px;top:24px}
.lm-ring + .tag.hd .tt{max-width:calc(100% - 140px)}
.lm-huge{font-family:var(--disp);letter-spacing:-.05em;line-height:.85;font-size:clamp(52px,6vw,88px)}
.lm-huge.b{font-weight:700}.lm-huge.l{font-weight:300}.lm-huge.m{font-weight:500}
.lm-huge u{text-decoration:none;font-size:.36em;font-weight:400;margin-left:4px;letter-spacing:0}
.lm-mt{margin-top:28px}
.lm-sub{font-family:var(--mono);font-size:12px;letter-spacing:.02em;margin-top:12px;opacity:.85}
.lm-foot{position:absolute;left:26px;right:26px;bottom:22px}
.lm-row{display:flex;justify-content:space-between;align-items:baseline;font-size:13px;gap:10px}
.lm-row b{font-family:var(--disp);font-size:28px;letter-spacing:-.02em;white-space:nowrap}
.lm-ln{height:2px;margin-top:6px;position:relative}.lm-ln i{position:absolute;left:0;top:-2px;height:6px;border-radius:3px}
.lm-gauge{height:14px;border-radius:999px;margin-top:8px;overflow:hidden}.lm-gauge i{display:block;height:100%;border-radius:999px}
.lm-vl{list-style:none;margin:16px 0 0;padding:0}
.lm-vl li{display:grid;grid-template-columns:minmax(0,1fr) 64px 64px;align-items:baseline;padding:8px 0;margin:0;border-bottom:1px solid rgba(255,255,255,.12)}
.lm-vl li span{font-size:clamp(16px,1.6vw,23px);font-weight:600;letter-spacing:-.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lm-vl li b{font-family:var(--disp);font-size:clamp(17px,1.6vw,23px);text-align:right}
.lm-vl.wide li{grid-template-columns:minmax(0,1fr) 80px 80px}
.lm-vl li:nth-child(2){opacity:.78}.lm-vl li:nth-child(3){opacity:.55}.lm-vl li:nth-child(n+4){opacity:.32}
.lbA{color:var(--lbA)}.lbB{color:var(--lbB)}
.lm-legend{display:flex;gap:14px;font-size:12px;align-items:center;flex-wrap:wrap}
.lm-legend i{display:inline-block;width:12px;height:12px;border-radius:4px;vertical-align:-1px;margin-right:5px}
.lm-hatch{background:repeating-linear-gradient(135deg,transparent 0 4px,var(--hatch,#9A968D) 4px 5px);border:1px solid var(--hatch,#9A968D)}
.lm-chip{display:inline-block;font-size:11px;border-radius:999px;padding:2px 9px;border:1px solid currentColor}
.lm-empty{font-size:13px;opacity:.7;margin-top:14px}
.lm-split{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.lm-split > b{font-family:var(--disp);font-size:22px;width:18px}
.lm-split .bar{flex:1;display:flex;height:52px;border-radius:999px;overflow:hidden;border:1px solid var(--ink);min-width:0}
.lm-split .bar > div{display:flex;align-items:center;font-family:var(--disp);font-size:14px;overflow:hidden;white-space:nowrap}
.lm-ppl{display:flex;flex-wrap:wrap;gap:6px;margin-top:22px}
.lm-ppl svg{width:30px;height:36px}
.lm-ppl .more{font-family:var(--disp);font-size:18px;align-self:center;margin-left:6px}
.lm-grass{margin-top:18px;display:grid;grid-template-columns:40px repeat(12,minmax(0,1fr));gap:4px;align-items:center}
.lm-grass span{aspect-ratio:1;border-radius:4px}
.lm-grass em{font-style:normal;font-family:var(--mono);font-size:11px;opacity:.75}
/* 박스 제목: 무슨 그래프인지 먼저 읽히게 */
.lm .tag.hd{align-items:flex-start;gap:16px}
.lm .tag.hd .tt{display:flex;flex-direction:column;gap:4px;min-width:0}
.lm .tag.hd .tt b{word-break:keep-all;font-family:var(--kr);font-size:17px;font-weight:700;letter-spacing:-.01em;color:var(--ink);line-height:1.3}
.lm .tag.hd .tt b i{font-style:normal;font-family:var(--mono);font-size:11px;font-weight:500;letter-spacing:.08em;margin-right:8px;opacity:.6;vertical-align:2px}
.lm .tag.hd .tt span{font-family:var(--kr);font-size:13px;letter-spacing:0;line-height:1.45;color:var(--mute)}
.lm .tag.hd > span{flex:none;padding-top:4px}
.solA .tag.hd .tt b,.solB .tag.hd .tt b,.tinA .tag.hd .tt b,.tinB .tag.hd .tt b,.blk .tag.hd .tt b{color:inherit}
.solA .tag.hd .tt span,.solB .tag.hd .tt span,.tinA .tag.hd .tt span,.tinB .tag.hd .tt span{color:inherit;opacity:.8}
.blk .tag.hd .tt b{color:#F3F2EE}.blk .tag.hd .tt span{color:#F3F2EE;opacity:.62}
.solA .tag.hd,.solB .tag.hd,.tinA .tag.hd,.tinB .tag.hd{opacity:1}
.lm-key{display:flex;align-items:center;gap:6px;margin-top:16px;font-size:12.5px;flex-wrap:wrap}
.lm-key svg{width:14px;height:17px}.lm-key span{margin-right:10px;opacity:.85}
/* 신호등 */
.lm-lights{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:22px}
.lm-light{display:flex;align-items:center;gap:22px;min-width:0}
.lm-light .sl{font-family:var(--mono);font-size:12px;letter-spacing:.08em;opacity:.7;writing-mode:vertical-rl;transform:rotate(180deg)}
.lm-light .box{display:flex;gap:12px;padding:12px 16px;border-radius:999px;background:#0A0A0C;border:1px solid #2E2E36;flex:none}
.lm-light .box i{width:34px;height:34px;border-radius:50%;background:var(--c);opacity:.16}
.lm-light .box i.on{opacity:1;box-shadow:0 0 0 4px color-mix(in srgb,var(--c) 28%,transparent),0 0 26px 2px var(--c)}
.lm-light b{display:block;font-size:clamp(26px,2.6vw,36px);font-weight:700;letter-spacing:-.02em;line-height:1.1}
.lm-light p{font-size:13.5px;opacity:.75;margin-top:6px!important;line-height:1.45}
@media (max-width:900px){.lm-lights{grid-template-columns:1fr}.lm-light .box i{width:26px;height:26px}}
@media (max-width:700px){.lm .tag.hd{flex-wrap:wrap}.lm .tag.hd > span{width:100%;padding-top:0}.lm-ring{width:84px;height:84px}.lm-ring + .tag.hd .tt{max-width:calc(100% - 96px)}}
.lm-sig{display:flex;gap:6px;align-items:center;font-size:13px;font-family:var(--kr);letter-spacing:0}
.lm-sig i{width:12px;height:12px;border-radius:50%;display:inline-block;background:currentColor;opacity:.25}
.lm-sig i.on{opacity:1}
.lm-inline{display:flex;align-items:flex-end;gap:18px;margin-top:28px;flex-wrap:wrap}
.lm-inline .lm-sub{margin:0 0 8px}
.lm svg text{font-family:"IBM Plex Sans KR",sans-serif}
.lm svg text:not([fill]){fill:var(--ink)}
/* 인덱스 폴더: 지표 5장을 겹쳐 두고, 누르면 열림 (한 번에 한 장) */
:root{interpolate-size:allow-keywords}
.lm-folders{position:relative;padding-top:44px}
/* 정면에서 보는 겹친 폴더. 그림자는 가벼운 box-shadow (filter:drop-shadow는 휴대폰에서 큰 장 전체를 따로 그려서 느려지고 화면이 끊겼음) */
.lm-fold{position:relative;border:1px solid var(--line);border-radius:0 26px 26px 26px;margin-top:-2px;background:var(--fbg);
 box-shadow:0 -6px 14px -6px rgba(0,0,0,.10);transition:transform .6s cubic-bezier(.16,1,.3,1),background-color .4s}
.lm-fold:first-child{margin-top:0}
.lm-fold:not([open]):hover{transform:translateY(-8px)}
.lm-fold[open]{--fbg:var(--paper)}
.lm-fold > summary{background:var(--fbg);border-radius:inherit;list-style:none;cursor:pointer;display:grid;grid-template-columns:44px minmax(0,1fr) auto auto 40px;align-items:center;gap:14px;padding:22px 36px 44px;position:relative}
.lm-fold > summary::-webkit-details-marker{display:none}
.lm-fold > summary:focus-visible{outline:2px solid var(--A);outline-offset:-4px;border-radius:20px}
.lm-ftab{position:absolute;z-index:2;top:-35px;left:calc(var(--i) * 168px - 1px);height:36px;min-width:150px;padding:0 18px;border:1px solid var(--line);border-bottom:0;
 border-radius:14px 14px 0 0;background:var(--fbg);display:flex;align-items:center;gap:10px;font-family:var(--mono);font-size:11px;letter-spacing:.06em;color:var(--mute)}
.lm-ftab::after{content:"";position:absolute;left:0;right:0;bottom:-2px;height:3px;background:var(--fbg)}
.lm-fold > summary .mine{font-size:12px;font-weight:600;color:var(--paper);background:var(--ink);border-radius:999px;padding:4px 11px;white-space:nowrap}
.lm-ftab b{font-family:var(--kr);font-size:13px;letter-spacing:0;color:var(--ink);font-weight:600}
.lm-fold > summary .no{font-family:var(--mono);font-size:13px;color:var(--mute)}
.lm-fold > summary .q{font-size:clamp(22px,2.4vw,34px);font-weight:700;letter-spacing:-.03em;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lm-fold[open] > summary .q{font-size:clamp(26px,2.8vw,40px);white-space:normal}
.lm-fold > summary .ab{display:flex;gap:16px;align-items:baseline;font-family:var(--disp);font-size:24px;white-space:nowrap}
.lm-fold > summary .ab b{font-weight:700}.lm-fold > summary .ab s{text-decoration:none;font-weight:300;opacity:.5}
.lm-fold > summary .chev{font-family:var(--disp);font-weight:300;font-size:34px;line-height:1;text-align:right;transition:transform .6s cubic-bezier(.16,1,.3,1)}
.lm-fold[open] > summary .chev{transform:rotate(180deg)}
.lm-fold[open] > summary .ab{opacity:0;pointer-events:none}
.lm-fold::details-content{block-size:0;overflow:clip;transition:block-size .7s cubic-bezier(.16,1,.3,1),content-visibility .7s allow-discrete}
.lm-fold[open]::details-content{block-size:auto}
.lm-fbody{padding:0 36px 58px;animation:lmRise .7s cubic-bezier(.16,1,.3,1)}
@keyframes lmRise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
.lm-slidefoot{display:flex;justify-content:space-between;gap:12px;font-family:var(--mono);font-size:11px;letter-spacing:.06em;color:var(--mute);border-top:1px solid var(--line);margin-top:26px;padding-top:12px}
.lm-slidefoot span:nth-child(2){flex:1;text-align:center}
.lm-hint2{font-size:13px;color:var(--mute);margin:0 0 6px}
@media (prefers-reduced-motion:reduce){.lm-fold,.lm-fold::details-content,.lm-fbody,.lm-fold > summary .chev{transition:none;animation:none}}
@media (max-width:1100px){.lm-ftab{left:calc(var(--i) * 112px - 1px);min-width:104px;padding:0 12px}.lm-ftab b{display:none}.lm-fold > summary{padding:22px 22px 30px}.lm-fbody{padding:0 22px 30px}}
@media (max-width:700px){.lm-ftab{left:calc(var(--i) * 64px - 1px);min-width:58px;padding:0 10px;top:-29px;height:30px}
 .lm-fold > summary{grid-template-columns:28px minmax(0,1fr) 28px;padding:18px 14px 42px}.lm-fold > summary .ab{grid-column:2;font-size:18px}
 .lm-fold > summary > span:empty{display:none}.lm-fold > summary .mine{grid-column:2;justify-self:start;font-size:11px;padding:2px 9px}.lm-fold > summary .chev{grid-column:3;grid-row:1}
 .lm-fold[open] > summary .ab{display:none}.lm-fbody{padding:0 12px 24px}.lm-slidefoot span:nth-child(2){display:none}}
@media (max-width:1100px){
 .lm-bento{grid-template-columns:repeat(2,minmax(0,1fr))}
 .s3,.s4,.s5{grid-column:span 6}.s7,.s8{grid-column:span 12}
 .lm-sheet{padding:26px 22px}
}
@media (max-width:700px){
 .lm-bento{grid-template-columns:minmax(0,1fr)}.lm-tile{min-height:0}
 .s3,.s4,.s5,.s6,.s7,.s8{grid-column:span 12}
 .lm-names{gap:10px}.lm-vs{font-size:24px}
 .lm-brief{grid-template-columns:minmax(0,1fr)}.lm-arrow{display:none}
 .lm-brief li{grid-template-columns:64px minmax(0,1fr) auto}
 .lm-hd{grid-template-columns:30px minmax(0,1fr)}.lm-hd .star{display:none}
 .lm-sheet{padding:22px 14px;border-radius:22px}
 .lm-t{padding:20px}.lm-foot{left:20px;right:20px}
 .h280{min-height:0}.h300{min-height:240px}.lm-mt{margin-top:28px}
 .lm-nm{font-size:28px}.lm-nm small{font-size:13px}
}
/* 저장 버튼 (PDF·PNG) */
.lm-hintrow{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px}.lm-hintrow .lm-hint2{margin:0}
.lm-xbtn{font-family:var(--kr);font-size:12.5px;font-weight:600;color:var(--ink);background:transparent;border:1px solid var(--line);border-radius:999px;padding:6px 14px;cursor:pointer}
.lm-xbtn:hover{border-color:var(--ink)}.lm-xbtn[disabled]{opacity:.5;cursor:wait}
.lm-savebar{display:flex;justify-content:flex-end;margin-top:10px}
/* 저장용 한 장 (화면 밖에서 그려서 캡처·인쇄) */
.lm-pslide{width:1200px;box-sizing:border-box;background:var(--paper);color:var(--ink);padding:34px 36px 26px;font-family:var(--kr)}
.lm-pslide .lm-hd{margin-bottom:22px}
/* 저장본은 휴대폰·인쇄 화면 폭과 상관없이 항상 노트북 배치로 */
.lm-pslide .lm-g{grid-template-columns:repeat(12,minmax(0,1fr))!important}
.lm-pslide .s3{grid-column:span 3!important}.lm-pslide .s4{grid-column:span 4!important}.lm-pslide .s5{grid-column:span 5!important}
.lm-pslide .s6{grid-column:span 6!important}.lm-pslide .s7{grid-column:span 7!important}.lm-pslide .s8{grid-column:span 8!important}.lm-pslide .s12{grid-column:span 12!important}
.lm-pslide .lm-lights{grid-template-columns:1fr 1fr!important}
</style>
"""


# ================================================================ 숫자 모으기
def _pct(n, d):
    return round(100 * n / d, 1) if d else 0.0


def _shares_top(earlier, later, n=5):
    """생키에 넣을 분야: 두 기간 비중 합이 큰 n개 + 나머지는 '기타'"""
    keys = sorted(earlier.keys() | later.keys(), key=lambda k: -(earlier.get(k, 0) + later.get(k, 0)))
    keep, rest = keys[:n], keys[n:]

    def fold(d):
        out = {FIELD_KO.get(k, k): d.get(k, 0) for k in keep}
        if rest:
            out["기타"] = sum(d.get(k, 0) for k in rest)
        return out
    return fold(earlier), fold(later)


def _mix(lab):
    papers = [p for p in lab.get("interdisciplinarity_demo_papers") or []
              if isinstance(p, dict) and isinstance(p.get("year"), int) and 2021 <= p["year"] <= 2025]
    for p in papers:
        p.setdefault("field_ids", [])
    s = summarize_fields(papers)
    early = summarize_fields([p for p in papers if p["year"] <= 2023])
    late = summarize_fields([p for p in papers if p["year"] >= 2024])
    main = max(s["shares"], key=s["shares"].get) if s["shares"] else None
    left, right = _shares_top(early["shares"], late["shares"], n=4) if early["shares"] and late["shares"] else ({}, {})
    return {**s, "score": round(s["score"], 1) if s["score"] is not None else None,
            "coverage": round(s["coverage"], 1) if s["coverage"] is not None else None,
            "main": FIELD_KO.get(main, main) if main else None, "left": left, "right": right}


def _top(lab):
    r = compute_toptier(lab)
    df = r["df"]
    yearly, venues = {}, {}
    if r["has_papers"] and len(df):
        for y in YEARS:
            d = df[df["year"] == y]
            yearly[y] = (len(d), int((d["tier"] == 1).sum()))
        venues = df[df["tier"] == 1]["venue"].value_counts().to_dict()
    return {**r, "ratio": _pct(r["n_top"], r["n_all"]), "yearly": yearly, "venues": venues}


def collect(data_a, data_b):
    """두 연구실의 다섯 지표 계산 결과 (팀원 compute 함수 그대로)"""
    out = {}
    for slot, lab in (("A", data_a), ("B", data_b)):
        out[slot] = {
            "top": _top(lab),
            "ind": compute_industry_collab(lab),
            "mix": _mix(lab),
            "size": compute_lab_size(lab),
            "cont": compute_continuity(lab),
        }
    return out


def headline(m, key):
    """요약 칸과 브리프에 쓰는 대표값 (A값, B값, 단위, 최대값)"""
    a, b = m["A"], m["B"]
    if key == "top":
        return a["top"]["ratio"], b["top"]["ratio"], "%", 100
    if key == "ind":
        return a["ind"]["external_ratio"], b["ind"]["external_ratio"], "%", 100
    if key == "mix":
        return a["mix"]["score"] or 0.0, b["mix"]["score"] or 0.0, "%", 100
    if key == "size":
        va, vb = a["size"]["active_members"], b["size"]["active_members"]
        return va, vb, "명", max(va, vb, 1) * 1.15
    return a["cont"]["active_month_ratio"], b["cont"]["active_month_ratio"], "%", 100


def lead_of(a, b, unit):
    """더 높은 쪽 'A'/'B', 차이가 작으면 None"""
    close = abs(a - b) < (5 if unit == "%" else max(2, 0.15 * max(a, b)))
    return None if close else ("A" if a > b else "B")


def brief_line(key, a, b, unit):
    w = lead_of(a, b, unit)
    if w is None:
        return {"top": "좋은 학회·저널에 싣는 비중은 두 연구실이 비슷해요",
                "ind": "학교 밖과 함께 쓰는 정도는 비슷해요",
                "mix": "여러 분야를 섞는 정도는 비슷해요",
                "size": "함께 쓰는 사람 수는 비슷해요",
                "cont": "논문이 나오는 꾸준함은 비슷해요"}[key]
    gap = abs(a - b)
    return {"top": f"좋은 학회·저널에는 {w} 연구실이 더 자주 실어요",
            "ind": f"학교 밖과 함께 쓰는 건 {w} 연구실이 {gap:.0f}%p 많아요",
            "mix": f"여러 분야를 섞는 건 {w} 연구실 쪽이에요",
            "size": f"함께 쓰는 사람은 {w} 연구실이 {int(gap)}명 더 많아요",
            "cont": f"논문은 {w} 연구실이 더 꾸준히 나와요"}[key]


def brief_pick(m, chosen):
    """내 기준을 먼저, 그다음 차이가 큰 지표 순으로 3개"""
    def diff(q):
        a, b, *_ = headline(m, q["key"])
        return abs(a - b) / max(a, b, 1e-9)
    return sorted(QUESTIONS, key=lambda q: (q["key"] not in chosen, -diff(q)))[:3]


# ================================================================ 면담 질문
Q_LOW = {
    "top": "우수 학회·저널 비중이 상대적으로 낮게 나왔는데, 연구실이 목표로 하는 학회·저널과 투고 방향이 궁금합니다.",
    "ind": "외부 기관·기업과의 공동 연구는 어떻게 진행되고, 학생이 참여할 기회가 있나요?",
    "mix": "다른 분야와 융합하는 연구에 관심이 있다면 연구실에서 어떻게 진행할 수 있나요?",
    "size": "함께 논문을 쓰는 구성원이 많지 않아 보이는데, 신입생은 누구에게 지도와 피드백을 받게 되나요?",
    "cont": "논문이 덜 나온 시기도 있었는데, 그 기간에 진행된 연구나 프로젝트가 있었나요?",
}
Q_HIGH = {
    "top": "우수 학회·저널 논문이 많은데, 신입생이 1저자 논문을 쓰기까지 보통 얼마나 걸리나요?",
    "ind": "외부 협업이 활발한데, 학생이 기업·기관 과제에 참여할 때 역할과 저자 기준은 어떻게 정해지나요?",
    "mix": "여러 분야를 넘나드는 연구가 많은데, 배경이 다른 학생은 어떤 공부부터 준비하면 좋을까요?",
    "size": "함께 쓰는 구성원이 많은데, 팀은 어떻게 나뉘고 사수·멘토링은 어떻게 이뤄지나요?",
    "cont": "논문이 꾸준히 나오는데, 연구실의 연간 연구·투고 일정은 어떻게 운영되나요?",
}
Q_COMMON = ("인건비·연구비 지원과 학회 참석 지원은 어떻게 되나요?",
            "졸업까지 걸리는 기간과 졸업생들의 진로가 궁금합니다.")


def interview_questions(m, slot, chosen=()):
    """교수님께 드릴 질문 5개: 상대 연구실보다 강한 지표 1개, 약한 지표 2개(내 기준 먼저), 공통 2개"""
    other = "B" if slot == "A" else "A"
    def d(q):
        v = dict(zip(("A", "B"), headline(m, q["key"])[:2]))
        return (v[slot] - v[other]) / max(v[slot], v[other], 1e-9)
    qs = sorted(QUESTIONS, key=d)
    high = qs[-1]
    low = sorted([q for q in qs if q is not high], key=lambda q: (q["key"] not in chosen, d(q)))[:2]
    out = [(Q_LOW if d(q) < 0 else Q_HIGH)[q["key"]] for q in low] + [Q_HIGH[high["key"]]]
    return out + list(Q_COMMON)


# ================================================================ 이름 · 요약
def _fmt(v, unit):
    if unit == "%":
        return f"{v:.0f}" if v >= 10 or v == 0 else f"{v:.1f}"
    return f"{int(v)}"


def names_html(pa, pb, logo_a, logo_b):
    def side(p, logo, slot):
        sub = " · ".join(x for x in (p.get("school"), p.get("sub")) if x)
        eng = f'<span class="eng">{esc(p["eng"])}</span>' if p.get("eng") else ""
        lg = f'<span class="lm-logo">{logo}</span>'
        meta = f'{lg}<span class="t">{esc(sub)}</span>' if slot == "A" else f'<span class="t">{esc(sub)}</span>{lg}'
        return f'<div class="lm-nm {slot}"><small>{meta}</small><span class="nm">{esc(p.get("name") or "")}</span>{eng}</div>'
    return f'<div class="lm"><div class="lm-names">{side(pa, logo_a, "A")}<div class="lm-vs">vs</div>{side(pb, logo_b, "B")}</div></div>'


def summary_html(m, chosen, demo=False, title=""):
    tiles = []
    for q in QUESTIONS:
        a, b, unit, mx = headline(m, q["key"])
        w = lead_of(a, b, unit)
        fill = f"fill{w}" if (q["key"] in chosen and w) else ""
        ca = cb = ("var(--onA)" if w == "A" else "var(--onB)") if fill else None
        if not fill:
            ca, cb = "var(--tinA)", "var(--tinB)"
        fa, fb = (ca, ca) if fill else ("var(--A)", "var(--B)")
        cls = (lambda me: "even" if w is None else ("lead" if w == me else "lag"))
        tiles.append(
            f'<div class="lm-tile {fill}"><div class="tag"><span>{q["no"]}</span><span>{q["en"]}</span></div><h4>{esc(q["chip"])}</h4>'
            f'<div class="lm-big"><div class="r" style="color:{ca}"><i>A</i><span class="{cls("A")}">{_fmt(a, unit)}<u>{unit}</u></span></div>'
            f'<div class="r" style="color:{cb}"><i>B</i><span class="{cls("B")}">{_fmt(b, unit)}<u>{unit}</u></span></div></div>'
            f'<div class="lm-bars"><span><b style="width:{min(a / mx, 1) * 100:.1f}%;background:{fa}"></b></span>'
            f'<span><b style="width:{min(b / mx, 1) * 100:.1f}%;background:{fb}"></b></span></div></div>')
    rows = []
    for i, q in enumerate(brief_pick(m, chosen)):
        a, b, unit, _ = headline(m, q["key"])
        rows.append(f'<li><span class="n">BRIEF {i + 1}</span><p>{esc(brief_line(q["key"], a, b, unit))}</p><em>{q["no"]}</em></li>')
    note = '<div style="margin-bottom:12px"><span class="note">화면 확인용 예시 데이터예요. 실제 교수님 데이터가 아닙니다.</span></div>' if demo else ""
    return (f'<div class="lm">{note}<div class="lm-bento">{"".join(tiles)}</div>'
            f'<div class="lm-brief"><ol>{"".join(rows)}</ol><div class="lm-arrow">↓</div></div>'
            f'<div class="lm-hint">최근 5년(2021~2025) 논문 기준 · 자세한 그래프는 <b>지표</b> 탭에서 볼 수 있어요.</div>'
            f'<div class="lm-slidefoot"><span>LABMATCH</span><span>{esc(title)}</span><span>SUMMARY</span></div></div>')


# ================================================================ 지표 장 공통
def _hatch(pid):
    return (f'<pattern id="{pid}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<line x1="0" y1="0" x2="0" y2="6" stroke="{HA}" stroke-width="1"/></pattern>')


def _tiles_class(w):
    """더 높은 쪽은 진한 칸, 다른 쪽은 연한 칸. 비슷하면 둘 다 연한 칸"""
    ta = "solA" if w == "A" else "tinA"
    tb = "solB" if w == "B" else "tinB"
    wa = "b" if w == "A" else ("m" if w is None else "l")
    wb = "b" if w == "B" else ("m" if w is None else "l")
    return ta, tb, wa, wb


def sheet_html(q, body, mine=False):
    star = '<span class="lm-star star">내 기준</span>' if mine else ""
    return (f'<div class="lm"><section class="lm-sheet"><div class="lm-hd"><span class="no">{q["no"]}</span>'
            f'<div class="q">{esc(q["q"])}</div>{star}</div><div class="lm-g">{body}</div></section></div>')


def _ring(v, color, track):
    circ = 2 * math.pi * 50
    return (f'<svg class="lm-ring" width="120" height="120" viewBox="0 0 120 120">'
            f'<circle cx="60" cy="60" r="50" fill="none" stroke="{track}" stroke-width="14"/>'
            f'<circle cx="60" cy="60" r="50" fill="none" stroke="{color}" stroke-width="14" stroke-linecap="round" '
            f'stroke-dasharray="{circ * min(v, 100) / 100:.1f} {circ:.1f}" transform="rotate(-90 60 60)"/></svg>')


def _on_dark(cls):
    return cls.startswith("sol")


# ================================================================ 01 우수 학회·저널
def sheet_top(m):
    a, b = m["A"]["top"], m["B"]["top"]
    w = lead_of(a["ratio"], b["ratio"], "%")
    ta, tb, wa, wb = _tiles_class(w)
    mx = max(a["n_top"], b["n_top"], 1)

    def big(r, cls, wt, slot, other):
        dark = _on_dark(cls)
        col = P["ON_" + slot] if dark else P["T" + slot]
        track = rgba(col, .2)
        sub = f'{r["n_top"]} / {r["n_all"]}편'
        if r["ratio"] > other["ratio"] and w:
            sub += f' · {"B" if slot == "A" else "A"}보다 +{r["ratio"] - other["ratio"]:.1f}%p'
        return (f'<div class="lm-t s4 {cls} h300">{_ring(r["ratio"], col, track)}<div class="tag hd"><div class="tt"><b><i>LAB {slot}</i>우수 학회·저널 비중</b><span>최근 5년 논문 중 상위 등급 학회·저널에 실린 비율</span></div></div>'
                f'<div class="lm-huge {wt} lm-mt">{r["ratio"]:.1f}<u>%</u></div><div class="lm-sub">{sub}</div>'
                f'<div class="lm-foot"><div class="lm-row"><span>우수 학회·저널 건수</span><b style="font-weight:{700 if wt == "b" else 400}">{r["n_top"]}편</b></div>'
                f'<div class="lm-ln" style="background:{track}"><i style="width:{r["n_top"] / mx * 100:.0f}%;background:{col}"></i></div></div></div>')

    # 피라미드: A·B를 한 축에 거울처럼 (우수 / 중위권 / 기타)
    if a["n_mid"] is None or b["n_mid"] is None:
        pyr = '<div class="lm-empty">등급별 정보가 없어요 · 수집 예정</div>'
    else:
        def num(x, y, n, anchor, col, size, wt):
            return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Space Grotesk" font-size="{size}" font-weight="{wt}" fill="{col}">{n}</text>'
        pyr = (f'<svg width="100%" viewBox="0 0 400 250" style="margin-top:14px">'
               f'<polygon points="200,10 200,80 130,80 165,10" fill="{A}"/><polygon points="200,10 200,80 270,80 235,10" fill="{B}"/>'
               f'<polygon points="200,90 200,160 92,160 127,90" fill="{P['AT']}"/><polygon points="200,90 200,160 308,160 273,90" fill="{P['BT']}"/>'
               f'<polygon points="200,170 200,240 54,240 89,170" fill="{P['SAND']}"/><polygon points="200,170 200,240 346,240 311,170" fill="{P['SAND']}"/>'
               f'<line x1="200" y1="0" x2="200" y2="250" stroke="{INK}"/>'
               + num(14, 54, a["n_top"], "start", P["TA"], 32, 700 if a["n_top"] >= b["n_top"] else 300)
               + num(386, 54, b["n_top"], "end", P["TB"], 32, 700 if b["n_top"] >= a["n_top"] else 300)
               + num(14, 134, a["n_mid"], "start", MU, 22, 400) + num(386, 134, b["n_mid"], "end", MU, 22, 400)
               + num(14, 214, a["n_oth"], "start", MU, 22, 400) + num(386, 214, b["n_oth"], "end", MU, 22, 400)
               + f'<rect x="166" y="52" width="68" height="20" rx="10" fill="{INK}"/><text x="200" y="66" text-anchor="middle" fill="{P['PAPER']}" font-weight="700" font-size="12">★ 우수</text>'
               f'<rect x="172" y="116" width="56" height="20" rx="10" fill="{P['PAPER']}" stroke="{INK}"/><text x="200" y="130" text-anchor="middle" font-size="12" fill="{INK}">중위권</text>'
               f'<rect x="178" y="196" width="44" height="20" rx="10" fill="{P['PAPER']}" stroke="{INK}"/><text x="200" y="210" text-anchor="middle" font-size="12" fill="{INK}">기타</text></svg>')

    # 연도별: 빗금 = 전체 정식 논문, 채움 = 우수
    if a["yearly"] and b["yearly"]:
        top_v = max([v[0] for v in a["yearly"].values()] + [v[0] for v in b["yearly"].values()] + [1])
        H, base, bw, gap = 170, 196, 58, 10
        s = f'<defs>{_hatch("h1")}</defs>'
        for i, y in enumerate(YEARS):
            x0 = 30 + i * 168
            for k, (r, c) in enumerate(((a, A), (b, B))):
                al, tp = r["yearly"].get(y, (0, 0))
                x, ha, ht = x0 + k * (bw + gap), al / top_v * H, tp / top_v * H
                if al:
                    s += f'<rect x="{x}" y="{base - ha:.1f}" width="{bw}" height="{ha:.1f}" rx="16" fill="url(#h1)" stroke="{HA}"/>'
                if tp:
                    s += (f'<rect x="{x + 4}" y="{base - ht:.1f}" width="{bw - 8}" height="{max(ht - 4, 10):.1f}" rx="12" fill="{c}"/>'
                          f'<text x="{x + bw / 2}" y="{base - ht - 8:.1f}" text-anchor="middle" font-family="Space Grotesk" font-size="15" font-weight="700" fill="{P["T" + ("A" if k == 0 else "B")]}">{tp}</text>')
                if not al:
                    s += f'<text x="{x + bw / 2}" y="{base - 6}" text-anchor="middle" font-family="IBM Plex Mono" font-size="11" fill="{MU}">0</text>'
            s += f'<text x="{x0 + bw + gap / 2}" y="{base + 24}" text-anchor="middle" font-family="IBM Plex Mono" font-size="13">{y}</text>'
        s += f'<line x1="0" y1="{base}" x2="860" y2="{base}" stroke="{INK}"/>'
        yearly = f'<svg width="100%" viewBox="0 0 860 230" style="margin-top:12px">{s}</svg>'
    else:
        yearly = '<div class="lm-empty">논문 목록이 없어 연도별 그래프는 수집 예정이에요.</div>'

    # 학회·저널 목록
    names = sorted(a["venues"].keys() | b["venues"].keys(), key=lambda v: -(a["venues"].get(v, 0) + b["venues"].get(v, 0)))[:5]
    if names:
        vl = "".join(f'<li><span title="{esc(v)}">{esc(v)}</span><b class="lbA">{a["venues"].get(v, 0)}</b><b class="lbB">{b["venues"].get(v, 0)}</b></li>' for v in names)
        vl = f'<ul class="lm-vl">{vl}</ul>'
    else:
        vl = '<div class="lm-empty">우수 학회·저널 논문이 없어요.</div>'

    return (big(a, ta, wa, "A", b) + big(b, tb, wb, "B", a)
            + f'<div class="lm-t s4 out h300"><div class="tag hd"><div class="tt"><b>등급별 논문 수</b><span>우수 · 중위권 · 기타로 나눈 편수 (왼쪽 A, 오른쪽 B)</span></div><span>A ◀ ▶ B</span></div>{pyr}</div>'
            + f'<div class="lm-t s8 sand h280"><div class="tag hd"><div class="tt"><b>연도별 우수 논문</b><span>해마다 낸 전체 논문(빗금) 중 우수 학회·저널 논문(색)</span></div><span class="lm-legend"><span><i class="lm-hatch"></i>전체 논문</span>'
              f'<span><i style="background:{A}"></i>A 우수</span><span><i style="background:{B}"></i>B 우수</span></span></div>{yearly}</div>'
            + f'<div class="lm-t s4 blk h280"><div class="tag hd"><div class="tt"><b>자주 싣는 우수 학회·저널</b><span>우수 등급 중 논문을 많이 실은 곳</span></div><span>A &nbsp;&nbsp;&nbsp;&nbsp; B</span></div>{vl}</div>')


# ================================================================ 02 산학·외부 협업
def sheet_ind(m):
    a, b = m["A"]["ind"], m["B"]["ind"]
    w = lead_of(a["external_ratio"], b["external_ratio"], "%")
    ta, tb, wa, wb = _tiles_class(w)

    def big(r, cls, wt, slot):
        dark = _on_dark(cls)
        col = P["ON_" + slot] if dark else P["T" + slot]
        track = rgba(col, .2)
        return (f'<div class="lm-t s4 {cls} h300"><div class="tag hd"><div class="tt"><b><i>LAB {slot}</i>외부 기관 협업</b><span>다른 기관 사람과 함께 쓴 논문 비율 (같은 대학 공저자는 제외)</span></div></div>'
                f'<div class="lm-huge {wt} lm-mt">{r["external_ratio"]:.1f}<u>%</u></div>'
                f'<div class="lm-sub">{r["external"]} / {r["total"]}편 · 같은 대학 공저자 제외</div>'
                f'<div class="lm-foot"><div class="lm-row"><span>기업 공저</span><b style="font-weight:{700 if wt == "b" else 400}">{r["industry_ratio"]:.1f}%</b></div>'
                f'<div class="lm-gauge" style="background:{track}"><i style="width:{min(r["industry_ratio"], 100):.1f}%;background:{col}"></i></div></div></div>')

    def split(slot, r, c):
        v = [r["split"]["기업 협업"], r["split"]["기타 외부 기관"], r["split"]["내부 연구"]]
        lab = lambda x: f"{x:.0f}%" if x >= 12 else ""
        return (f'<div class="lm-split"><b style="color:{c}">{slot}</b><div class="bar">'
                f'<div style="width:{v[0]}%;background:{INK};color:{P['PAPER']};padding-left:12px;font-weight:700">{lab(v[0])}</div>'
                f'<div style="width:{v[1]}%;background:{HA};color:{P['PAPER'] if not DARK_MODE else INK};padding-left:10px">{lab(v[1])}</div>'
                f'<div class="lm-hatch" style="width:{v[2]}%;border:0;justify-content:flex-end;padding-right:14px">{lab(v[2])}</div></div></div>')

    # 연도별 기업 공저 비율 꺾은선
    ys = [y for y in YEARS if y in a["yearly"] or y in b["yearly"]]
    if ys:
        top_v = max([60] + list(a["yearly"].values()) + list(b["yearly"].values()))
        top_v = math.ceil(top_v / 20) * 20
        x = lambda i: 50 + i * 150
        y = lambda v: 180 - v / top_v * 160
        s = "".join(f'<line x1="40" x2="680" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{P['GRID']}" stroke-dasharray="2 4"/>'
                    f'<text x="0" y="{y(v) + 4:.1f}" font-family="IBM Plex Mono" font-size="11" fill="{MU}">{v}%</text>'
                    for v in range(20, top_v + 1, 20))
        s += f'<line x1="40" x2="680" y1="180" y2="180" stroke="{INK}"/>'
        for r, c, wt in ((b, B, 300), (a, A, 700)):
            pts = [(i, r["yearly"][yy]) for i, yy in enumerate(YEARS) if yy in r["yearly"]]
            if not pts:
                continue
            s += f'<polyline points="{" ".join(f"{x(i)},{y(v):.1f}" for i, v in pts)}" fill="none" stroke="{c}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>'
            s += "".join(f'<circle cx="{x(i)}" cy="{y(v):.1f}" r="6" fill="{c if j == len(pts) - 1 else P['SAND']}" stroke="{c}" stroke-width="3"/>' for j, (i, v) in enumerate(pts))
            li, lv = pts[-1]
            s += f'<text x="{x(li) + 14}" y="{y(lv) + 8:.1f}" font-family="Space Grotesk" font-size="24" font-weight="{wt}" fill="{P["TA"] if r is a else P["TB"]}">{lv:.0f}%</text>'
        s += "".join(f'<text x="{x(i)}" y="204" text-anchor="middle" font-family="IBM Plex Mono" font-size="12">{yy}</text>' for i, yy in enumerate(YEARS))
        trend = f'<svg width="100%" viewBox="0 0 760 220" style="margin-top:12px">{s}</svg>'
    else:
        trend = '<div class="lm-empty">연도별 정보가 없어요.</div>'

    # 파트너 기업 버블: A만 / 공통 / B만 (원 크기 = 공저 논문 수)
    pa = {p["name"]: p.get("count", 0) for p in a["partners"]}
    pb = {p["name"]: p.get("count", 0) for p in b["partners"]}
    if pa or pb:
        cols = [("A만", 80, P["BUB_A"], [(n, pa[n]) for n in pa if n not in pb]),
                ("공통", 240, P["BUB_C"], [(n, pa[n] + pb[n]) for n in pa if n in pb]),
                ("B만", 400, P["BUB_B"], [(n, pb[n]) for n in pb if n not in pa])]
        s = ""
        for title, cx, c, items in cols:
            s += f'<text x="{cx}" y="16" text-anchor="middle" font-family="IBM Plex Mono" font-size="11" fill="rgba(255,255,255,.55)">{title}</text>'
            yy = 30
            for n, v in sorted(items, key=lambda t: -t[1])[:3]:
                rr = 8 + math.sqrt(v) * 6
                yy += rr
                short = n if len(n) <= 14 else n[:13] + "…"
                s += (f'<circle cx="{cx}" cy="{yy:.1f}" r="{rr:.1f}" fill="{c}"/>'
                      f'<text x="{cx}" y="{yy + 6:.1f}" text-anchor="middle" font-family="Space Grotesk" font-weight="700" font-size="16" fill="{P['BUB_TXT']}">{v}</text>'
                      f'<text x="{cx}" y="{yy + rr + 14:.1f}" text-anchor="middle" font-size="11" fill="rgba(255,255,255,.78)">{esc(short)}</text>')
                yy += rr + 20
            if not items:
                s += f'<text x="{cx}" y="52" text-anchor="middle" font-size="12" fill="rgba(255,255,255,.35)">없음</text>'
        s += '<line x1="160" y1="28" x2="160" y2="226" stroke="rgba(255,255,255,.15)"/><line x1="320" y1="28" x2="320" y2="226" stroke="rgba(255,255,255,.15)"/>'
        bub = f'<svg width="100%" viewBox="0 0 480 240" style="margin-top:8px">{s}</svg>'
    else:
        bub = '<div class="lm-empty" style="color:rgba(255,255,255,.6)">함께 쓴 기업이 없어요.</div>'

    return (big(a, ta, wa, "A") + big(b, tb, wb, "B")
            + f'<div class="lm-t s4 out h300"><div class="tag hd"><div class="tt"><b>논문 구성</b><span>기업 공저 · 기타 외부 기관 · 내부 연구 비율 (합계 100%)</span></div></div><div style="margin-top:26px">{split("A", a, P["TA"])}{split("B", b, P["TB"])}</div>'
              f'<div class="lm-legend" style="margin-top:6px;color:{MU}"><span><i style="background:{INK}"></i>기업</span><span><i style="background:{HA}"></i>기타 외부</span><span><i class="lm-hatch"></i>내부</span></div></div>'
            + f'<div class="lm-t s7 sand h280"><div class="tag hd"><div class="tt"><b>연도별 기업 공저 비율</b><span>해마다 기업과 함께 쓴 논문의 비율</span></div><span class="lm-legend"><span><i style="background:{A}"></i>A</span><span><i style="background:{B}"></i>B</span></span></div>{trend}</div>'
            + f'<div class="lm-t s5 blk h280"><div class="tag hd"><div class="tt"><b>파트너 기업</b><span>함께 논문을 쓴 기업 · 원이 클수록 공저 논문이 많아요</span></div></div>{bub}</div>')


# ================================================================ 03 학제 간 융합도
def _sankey(left, right, color, pid):
    """팀원 생키와 같은 규칙: 같은 분야는 두 기간 공통 비중(min)으로 잇고, 늘어난 만큼은 '증가분'에서, 줄어든 만큼은 '감소분'으로"""
    fields = list(left.keys())
    inc = sum(max(right.get(f, 0) - left.get(f, 0), 0) for f in fields)
    dec = sum(max(left.get(f, 0) - right.get(f, 0), 0) for f in fields)
    L = [(f, left[f]) for f in fields if left[f] > 1e-9] + ([("증가분", inc)] if inc > 0.5 else [])
    R = [(f, right[f]) for f in fields if right.get(f, 0) > 1e-9] + ([("감소분", dec)] if dec > 0.5 else [])
    H, top, gap, x1, x2, wd = 196, 10, 10, 150, 410, 14
    last = {"L": -99, "R": -99}  # 라벨이 겹치지 않게 마지막 라벨 위치
    shades = [color, color + "CC", color + "99", color + "73", color + "55", color + "40"]

    def lay(arr):
        k = (H - gap * (len(arr) - 1)) / max(sum(v for _, v in arr), 1e-9)
        y, out = top, {}
        for n, v in arr:
            out[n] = [y, v * k, y]  # 시작 y, 높이, 다음 띠가 붙을 y
            y += v * k + gap
        return out, k
    lo, k = lay(L)
    ro, _ = lay(R)
    mid = (x1 + x2) / 2
    s = f'<defs>{_hatch(pid)}</defs>'

    def ribbon(src, dst, v, fill, extra=""):
        h = v * k
        if h < 0.5:
            return ""
        ya, yb = lo[src][2], ro[dst][2]
        lo[src][2] += h
        ro[dst][2] += h
        return (f'<path d="M{x1 + wd},{ya:.1f} C{mid},{ya:.1f} {mid},{yb:.1f} {x2},{yb:.1f} L{x2},{yb + h:.1f} '
                f'C{mid},{yb + h:.1f} {mid},{ya + h:.1f} {x1 + wd},{ya + h:.1f} Z" fill="{fill}" {extra}/>')
    for i, f in enumerate(fields):
        if f in lo and f in ro:
            s += ribbon(f, f, min(left[f], right.get(f, 0)), shades[i % 6], 'opacity=".55"')
    for i, f in enumerate(fields):
        d = left[f] - right.get(f, 0)
        if d > 0.5 and "감소분" in ro:
            s += ribbon(f, "감소분", d, f"url(#{pid})", f'stroke="{HA}" stroke-width=".6" opacity=".6"')
        if -d > 0.5 and "증가분" in lo:
            s += ribbon("증가분", f, -d, f"url(#{pid})", f'stroke="{HA}" stroke-width=".6" opacity=".6"')

    def node(x, n, y, h, i, side):
        special = n in ("증가분", "감소분")
        fill = INK if special else shades[i % 6]
        tx, anchor = (x - 10, "end") if side == "L" else (x + wd + 10, "start")
        val = left.get(n) if side == "L" else right.get(n)
        num = "" if special else f' <tspan font-family="Space Grotesk" fill="{MU}">{val:.0f}</tspan>'
        rect = f'<rect x="{x}" y="{y:.1f}" width="{wd}" height="{max(h, 2):.1f}" rx="4" fill="{fill}"/>'
        ly = max(y + h / 2 + 5, last[side] + 16)
        if ly > H + top + 8:
            return rect
        last[side] = ly
        return (rect + f'<text x="{tx}" y="{ly:.1f}" text-anchor="{anchor}" font-size="{12 if special else 14}" font-weight="{700 if i == 0 else 400}" fill="{MU if special else INK}">{esc(n)}{num}</text>')
    for i, (n, _) in enumerate(L):
        s += node(x1, n, lo[n][0], lo[n][1], fields.index(n) if n in fields else 9, "L")
    for i, (n, _) in enumerate(R):
        s += node(x2, n, ro[n][0], ro[n][1], fields.index(n) if n in fields else 9, "R")
    return f'<svg width="100%" viewBox="0 0 560 220" style="margin-top:14px">{s}</svg>'


def sheet_mix(m):
    a, b = m["A"]["mix"], m["B"]["mix"]
    va, vb = a["score"] or 0.0, b["score"] or 0.0
    w = lead_of(va, vb, "%")
    ta, tb, wa, wb = _tiles_class(w)

    def big(r, v, cls, wt, slot, other):
        sub = f'다분야 {r["cross_field"]} / 분류 {r["classified"]}편'
        if w == slot:
            sub += f' · {"B" if slot == "A" else "A"}보다 +{v - other:.1f}%p'
        val = "–" if r["score"] is None else f'{v:.1f}<u>%</u>'
        return (f'<div class="lm-t s4 {cls} h300"><div class="tag hd"><div class="tt"><b><i>LAB {slot}</i>학제 간 융합도</b><span>두 개 이상 분야에 걸친 논문의 비율</span></div></div>'
                f'<div class="lm-huge {wt} lm-mt">{val}</div><div class="lm-sub">{sub}</div>'
                f'<div class="lm-foot"><div class="lm-row"><span>가장 많이 쓴 분야</span><b style="font-size:20px;font-weight:500">{esc(r["main"] or "정보 없음")}</b></div></div></div>')

    def fmt(v):
        return "–" if v is None else f"{v:.0f}%"
    warn = [s for s, r in (("A", a), ("B", b)) if r["classified"] < 10 or (r["coverage"] or 0) < 70]
    warn_html = (f'<div class="lm-foot"><span class="lm-chip" style="color:#F2C46D">{"·".join(warn)} 해석 주의 · 분류 논문 10편 미만 또는 분류율 70% 미만</span></div>'
                 if warn else "")
    trust = (f'<div class="lm-t s4 blk h300"><div class="tag hd"><div class="tt"><b>데이터 신뢰도</b><span>분야가 분류된 논문 비율 · 분석에 쓴 논문 수</span></div><span>A &nbsp;&nbsp;&nbsp;&nbsp; B</span></div>'
             f'<ul class="lm-vl wide"><li><span>분야 분류율</span><b class="lbA">{fmt(a["coverage"])}</b><b class="lbB">{fmt(b["coverage"])}</b></li>'
             f'<li><span>분석 논문</span><b class="lbA">{a["total"]}</b><b class="lbB">{b["total"]}</b></li></ul>{warn_html}</div>')

    def flow(r, slot, c, pid):
        body = _sankey(r["left"], r["right"], c, pid) if r["left"] else '<div class="lm-empty">두 기간 모두 분류된 논문이 있어야 그릴 수 있어요.</div>'
        return (f'<div class="lm-t s6 sand h280"><div class="tag hd"><div class="tt"><b><i>LAB {slot}</i>연구 분야 변천</b><span>2021–23년 → 2024–25년, 분야별 비중(%p)이 어떻게 바뀌었나</span></div></div>{body}</div>')

    return big(a, va, ta, wa, "A", vb) + big(b, vb, tb, wb, "B", va) + trust + flow(a, "A", A, "h3a") + flow(b, "B", B, "h3b")


# ================================================================ 04 연구실 규모·사수
def _person(c, o):
    return (f'<svg viewBox="0 0 34 40"><circle cx="17" cy="11" r="8" fill="{c}" opacity="{o}"/>'
            f'<path d="M3 39 C3 26 9 22 17 22 C25 22 31 26 31 39 Z" fill="{c}" opacity="{o}"/></svg>')


def sheet_size(m):
    a, b = m["A"]["size"], m["B"]["size"]
    w = lead_of(a["active_members"], b["active_members"], "명")
    ta, tb, wa, wb = _tiles_class(w)
    style = lambda s: s.split(" ", 1)[-1]

    def big(r, cls, wt, slot):
        dark = _on_dark(cls)
        col = P["ON_" + slot] if dark else P["T" + slot]
        n_s, n_o = r["senior_count"], r["active_members"] - r["senior_count"]
        cap = 36
        shown_s, shown_o = min(n_s, cap), min(n_o, max(cap - n_s, 0))
        more = r["active_members"] - shown_s - shown_o
        icons = _person(col, 1) * shown_s + _person(col, .28) * shown_o + (f'<span class="more">+{more}</span>' if more > 0 else "")
        if not r["active_members"]:
            icons = '<span class="lm-empty">같은 기관 공저자 정보가 없어요</span>'
        return (f'<div class="lm-t s6 {cls} h300"><div class="tag hd"><div class="tt"><b><i>LAB {slot}</i>함께 쓴 구성원</b><span>교수님과 같은 기관에서 함께 논문을 쓴 사람</span></div><span>{esc(style(r["style"]))}</span></div>'
                f'<div class="lm-inline"><div class="lm-huge {wt}">{r["active_members"]}<u>명</u></div>'
                f'<div class="lm-sub">사수 후보 {n_s} · 일반 {n_o}</div></div><div class="lm-ppl">{icons}</div>'
                f'<div class="lm-key">{_person(col, 1)}<span>사수 후보 = 교수님과 2편 이상 함께 쓴 사람</span>{_person(col, .28)}<span>일반</span></div></div>')

    avg = (f'<div class="lm-t s4 blk h280"><div class="tag hd"><div class="tt"><b>논문당 평균 저자</b><span>논문 한 편에 이름을 올린 저자 수의 평균</span></div><span>A &nbsp;&nbsp;&nbsp;&nbsp; B</span></div>'
           f'<div style="display:flex;gap:30px;margin-top:40px;align-items:baseline">'
           f'<div class="lm-huge {"b" if a["avg_authors"] >= b["avg_authors"] else "l"} lbA" style="font-size:clamp(46px,4.8vw,72px)">{a["avg_authors"]:g}</div>'
           f'<div class="lm-huge {"b" if b["avg_authors"] > a["avg_authors"] else "l"} lbB" style="font-size:clamp(46px,4.8vw,72px)">{b["avg_authors"]:g}</div></div>'
           f'</div>')

    rows = list(a["distribution"].keys())
    mx = max(list(a["distribution"].values()) + list(b["distribution"].values()) + [1])
    k = 290 / mx
    s = ""
    for i, n in enumerate(rows):
        va, vb = a["distribution"][n], b["distribution"].get(n, 0)
        y = 14 + i * 64
        wa_, wb_ = max(va * k, 40 if va else 0), max(vb * k, 40 if vb else 0)
        s += (f'<rect x="{354 - wa_:.1f}" y="{y}" width="{wa_:.1f}" height="40" rx="20" fill="{A}" opacity="{1 if va >= vb else .35}"/>'
              f'<rect x="446" y="{y}" width="{wb_:.1f}" height="40" rx="20" fill="{B}" opacity="{1 if vb >= va else .35}"/>'
              f'<text x="400" y="{y + 25}" text-anchor="middle" font-size="13" font-weight="600">{esc(n)}</text>'
              f'<text x="{344 - wa_:.1f}" y="{y + 28}" text-anchor="end" font-family="Space Grotesk" font-size="22" font-weight="{700 if va >= vb else 300}" fill="{P["TA"]}">{va}</text>'
              f'<text x="{456 + wb_:.1f}" y="{y + 28}" font-family="Space Grotesk" font-size="22" font-weight="{700 if vb >= va else 300}" fill="{P["TB"]}">{vb}</text>')
    dist = (f'<div class="lm-t s8 out h280"><div class="tag hd"><div class="tt"><b>한 논문에 몇 명이 쓰나</b><span>저자 수 구간별 논문 편수 (왼쪽 A, 오른쪽 B)</span></div><span>A ◀ 논문 수 ▶ B</span></div>'
            f'<svg width="100%" viewBox="0 0 800 210" style="margin-top:16px">{s}</svg></div>')
    return big(a, ta, wa, "A") + big(b, tb, wb, "B") + avg + dist


# ================================================================ 05 연구 산출 연속성
SIG = {"green": (0, "#7FD39A", "꾸준함"), "yellow": (1, "#D9A93B", "주의"), "red": (2, "#D9705B", "공백 많음")}


def sheet_cont(m):
    a, b = m["A"]["cont"], m["B"]["cont"]
    w = lead_of(a["active_month_ratio"], b["active_month_ratio"], "%")
    ta, tb, wa, wb = _tiles_class(w)

    def big(r, cls, wt, slot):
        dark = _on_dark(cls)
        col = P["ON_" + slot] if dark else P["T" + slot]
        empty = rgba(col, .1 if dark else .13)
        peak = max(r["by_month"].values()) or 1
        cells = ""
        for y in YEARS:
            cells += f"<em>{y}</em>"
            for mth in range(1, 13):
                n = r["by_month"][(y, mth)]
                lv = 0 if n == 0 else min(4, 1 + int((n - 1) / peak * 4))
                cells += (f'<span title="{y}년 {mth}월 · {n}편" style="background:{col if lv else empty};opacity:{[1, .5, .68, .84, 1][lv]}"></span>')
        months = round(r["active_month_ratio"] * 60 / 100)
        gaps = ", ".join(map(str, r["gap_years"])) if r["gap_years"] else "없음"
        trend = f'{r["trend"]}배' if r["trend"] is not None else "판정 불가"
        return (f'<div class="lm-t s6 {cls}"><div class="tag hd"><div class="tt"><b><i>LAB {slot}</i>논문이 나온 달</b><span>최근 60개월을 한 칸씩 · 진할수록 그 달 논문이 많아요</span></div></div>'
                f'<div class="lm-inline"><div class="lm-huge {wt}">{r["active_month_ratio"]:.0f}<u>%</u></div>'
                f'<div class="lm-sub">60개월 중 {months}개월 · 공백 연도 {gaps} · 최근 {trend}</div></div><div class="lm-grass">{cells}</div></div>')

    # 연도별 논문 수 꺾은선 (공백 연도는 빗금 띠)
    top_v = max(list(a["by_year"].values()) + list(b["by_year"].values()) + [4])
    x = lambda i: 90 + i * 265
    y = lambda v: 170 - v / top_v * 150
    s = f'<defs>{_hatch("h5")}</defs>'
    for i, yy in enumerate(YEARS):
        who = [sl for sl, r in (("A", a), ("B", b)) if yy in r["gap_years"]]
        if who:
            s += (f'<rect x="{x(i) - 50}" y="10" width="100" height="160" rx="16" fill="url(#h5)" opacity=".7"/>'
                  f'<text x="{x(i)}" y="30" text-anchor="middle" font-family="IBM Plex Mono" font-size="11" fill="{MU}">{"·".join(who)} 공백</text>')
    s += f'<line x1="40" x2="1220" y1="170" y2="170" stroke="{INK}"/>'
    for r, c, wt in ((b, B, 300 if w != "B" else 700), (a, A, 700 if w != "B" else 300)):
        d = [r["by_year"][yy] for yy in YEARS]
        s += f'<polyline points="{" ".join(f"{x(i)},{y(v):.1f}" for i, v in enumerate(d))}" fill="none" stroke="{c}" stroke-width="4" stroke-linejoin="round"/>'
        s += "".join(f'<circle cx="{x(i)}" cy="{y(v):.1f}" r="6" fill="{P['SAND']}" stroke="{c}" stroke-width="3"/>' for i, v in enumerate(d))
        s += f'<text x="{x(4) + 16}" y="{y(d[4]) + 8:.1f}" font-family="Space Grotesk" font-size="26" font-weight="{wt}" fill="{P["TA"] if r is a else P["TB"]}">{d[4]}편</text>'
    s += "".join(f'<text x="{x(i)}" y="194" text-anchor="middle" font-family="IBM Plex Mono" font-size="12">{yy}</text>' for i, yy in enumerate(YEARS))
    line = (f'<div class="lm-t s12 sand"><div class="tag hd"><div class="tt"><b>연도별 논문 수</b><span>해마다 낸 논문 수 · 빗금은 논문이 없던 해</span></div><span class="lm-legend"><span><i style="background:{A}"></i>A</span>'
            f'<span><i style="background:{B}"></i>B</span><span><i class="lm-hatch"></i>공백 연도</span></span></div>'
            f'<svg width="100%" viewBox="0 0 1240 200" style="margin-top:12px">{s}</svg></div>')
    return lights(a, b) + big(a, ta, wa, "A") + big(b, tb, wb, "B") + line


LAMPS = (("red", "#E5484D"), ("yellow", "#F5B83D"), ("green", "#3DBE6B"))
SIG_TEXT = {"green": ("꾸준함", "5년 내내 논문이 나왔고 최근에도 페이스가 유지돼요"),
            "yellow": ("주의", "공백 연도가 1년 있거나 최근 논문 수가 줄었어요"),
            "red": ("공백 많음", "논문이 나오지 않은 해가 2년 이상이에요")}


def lights(a, b):
    """지표 5의 핵심: 연구실별 신호등 (빨강·노랑·초록 중 하나에 불이 켜짐)"""
    def one(slot, r):
        sig = r["signal"]
        lamps = "".join(f'<i class="{"on" if k == sig else ""}" style="--c:{c}"></i>' for k, c in LAMPS)
        name, why = SIG_TEXT[sig]
        c_on = dict(LAMPS)[sig]
        return (f'<div class="lm-light"><span class="sl">LAB {slot}</span><span class="box">{lamps}</span>'
                f'<div><b style="color:{c_on}">{name}</b><p>{why}</p></div></div>')
    return (f'<div class="lm-t s12 blk">{H5("꾸준함 신호등", "공백 연도와 최근 논문 추세로 매긴 신호 · 초록 꾸준함 / 노랑 주의 / 빨강 공백 많음")}'
            f'<div class="lm-lights">{one("A", a)}{one("B", b)}</div></div>')


def H5(t, d):
    return f'<div class="tag hd"><div class="tt"><b>{t}</b><span>{d}</span></div></div>'


def _fold_bg(i):
    """뒤로 갈수록 살짝 진한 종이 (겹친 층이 보이게)"""
    paper = P["PAPER"] if DARK_MODE else "#FBFAF7"
    deep = "#26262E" if DARK_MODE else "#E4E0D7"
    return blend(deep, paper, min(i * .2, .8))


def folders_html(order, m, chosen, title):
    """지표 5장을 인덱스 폴더처럼 겹쳐 둠. 맨 위 장만 열려 있고, 다른 장을 누르면 그 장이 열림"""
    parts = []
    for i, q in enumerate(order):
        a, b, unit, _ = headline(m, q["key"])
        w = lead_of(a, b, unit)
        va, vb = f"A {_fmt(a, unit)}{unit}", f"B {_fmt(b, unit)}{unit}"
        ab = (f'<b style="color:var(--tinA)">{va}</b><s style="color:var(--tinB)">{vb}</s>' if w == "A" else
              f'<s style="color:var(--tinA)">{va}</s><b style="color:var(--tinB)">{vb}</b>' if w == "B" else
              f'<span style="color:var(--tinA)">{va}</span><span style="color:var(--tinB)">{vb}</span>')
        star = '<span class="mine">★ 내 기준</span>' if q["key"] in chosen else "<span></span>"
        parts.append(
            f'<details class="lm-fold" name="lmfold"{" open" if i == 0 else ""} style="--i:{i};--fbg:{_fold_bg(i)}">'
            f'<summary><span class="lm-ftab">{q["no"]}<b>{esc(q["chip"])}</b></span><span class="no">{q["no"]}</span>'
            f'<span class="q">{esc(q["q"])}</span><span class="ab">{ab}</span>{star}<span class="chev">↓</span></summary>'
            f'<div class="lm-fbody"><div class="lm-g">{SHEETS[q["key"]](m)}</div>'
            f'<div class="lm-slidefoot"><span>LABMATCH</span><span>{esc(title)}</span><span>{i + 1:02d} / {len(order):02d}</span></div>'
            f'<div class="lm-savebar"><button type="button" class="lm-xbtn" data-lmx="png" data-i="{i}">이 장 이미지(PNG)로 저장</button></div></div></details>')
    return (f'<div class="lm" data-title="{esc(title)}"><div class="lm-hintrow"><p class="lm-hint2">장을 누르면 펼쳐져요. 한 번에 한 장씩 열려요.</p>'
            f'<button type="button" class="lm-xbtn" data-lmx="pdf">다섯 장 모두 PDF로 저장</button></div>'
            f'<div class="lm-folders">{"".join(parts)}</div></div>')


SHEETS = {"top": sheet_top, "ind": sheet_ind, "mix": sheet_mix, "size": sheet_size, "cont": sheet_cont}
