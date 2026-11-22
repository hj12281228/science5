"""영문(로마자) 한국인 이름 → 한글 이름

- OpenAlex가 모아 둔 이름 표기(display_name_alternatives)에 한글이 있고 영문 이름과 소리가 맞으면 그것을 씀
- 없으면 로마자 음절을 한글 음절로 바꿈 (가장 흔한 음절 하나만 골라서, 동음이의 글자는 틀릴 수 있음)
- 한국식 이름이 아니면(외국인 연구자 등) None
"""

import re

# 영문 성 → 한글 성
SURNAME_KO = {
    "kim": "김", "gim": "김", "lee": "이", "yi": "이", "rhee": "이", "park": "박", "pak": "박", "bak": "박", "choi": "최", "choe": "최",
    "jung": "정", "jeong": "정", "chung": "정", "cheong": "정", "kang": "강", "cho": "조", "jo": "조", "yoon": "윤", "yun": "윤",
    "jang": "장", "chang": "장", "lim": "임", "im": "임", "han": "한", "oh": "오", "seo": "서", "suh": "서", "shin": "신", "sin": "신",
    "kwon": "권", "hwang": "황", "ahn": "안", "an": "안", "song": "송", "yoo": "유", "yu": "유", "ryu": "류", "hong": "홍", "jeon": "전",
    "chun": "전", "go": "고", "ko": "고", "moon": "문", "mun": "문", "yang": "양", "son": "손", "sohn": "손", "bae": "배", "baek": "백",
    "paik": "백", "heo": "허", "huh": "허", "nam": "남", "noh": "노", "roh": "노", "no": "노", "ha": "하", "kwak": "곽", "seong": "성",
    "sung": "성", "cha": "차", "joo": "주", "ju": "주", "woo": "우", "wu": "우", "min": "민", "na": "나", "ra": "라", "jin": "진",
    "chin": "진", "ji": "지", "chi": "지", "eom": "엄", "um": "엄", "byun": "변", "byeon": "변", "pyo": "표", "won": "원", "chae": "채",
    "cheon": "천", "bang": "방", "kong": "공", "hyun": "현", "hyeon": "현", "ham": "함", "yeo": "여", "yeom": "염", "yum": "염",
    "shim": "심", "sim": "심", "do": "도", "seok": "석", "suk": "석", "sun": "선", "sunwoo": "선우", "gu": "구", "koo": "구", "ku": "구",
    "maeng": "맹", "myung": "명", "myeong": "명", "tak": "탁", "ye": "예", "ok": "옥", "kil": "길", "gil": "길", "wang": "왕",
    "ryoo": "류", "yook": "육", "yuk": "육", "in": "인", "ma": "마", "jee": "지", "kee": "기", "ki": "기", "hahn": "한", "kye": "계",
}
SURNAME_KO.update({"rha": "나", "koo": "구", "pan": "판", "yon": "연", "chu": "추", "choo": "추", "paek": "백", "rho": "노", "youn": "윤",
    "lyu": "류", "hur": "허", "joh": "조", "shon": "손", "kweon": "권", "jhang": "장", "jhung": "정", "bahk": "박", "nho": "노",
    "pyun": "편", "hahm": "함", "cheong": "정", "eun": "은", "joung": "정", "uhm": "엄", "pack": "박", "you": "유", "suhr": "서",
    "koh": "고", "jun": "전", "rhim": "임", "pae": "배", "kweon": "권"})
# 이름에 흔한 음절의 로마자 표기 → 한글 (가장 흔한 한자음 하나만)
SYL = {}
def add(h, *roms):
    for r in roms: SYL.setdefault(r, h)
