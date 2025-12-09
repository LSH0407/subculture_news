// 데이터 로딩 및 렌더링 로직

const state = {
    games: [],
    updates: [],
    calendar: null,
    selectedGames: new Set(), // 선택된 게임 ID들을 저장
    eventLimit: 10, // 하루 최대 이벤트 수
};

async function fetchJson(path) {
    const res = await fetch(path, { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to load ${path}`);
    return await res.json();
}

function buildGameMap(games) {
    const map = new Map();
    for (const game of games) {
        map.set(game.id, game);
    }
    return map;
}

function formatDate(dateStr) {
    try {
        const d = dayjs(dateStr);
        if (!d.isValid()) return dateStr;
        // ISO 문자열에 시간이 포함되어 있으면 시간까지 표시
        const hasTime = typeof dateStr === 'string' && dateStr.includes('T');
        return d.format(hasTime ? "YYYY-MM-DD HH:mm" : "YYYY-MM-DD");
    } catch (e) {
        return dateStr;
    }
}

function filterUpdates(updates) {
    // 날짜 필터링: 오늘 기준으로 3개월 이전 ~ 무한대 미래
    const now = dayjs();
    const threeMonthsAgo = now.subtract(3, 'month');
    
    const filtered = updates.filter(update => {
        const gameId = String(update.game_id || '');
        const isComingSoon = gameId.startsWith('steam_') || gameId.startsWith('coming_') || update.platform === 'switch';
        
        // Steam/Switch 발매예정 게임은 필터링 없이 전부 표시
        if (isComingSoon) {
            // 게임 필터 체크만 수행
            if (state.selectedGames.size === 0) return true;
            if (state.selectedGames.has('steam_all') && gameId.startsWith('steam_')) return true;
            if (state.selectedGames.has('switch_all') && update.platform === 'switch') return true;
            return state.selectedGames.has(gameId);
        }
        
        // 서브컬처 게임 등 일반 업데이트는 3개월 필터 적용
        const updateDate = update.update_date ? dayjs(update.update_date) : null;
        const endDate = update.end_date ? dayjs(update.end_date) : null;
        const isUpdateDateValid = updateDate && updateDate.isValid();
        const isEndDateValid = endDate && endDate.isValid();
        
        if (!isUpdateDateValid && !isEndDateValid) {
            return false; // 날짜 없는 일반 게임은 표시 안함
        }
        
        const isUpdateDateOld = isUpdateDateValid && updateDate.isBefore(threeMonthsAgo, 'day');
        const isEndDateOld = isEndDateValid && endDate.isBefore(threeMonthsAgo, 'day');
        
        if (isEndDateValid) {
            if (isEndDateOld) return false;
        } else if (isUpdateDateValid) {
            if (isUpdateDateOld) return false;
        }
        
        // 게임 필터링
        if (state.selectedGames.size === 0) return true;
        return state.selectedGames.has(update.game_id);
    });
    
    return filtered;
}

function renderStats(filtered) {
    const statsEl = document.getElementById("stats");
    if (!statsEl) return;
    const total = state.updates.length;
    const shown = filtered.length;
    
    statsEl.textContent = `표시: ${shown} / 전체: ${total}`;
}

function createGameCard(game, updates) {
    const col = document.createElement("div");
    col.className = "col-12";

    const card = document.createElement("div");
    card.className = "card shadow-sm";

    const row = document.createElement("div");
    row.className = "row g-0 align-items-center";

    const imgCol = document.createElement("div");
    imgCol.className = "col-auto p-2";
    const img = document.createElement("img");
    img.src = game.thumbnail || "";
    img.alt = game.name;
    img.className = "rounded object-fit-cover thumb-64";
    img.width = 64;
    img.height = 64;
    imgCol.appendChild(img);

    const bodyCol = document.createElement("div");
    bodyCol.className = "col p-2";

    const title = document.createElement("h5");
    title.className = "mb-1";
    const nameLink = document.createElement("a");
    nameLink.href = `detail.html?game=${encodeURIComponent(game.id)}`;
    nameLink.textContent = game.name;
    nameLink.className = "text-decoration-none";
    title.appendChild(nameLink);

    const meta = document.createElement("div");
    meta.className = "text-secondary small mb-2";
    meta.textContent = `${game.developer} · ${game.platform} · 출시일 ${formatDate(game.release_date)}`;

    const list = document.createElement("ul");
    list.className = "list-group list-group-flush";

    for (const u of updates) {
        const li = document.createElement("li");
        li.className = "list-group-item d-flex justify-content-between align-items-start gap-2 flex-wrap";

        const left = document.createElement("div");
        left.className = "me-auto";
        left.innerHTML = `<div class=\"fw-semibold\">v${u.version || "-"}</div><div class=\"text-secondary small\">${u.description || ""}</div>`;

        const right = document.createElement("div");
        right.className = "text-nowrap text-secondary small";
        right.textContent = formatDate(u.update_date);

        li.append(left, right);
        list.appendChild(li);
    }

    bodyCol.append(title, meta, list);
    row.append(imgCol, bodyCol);
    card.appendChild(row);
    col.appendChild(card);

    return col;
}

function render(filtered, gameMap) {
    renderStats(filtered);
    renderCalendarEvents(filtered, gameMap);
}

function populateGameFilter(games) {
    const container = document.getElementById('gameFilter');
    const subEl = document.getElementById('subcultureFilter');
    const conEl = document.getElementById('consoleFilter');
    if (!container || !subEl || !conEl) {
        console.error('gameFilter containers not found!');
        return;
    }
    
    subEl.innerHTML = '';
    conEl.innerHTML = '';
    
    // 고유한 게임 ID들
    const gameIds = new Set();
    state.updates.forEach(u => gameIds.add(u.game_id));
    const steamGames = Array.from(gameIds).filter(id => id.startsWith('steam_'));
    const switchGames = Array.from(gameIds).filter(id => {
        const u = state.updates.find(x => x.game_id === id);
        return u && u.platform === 'switch';
    });
    
    // 서브컬쳐 그룹
    const subcultureIds = ['nikke','ww','genshin','star_rail','zzz'];
    const subcultureGames = games.filter(g => subcultureIds.includes(g.id));
    subcultureGames.forEach(game => {
        subEl.appendChild(createGameCheckbox(game.id, game.name, game.thumbnail));
    });
    
    // 콘솔 그룹 (같은 줄에 Switch, Steam)
    if (switchGames.length > 0) {
        conEl.appendChild(createGameCheckbox('switch_all', '닌텐도 스위치', 'assets/switch.png'));
    }
    if (steamGames.length > 0) {
        conEl.appendChild(createGameCheckbox('steam_all', 'Steam(인기발매예정)', 'assets/steam.png'));
    }
}

function createGameCheckbox(gameId, gameName, thumbnail) {
    const col = document.createElement('div');
    col.className = 'col-auto';
    
    const checkbox = document.createElement('div');
    checkbox.className = 'form-check';
    
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.className = 'form-check-input';
    input.id = `game-${gameId}`;
    input.value = gameId;
    input.checked = true; // 기본적으로 모두 선택
    
    const label = document.createElement('label');
    label.className = 'form-check-label d-flex align-items-center';
    label.htmlFor = `game-${gameId}`;
    
    let labelContent = gameName;
    if (thumbnail) {
        labelContent = `<img src="${thumbnail}" alt="${gameName}" class="me-2" style="width: 20px; height: 20px; object-fit: cover; border-radius: 3px;">${gameName}`;
    }
    label.innerHTML = labelContent;
    
    checkbox.appendChild(input);
    checkbox.appendChild(label);
    col.appendChild(checkbox);
    
    return col;
}

function bindControls(updateView) {
    // 이벤트 제한 설정 변경 이벤트
    const eventLimitSelect = document.getElementById('eventLimit');
    if (eventLimitSelect) {
        eventLimitSelect.addEventListener('change', updateEventLimit);
    }

    const gameFilter = document.getElementById('gameFilter');
    const subEl = document.getElementById('subcultureFilter');
    const conEl = document.getElementById('consoleFilter');

    const getAllCheckboxes = () => document.querySelectorAll('#subcultureFilter input[type="checkbox"], #consoleFilter input[type="checkbox"]');

    if (gameFilter) {
        gameFilter.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox') {
                const gameId = e.target.value;
                if (e.target.checked) {
                    state.selectedGames.add(gameId);
                } else {
                    state.selectedGames.delete(gameId);
                }
                updateView();
            }
        });
    }

    // 전체 선택
    const selectAllBtn = document.getElementById('selectAll');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            const checkboxes = getAllCheckboxes();
            checkboxes.forEach(cb => { cb.checked = true; state.selectedGames.add(cb.value); });
            updateView();
        });
    }

    // 전체 해제
    const selectNoneBtn = document.getElementById('selectNone');
    if (selectNoneBtn) {
        selectNoneBtn.addEventListener('click', () => {
            const checkboxes = getAllCheckboxes();
            checkboxes.forEach(cb => { cb.checked = false; });
            state.selectedGames.clear();
            updateView();
        });
    }

    // 콘솔만
    const selectConsoleBtn = document.getElementById('selectConsole');
    if (selectConsoleBtn) {
        selectConsoleBtn.addEventListener('click', () => {
            const checkboxes = getAllCheckboxes();
            state.selectedGames.clear();
            checkboxes.forEach(cb => {
                const v = cb.value;
                const on = (v === 'switch_all' || v === 'steam_all' || String(v).startsWith('steam_'));
                cb.checked = on;
                if (on) state.selectedGames.add(v);
            });
            updateView();
        });
    }

    // 서브컬쳐만
    const selectSubBtn = document.getElementById('selectSubculture');
    if (selectSubBtn) {
        selectSubBtn.addEventListener('click', () => {
            const subs = new Set(['nikke','ww','genshin','star_rail','zzz']);
            const checkboxes = getAllCheckboxes();
            state.selectedGames.clear();
            checkboxes.forEach(cb => {
                const on = subs.has(cb.value);
                cb.checked = on;
                if (on) state.selectedGames.add(cb.value);
            });
            updateView();
        });
    }

    // 달력 이미지 저장
    const downloadBtn = document.getElementById('downloadCalendar');
    if (downloadBtn && window.html2canvas) {
        downloadBtn.addEventListener('click', async () => {
            try {
                const cal = document.getElementById('calendar');
                if (!cal) return;
                // FullCalendar 내부 스크롤을 고려하여 현재 보이는 달력 영역을 캡처
                const canvas = await window.html2canvas(cal, {
                    backgroundColor: '#ffffff',
                    useCORS: true,
                    scale: window.devicePixelRatio || 2,
                });
                const url = canvas.toDataURL('image/png');
                const a = document.createElement('a');
                const ym = dayjs(state.calendar?.getDate()).format('YYYY-MM');
                a.href = url;
                a.download = `subculture-calendar-${ym}.png`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            } catch (e) {
                console.error('달력 저장 실패:', e);
            }
        });
    }
}

