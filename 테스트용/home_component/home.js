// LABMATCH 첫 화면 컴포넌트 (st.components.v2)
// Python이 data로 넘겨주는 것: slots, yonsei, fields(스냅샷), search(검색 결과)
// Python으로 보내는 것: setTriggerValue('event', {type: 'slots' | 'search' | 'compare', ...})

const UI = { mode: 'hero', dept: null, idx: 0, field: null, sub: null, showAll: false, help: false, drop: false, q: '', popSlot: null };

const UNI_KO = {
  'Yonsei University': '연세대', 'Seoul National University': '서울대', 'Korea Advanced Institute of Science and Technology': 'KAIST',
  'Pohang University of Science and Technology': 'POSTECH', 'Korea University': '고려대', 'Sungkyunkwan University': '성균관대',
  'Hanyang University': '한양대', 'Ulsan National Institute of Science and Technology': 'UNIST', 'Ewha Womans University': '이화여대',
  'Kyungpook National University': '경북대', 'Pusan National University': '부산대', 'Gwangju Institute of Science and Technology': 'GIST',
  'Daegu Gyeongbuk Institute of Science and Technology': 'DGIST', 'Kyung Hee University': '경희대', 'Chung-Ang University': '중앙대',
  'Sogang University': '서강대', 'Seoul National University Hospital': '서울대병원', 'Samsung Medical Center': '삼성서울병원',
  'Asan Medical Center': '서울아산병원', 'Severance Hospital': '세브란스병원', 'Chonnam National University': '전남대',
  'Chungnam National University': '충남대', 'Inha University': '인하대', 'Ajou University': '아주대', 'Konkuk University': '건국대',
  'Dongguk University': '동국대', 'Hankuk University of Foreign Studies': '한국외대', 'University of Seoul': '서울시립대',
  'Korea Institute of Science and Technology': 'KIST', 'Catholic University of Korea': '가톨릭대', 'Chonbuk National University': '전북대',
  'Jeonbuk National University': '전북대', 'Chungbuk National University': '충북대', 'Gyeongsang National University': '경상국립대',
  'Kangwon National University': '강원대', 'Hallym University': '한림대', 'Sejong University': '세종대', 'Kookmin University': '국민대',
  'Yeungnam University': '영남대', 'Gachon University': '가천대', 'Pukyong National University': '부경대', 'Jeju National University': '제주대',
  'Inje University': '인제대', 'Kwangwoon University': '광운대', 'Dankook University': '단국대', 'Chosun University': '조선대', 'University of Ulsan': '울산대',
  'Incheon National University': '인천대', 'Seoul National University of Science and Technology': '서울과기대', 'Changwon National University': '창원대',
  'Kunsan National University': '군산대', 'Kumoh National Institute of Technology': '금오공대', 'Korea Maritime and Ocean University': '한국해양대',
  'Sangmyung University': '상명대', 'Soongsil University': '숭실대', 'Hongik University': '홍익대', 'Kyonggi University': '경기대', 'Joongbu University': '중부대',
  'Woosong University': '우송대', 'Konyang University': '건양대', 'Kongju National University': '공주대', 'Kyungsung University': '경성대',
  "Sungshin Women's University": '성신여대', "Sookmyung Women's University": '숙명여대', 'Korea University of Technology and Education': '한국기술교육대',
  'Hannam University': '한남대', 'Hankyong National University': '한경국립대', 'Wonkwang University': '원광대', 'Keimyung University': '계명대',
  'Sahmyook University': '삼육대', 'Dong-A University': '동아대', 'Sunchon National University': '순천대', 'Korea National University of Transportation': '한국교통대',
  'Tongmyong University': '동명대', 'Mokpo National University': '목포대', "Dongduk Women's University": '동덕여대', 'Gangneung–Wonju National University': '강릉원주대',
  'Hanbat National University': '한밭대', 'Cheongju University': '청주대', 'Soonchunhyang University': '순천향대', 'Jeonju University': '전주대',
  'Daegu Catholic University': '대구가톨릭대', 'Sun Moon University': '선문대', 'Korea National University of Education': '한국교원대', 'Daegu National University of Education': '대구교대',
  'Cheju Halla University': '제주한라대', 'Myongji University': '명지대', 'Kyungnam University': '경남대', 'Hoseo University': '호서대', 'Daegu University': '대구대',
  'Kangwon National University Hospital': '강원대병원', 'Hanyang University Hospital': '한양대병원', 'Korea University Anam Hospital': '고려대안암병원',
  'Korea University Ansan Hospital': '고려대안산병원', 'Korea University Guro Hospital': '고려대구로병원', 'Seoul National University Bundang Hospital': '서울대분당병원',
  'Pusan National University Hospital': '부산대병원', 'Pusan National University Yangsan Hospital': '양산부산대병원', 'Pusan National University Dental Hospital': '부산대치과병원',
  'Chung-Ang University Hospital': '중앙대병원', 'Ajou University Hospital': '아주대병원', 'Kyung Hee University Hospital': '경희대병원', 'Inha University Hospital': '인하대병원',
  'Yonsei University Health System': '연세의료원', 'Gangnam Severance Hospital': '강남세브란스병원', 'Samsung (South Korea)': '삼성전자', 'Korea Institute of Science and Technology Information': 'KISTI',
  'Korea Research Institute of Chemical Technology': '화학연', 'Korea Atomic Energy Research Institute': '원자력연', 'Korea Institute of Geoscience and Mineral Resources': '지질자원연',
  'Institute for Basic Science': 'IBS', 'Korea Institute of Ocean Science and Technology': '해양과기원', 'Electronics and Telecommunications Research Institute': 'ETRI',
  'Korea Institute of Materials Science': '재료연', 'Korea Astronomy and Space Science Institute': '천문연', 'Korea Polar Research Institute': '극지연',
  'Rural Development Administration': '농촌진흥청', 'Korea Disease Control and Prevention Agency': '질병관리청', 'National Cancer Center': '국립암센터',
  'Korea Institute for International Economic Policy': '대외경제정책연', 'International Vaccine Institute': '국제백신연', 'Korea Basic Science Institute': '기초과학지원연',
  'Korea Institute for Advanced Study': '고등과학원', 'Korea Institute of Energy Research': '에너지연', 'Korea National Institute of Health': '국립보건연',
  'Korea Institute of Oriental Medicine': '한의학연', 'National Institute of Environmental Research': '국립환경과학원', 'National Institute of Fisheries Science': '수산과학원',
  'World Institute of Kimchi': '세계김치연', 'The Seoul Institute': '서울연구원', 'Korea Institute of Industrial Technology': '생기연', 'Korea Institute of Machinery and Materials': '기계연',
  'Korea Electrotechnology Research Institute': '전기연', 'Korea Institute of Civil Engineering and Building Technology': '건설연', 'Korea Food Research Institute': '식품연',
  'Korea Research Institute of Bioscience and Biotechnology': '생명연', 'Korea Research Institute of Standards and Science': '표준연', 'Korea Institute of Toxicology': '안전성평가연',
  "The Catholic University of Korea Seoul St. Mary's Hospital": '서울성모병원', "Seoul St. Mary's Hospital": '서울성모병원', "The Catholic University of Korea St. Vincent's Hospital": '성빈센트병원',
  'Keimyung University Dongsan Medical Center': '계명대동산병원', 'Jeju National University Hospital': '제주대병원', 'Dong-A University Hospital': '동아대병원', 'SUNY Korea': '한국뉴욕주립대',
};
const uniKo = (s) => (s && UNI_KO[s]) || s || '소속 정보 없음';
const isYonsei = (s) => !!s && /Yonsei|연세/.test(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
// 학교 배지: logos에 파일이 있으면 로고, 없으면 글자 배지 (한글 이름은 앞 두 글자, 영문은 대문자 머리글자)
const badgeText = (s) => {
  s = String(s || '').trim();
  if (!s) return '?';
  if (/[가-힣]/.test(s)) return s.replace(/(대학교|대학|대)$/, '').slice(0, 2) || s.slice(0, 2);
  const caps = s.split(/\s+/).filter((w) => /^[A-Z]/.test(w) && !/^(Of|And|The|For)$/i.test(w)).map((w) => w[0]).join('');
  return (caps || s).slice(0, 4);
};
const fmtGrowth = (g) => (g == null ? '' : (g >= 0 ? '+' : '') + Math.round(g * 100) + '%');

function ensureFonts() {
  if (document.getElementById('lm-fonts')) return;
  const l = document.createElement('link');
  l.id = 'lm-fonts'; l.rel = 'stylesheet';
  l.href = 'https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap';
  document.head.appendChild(l);
}

const HTML = `
<div class="lm">
  <div class="top"><div class="logo">LAB<i>MATCH</i></div><button class="ghost" data-act="help" type="button">이용 안내</button></div>
  <div class="hero">
    <div>
      <h1>어느 연구실이 나에게 맞을까?</h1>
      <p class="lead">교수님 두 분을 고르면 최근 논문으로 5가지 지표를 비교합니다.</p>
      <div class="searchbox">
        <div class="searchrow">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input class="q" type="text" autocomplete="off" placeholder="교수님 성함 (한글/영문)" aria-label="교수님 성함">
          <button class="go" data-act="search" type="button">검색</button>
        </div>
        <div class="modes">
          <button class="mode" data-mode="hero" type="button">이름으로 찾기</button>
          <button class="mode" data-mode="dept" type="button">연세대 학과로 둘러보기</button>
          <button class="mode" data-mode="field" type="button">분야별 연구자 찾기</button>
        </div>
        <div class="drop" hidden></div>
      </div>
      <div class="suggest">
        <div class="lbl">아는 교수님이 없다면 이렇게 시작해 보세요</div>
        <button type="button" data-mode="dept"><span>↳</span>내 전공 학과 교수님 둘러보기</button>
        <button type="button" data-mode="field"><span>↳</span>요즘 논문이 많이 나오는 분야의 전국 연구자 보기</button>
        <button type="button" data-act="sample"><span>↳</span><span class="sample-label" style="color:inherit"></span></button>
      </div>
    </div>
    <div class="arena" aria-label="비교할 연구실">
      <div class="arena-top"><b>비교할 연구실</b><span class="count"></span></div>
      <div class="duel"><div class="pc A"></div><div class="vs">VS</div><div class="pc B"></div></div>
      <button class="cta" data-act="compare" type="button">비교 시작</button>
      <div class="cta-hint"></div>
    </div>
  </div>
  <section class="sec-dept">
    <div class="sh"><h2>연세대 학과로 둘러보기</h2><p class="dept-cap"></p></div>
    <div class="dept-browser">
      <nav class="dcol" aria-label="단과대학"><div class="dh">단과대학</div><div class="dlist dept-cols"></div></nav>
      <nav class="ddep" aria-label="학과"><div class="dh dep-h">학과</div><div class="dlist dept-chips"></div></nav>
      <div class="dpane">
        <div class="dh prof-h">교수님</div>
        <div class="dept-names" role="list" aria-label="이 학과 교수님 (가나다순)"></div>
        <div class="strip"><button class="nav l" data-act="prev" type="button" aria-label="이전">‹</button><button class="nav r" data-act="next" type="button" aria-label="다음">›</button></div>
        <div class="dots"></div>
      </div>
    </div>
  </section>
  <section class="sec-field">
    <div class="sh"><h2>분야별 국내 연구자 별자리</h2><p>점 하나가 연구자 한 명, 선은 최근 3년 함께 논문을 쓴 사이예요. 클수록 논문이 많아요. 돌려 보고, 점을 끌어 떼어 놓고, 눌러서 공저자를 따라가 보세요.</p></div>
    <div class="field-body"></div>
  </section>
  <div class="scrim" hidden>
    <div class="modal" role="dialog" aria-modal="true" aria-label="이용 안내">
      <button class="close" data-act="close" type="button" aria-label="닫기">✕</button>
      <h3>이용 안내</h3>
      <p class="msub">예비 대학원생이 연구실을 고를 때 궁금한 다섯 가지를 논문 데이터로 보여드려요.</p>
      <div class="steps">
        <div class="step"><b>STEP 1</b><p>이름, 학과, 분야로 교수님 찾기</p></div>
        <div class="step"><b>STEP 2</b><p>A, B에 한 분씩 담기</p></div>
        <div class="step"><b>STEP 3</b><p>5가지 지표 비교 후 리포트 저장</p></div>
      </div>
      <table>
        <tr><th>지표</th><th>이런 질문에 답해요</th></tr>
        <tr><td>① 우수 학회·저널 비중</td><td>주요 학회와 저널에 얼마나 자주 싣나요?</td></tr>
        <tr><td>② 산학·외부 협업 비율</td><td>기업 과제 중심인가요, 학술 연구 중심인가요?</td></tr>
        <tr><td>③ 학제 간 융합도</td><td>다른 전공 출신도 적응할 수 있을까요?</td></tr>
        <tr><td>④ 연구실 규모·사수</td><td>질문할 선배와 동료가 얼마나 있나요?</td></tr>
        <tr><td>⑤ 연구 산출 연속성</td><td>논문이 꾸준히 나오나요?</td></tr>
      </table>
      <ul>
        <li>동명이인은 소속 기관으로 구분합니다.</li>
        <li>최근 논문 100편을 분석하며, 핵심 지표는 2021~2025년 기준입니다.</li>
        <li>연구실 분위기, 인건비처럼 논문에 없는 정보는 면담에서 확인하세요.</li>
      </ul>
    </div>
  </div>
</div>`;

export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  ensureFonts();
  const D = data || {};
  const slots = { A: (D.slots && D.slots.A) || null, B: (D.slots && D.slots.B) || null };
  const YON = (D.yonsei || []).map((p) => ({ ...p, key: 'y:' + p.col + '|' + p.dept + '|' + p.name, aff: `연세대 ${p.dept}`, school: '연세대', sub: p.dept, tags: p.tags || [], works_label: p.works != null ? (p.yonsei ? '최근 5년 논문' : '전체 논문') : undefined }));
  const LOGOS = D.logos || {};
  // 학교 로고: 이름이 같은 로고, 없으면 앞부분이 같은 가장 긴 로고 (예: 서울대병원 → 서울대)
  const LOGO_KEYS = Object.keys(LOGOS).sort((a, b) => b.length - a.length);
  const logoKey = (school) => (school && (LOGOS[school] ? school : LOGO_KEYS.find((k) => school.startsWith(k)))) || null;
  const badge = (school, cls = '') => logoKey(school)
    ? `<span class="badge ${cls}"><img src="${LOGOS[logoKey(school)]}" alt="${esc(school)}"></span>`
    : `<span class="badge txt ${cls}" aria-label="${esc(school)}">${esc(badgeText(school))}</span>`;
  const FS = D.fields || null;

  let root = parentElement.querySelector('.lm');
  if (!root) {
    const holder = document.createElement('div');
    holder.innerHTML = HTML;
    parentElement.appendChild(holder);
    root = holder.querySelector('.lm');
  }
  // 다크모드: Streamlit의 실제 배경색으로 테마를 알아내서 색을 바꿈.
  // (메뉴에서 Light/Dark를 바꾸면 파이썬은 다시 실행되지 않으므로, 여기서 0.4초마다 확인해서 바로 따라감)
  const hostEl = parentElement instanceof Element ? parentElement : parentElement.host;
  const detectDark = () => {
    const v = (getComputedStyle(hostEl).getPropertyValue('--st-background-color') || '').trim();
    const m = v.match(/^#?([0-9a-f]{6})$/i);
    if (!m) return null;
    const n = parseInt(m[1], 16);
    return (0.2126 * (n >> 16 & 255) + 0.7152 * (n >> 8 & 255) + 0.0722 * (n & 255)) / 255 < 0.5;
  };
  const applyTheme = (dark) => {
    root.__dark = dark;
    root.classList.toggle('dark', dark);
    const pal = (D.palettes || {})[dark ? 'dark' : 'light'] || {};
    for (const [k, v] of Object.entries(pal)) root.style.setProperty('--' + k, v);
    if (parentElement.__lmSky && parentElement.__lmSky.refreshColors) { parentElement.__lmSky.refreshColors(); parentElement.__lmSky.kick(); }
  };
  { const d = detectDark(); applyTheme(d === null ? D.theme === 'dark' : d); }
  clearInterval(root.__themeTimer);
  root.__themeTimer = setInterval(() => { const d = detectDark(); if (d !== null && d !== root.__dark) applyTheme(d); }, 400);
  const $ = (s) => root.querySelector(s);
  const $$ = (s) => Array.from(root.querySelectorAll(s));
  const send = (ev) => setTriggerValue('event', { ...ev, t: Date.now() });

  // ---------- 비교함 ----------
  const sameP = (a, b) => a && b && a.key === b.key;
  function put(slot, p) {
    const other = slot === 'A' ? 'B' : 'A';
    if (sameP(slots[other], p)) slots[other] = null;
    slots[slot] = p;
    UI.popSlot = slot;
    send({ type: 'slots', A: slots.A, B: slots.B });
    renderAll();
  }
  // 카드 크기는 고정. 이름은 fitName이, 태그는 fitTags가 칸에 맞춰 줄임
  function cardHTML(p, slot) {
    if (!p) return `<div class="qm">?</div><p><b>${slot}</b> 칸이 비어 있어요<br>아래에서 교수님을 담아 주세요</p>`;
    const school = p.school || p.aff || '';
    const sub = p.sub || (p.inst && p.inst !== school ? p.inst : '');
    const tags = (p.tags || []).filter(Boolean);
    const tagHTML = tags.length
      ? tags.slice(0, 3).map((t) => `<span class="tag">${esc(t)}</span>`).join('') + (tags.length > 3 ? `<span class="tag more">+${tags.length - 3}</span>` : '')
      : '<span class="none">논문 데이터를 받으면 표시돼요</span>';
    const stat = p.works != null
      ? `<span>${esc(p.works_label === '3년 논문' ? '최근 3년 논문' : p.works_label || '논문')}</span><b>${p.works}<small> 편</small></b>`
      : `<span>${esc(p.col || '')}</span>`;
    return `<div class="sheen"></div>
      <div class="ctop"><div class="slot">LAB ${slot}</div><button class="rm" type="button" data-rm="${slot}" aria-label="${slot} 칸에서 빼기" title="빼기">−</button></div>
      <div class="school">${badge(school)}<div class="sch"><b>${esc(school || '소속 정보 없음')}</b>${sub ? `<span title="${esc(sub)}">${esc(sub)}</span>` : ''}</div></div>
      <div class="nmbox"><div class="pn" title="${esc(p.name)}">${esc(p.name)}</div></div><div class="pe">${esc(p.eng || '')}</div>
      <div class="flabel">연구 분야</div><div class="tags">${tagHTML}</div>
      <div class="stats">${stat}</div>`;
  }
  // 한글 이름(띄어쓰기 없음)은 1줄, 영문 이름은 2줄까지. 큰 글자부터 줄여 보고, 최소 크기에서도 넘치면 말줄임(마우스를 올리면 전체 이름)
  function fitName(el) {
    const narrow = el.closest('.pc').clientWidth < 200;
    const max = narrow ? 20 : 25, min = narrow ? 14 : 15;
    const lines = /\s/.test(el.textContent.trim()) ? 2 : 1;
    el.style.webkitLineClamp = 'unset';
    let size = max;
    for (; size > min; size--) { el.style.fontSize = size + 'px'; if (Math.round(el.scrollHeight / (size * 1.2)) <= lines && el.scrollWidth <= el.clientWidth + 1) break; }
    el.style.fontSize = size + 'px';
    el.style.webkitLineClamp = String(lines);
    el.style.overflowWrap = lines === 1 ? 'normal' : 'anywhere';
  }
  // 태그가 한 줄을 넘으면 뒤에서부터 접어서 +n으로. 남은 태그 하나도 길면 말줄임(마우스를 올리면 전체 이름)
  function fitTags(box, sel = '.tag', moreCls = 'tag more') {
    if (!box) return;
    box.classList.add('measure');
    const all = Array.from(box.querySelectorAll(sel + ':not(.more)'));
    all.forEach((t) => (t.title = t.textContent));
    let more = box.querySelector('.more'), hidden = more ? +more.textContent.slice(1) : 0;
    while ((box.scrollHeight > box.clientHeight + 1 || box.scrollWidth > box.clientWidth + 1) && all.length > 1) {
      const gone = all.pop(); gone.remove(); hidden++;
      if (!more) { more = document.createElement('span'); more.className = moreCls; box.appendChild(more); }
      more.textContent = '+' + hidden;
      more.title = [gone.textContent, more.title].filter(Boolean).join(', ');
    }
    box.classList.remove('measure');
  }
  // 카드 안전장치: 내용이 카드 높이를 넘으면 덜 중요한 것부터 줄임 (태그 → 영문 이름 → 분야 줄 전체)
  function fitCard(card, tagsSel, tagSel, moreCls) {
    const over = () => card.scrollHeight > card.clientHeight + 1;
    if (!over()) return;
    const box = card.querySelector(tagsSel);
    if (box) {
      const tags = Array.from(box.querySelectorAll(tagSel + ':not(.more)'));
      let more = box.querySelector('.more'), hidden = more ? +more.textContent.slice(1) : 0;
      while (over() && tags.length > 1) {
        const gone = tags.pop(); gone.remove(); hidden++;
        if (!more) { more = document.createElement('span'); more.className = moreCls; box.appendChild(more); }
        more.textContent = '+' + hidden;
        more.title = [gone.textContent, more.title].filter(Boolean).join(', ');
      }
    }
    const pe = card.querySelector('.pe');
    if (over() && pe) pe.style.display = 'none';
    if (over()) card.querySelectorAll('.flabel,' + tagsSel).forEach((n) => (n.style.display = 'none'));
  }
  function renderSlots() {
    ['A', 'B'].forEach((k) => {
      const el = $('.pc.' + k);
      const p = slots[k];
      el.className = 'pc ' + k + (p ? ' filled' : ' empty') + (UI.popSlot === k ? ' pop' : '');
      el.innerHTML = cardHTML(p, k);
      if (p) { fitName(el.querySelector('.pn')); fitTags(el.querySelector('.tags')); fitCard(el, '.tags', '.tag', 'tag more'); }
    });
    UI.popSlot = null;
    const n = (slots.A ? 1 : 0) + (slots.B ? 1 : 0);
    $('.count').textContent = n + ' / 2';
    $('.cta').classList.toggle('ready', n === 2);
    $('.cta-hint').textContent = n === 2 ? `${slots.A.name} vs ${slots.B.name}` : !slots.A ? 'A 연구실을 선택하세요' : 'B 연구실을 선택하세요';
    const hint = $('.cta-hint');
    hint.classList.toggle('warn', !!D.notice);
    if (D.notice) hint.textContent = D.notice;
  }

  // ---------- 검색 ----------
  function personFromOA(r) {
    // 한글 이름을 찾았으면 한글을 크게, OpenAlex 영문 이름을 작게
    // OpenAlex에는 학과 정보가 없어서, 학과 자리에는 주 연구 분야(첫 번째 세부 분야)를 넣음
    const tags = r.tags || [];
    return { key: 'oa:' + r.oa_id, oa_id: r.oa_id, name: r.ko || r.name, eng: r.ko ? r.name : '', aff: uniKo(r.inst), school: uniKo(r.inst), inst: r.inst, works: r.works, works_label: r.works_label || '전체 논문', field: tags[0] || r.field || null, sub: tags[0] || '', tags: tags.slice(1) };
  }
  function rowHTML(p) {
    const onA = sameP(slots.A, p), onB = sameP(slots.B, p);
    const extra = p.works != null ? `, ${esc(p.works_label || '논문')} ${p.works}편` : '';
    return `<div class="row">${badge(p.school || p.aff, 'sm')}<div class="meta"><div class="nm">${esc(p.name)} <span style="color:var(--faint);font-weight:400">${esc(p.eng || '')}</span></div><div class="af">${esc(p.aff)}${extra}</div></div>
      <div class="mini"><button class="a ${onA ? 'on' : ''}" type="button" data-add="A" data-key="${esc(p.key)}">A</button><button class="b ${onB ? 'on' : ''}" type="button" data-add="B" data-key="${esc(p.key)}">B</button></div></div>`;
  }
  const searchPool = {};
  function renderDrop() {
    const d = $('.drop');
    const q = UI.q.trim();
    if (!UI.drop || !q) { d.hidden = true; return; }
    const local = YON.filter((p) => p.name.includes(q) || (p.eng || '').toLowerCase().includes(q.toLowerCase()));
    local.forEach((p) => (searchPool[p.key] = p));
    let html = '';
    if (local.length) html += `<div class="grp">연세대 등록 교수님</div>` + local.map(rowHTML).join('');
    const S = D.search;
    if (S && S.q === q) {
      if (S.error) html += `<div class="note">${esc(S.error)}</div>`;
      else if (S.results && S.results.length) {
        const ps = S.results.map(personFromOA);
        ps.forEach((p) => (searchPool[p.key] = p));
        html += `<div class="grp">OpenAlex 검색 결과</div>` + ps.map(rowHTML).join('') + `<div class="note">동명이인은 소속을 확인하세요</div>`;
      } else html += `<div class="note">검색 결과가 없습니다. 영문 이름으로 다시 검색하세요.</div>`;
    } else if (!local.length) {
      html += `<div class="note">Enter 또는 검색 버튼을 누르면 OpenAlex에서 찾아요.</div>`;
    } else {
      html += `<div class="note">다른 대학 교수님은 검색 버튼을 누르면 OpenAlex에서 찾아요.</div>`;
    }
    d.innerHTML = html;
    d.hidden = false;
  }
  function doSearch() {
    const q = UI.q.trim();
    if (!q) return;
    UI.drop = true;
    renderDrop();
    if (!(D.search && D.search.q === q)) send({ type: 'search', q });
  }

  // ---------- 학과 필름스트립 ----------
  // 단과대학 → 학과 두 단계로 고름 (학과가 150개라 한 줄에 다 늘어놓지 않음)
  const dkey = (y) => y.col + '|' + y.dept;
  const DEPTS = [...new Set(YON.map(dkey))];
  const COLS = [...new Set(YON.map((y) => y.col))];
  const deptCount = {}; YON.forEach((y) => { deptCount[dkey(y)] = (deptCount[dkey(y)] || 0) + 1; });
  if (!UI.dept || !DEPTS.includes(UI.dept)) { const lis = DEPTS.find((k) => k.includes('|문헌정보')); UI.dept = lis || DEPTS[0] || null; UI.idx = 0; }
  function renderDept() {
    const curCol = UI.dept ? UI.dept.split('|')[0] : COLS[0];
    $('.dept-cap').textContent = `${COLS.length}개 단과대학 ${DEPTS.length}개 학과, 교수님 ${YON.length}명 (연세대 교원정보 기준)`;
    // 단과대학 → 학과 → 교수님: 왼쪽에서 오른쪽으로 좁혀 가는 세 칸 (앞의 두 칸은 목록, 마지막은 교수님 카드)
    const colCount = {}; DEPTS.forEach((k) => { const c = k.split('|')[0]; colCount[c] = (colCount[c] || 0) + 1; });
    $('.dept-cols').innerHTML = COLS.map((c) => `<button class="drow ${c === curCol ? 'on' : ''}" type="button" aria-current="${c === curCol}" data-col="${esc(c)}"><span>${esc(c)}</span><em>${colCount[c]}</em><i>›</i></button>`).join('');
    $('.dept-chips').innerHTML = DEPTS.filter((k) => k.split('|')[0] === curCol).map((k) => {
      const d = k.split('|')[1];
      return `<button class="drow ${k === UI.dept ? 'on' : ''}" type="button" aria-current="${k === UI.dept}" data-dept="${esc(k)}"><span>${esc(d)}</span><em>${deptCount[k]}</em><i>›</i></button>`;
    }).join('');
    $('.dep-h').textContent = `${curCol} 학과`;
    $('.prof-h').textContent = `${UI.dept ? UI.dept.split('|')[1] : ''} 교수님 ${deptCount[UI.dept] || 0}명`;
    // 고른 줄이 목록 밖에 있으면 목록 안에서만 스크롤 (페이지는 움직이지 않게)
    ['.dept-cols', '.dept-chips'].forEach((sel) => {
      const box = $(sel), on = box.querySelector('.on');
      if (!on) return;
      const top = on.offsetTop - box.offsetTop, bot = top + on.offsetHeight;
      if (top < box.scrollTop) box.scrollTop = top - 8;
      else if (bot > box.scrollTop + box.clientHeight) box.scrollTop = bot - box.clientHeight + 8;
    });
    const st = $('.strip');
    // 가나다순 이름 목록: 교수님이 많은 학과도 카드를 하나씩 넘기지 않고 바로 찾을 수 있게
    const list = YON.filter((y) => dkey(y) === UI.dept).sort((x, y) => x.name.localeCompare(y.name, 'ko'));
    if (UI.idx >= list.length) UI.idx = 0;
    $('.dept-names').innerHTML = list.map((p, i) => `<button type="button" role="listitem" class="${i === UI.idx ? 'on' : ''}" data-pick="${i}" aria-current="${i === UI.idx}">${esc(p.name)}</button>`).join('');
    // 같은 학과면 카드를 다시 만들지 않고 위치만 옮김 → 옆으로 미끄러지는 움직임이 이어지고, 한 번에 한 칸씩만 이동
    const sig = UI.dept + '|' + list.map((p) => p.key).join(',');
    const rebuild = st.dataset.sig !== sig;
    if (rebuild) { st.querySelectorAll('.fc').forEach((n) => n.remove()); st.dataset.sig = sig; }
    list.forEach((p, i) => {
      searchPool[p.key] = p;
      const off = i - UI.idx;
      let el = rebuild ? null : st.querySelector(`.fc[data-idx="${i}"]`);
      const fresh = !el;
      if (fresh) { el = document.createElement('div'); el.className = 'fc'; el.dataset.idx = i; }
      el.style.transform = `translateX(${off * 190}px) scale(${off === 0 ? 1 : 0.84}) rotateY(${off * -8}deg)`;
      el.style.opacity = Math.abs(off) > 2 ? 0 : off === 0 ? 1 : 0.55;
      el.style.zIndex = 10 - Math.abs(off);
      el.style.pointerEvents = Math.abs(off) > 1 ? 'none' : '';
      el.classList.toggle('side', off !== 0);
      el.setAttribute('aria-hidden', off !== 0);
      const onA = sameP(slots.A, p), onB = sameP(slots.B, p);
      const html = `<div class="eyebrow">${esc(p.col)}</div><div class="pn">${esc(p.name)}</div><div class="pe">${esc(p.eng)}</div>
        <div class="pd">${esc(p.dept)}</div>
        <div class="flabel">연구 분야</div>
        <div class="ftags">${(p.tags || []).length ? p.tags.slice(0, 3).map((t) => `<span>${esc(t)}</span>`).join('') + (p.tags.length > 3 ? `<span class="more">+${p.tags.length - 3}</span>` : '') : '<em>논문 데이터를 받으면 표시돼요</em>'}</div>
        ${p.works != null ? `<div class="fw"><span>${esc(p.works_label || "전체 논문")}</span><b>${p.works}<small> 편</small></b></div>` : ''}
        <div class="acts"><button class="add a ${onA ? 'on' : ''}" type="button" data-add="A" data-key="${esc(p.key)}" tabindex="${off === 0 ? 0 : -1}">${onA ? 'A에 담김' : 'A에 담기'}</button><button class="add b ${onB ? 'on' : ''}" type="button" data-add="B" data-key="${esc(p.key)}" tabindex="${off === 0 ? 0 : -1}">${onB ? 'B에 담김' : 'B에 담기'}</button></div>`;
      if (el.__html !== html) {
        el.innerHTML = html; el.__html = html;
        if (fresh) st.appendChild(el);
        fitTags(el.querySelector('.ftags'), 'span', 'more');
        fitCard(el, '.ftags', 'span', 'more');
      }
    });
    $('.dots').innerHTML = list.length > 24 ? `<span class="cnt">${UI.idx + 1} / ${list.length}</span>` : list.map((_, i) => `<i class="${i === UI.idx ? 'on' : ''}"></i>`).join('');
    $('.nav.l').disabled = UI.idx === 0;
    $('.nav.r').disabled = UI.idx >= list.length - 1;
  }

  // ---------- 분야 ----------
  const fieldsById = {};
  (FS && FS.fields ? FS.fields : []).forEach((f) => (fieldsById[f.id] = f));
  const featured = FS ? (FS.featured || []).filter((id) => fieldsById[id]) : [];
  if (FS && (!UI.field || !fieldsById[UI.field])) { UI.field = featured[0] || (FS.fields[0] && FS.fields[0].id); UI.sub = null; }
  const curField = () => fieldsById[UI.field];
  const curSubs = () => ((curField() && curField().subfields) || []).filter((s) => s.researchers && s.researchers.length);
  function researchersOf(field, subId) {
    const subs = (field && field.subfields) || [];
    const pick = subId ? subs.filter((s) => s.id === subId) : subs;
    const seen = {};
    const out = [];
    pick.forEach((s) => (s.researchers || []).forEach((r) => {
      const prev = seen[r.oa_id];
      if (prev) { prev.works = Math.max(prev.works, r.works); return; }
      const subName = s.ko || s.en, fieldName = field.ko || field.en;
      const p = { key: 'oa:' + r.oa_id, oa_id: r.oa_id, name: r.ko || r.name, eng: r.ko ? r.name : '', aff: uniKo(r.inst), school: uniKo(r.inst), inst: r.inst, works: r.works, works_label: '3년 논문', field: subName, sub: subName, subId: s.id, tags: fieldName && fieldName !== subName ? [fieldName] : [], yon: isYonsei(r.inst) };
      seen[r.oa_id] = p; out.push(p); searchPool[p.key] = p;
    }));
    return out.sort((a, b) => b.works - a.works);
  }
  function renderFields() {
    const body = $('.field-body');
    if (!FS || !FS.fields || !FS.fields.length) {
      body.innerHTML = `<div class="empty-note">분야 데이터를 아직 불러오지 못했어요. 이름 검색과 학과 둘러보기는 그대로 쓸 수 있어요.</div>`;
      stopSky();
      return;
    }
    const f = curField();
    const chip = (x, on) => `<button class="chip ${on ? 'on' : ''}" type="button" data-field="${esc(x.id)}">${esc(x.ko || x.en)}<em>${fmtGrowth(x.growth)}</em></button>`;
    let chips = featured.map((id) => chip(fieldsById[id], id === UI.field)).join('');
    if (!featured.includes(UI.field)) chips += chip(f, true);
    chips += `<button class="chip more" type="button" data-act="all">${UI.showAll ? '접기' : `더보기 (${FS.fields.length}개 분야)`}</button>`;
    let all = '';
    if (UI.showAll) {
      const groups = {};
      FS.fields.forEach((x) => (groups[x.domain || '기타'] = groups[x.domain || '기타'] || []).push(x));
      all = `<div class="allfields">` + Object.keys(groups).map((g) => `<div><h4>${esc(g)}</h4>${groups[g].sort((a, b) => b.works - a.works).map((x) => `<button type="button" class="${x.id === UI.field ? 'on' : ''}" data-field="${esc(x.id)}"><span>${esc(x.ko || x.en)}</span><em>${fmtGrowth(x.growth)}</em></button>`).join('')}</div>`).join('') + `</div>`;
    }
    const subs = curSubs();
    const subChips = subs.length ? `<div class="chips sub"><button class="chip ${!UI.sub ? 'on' : ''}" type="button" data-sub="">${esc(f.ko || f.en)} 전체</button>${subs.map((s) => `<button class="chip ${s.id === UI.sub ? 'on' : ''}" type="button" data-sub="${esc(s.id)}">${esc(s.ko || s.en)}</button>`).join('')}</div>` : '';
    const sel = UI.sub ? subs.find((s) => s.id === UI.sub) : null;
    const title = `${esc(sel ? sel.ko || sel.en : f.ko || f.en)} 상위 연구자`;
    const [y0, y1] = FS.window || [2023, 2025];
    body.innerHTML = `<p class="basis">국내 기관 논문이 ${FS.prev ? FS.prev[0] + '~' + FS.prev[1] + '년 대비 ' : ''}${y0}~${y1}년에 많이 늘어난 분야 순</p>
      <div class="chips">${chips}</div>${all}${subChips}
      <div class="sky"><div class="canvasbox"><canvas aria-label="세부 분야별 연구자 별자리. 빈 곳을 끌어 돌려 보고, 점을 끌어 옮기거나 눌러서 함께 쓴 연구자를 따라가 볼 수 있어요. 같은 연구자 목록은 오른쪽 순위에 있어요." role="img"></canvas><div class="skybar"><div class="skytools"><button class="ghost sm" type="button" data-sky="names">이름 보기</button><button class="ghost sm" type="button" data-sky="linked">공저 있는 사람만</button><button class="ghost sm icon" type="button" data-sky="out" aria-label="작게">−</button><button class="ghost sm icon" type="button" data-sky="in" aria-label="크게">+</button><button class="ghost sm" type="button" data-sky="clear" hidden>처음 모양으로</button></div></div><div class="legend"><span><i style="background:var(--A)"></i>연세대</span><span><i style="background:var(--dot)"></i>다른 국내 기관</span><span><i class="co-line"></i>함께 쓴 논문 (굵을수록 많이)</span></div></div>
      <div class="rank"><h3>${title}</h3><p class="cap">국내 기관 전체, ${y0}~${y1}년 논문 수 기준</p><div class="rank-list"></div><div class="src">출처: OpenAlex (${esc(FS.generated || '')} 집계)</div></div></div>`;
    renderRank();
    startSky();
  }
  function renderRank() {
    const box = $('.rank-list');
    if (!box) return;
    const list = researchersOf(curField(), UI.sub).slice(0, 8);
    const mx = list[0] ? list[0].works : 1;
    box.innerHTML = list.length ? list.map((p, i) => {
      const onA = sameP(slots.A, p), onB = sameP(slots.B, p);
      return `<div class="rk${p.yon ? ' yon-row' : ''}"><span class="n">${i + 1}</span>${badge(p.school, 'sm')}<div style="min-width:0"><div class="nm">${esc(p.name)}${p.eng ? `<span class="en">${esc(p.eng)}</span>` : ''}</div><div class="af">${esc(p.aff)}, 최근 3년 논문 ${p.works}편</div><div class="bar"><i style="width:${(p.works / mx) * 100}%"></i></div></div>
        <div class="mini"><button class="a ${onA ? 'on' : ''}" type="button" data-add="A" data-key="${esc(p.key)}">A</button><button class="b ${onB ? 'on' : ''}" type="button" data-add="B" data-key="${esc(p.key)}">B</button></div></div>`;
    }).join('') : `<div class="empty-note">이 분야의 연구자 데이터가 없어요.</div>`;
  }

  // ---------- 별자리 (입체 공간에서 둘러보고 파헤치기) ----------
  // 점 = 연구자, 선 = 함께 쓴 논문(공저). 세부 분야마다 한 무리가 공간 속에 떠 있음.
  // 둘러보기: 빈 곳을 끌면 공간이 어느 방향으로든 돌고, 가만히 두면 천천히 돎. +/- 로 가까이 보기
  // 파헤치기: 점을 끌어 옮기면 놓은 자리에 그대로 남음(선이 늘어나며 누구와 이어졌는지 드러남)
  //          점을 누르면 표시가 남고(여러 명 가능), 카드에서 공저자 이름을 눌러 그 사람으로 건너감
  //          '이 사람 중심으로'를 눌러야만 나머지가 흐려짐. 끄는 것만으로는 아무것도 모이거나 바뀌지 않음
  let sky = parentElement.__lmSky || null;
  function stopSky() {
    if (sky) { cancelAnimationFrame(sky.raf); if (sky.ro) sky.ro.disconnect(); if (sky.io) sky.io.disconnect(); }
    sky = null; parentElement.__lmSky = null;
  }
  const logoImgs = {};
  const logoImg = (school) => {
    const k = logoKey(school);
    if (!k) return null;
    if (!logoImgs[k]) { const im = new Image(); im.src = LOGOS[k]; logoImgs[k] = im; }
    return logoImgs[k].complete ? logoImgs[k] : null;
  };
  function skyColors() {
    const cs = getComputedStyle(root), tok = (n, d) => (cs.getPropertyValue(n) || '').trim() || d;
    return { A: tok('--A', '#93BAB5'), B: tok('--B', '#F5CB71'), ink: tok('--ink', '#1C2430'), sub: tok('--sub', '#5F6B7A'), faint: tok('--faint', '#98A2B0'), other: tok('--dot', '#7D8898'), surface: tok('--surface', '#FFFFFF'), line: tok('--line', '#E3E6EB') };
  }
  const skyUI = parentElement.__lmSkyUI || (parentElement.__lmSkyUI = { marked: new Set(), focus: null, onlyLinked: false, names: false, zoom: 1, pos: {} });
  function startSky() {
    stopSky();
    const box = $('.canvasbox');
    const cv = box.querySelector('canvas');
    const ctx = cv.getContext('2d');
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const subs = curSubs().slice(0, 6);
    const fieldKey = UI.field;
    if (skyUI.field !== fieldKey) { skyUI.field = fieldKey; skyUI.marked = new Set(); skyUI.focus = null; skyUI.pos = {}; }
    let seed = 11; const rnd = () => ((seed = (seed * 9301 + 49297) % 233280), seed / 233280);
    // 무리 중심: 둥근 고리 위에 두되 앞뒤(z)로 번갈아 띄워서 돌렸을 때 공간감이 나게
    const RING = 150;
    const centers = subs.map((s, i) => {
      if (subs.length === 1) return { x: 0, y: 0, z: 0 };
      const a = (i / subs.length) * Math.PI * 2 - Math.PI / 2;
      return { x: Math.cos(a) * RING, y: Math.sin(a) * RING * 0.8, z: (i % 2 ? 1 : -1) * 75 };
    });
    const nodes = [];
    subs.forEach((s, ci) => {
      const list = researchersOf(curField(), s.id).slice(0, 14);
      const mx = list[0] ? list[0].works : 1;
      list.forEach((p) => {
        // 공 모양 안에 고르게 (가운데에 몰리지 않게 세제곱근)
        const u = rnd() * 2 - 1, th = rnd() * Math.PI * 2, rr = 22 + Math.cbrt(rnd()) * 46, q = Math.sqrt(1 - u * u);
        const x = centers[ci].x + rr * q * Math.cos(th), y = centers[ci].y + rr * q * Math.sin(th), z = centers[ci].z + rr * u;
        const id = String(p.oa_id || '').split('/').pop();
        const saved = skyUI.pos[id];
        nodes.push({ p, id, ci, hx: x, hy: y, hz: z, x: saved ? saved.x : x, y: saved ? saved.y : y, z: saved ? saved.z : z, tx: null, r: 3.5 + (p.works / mx) * 6.5 });
      });
    });
    // 배경 별가루: 무리보다 먼 곳에 흩어 두어서 돌리면 원근(시차)이 느껴짐
    const dust = [];
    for (let i = 0; i < 140; i++) { const u = rnd() * 2 - 1, th = rnd() * Math.PI * 2, rr = 240 + rnd() * 120, q = Math.sqrt(1 - u * u); dust.push({ x: rr * q * Math.cos(th), y: rr * q * Math.sin(th), z: rr * u, s: 0.6 + rnd() * 0.9, ph: rnd() * 6 }); }
    // 선 = 실제 공저 관계 (build_coauthor_links.py). 세부 분야가 달라도 함께 쓴 논문이 있으면 이어짐
    const byId = {}; nodes.forEach((n, i) => { byId[n.id] = i; });
    const co = ((curField() && curField().links) || []).filter((l) => byId[l[0]] != null && byId[l[1]] != null)
      .map((l) => ({ a: byId[l[0]], b: byId[l[1]], n: l[2] }));
    nodes.forEach((n) => { n.nb = []; });
    co.forEach((l) => { nodes[l.a].nb.push({ i: l.b, n: l.n }); nodes[l.b].nb.push({ i: l.a, n: l.n }); });
    nodes.forEach((n) => n.nb.sort((u, v) => v.n - u.n));
    const marked = new Set([...skyUI.marked].map((id) => byId[id]).filter((i) => i != null).map((i) => nodes[i]));
    const rot0 = parentElement.__lmRot || { yaw: 0.45, pitch: -0.28 };
    const st = { nodes, co, dust, marked, hover: null, raf: 0, yaw: rot0.yaw, pitch: rot0.pitch, spinX: 0, spinY: 0, drag: null, tipNode: null, visible: true, C: skyColors(), W: 0, H: 0, scale: 1, zoom: skyUI.zoom, lastTouch: performance.now() };
    st.focus = skyUI.focus && byId[skyUI.focus] != null ? nodes[byId[skyUI.focus]] : null;
    sky = st; parentElement.__lmSky = st;
    st.refreshColors = () => { st.C = skyColors(); };
    const resize = () => {
      const r = box.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
      st.W = r.width || 700; st.H = r.height || 420;
      cv.width = st.W * dpr; cv.height = st.H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      st.scale = Math.min(st.W / 600, (st.H - 40) / 470, 1.2);
    };
    resize();
    st.ro = new ResizeObserver(() => { resize(); st.kick && st.kick(); }); st.ro.observe(box);
    st.io = new IntersectionObserver((es) => { st.visible = es[0].isIntersecting; if (st.visible) st.kick(); }); st.io.observe(box);
    // 3D ↔ 화면: 좌우로 끌면 세로축(yaw), 위아래로 끌면 가로축(pitch). 가까운 점은 크고 진하게, 먼 점은 작고 흐리게
    const DEPTH = 560;
    const rotate = (x, y, z) => {
      const cy = Math.cos(st.yaw), sy = Math.sin(st.yaw), cp = Math.cos(st.pitch), sp = Math.sin(st.pitch);
      const x1 = x * cy - z * sy, z1 = x * sy + z * cy;
      return { x: x1, y: y * cp - z1 * sp, z: y * sp + z1 * cp };
    };
    const K = () => st.scale * st.zoom;
    const toScreen = (x, y, z) => { const r = rotate(x, y, z), f = DEPTH / (DEPTH + Math.max(-DEPTH * 0.7, r.z)); return { x: st.W / 2 + r.x * K() * f, y: st.H / 2 + 14 + r.y * K() * f, z: r.z, f }; };
    const toWorld = (sx, sy, rz) => {
      const f = DEPTH / (DEPTH + rz);
      const x1 = (sx - st.W / 2) / (K() * f), y2 = (sy - st.H / 2 - 14) / (K() * f);
      const c1 = Math.cos(st.yaw), s1 = Math.sin(st.yaw), c2 = Math.cos(st.pitch), s2 = Math.sin(st.pitch);
      const y = y2 * c2 + rz * s2, z1 = -y2 * s2 + rz * c2;
      return { x: x1 * c1 + z1 * s1, y, z: -x1 * s1 + z1 * c1 };
    };
    // 점을 정면으로 데려오는 회전값 (공저자 이름을 눌러 건너갈 때)
    const faceFront = (n) => { const r = Math.hypot(n.x, n.z) || 1; return { yaw: Math.atan2(-n.x, -n.z), pitch: Math.max(-1.2, Math.min(1.2, Math.atan2(-n.y, r))) }; };
    const alpha = (hex, a) => { const h = hex.replace('#', ''); if (!/^[0-9a-f]{3,6}$/i.test(h)) return hex; const n = parseInt(h.length === 3 ? h.replace(/./g, '$&$&') : h, 16); return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`; };
    const inSub = (n) => !UI.sub || subs[n.ci].id === UI.sub;
    const isNb = (n, m) => m && m.nb.some((x) => st.nodes[x.i] === n);
    // 점이 지금 얼마나 또렷해야 하는지 (0~1). 중심 보기 > 공저 있는 사람만 > 세부 분야 순으로 흐리게
    const lit = (n) => {
      if (st.focus) return n === st.focus || isNb(n, st.focus) ? 1 : 0.12;
      if (skyUI.onlyLinked && !n.nb.length) return 0.12;
      return inSub(n) ? 1 : 0.3;
    };
    st.target = UI.sub ? { yaw: 0, pitch: 0 } : null;
    const save = () => {
      skyUI.marked = new Set([...st.marked].map((n) => n.id)); skyUI.focus = st.focus ? st.focus.id : null; skyUI.zoom = st.zoom;
      parentElement.__lmRot = { yaw: st.yaw, pitch: st.pitch };
    };
    function step() {
      // 옮긴 점이 '처음 모양으로'를 누르면 원래 자리로 미끄러져 돌아감. 그 밖에는 점이 스스로 움직이지 않음
      let moving = 0;
      for (const n of st.nodes) {
        if (n.tx == null) continue;
        const k = reduce ? 1 : 0.14;
        n.x += (n.tx - n.x) * k; n.y += (n.ty - n.y) * k; n.z += (n.tz - n.z) * k;
        if (Math.abs(n.tx - n.x) + Math.abs(n.ty - n.y) + Math.abs(n.tz - n.z) < 0.3) { n.x = n.tx; n.y = n.ty; n.z = n.tz; n.tx = null; } else moving++;
      }
      return moving;
    }
    function label(text, x, y, C, strong) {
      ctx.font = `${strong ? 600 : 500} 12px "IBM Plex Sans KR", sans-serif`;
      const w = ctx.measureText(text).width;
      ctx.fillStyle = alpha(C.surface, 0.82); ctx.fillRect(x - 3, y - 9, w + 6, 17);
      ctx.fillStyle = strong ? C.ink : C.sub; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText(text, x, y);
    }
    function draw(t) {
      const C = st.C, W = st.W, H = st.H;
      ctx.clearRect(0, 0, W, H);
      // 별가루
      for (const d of st.dust) {
        const s = toScreen(d.x, d.y, d.z);
        if (s.x < -4 || s.x > W + 4 || s.y < -4 || s.y > H + 4) continue;
        const tw = reduce ? 1 : 0.75 + Math.sin(t / 900 + d.ph) * 0.25;
        ctx.globalAlpha = Math.max(0.08, Math.min(0.5, (s.f - 0.55) * 0.7)) * tw;
        ctx.fillStyle = C.faint; ctx.beginPath(); ctx.arc(s.x, s.y, d.s * s.f, 0, Math.PI * 2); ctx.fill();
      }
      ctx.globalAlpha = 1;
      const P = st.nodes.map((n) => toScreen(n.x, n.y, n.z));
      const depthA = (i) => Math.max(0.3, Math.min(1, (P[i].f - 0.62) * 1.5));   // 먼 점일수록 흐리게
      const hot = st.hover && !st.drag ? st.hover : st.drag && st.drag.node && st.drag.moved ? st.drag.node : null;
      const keyNodes = new Set([...st.marked, st.tipNode, st.focus, hot].filter(Boolean));
      // 공저 선: 먼 선부터, 함께 쓴 논문이 많을수록 굵게. 표시한 사람·마우스를 올린 사람의 선은 진하게
      const lines = st.co.map((l) => ({ l, z: (P[l.a].z + P[l.b].z) / 2 })).sort((u, v) => v.z - u.z);
      for (const { l } of lines) {
        const a = st.nodes[l.a], b = st.nodes[l.b];
        const strong = keyNodes.has(a) || keyNodes.has(b);
        const base = Math.min(lit(a), lit(b)) * Math.min(depthA(l.a), depthA(l.b));
        ctx.lineWidth = Math.min(3.4, 0.8 + Math.log2(1 + l.n) * 0.75) * (strong ? 1.25 : 1);
        ctx.strokeStyle = strong ? alpha(C.ink, 0.8) : alpha(a.p.yon || b.p.yon ? C.A : C.other, 0.18 + 0.4 * base);
        ctx.beginPath(); ctx.moveTo(P[l.a].x, P[l.a].y); ctx.lineTo(P[l.b].x, P[l.b].y); ctx.stroke();
      }
      ctx.lineWidth = 1;
      const order = st.nodes.map((_, i) => i).sort((i, j) => P[j].z - P[i].z);   // 먼 점부터 그림
      const labels = [];
      order.forEach((i) => {
        const n = st.nodes[i], s = P[i], L = lit(n), A = depthA(i) * (0.25 + 0.75 * L);
        const tw = !reduce && L > 0.5 ? 1 + Math.sin(t / 700 + n.hx) * 0.06 : 1;
        n.sx = s.x; n.sy = s.y; n.sr = Math.max(1.6, n.r * tw * Math.max(0.85, st.scale) * st.zoom ** 0.6 * s.f);
        const col = n.p.yon ? C.A : C.other;
        ctx.globalAlpha = A; ctx.fillStyle = col; ctx.beginPath(); ctx.arc(s.x, s.y, n.sr, 0, Math.PI * 2); ctx.fill();
        ctx.globalAlpha = 1;
        const isA = sameP(slots.A, n.p), isB = sameP(slots.B, n.p), mk = st.marked.has(n);
        if (isA || isB || mk || hot === n || st.tipNode === n) {
          ctx.lineWidth = mk || st.tipNode === n ? 2.2 : 1.6; ctx.strokeStyle = isB ? C.B : isA ? C.A : C.ink;
          ctx.beginPath(); ctx.arc(s.x, s.y, n.sr + 4, 0, Math.PI * 2); ctx.stroke(); ctx.lineWidth = 1;
        }
        // 이름표: 표시한 사람·중심·마우스를 올린 사람과 그 공저자, '이름 보기'를 켜면 또렷한 점 모두
        const near = [...keyNodes].some((m) => isNb(n, m));
        if (keyNodes.has(n) || near || (skyUI.names && L > 0.5 && s.f > 0.85)) labels.push({ n, strong: keyNodes.has(n), z: s.z });
      });
      // 이름표는 점 위에 한꺼번에, 가까운 것이 위로. 겹치면 뒤쪽 것을 생략
      const taken = [];
      labels.sort((u, v) => (v.strong - u.strong) || (u.z - v.z)).forEach(({ n, strong }) => {
        const x = n.sx + n.sr + 5, y = n.sy;
        ctx.font = `${strong ? 600 : 500} 12px "IBM Plex Sans KR", sans-serif`;
        const w = ctx.measureText(n.p.name).width + 6;
        if (!strong && taken.some((r) => x < r.x + r.w && x + w > r.x && Math.abs(y - r.y) < 16)) return;
        taken.push({ x, y, w });
        label(n.p.name, x, y, C, strong);
      });
      // 무리 이름: 무리의 가장 위쪽 점 위에
      ctx.font = '600 13px "IBM Plex Sans KR", sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
      subs.forEach((s, ci) => {
        const mem = st.nodes.filter((n) => n.ci === ci && n.hx === n.x && n.hy === n.y);
        if (!mem.length) return;
        const cx = mem.reduce((a, n) => a + n.sx, 0) / mem.length, top = Math.min(...mem.map((n) => n.sy - n.sr));
        const on = !st.focus && (!UI.sub || s.id === UI.sub);
        ctx.fillStyle = on ? C.ink : C.faint; ctx.globalAlpha = on ? 0.9 : 0.6;
        // 돌려서 무리가 겹쳐 보이면 이름표가 겹치지 않게 아래로 비켜 씀
        const text = s.ko || s.en, w = ctx.measureText(text).width, lx = Math.min(Math.max(cx, 60), W - 60);
        let ly = Math.max(52, top - 12);
        while (taken.some((r) => Math.abs(lx - r.cx) < (w + r.w) / 2 + 6 && Math.abs(ly - r.ly) < 16)) ly += 17;
        taken.push({ cx: lx, ly, w, x: -1e9, y: -1e9 });
        ctx.fillText(text, lx, ly);
        ctx.globalAlpha = 1;
      });
      if (st.tipNode && tip) placeTip(st.tipNode);
    }
    function frame(t) {
      st.raf = 0;
      if (!sky || sky !== st) return;
      const m = step();
      const idle = performance.now() - st.lastTouch > 3500 && !st.drag && !st.tipNode && !st.focus && !st.marked.size;
      if (!st.drag) {
        if (st.target != null) {
          const wrap = (d) => Math.atan2(Math.sin(d), Math.cos(d));
          const dy = wrap(st.target.yaw - st.yaw), dp = wrap(st.target.pitch - st.pitch), k = reduce ? 1 : 0.09;
          st.yaw += dy * k; st.pitch += dp * k;
          if (Math.abs(dy) + Math.abs(dp) < 0.003) st.target = null;
        } else if (Math.abs(st.spinX) + Math.abs(st.spinY) > 0.0005) { st.yaw += st.spinX; st.pitch = Math.max(-1.3, Math.min(1.3, st.pitch + st.spinY)); st.spinX *= 0.95; st.spinY *= 0.95; }
        else { st.spinX = st.spinY = 0; if (idle && !reduce) st.yaw += 0.0016; }   // 가만히 두면 천천히 돎
      }
      save();
      draw(t);
      const moving = st.drag || m || st.spinX || st.spinY || st.target != null || (idle && !reduce) || st.hover || st.tipNode || st.marked.size;
      if (st.visible && moving && !document.hidden) st.raf = requestAnimationFrame(frame);
    }
    st.kick = () => { if (!st.raf) st.raf = requestAnimationFrame(frame); };
    st.raf = requestAnimationFrame(frame);
    const touch = () => { st.lastTouch = performance.now(); };

    let tip = null;
    function placeTip(n) {
      if (!tip) return;
      const W = st.W, H = st.H, tw = tip.offsetWidth || 230;
      const x = n.sx > W / 2 ? Math.max(8, n.sx - n.sr - tw - 14) : Math.min(n.sx + n.sr + 14, W - tw - 8);
      const y = Math.min(Math.max(n.sy - 44, 48), H - tip.offsetHeight - 8);
      tip.style.left = x + 'px'; tip.style.top = y + 'px';
    }
    const showTip = (n) => {
      if (tip) tip.remove(); tip = null; st.tipNode = n || null;
      if (!n) { st.kick(); return; }
      tip = document.createElement('div'); tip.className = 'tip';
      const nb = n.nb.slice(0, 8).map((x) => { const m = st.nodes[x.i]; return `<button type="button" class="nbtn ${st.marked.has(m) ? 'on' : ''}" data-hop="${x.i}">${m.p.yon ? '<i class="yd"></i>' : ''}${esc(m.p.name)}<em>${x.n}편</em></button>`; }).join('');
      const more = n.nb.length > 8 ? `<span class="more">외 ${n.nb.length - 8}명</span>` : '';
      const foc = st.focus === n;
      tip.innerHTML = `<button type="button" class="x" data-tip="close" aria-label="닫기">×</button><div class="tip-h">${badge(n.p.school, 'sm')}<div style="min-width:0"><b class="${n.p.yon ? 'yname' : ''}">${esc(n.p.name)}</b>${n.p.eng ? `<div class="en">${esc(n.p.eng)}</div>` : ''}</div></div><div class="af">${esc(n.p.aff)}</div><div class="af">${esc(n.p.field)}, 최근 3년 논문 ${n.p.works}편</div>
        <div class="nb-h">${n.nb.length ? `함께 쓴 연구자 ${n.nb.length}명 <span>이름을 누르면 그 사람으로</span>` : '이 별자리 안에는 함께 쓴 연구자가 없어요'}</div>${n.nb.length ? `<div class="nbs">${nb}${more}</div>` : ''}
        <div class="acts"><button class="add a" type="button" data-add="A" data-key="${esc(n.p.key)}">A에 담기</button><button class="add b" type="button" data-add="B" data-key="${esc(n.p.key)}">B에 담기</button>${n.nb.length ? `<button type="button" class="ghost sm fbtn ${foc ? 'on' : ''}" data-tip="focus">${foc ? '모두 보기' : '이 사람 중심으로'}</button>` : ''}</div>`;
      tip.addEventListener('pointerdown', (e) => e.stopPropagation());
      tip.addEventListener('click', (e) => {
        const hop = e.target.closest('[data-hop]'), act = e.target.closest('[data-tip]');
        if (hop) { e.stopPropagation(); const m = st.nodes[+hop.dataset.hop]; st.marked.add(m); if (st.focus) st.focus = m; st.target = faceFront(m); touch(); showTip(m); }
        else if (act && act.dataset.tip === 'close') { e.stopPropagation(); showTip(null); }
        else if (act && act.dataset.tip === 'focus') { e.stopPropagation(); st.focus = st.focus === n ? null : n; syncBar(); showTip(n); }
      });
      box.appendChild(tip);
      placeTip(n);
      st.kick();
    };
    const at = (e) => { const rr = cv.getBoundingClientRect(); return { x: e.clientX - rr.left, y: e.clientY - rr.top }; };
    // 겹쳐 있으면 앞쪽(가까운) 점을 고름
    const hit = (x, y) => { let best = null, bz = 1e9; for (const n of st.nodes) { if (n.sx == null) continue; const d = Math.hypot(n.sx - x, n.sy - y); if (d < n.sr + 7) { const z = rotate(n.x, n.y, n.z).z + d * 2; if (z < bz) { best = n; bz = z; } } } return best; };
    const pointers = new Map();
    cv.onpointerdown = (e) => {
      const p = at(e); touch();
      pointers.set(e.pointerId, p);
      if (pointers.size === 2) { const [a, b] = [...pointers.values()]; st.pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), z: st.zoom }; st.drag = null; return; }
      const n = hit(p.x, p.y);
      st.target = null;
      st.drag = { node: n, sx: p.x, sy: p.y, moved: false, lx: p.x, ly: p.y, t: performance.now(), rz: n ? rotate(n.x, n.y, n.z).z : 0 };
      st.spinX = st.spinY = 0;
      cv.setPointerCapture(e.pointerId);
      cv.style.cursor = 'grabbing';
      st.kick();
    };
    cv.onpointermove = (e) => {
      const p = at(e);
      if (pointers.has(e.pointerId)) pointers.set(e.pointerId, p);
      if (st.pinch && pointers.size === 2) { const [a, b] = [...pointers.values()]; setZoom(st.pinch.z * Math.hypot(a.x - b.x, a.y - b.y) / Math.max(20, st.pinch.d)); return; }
      if (st.drag) {
        const d = st.drag; touch();
        if (!d.moved && Math.hypot(p.x - d.sx, p.y - d.sy) > 4) d.moved = true;
        if (!d.moved) return;
        if (d.node) {
          // 점 옮기기: 화면에서의 깊이를 그대로 둔 채 손가락을 따라감. 놓으면 그 자리에 남음
          const w = toWorld(p.x, p.y, d.rz); d.node.x = w.x; d.node.y = w.y; d.node.z = w.z; d.node.tx = null;
        } else {
          const ax = (p.x - d.lx) * 0.008, ay = -(p.y - d.ly) * 0.008;
          st.yaw += ax; st.pitch = Math.max(-1.3, Math.min(1.3, st.pitch + ay)); d.lx = p.x; d.ly = p.y;
          const now = performance.now(), k = reduce ? 0 : Math.min(1, 16 / Math.max(1, now - d.t));
          st.spinX = ax * k; st.spinY = ay * k; d.t = now;
        }
        st.kick();
        return;
      }
      const h = hit(p.x, p.y);
      if (h !== st.hover) { st.hover = h; cv.style.cursor = h ? 'pointer' : 'grab'; st.kick(); }
    };
    const end = (e) => {
      pointers.delete(e.pointerId);
      if (st.pinch) { if (pointers.size < 2) st.pinch = null; return; }
      const d = st.drag; st.drag = null; touch();
      cv.style.cursor = st.hover ? 'pointer' : 'grab';
      if (d && d.node && d.moved) { skyUI.pos[d.node.id] = { x: d.node.x, y: d.node.y, z: d.node.z }; syncBar(); }
      if (d && !d.moved) {
        // 누르기: 점 → 표시 켜고 카드 열기 (이미 카드가 열린 점을 다시 누르면 표시 끄기), 빈 곳 → 카드만 닫기
        if (d.node) {
          if (st.tipNode === d.node) { st.marked.delete(d.node); showTip(null); }
          else { st.marked.add(d.node); showTip(d.node); }
          syncBar();
        } else showTip(null);
      }
      st.kick();
    };
    cv.onpointerup = end; cv.onpointercancel = (e) => { pointers.delete(e.pointerId); st.pinch = null; st.drag = null; st.kick(); };
    cv.onpointerleave = () => { if (!st.drag && st.hover) { st.hover = null; st.kick(); } };
    cv.style.cursor = 'grab';
    const setZoom = (z) => { st.zoom = Math.max(0.7, Math.min(2.6, z)); touch(); st.kick(); };
    // 휠: Ctrl(또는 트랙패드 핀치)일 때만 확대·축소. 그냥 휠은 페이지 스크롤 그대로
    cv.addEventListener('wheel', (e) => { if (!e.ctrlKey) return; e.preventDefault(); setZoom(st.zoom * Math.exp(-e.deltaY * 0.01)); }, { passive: false });
    const bar = box.querySelector('.skytools');
    function syncBar() {
      if (!bar) return;
      const moved = st.nodes.some((n) => n.x !== n.hx || n.y !== n.hy || n.z !== n.hz);
      bar.querySelector('[data-sky="names"]').classList.toggle('on', skyUI.names);
      bar.querySelector('[data-sky="linked"]').classList.toggle('on', skyUI.onlyLinked);
      const clr = bar.querySelector('[data-sky="clear"]');
      clr.hidden = !(st.marked.size || st.focus || moved);
      clr.textContent = st.marked.size ? `표시 ${st.marked.size}명 지우기` : '처음 모양으로';
      save();
    }
    if (bar) bar.onclick = (e) => {
      const b = e.target.closest('[data-sky]'); if (!b) return;
      const k = b.dataset.sky; touch();
      if (k === 'in') setZoom(st.zoom * 1.25);
      else if (k === 'out') setZoom(st.zoom / 1.25);
      else if (k === 'names') skyUI.names = !skyUI.names;
      else if (k === 'linked') skyUI.onlyLinked = !skyUI.onlyLinked;
      else if (k === 'clear') {
        // 표시가 있으면 표시만 지우고, 없으면 옮긴 점과 시점을 처음으로
        if (st.marked.size || st.focus) { st.marked.clear(); st.focus = null; showTip(null); }
        else { st.nodes.forEach((n) => { n.tx = n.hx; n.ty = n.hy; n.tz = n.hz; }); skyUI.pos = {}; st.target = { yaw: 0.45, pitch: -0.28 }; st.zoom = 1; }
      }
      syncBar(); st.kick();
    };
    syncBar();
    if (st.tipNode == null && st.focus) showTip(st.focus);
  }

  // ---------- 전체 그리기 ----------
  function renderModes() { $$('.mode').forEach((b) => b.classList.toggle('on', b.dataset.mode === UI.mode)); }
  function renderAll() {
    renderModes(); renderSlots(); renderDrop(); renderDept();
    if (FS) { renderRank(); } else renderFields();
    $('.scrim').hidden = !UI.help;
  }

  // 예시 비교: 문헌정보학과 송민 vs 이지연 (없으면 교수님이 두 분 이상인 첫 학과)
  const pref = ['송민', '이지연'].map((n) => YON.find((y) => y.name === n && y.dept.startsWith('문헌정보'))).filter(Boolean);
  const sampleDept = pref.length === 2 ? dkey(pref[0]) : DEPTS.find((d) => deptCount[d] >= 2);
  const sample = pref.length === 2 ? pref : sampleDept ? YON.filter((y) => dkey(y) === sampleDept).slice(0, 2) : [];
  $('.sample-label').textContent = sample.length === 2 ? `예시 비교: ${sample[0].name} vs ${sample[1].name} (${sample[0].dept})` : '예시 비교';

  // ---------- 이벤트 (한 번만 연결) ----------
  root.__lm = { put, doSearch, send, slots, searchPool, renderAll, renderFields, renderDept, renderDrop, sample };
  if (!root.__bound) {
    root.__bound = true;
    const S = () => root.__lm;
    const input = root.querySelector('.q');
    input.addEventListener('input', () => { UI.q = input.value; UI.drop = true; S().renderDrop(); });
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') S().doSearch(); if (e.key === 'Escape') { UI.drop = false; S().renderDrop(); } });
    input.addEventListener('focus', () => { if (UI.q) { UI.drop = true; S().renderDrop(); } });
    root.addEventListener('click', (e) => {
      const t = e.target;
      const rm = t.closest('[data-rm]');
      if (rm) { const s = S(); s.slots[rm.dataset.rm] = null; s.send({ type: 'slots', A: s.slots.A, B: s.slots.B }); s.renderAll(); return; }
      const ad = t.closest('[data-add]');
      if (ad) { const p = S().searchPool[ad.dataset.key]; if (p) { UI.drop = false; S().put(ad.dataset.add, p); } return; }
      const md = t.closest('[data-mode]');
      if (md) {
        UI.mode = md.dataset.mode;
        root.querySelectorAll('.mode').forEach((b) => b.classList.toggle('on', b.dataset.mode === UI.mode));
        if (UI.mode === 'hero') input.focus();
        else root.querySelector(UI.mode === 'dept' ? '.sec-dept' : '.sec-field').scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
      const dp = t.closest('[data-dept]');
      if (dp) { UI.dept = dp.dataset.dept; UI.idx = 0; S().renderDept(); return; }
      const cl = t.closest('[data-col]');
      if (cl) { UI.dept = DEPTS.find((k) => k.split('|')[0] === cl.dataset.col) || UI.dept; UI.idx = 0; S().renderDept(); const dl = root.querySelector('.dept-chips'); if (dl) dl.scrollTop = 0; return; }
      const fc = t.closest('.fc');
      if (fc && !t.closest('button')) { UI.idx = +fc.dataset.idx; S().renderDept(); return; }
      const pk = t.closest('[data-pick]');
      if (pk) { UI.idx = +pk.dataset.pick; S().renderDept(); return; }
      const fd = t.closest('[data-field]');
      if (fd) { UI.field = fd.dataset.field; UI.sub = null; S().renderFields(); return; }
      const sb = t.closest('[data-sub]');
      if (sb) { UI.sub = sb.dataset.sub || null; S().renderFields(); return; }
      const act = t.closest('[data-act]');
      if (act) {
        const a = act.dataset.act;
        if (a === 'search') S().doSearch();
        else if (a === 'help') { UI.help = true; root.__helpFrom = act; root.querySelector('.scrim').hidden = false; root.querySelector('.modal .close').focus(); }
        else if (a === 'close') { UI.help = false; root.querySelector('.scrim').hidden = true; if (root.__helpFrom) root.__helpFrom.focus(); }
        else if (a === 'prev') { UI.idx = Math.max(0, UI.idx - 1); S().renderDept(); }
        else if (a === 'next') { UI.idx = UI.idx + 1; S().renderDept(); }
        else if (a === 'all') { UI.showAll = !UI.showAll; S().renderFields(); }
        else if (a === 'sample') { const s = S(); if (s.sample.length === 2) { s.slots.A = s.sample[0]; s.put('B', s.sample[1]); } }
        else if (a === 'compare') { const s = S(); if (s.slots.A && s.slots.B) s.send({ type: 'compare', A: s.slots.A, B: s.slots.B }); }
        return;
      }
      if (t.classList && t.classList.contains('scrim')) { UI.help = false; t.hidden = true; return; }
      if (!t.closest('.searchbox')) { UI.drop = false; S().renderDrop(); }
    });
    root.addEventListener('pointermove', (e) => {
      const el = e.target.closest && e.target.closest('.pc.filled');
      if (!el) return;
      const r = el.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      el.style.transform = `rotateY(${(x - 0.5) * 14}deg) rotateX(${(0.5 - y) * 12}deg)`;
      el.style.setProperty('--mx', x * 100 + '%'); el.style.setProperty('--my', y * 100 + '%');
    });
    root.addEventListener('pointerout', (e) => { const el = e.target.closest && e.target.closest('.pc'); if (el && !el.contains(e.relatedTarget)) el.style.transform = ''; });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && UI.help) { UI.help = false; root.querySelector('.scrim').hidden = true; if (root.__helpFrom) root.__helpFrom.focus(); } });
    // 이용 안내 창이 열려 있으면 Tab 키 이동을 창 안에서만 (창 안의 버튼은 닫기 하나뿐)
    root.addEventListener('keydown', (e) => { if (e.key === 'Tab' && UI.help) { e.preventDefault(); root.querySelector('.modal .close').focus(); } });
  }

  // 웹폰트가 늦게 도착하거나 창 크기가 바뀌면 카드 이름과 태그를 다시 맞춤
  const refit = () => root.querySelectorAll('.pc.filled').forEach((el) => { fitName(el.querySelector('.pn')); fitTags(el.querySelector('.tags')); fitCard(el, '.tags', '.tag', 'tag more'); });
  root.__lm.refit = refit;
  if (!root.__fitBound) {
    root.__fitBound = true;
    let tm = 0;
    window.addEventListener('resize', () => { clearTimeout(tm); tm = setTimeout(() => root.__lm.renderAll(), 150); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => root.__lm.refit());
  }

  // 처음 그리기 (데이터가 바뀔 때마다 다시 호출됨)
  const input = $('.q');
  if (input.value !== UI.q) input.value = UI.q;
  renderModes(); renderSlots(); renderDrop(); renderDept(); renderFields();
  $('.scrim').hidden = !UI.help;
  return () => { stopSky(); clearInterval(root.__themeTimer); };
}