for h, r in [
 ("가","ga ka"),("각","gak kak"),("간","gan kan"),("갑","gap kap"),("강","gang kang"),("개","gae kae"),("건","geon gun kun keon"),("걸","geol"),
 ("겸","gyeom kyeom kyum"),("경","gyeong kyeong kyung kyoung gyung kyong"),("계","gye kye"),("고","go ko"),("곤","gon kon"),("공","gong kong"),("관","gwan kwan"),
 ("광","gwang kwang"),("교","gyo kyo"),("구","gu koo ku goo"),("국","guk kuk kook gook"),("군","gun kun"),("권","gwon kwon"),("규","gyu kyu"),("균","gyun kyun"),
 ("근","geun keun kun"),("금","geum keum kum"),("기","gi ki kee gee"),("길","gil kil"),("나","na"),("난","nan"),("남","nam"),("내","nae"),("녕","nyeong nyoung"),
 ("노","no noh"),("는","neun"),("다","da"),("단","dan"),("담","dam"),("대","dae dai"),("덕","deok duk dok"),("도","do doh"),("돈","don"),("동","dong"),
 ("두","du doo"),("득","deuk"),("라","ra la"),("락","rak"),("란","ran"),("람","ram"),("래","rae"),("량","ryang"),("려","ryeo"),("련","ryeon"),("렬","ryeol yeol"),
 ("례","rye"),("로","ro"),("록","rok"),("룡","ryong"),("류","ryu"),("륜","ryun"),("률","ryul"),("름","reum"),("리","ri lee"),("린","rin lin"),("림","rim"),
 ("마","ma"),("만","man"),("명","myeong myung myoung"),("모","mo"),("목","mok"),("무","mu moo"),("문","mun moon"),("미","mi mee"),("민","min"),
 ("바","ba"),("박","bak pak park"),("반","ban"),("방","bang"),("배","bae"),("백","baek paik baik"),("범","beom bum"),("법","beop"),("벽","byeok"),
 ("변","byeon byun"),("병","byeong byung byoung"),("보","bo"),("복","bok"),("봉","bong"),("부","bu boo"),("비","bi"),("빈","bin"),("빛","bit"),
 ("사","sa"),("산","san"),("삼","sam"),("상","sang"),("새","sae"),("생","saeng"),("서","seo suh"),("석","seok suk sok"),("선","seon sun"),("설","seol sul"),
 ("섭","seop sub sup"),("성","seong sung soung"),("세","se"),("소","so"),("솔","sol"),("송","song"),("수","su soo"),("숙","suk sook"),("순","sun soon"),
 ("술","sul"),("숭","sung"),("슬","seul"),("승","seung"),("시","si shi"),("식","sik shik"),("신","sin shin"),("실","sil"),("심","sim shim"),
 ("아","a"),("안","an ahn"),("애","ae"),("양","yang"),("언","eon"),("엄","eom um"),("여","yeo yo"),("연","yeon yun youn"),("열","yeol yul"),
 ("염","yeom"),("엽","yeop yup"),("영","yeong young yong"),("예","ye"),("오","o oh"),("옥","ok"),("완","wan"),("왕","wang"),("요","yo"),("용","yong"),
 ("우","u woo wu"),("욱","uk wook ook"),("운","un woon"),("웅","ung woong"),("원","won weon"),("월","wol"),("위","wi"),("유","yu yoo"),("윤","yun yoon"),
 ("율","yul"),("은","eun"),("을","eul"),("음","eum"),("응","eung"),("의","ui eui"),("이","i yi"),("익","ik"),("인","in"),("일","il"),("임","im"),
 ("자","ja"),("작","jak"),("잔","jan"),("재","jae jai"),("전","jeon jun"),("정","jeong jung joung chung"),("제","je"),("조","jo cho"),("종","jong"),
 ("주","ju joo"),("준","jun joon"),("중","jung joong"),("지","ji jee"),("직","jik"),("진","jin"),("집","jip"),("찬","chan"),("창","chang"),("채","chae"),
 ("천","cheon chun"),("철","cheol chul"),("청","cheong"),("초","cho"),("춘","chun"),("충","chung choong"),("치","chi"),("칠","chil"),
 ("탁","tak"),("태","tae"),("택","taek"),("평","pyeong pyung"),("표","pyo"),("필","pil phil"),("하","ha"),("학","hak"),("한","han"),("해","hae"),
 ("행","haeng"),("향","hyang"),("허","heo"),("혁","hyeok hyuk"),("현","hyeon hyun hyoun"),("협","hyeop"),("형","hyeong hyung"),("혜","hye"),
 ("호","ho"),("홍","hong"),("화","hwa"),("환","hwan"),("황","hwang"),("회","hoe hoi"),("효","hyo"),("후","hu hoo"),("훈","hun hoon"),("휘","hwi"),
 ("희","hui hee heui hi"),("흠","heum"),("근","geun"),("규","kyu"),("겸","kyeom"),("솜","som"),("별","byeol byul"),("늘","neul"),("슬","seul"),
 ("담","dam"),("람","lam"),("뢰","roe"),("륭","ryung"),("녀","nyeo"),("년","nyeon"),("농","nong"),("탄","tan"),("통","tong"),("판","pan"),("팔","pal"),
 ("포","po"),("품","pum"),("풍","pung"),("행","haeng"),("헌","heon hun"),("혼","hon"),("홀","hol"),("후","hu"),("흥","heung"),("칠","chil"),
 ("규","gyu"),("곤","gon"),("길","gil"),("녹","nok"),("단","dan"),("돌","dol"),("두","du"),("래","rae lae"),("렴","ryeom"),("롱","rong"),
 ("명","myong"),("묵","muk"),("미","mi"),("빈","been"),("상","shang"),("새","sae"),("섬","seom"),("시","see"),("아","ah"),("엽","yeop"),
 ("영","yung"),("예","yea"),("온","on"),("완","wan"),("욱","wook"),("웅","woong"),("유","you"),("은","eun"),("인","een"),("재","jay"),
 ("중","joong"),("지","gee"),("찬","chan"),("철","chol"),("태","tai"),("하","hah"),("혁","hyuk"),("현","hyon"),("훈","hoon"),("희","hie"),
]:
    add(h, *r.split())