async function init() {
    console.log('=== INIT START ===');
    try {
        console.log('Loading data...');
        const [games, updates] = await Promise.all([
            fetchJson("data/games.json"),
            fetchJson("data/updates.json"),
        ]);
        console.log('Data loaded:', { games: games.length, updates: updates.length });
        
        state.games = games;
        state.updates = updates;

        const gameMap = buildGameMap(games);
        
        // 초기에 모든 게임을 선택된 상태로 설정
        const allGameIds = new Set();
        // 서브컬처 게임들만 개별적으로 추가 (games.json의 게임들)
        games.forEach(game => {
            // Steam이나 Switch 게임이 아닌 경우만 개별적으로 추가
            if (!game.id.startsWith('steam_') && game.id !== 'switch_all') {
                allGameIds.add(game.id);
            }
        });
        // Steam 게임 카테고리 추가 (개별 Steam 게임은 추가하지 않음)
        allGameIds.add('steam_all');
        // Switch 게임 카테고리 추가 (개별 Switch 게임은 추가하지 않음)
        allGameIds.add('switch_all');
        state.selectedGames = allGameIds;
        console.log('Selected games count:', state.selectedGames.size);
        
        // 게임 필터 생성 (데이터 로드 후)
        console.log('Creating game filter...');
        populateGameFilter(games);
        
        // updateView 함수를 먼저 정의 (bindControls에서 사용)
        const updateView = () => {
            const filtered = filterUpdates(state.updates);
            render(filtered, gameMap);
        };
        
        // 달력 설정
        setupCalendar(gameMap);
        
        // 초기 렌더링 (먼저 실행)
        updateView();
        
        // 컨트롤 바인딩 (updateView를 사용)
        bindControls(updateView);
        
        // 체크박스들을 모두 선택된 상태로 설정하고 화면 업데이트 (시각적 동기화)
        setTimeout(() => {
            const checkboxes = document.querySelectorAll('#gameFilter input[type="checkbox"]');
            console.log('Found checkboxes:', checkboxes.length);
            checkboxes.forEach(cb => {
                cb.checked = true;
            });
            // 초기 렌더링을 확실하게 하기 위해 updateView 호출
            updateView();
        }, 100);
        // 범례 제거
    } catch (err) {
        const calendar = document.getElementById("calendar");
        if (calendar) {
            calendar.innerHTML = `<div class=\"alert alert-danger\" role=\"alert\">데이터 로딩 실패: ${String(err)}</div>`;
        }
        // eslint-disable-next-line no-console
        console.error(err);
    }
}

document.addEventListener("DOMContentLoaded", init);

function toCalendarEvents(updates, gameMap) {
    const events = [];
    let steamValidCount = 0;
    let steamInvalidCount = 0;
    
    updates.forEach(u => {
        const game = gameMap.get(u.game_id);
        const isNew = String(u.game_id || '').startsWith('steam_') || String(u.game_id || '').startsWith('coming_');
        // 게임 이름 우선순위: games.json의 name > updates.json의 name > game_id
        const title = game?.name || (u.name && u.name.trim() ? u.name : null) || String(u.game_id || '');
        
        // 날짜 유효성 검사 및 변환
        // "2025년", "TBA" 등 파싱 불가능한 날짜 처리
        let eventDate = u.update_date;
        let isYearOnly = false; // 연도만 있는 날짜인지 표시
        const parsedDate = dayjs(eventDate);
        
        // Steam 게임 디버깅
        const isSteam = String(u.game_id || '').startsWith('steam_');
        if (isSteam) {
            if (parsedDate.isValid()) {
                steamValidCount++;
                if (steamValidCount <= 3) {
                    console.log(`[Steam OK] ${u.name}: '${eventDate}' -> ${parsedDate.format('YYYY-MM-DD')}`);
                }
            } else {
                steamInvalidCount++;
                if (steamInvalidCount <= 3) {
                    console.log(`[Steam FAIL] ${u.name}: '${eventDate}'`);
                }
            }
        }
        
        if (!parsedDate.isValid()) {
            // 연도만 있는 경우 (예: "2025년") -> 달력에 표시하지 않음 (TBA 처리)
            const yearMatch = String(eventDate).match(/(\d{4})/);
            if (yearMatch) {
                // 연도만 있는 게임은 달력에서 제외 (발매일 미정으로 처리)
                // 대신 별도의 "발매일 미정" 섹션에서 표시할 수 있음
                isYearOnly = true;
                // 달력에 표시하려면 현재 날짜 기준으로 표시 (옵션)
                // 여기서는 달력에서 제외
                return;
            } else {
                // 완전히 파싱 불가능한 경우 (TBA 등) -> 이벤트 생성 건너뛰기
                return;
            }
        }
        
        // 디버깅: 게임 이름이 제대로 설정되는지 확인
        if (['nikke', 'star_rail', 'zzz'].includes(u.game_id)) {
            console.log(`Game ID: ${u.game_id}, Game Name: ${game?.name}, Title: ${title}`);
        }
        
               // 헤더 이미지: Steam과 Switch 게임을 다르게 처리
               let headerImage = u.header_image || u.headerImage || '';
               let headerCandidates = [];
               
               if (typeof u.game_id === 'string' && u.game_id.startsWith('steam_')) {
                   // Steam 게임: CDN 후보들을 폴백으로 제공
                   const appid = u.game_id.replace('steam_', '');
                   const cdnCandidates = [
                       `https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/${appid}/header.jpg`,
                       `https://cdn.akamai.steamstatic.com/steam/apps/${appid}/header.jpg`,
                       `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/header.jpg`,
                       `https://cdn.akamai.steamstatic.com/steam/apps/${appid}/capsule_616x353.jpg`,
                       `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/capsule_616x353.jpg`
                   ];
                   // 현재 선택된 headerImage를 제외하고 폴백 목록 구성
                   headerCandidates = cdnCandidates.filter(u => u !== headerImage);
                   if (!headerImage) {
                       headerImage = cdnCandidates[0];
                   }
               } else if (u.platform === 'switch' && headerImage) {
                   // Switch 게임: HTML 태그에서 src 추출
                   const srcMatch = headerImage.match(/src="([^"]+)"/);
                   if (srcMatch) {
                       headerImage = srcMatch[1];
                       // Switch 게임은 프록시 없이 직접 사용
                       headerCandidates = [];
                   }
               }
        
        // 이벤트 유형 판정: 업데이트 / 공식방송 / 신규발매
        const pickType = () => {
            const desc = String(u.description || '');
            const link = String(u.url || '').toLowerCase();
            // 방송 키워드: 한글은 toLowerCase() 영향 없으므로 원본 그대로 체크
            if (desc.includes('방송') || desc.includes('프로그램') || desc.includes('라이브') || 
                link.includes('youtube.com') || link.includes('youtu.be')) {
                return 'broadcast';
            }
            // 신규발매: steam coming soon 또는 desc에 발매예정
            if (String(u.game_id || '').startsWith('steam_') || String(u.game_id || '').startsWith('coming_') || desc.includes('발매예정')) {
                return 'release';
            }
            // 그 외는 업데이트(신규 캐릭 포함)
            return 'update';
        };
        const type = pickType();
        // 유형 기본 색상: 업데이트(파랑), 방송(황금), 신규발매(초록)
        const typeColor = (t => ({
            update: '#0d6efd',
            broadcast: '#ffc107', // 황금색
            release: '#198754',
        })[t] || '#0d6efd')(type);
        const END_COLOR = '#dc3545'; // 종료일 이벤트는 빨간색

        const baseExtended = {
            gameId: u.game_id,
            description: u.description || "",
            version: u.version || "",
            thumb: game?.thumbnail || "",
            color: { bg: typeColor },
            url: u.url || '',
            isNew,
            platform: u.platform || 'steam',
            name: u.name || game?.name || title,
            tags: u.tags || '',
            summary: u.summary || '',
            headerImage,
            headerCandidates,
            type,
        };

        const isTimed = typeof eventDate === 'string' && eventDate.includes('T');

        // 날짜가 다른 범위일 때만 시작/종료로 분해 (같은 날 범위는 단일 이벤트로 처리)
        const startDateOnly = (eventDate || '').toString().slice(0, 10);
        const endDateOnly = (u.end_date || '').toString().slice(0, 10);
        if (u.end_date && endDateOnly && startDateOnly && endDateOnly !== startDateOnly) {
            // 시작일 이벤트 (단일)
            events.push({
                title,
                start: eventDate,
                allDay: !isTimed,
                backgroundColor: typeColor,
                borderColor: typeColor,
                textColor: '#fff',
                extendedProps: { ...baseExtended, milestone: 'start' }
            });
            // 종료일 이벤트 (단일, 빨간색 강조)
            events.push({
                title,
                start: u.end_date,
                allDay: !(typeof u.end_date === 'string' && u.end_date.includes('T')),
                backgroundColor: END_COLOR,
                borderColor: END_COLOR,
                textColor: '#fff',
                extendedProps: { ...baseExtended, milestone: 'end', color: { bg: END_COLOR } }
            });
        } else {
            // 단일 이벤트
            events.push({
                title,
                start: eventDate,
                end: undefined, // 막대 표시 방지
                allDay: !isTimed,
                backgroundColor: typeColor,
                borderColor: typeColor,
                textColor: '#fff',
                extendedProps: { ...baseExtended }
            });
        }
    });
    
    // Steam 게임 통계 출력
    console.log(`[Steam 통계] 유효: ${steamValidCount}, 무효: ${steamInvalidCount}, 총 이벤트: ${events.length}`);
    
    return events;
}