# 같은 로마자가 여러 음절에 쓰일 때 이름에 더 흔한 쪽
SYL.update({"yop": "엽", "myon": "면", "ick": "익", "heon": "헌", "whan": "환", "byoel": "별", "jun": "준", "yong": "용", "yeol": "열", "kun": "근", "youn": "윤", "yun": "윤", "chun": "천", "sung": "성", "hun": "훈",
            "chung": "정", "chong": "종", "suh": "서", "seock": "석", "bon": "본", "eue": "의", "whi": "휘", "hang": "항", "wuk": "욱",
            "hyoung": "형", "shick": "식", "keon": "건", "kwon": "권", "yeob": "엽", "yeop": "엽", "beum": "범", "yeoul": "열", "yeog": "역",
            "byeng": "병", "gwan": "관", "kwan": "관", "kyu": "규", "hwi": "휘", "seob": "섭", "sub": "섭", "wha": "화", "whan": "환",
            "gul": "걸", "kyo": "교", "soung": "성", "joon": "준", "jae": "재", "un": "운", "ung": "웅", "eon": "언", "uk": "욱", "ill": "일",
            "hwa": "화", "sang": "상", "bin": "빈", "gyu": "규", "gun": "건", "geon": "건", "ryeol": "렬", "suk": "석", "sook": "숙", "yoo": "유"})
SYL_KEYS = sorted(SYL, key=len, reverse=True)

def segment(word):
    """붙여 쓴 로마자 이름을 음절로 나누기 (가능한 분할 중 음절 수가 적고 긴 음절을 먼저)"""
    word = word.lower()
    best = {0: []}
    for i in range(len(word)):
        if i not in best: continue
        for k in SYL_KEYS:
            if word.startswith(k, i):
                j = i + len(k); cand = best[i] + [k]
                if j not in best or (len(cand), [-len(x) for x in cand]) < (len(best[j]), [-len(x) for x in best[j]]): best[j] = cand
    return best.get(len(word))



ROMS = {}
for _r, _h in SYL.items():
    ROMS.setdefault(_h, set()).add(_r)


def split_name(name, surname_map=SURNAME_KO):
    """영문 이름 → (성 로마자, 이름 로마자 목록). 한국식 이름이 아니면 None"""
    parts = [p for p in re.split(r"[\s.\-‐–]+", name.strip()) if p]
    if len(parts) < 2 or any(len(p) == 1 for p in parts):
        return None
    low = [p.lower() for p in parts]
    if low[-1] in surname_map:
        return low[-1], low[:-1]
    if low[0] in surname_map:
        return low[0], low[1:]
    return None


def fits(hangul_given, roman_given):
    """한글 이름(성 뺀 부분)이 로마자 표기와 맞는지 (예: 경호 ↔ kyungho)"""
    g = "".join(roman_given)
    def go(i, k):
        if k == len(hangul_given):
            return i == len(g)
        return any(g.startswith(r, i) and go(i + len(r), k + 1) for r in ROMS.get(hangul_given[k], ()))
    return go(0, 0)


def to_hangul(name, surname_map=SURNAME_KO):
    sp = split_name(name, surname_map)
    if not sp:
        return None
    sur, given = sp
    syls = []
    for g in given:
        seg = [g] if g in SYL else segment(g)
        if not seg:
            return None
        syls += seg
    if not 1 <= len(syls) <= 2:
        return None
    return surname_map[sur] + "".join(SYL[s] for s in syls)


def korean_name(display_name, alternatives=None, surname_map=SURNAME_KO):
    """한글 이름 고르기: OpenAlex 한글 표기 중 영문 이름과 소리가 맞는 것 → 없으면 로마자를 한글로 바꾼 것 → 둘 다 없으면 None
    돌려주는 값: (한글 이름, 출처 'openalex' | 'romaja')"""
    sp = split_name(display_name, surname_map)
    if not sp:
        return None, None
    sur, given = sp
    sk = surname_map[sur]
    for alt in alternatives or []:
        h = alt.replace(" ", "")
        if re.fullmatch(r"[가-힣]{2,4}", h) and h.startswith(sk) and fits(h[len(sk):], given):
            return h, "openalex"
    h = to_hangul(display_name, surname_map)
    return (h, "romaja") if h else (None, None)