function setupCalendar(gameMap) {
    const el = document.getElementById('calendar');
    if (!el || !window.FullCalendar) {
        console.warn('FullCalendar not available or calendar element not found');
        return;
    }
    
    console.log('Setting up calendar...');
    state.calendar = new FullCalendar.Calendar(el, {
        locale: 'ko', // 한국어 로케일 설정
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,listMonth'
        },
        // 이벤트 정렬: 게임 선택 필터 순서대로
        eventOrder: (a, b) => {
            // 게임 ID 우선순위 정의 (필터에 나오는 순서)
            const gameOrder = ['nikke', 'ww', 'genshin', 'star_rail', 'zzz', 'switch', 'steam'];
            
            const getGameOrder = (gameId) => {
                if (!gameId) return 999;
                // Steam 게임
                if (String(gameId).startsWith('steam_')) return 6;
                // Switch 게임 (platform으로 판별 필요)
                const idx = gameOrder.indexOf(gameId);
                return idx >= 0 ? idx : 999;
            };
            
            const orderA = getGameOrder(a.extendedProps?.gameId);
            const orderB = getGameOrder(b.extendedProps?.gameId);
            
            // Switch 플랫폼 체크
            const platformA = a.extendedProps?.platform;
            const platformB = b.extendedProps?.platform;
            const finalOrderA = platformA === 'switch' ? 5 : orderA;
            const finalOrderB = platformB === 'switch' ? 5 : orderB;
            
            if (finalOrderA !== finalOrderB) {
                return finalOrderA - finalOrderB;
            }
            
            // 같은 게임이면 제목 사전순
            return (a.title || '').localeCompare(b.title || '');
        },
        dayMaxEventRows: 10, // 최대 10개 행까지 표시
        moreLinkClick: 'popover',
        dayMaxEvents: () => state.eventLimit, // 동적으로 이벤트 제한 적용
        height: 'auto', // 높이 자동 조정
        datesSet: () => {
            const rightChunk = document.querySelector('.fc-header-toolbar .fc-toolbar-chunk:last-child');
            if (rightChunk && !document.getElementById('typeLegend')) {
                const legend = document.createElement('div');
                legend.id = 'typeLegend';
                legend.innerHTML = `
                    <span><i class=\"dot\" style=\"background:#0d6efd\"></i>업데이트</span>
                    <span><i class=\"dot\" style=\"background:#ffc107\"></i>방송</span>
                    <span><i class=\"dot\" style=\"background:#198754\"></i>신규발매</span>
                    <span><i class=\"dot\" style=\"background:#dc3545\"></i>종료</span>
                `;
                // 버튼 그룹 앞에 삽입하여 겹침 방지
                rightChunk.insertBefore(legend, rightChunk.firstChild);
            }
        },
        eventDisplay: 'block', // 이벤트를 블록으로 표시
        showNonCurrentDates: true, // 이전/다음 달 날짜들도 표시
        fixedWeekCount: false, // 고정된 주 수 사용하지 않음
        eventClick: (info) => {
            const ex = info.event.extendedProps || {};
            if (ex.url) {
                window.open(ex.url, '_blank');
                return;
            }
            if (ex.gameId) {
                window.location.href = `detail.html?game=${encodeURIComponent(ex.gameId)}`;
            }
        },
        eventContent: (arg) => {
            const ex = arg.event.extendedProps || {};
            const bg = ex.color?.bg || '#0d6efd';
            // 썸네일: 기존 5개 게임은 이미지, 신작은 플랫폼 아이콘
            let thumbHtml = '';
            if (ex.thumb) {
                thumbHtml = `<img class=\"chip-thumb\" src=\"${ex.thumb}\" alt=\"thumb\">`;
            } else if (ex.isNew || ex.platform === 'switch') {
                const icon = (ex.platform === 'switch') ? 'assets/switch.png' : 'assets/steam.png';
                thumbHtml = `<img class=\"chip-thumb\" src=\"${icon}\" alt=\"platform\">`;
            }
            // 칩 표시는 '썸네일 + 게임제목'만. 설명/장르 배지는 표시하지 않음.
            // 게임 이름 우선: extendedProps.name → games.json 매핑 → event.title
            let displayTitle = ex.name || '';
            if (!displayTitle && ex.gameId && Array.isArray(state.games)) {
                const found = state.games.find(g => g.id === ex.gameId);
                if (found && found.name) displayTitle = found.name;
            }
            if (!displayTitle) displayTitle = arg.event.title;
            
            // 디버깅: 헤더 이미지 확인
            if (ex.gameId === 'steam_3405690') {
                console.log('EA SPORTS FC 26 - EventContent Debug:', {
                    gameId: ex.gameId,
                    headerImage: ex.headerImage,
                    headerCandidates: ex.headerCandidates,
                    displayTitle
                });
            }

            const html = `<div class=\"event-chip\" style=\"background:${bg}\">${thumbHtml}<span class=\"event-title\">${displayTitle}</span></div>`;
            return { html };
        },
        eventMouseEnter: (info) => {
            // 이미 툴팁이 있다면 중복 생성 방지
            if (info.el._tooltip) {
                return;
            }
            
            const ex = info.event.extendedProps || {};
            const fullTitle = ex.name || info.event.title || '';
            
            // 이벤트 시간 표시 라인 (시간 포함 이벤트만)
            let whenLine = '';
            try {
                const hasTime = info.event && info.event.start && info.event.allDay === false;
                if (hasTime) {
                    whenLine = `일정: ${dayjs(info.event.start).format('YYYY-MM-DD HH:mm')}`;
                }
            } catch (e) {}
            
            // tags: comma-separated → take top 5
            let tagLine = '';
            if (ex.tags) {
                const firstFive = ex.tags.split(',').map(s => s.trim()).filter(Boolean).slice(0, 5);
                if (firstFive.length) tagLine = `이 제품의 인기 태그: ${firstFive.join(', ')}`;
            }
            const gameInfo = ex.summary || ex.description || '';
            
            let headerImg = '';
            if (ex.headerImage) {
                // 디버깅: Switch 게임 이미지 확인
                if (ex.platform === 'switch') {
                    console.log('Switch game header image:', ex.headerImage);
                }
                if (ex.platform === 'switch') {
                    // Switch 게임: CORS 회피 위해 프록시 우선 시도 후 원본
                    const raw = ex.headerImage;
                    const proxied = `https://r.jina.ai/http/${String(raw).replace(/^https?:\/\//,'')}`;
                    headerImg = `<div class=\"tooltip-header\"><img src=\"${proxied}\" data-fallback=\"${raw}\" alt=\"header\" loading=\"lazy\" onerror=\"this.onerror=null; this.src=this.dataset.fallback;\"></div>`;
                } else {
                    // Steam 게임: 프록시 사용
                    const buildProxyVariants = (url) => {
                        const variants = [];
                        const u = String(url);
                        // 원본
                        variants.push(u);
                        // r.jina.ai 프록시 (원본 품질 유지)
                        variants.push(`https://r.jina.ai/http/${u.replace(/^https?:\/\//,'')}`);
                        // weserv 고품질 설정
                        const clean = u.replace(/^https?:\/\//, '');
                        variants.push(`https://images.weserv.nl/?url=${encodeURIComponent(clean)}&q=100`);
                        return variants;
                    };
                    // 메인 이미지 + 후보들을 모두 프록시 변형 포함으로 전개
                    let candidates = buildProxyVariants(ex.headerImage);
                    if (Array.isArray(ex.headerCandidates)) {
                        for (const c of ex.headerCandidates) {
                            candidates = candidates.concat(buildProxyVariants(c));
                        }
                    }
                    // 중복 제거
                    candidates = Array.from(new Set(candidates));
                    const first = candidates.shift();
                    const dataCandidates = candidates.length ? String(JSON.stringify(candidates)).replace(/\"/g,'\\"') : '[]';
                    headerImg = `<div class=\"tooltip-header\"><img src=\"${first}\" alt=\"header\" loading=\"lazy\" referrerpolicy=\"no-referrer\" crossorigin=\"anonymous\" onerror=\"(function(img){try{var c=img.dataset.candidates?JSON.parse(img.dataset.candidates):[];var next=c.shift();if(next){img.dataset.candidates=JSON.stringify(c);img.src=next;} }catch(e){} })(this)\" data-candidates=\"${dataCandidates}\"></div>`;
                }
            }
            // 가격 표시: price가 없으면 description의 마지막 세그먼트에서 추출(… · 가격)
            let priceLine = '';
            if (ex.price && String(ex.price).trim()) {
                priceLine = `가격: ${ex.price}`;
            } else if (ex.description && ex.description.includes('·')) {
                const segs = ex.description.split('·').map(s => s.trim());
                const last = segs[segs.length - 1] || '';
                if (/[₩￦]|원|미표기/.test(last)) priceLine = `가격: ${last}`;
            }

            const desc = `
                <div class=\"tooltip-title\">${fullTitle}</div>
                ${whenLine ? `<div class=\"tooltip-tags\">${whenLine}</div>` : ''}
                ${headerImg}
                ${tagLine ? `<div class=\"tooltip-tags\">${tagLine}</div>` : ''}
                ${priceLine ? `<div class=\"tooltip-tags\">${priceLine}</div>` : ''}
                ${gameInfo ? `<div class=\"tooltip-summary\">${gameInfo}</div>` : ''}
            `;
            const tooltip = document.createElement('div');
            tooltip.className = 'event-tooltip';
            tooltip.innerHTML = `<div class=\"tooltip-content\">${desc}</div>`;
            
            // 툴팁 위치를 고정 (마우스 따라 움직이지 않음)
            const rect = info.el.getBoundingClientRect();
            const x = rect.left + window.scrollX;
            const y = rect.bottom + window.scrollY;
            
            // 툴팁 높이를 미리 계산해서 화면 밖으로 나가는지 확인
            tooltip.style.visibility = 'hidden';
            tooltip.style.position = 'absolute';
            document.body.appendChild(tooltip);
            
            const tooltipHeight = tooltip.offsetHeight;
            const viewportHeight = window.innerHeight;
            const isNearBottom = (rect.bottom + tooltipHeight + 12) > viewportHeight;
            
            tooltip.style.left = (x + 12) + 'px';
            if (isNearBottom) {
                // 맨 아래 주차의 경우 툴팁을 위로 표시
                tooltip.style.top = (rect.top + window.scrollY - tooltipHeight - 12) + 'px';
            } else {
                // 일반적인 경우 툴팁을 아래로 표시
                tooltip.style.top = (y + 12) + 'px';
            }
            tooltip.style.zIndex = '9999';
            tooltip.style.visibility = 'visible';
            
            info.el._tooltip = tooltip;
        },
        eventMouseLeave: (info) => {
            if (info.el._tooltip) {
                document.body.removeChild(info.el._tooltip);
                info.el._tooltip = null;
            }
        },
        events: []
    });
    
    // 상단 우측 범례 동적 생성
    const titleBar = el.querySelector('.fc-header-toolbar') || document.querySelector('.fc-header-toolbar');
    if (titleBar && !document.getElementById('typeLegend')) {
        const legend = document.createElement('div');
        legend.id = 'typeLegend';
        legend.innerHTML = `
            <span><i class="dot" style="background:#0d6efd"></i>업데이트</span>
            <span><i class="dot" style="background:#ffc107"></i>방송</span>
            <span><i class="dot" style="background:#198754"></i>신규발매</span>
            <span><i class="dot" style="background:#dc3545"></i>종료</span>
        `;
        titleBar.style.position = 'relative';
        titleBar.appendChild(legend);
    }

    // 탭이 없으므로 제거
    
    state.calendar.render();
}

function renderCalendarEvents(filtered, gameMap) {
    if (!state.calendar) {
        console.warn('Calendar not initialized');
        return;
    }
    
    console.log('Rendering calendar events:', filtered.length);
    state.calendar.removeAllEvents();
    const events = toCalendarEvents(filtered, gameMap);
    console.log('Calendar events created:', events.length);
    if (events.length) {
        state.calendar.addEventSource(events);
    }
    state.calendar.render();
}

function getThemeColor() {
    return '#0d6efd';
}

function updateEventLimit() {
    const eventLimitSelect = document.getElementById('eventLimit');
    if (eventLimitSelect) {
        const value = eventLimitSelect.value;
        state.eventLimit = value === 'false' ? false : parseInt(value);
        
        // 달력 설정 업데이트
        if (state.calendar) {
            state.calendar.setOption('dayMaxEvents', state.eventLimit);
        }
        
        console.log('Event limit updated to:', state.eventLimit);
    }
}

function updateView() {
    const filtered = filterUpdates(state.updates);
    const gameMap = buildGameMap(state.games);
    render(filtered, gameMap);
}
