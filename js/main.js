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
        return d.isValid() ? d.format("YYYY-MM-DD") : dateStr;
    } catch {
        return dateStr;
    }
}

function filterUpdates(updates) {
    // 선택된 게임이 없으면 모든 항목 표시
    if (state.selectedGames.size === 0) {
        return updates.slice();
    }
    
    // 선택된 게임들만 필터링
    return updates.filter(update => {
        // Steam 게임 카테고리가 선택된 경우
        if (state.selectedGames.has('steam_all') && update.game_id.startsWith('steam_')) {
            return true;
        }
        
        // Switch 게임 카테고리가 선택된 경우
        if (state.selectedGames.has('switch_all') && update.platform === 'switch') {
            return true;
        }
        
        // 개별 게임이 선택된 경우
        return state.selectedGames.has(update.game_id);
    });
}

function renderStats(filtered) {
    const statsEl = document.getElementById("stats");
    if (!statsEl) return;
    const total = state.updates.length;
    const shown = filtered.length;
    
    let dateRange = "표시할 업데이트가 없습니다";
    if (filtered.length > 0) {
        // 날짜순으로 정렬
        const sortedByDate = [...filtered].sort((a, b) => {
            const dateA = new Date(a.update_date);
            const dateB = new Date(b.update_date);
            return dateA - dateB;
        });
        
        const earliestDate = formatDate(sortedByDate[0].update_date);
        const latestDate = formatDate(sortedByDate[sortedByDate.length - 1].update_date);
        dateRange = `${earliestDate} ~ ${latestDate}`;
    }
    
    statsEl.textContent = `표시: ${shown} / 전체: ${total} · 범위: ${dateRange}`;
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
    const filterEl = document.getElementById('gameFilter');
    if (!filterEl) {
        console.error('gameFilter element not found!');
        return;
    }
    
    console.log('populateGameFilter called with', games.length, 'games');
    console.log('state.updates length:', state.updates.length);
    
    filterEl.innerHTML = '';
    
    // 고유한 게임 ID들을 수집 (updates.json에서)
    const gameIds = new Set();
    state.updates.forEach(update => {
        gameIds.add(update.game_id);
    });
    
    // games.json에 있는 모든 게임들 표시 (일정이 없어도 표시)
    const steamGames = Array.from(gameIds).filter(id => id.startsWith('steam_'));
    const switchGames = Array.from(gameIds).filter(id => {
        const update = state.updates.find(u => u.game_id === id);
        return update && update.platform === 'switch';
    });
    const otherGames = Array.from(gameIds).filter(id => 
        !games.find(g => g.id === id) && 
        !id.startsWith('steam_') && 
        !switchGames.includes(id)
    );
    
    console.log('All games from games.json:', games.length, 'Steam games:', steamGames.length, 'Switch games:', switchGames.length, 'Other games:', otherGames.length);
    
    // games.json의 모든 게임들 표시 (일정이 있든 없든)
    games.forEach(game => {
        const checkbox = createGameCheckbox(game.id, game.name, game.thumbnail);
        filterEl.appendChild(checkbox);
        console.log('Added checkbox for game:', game.name);
    });
    
    // Steam 게임들을 하나의 카테고리로 묶기
    if (steamGames.length > 0) {
        const steamCheckbox = createGameCheckbox('steam_all', `Steam 게임 (${steamGames.length}개)`, 'assets/steam.png');
        filterEl.appendChild(steamCheckbox);
        console.log('Added Steam games category:', steamGames.length);
    }
    
    // Switch 게임들을 하나의 카테고리로 묶기
    if (switchGames.length > 0) {
        const switchCheckbox = createGameCheckbox('switch_all', `닌텐도 스위치 게임 (${switchGames.length}개)`, 'assets/switch.png');
        filterEl.appendChild(switchCheckbox);
        console.log('Added Switch games category:', switchGames.length);
    }
    
    // 기타 게임들 표시
    otherGames.forEach(gameId => {
        const update = state.updates.find(u => u.game_id === gameId);
        const name = update?.name || gameId;
        const checkbox = createGameCheckbox(gameId, name, '');
        filterEl.appendChild(checkbox);
        console.log('Added checkbox for other game:', name);
    });
    
    console.log('Total checkboxes created:', filterEl.children.length);
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
    
    // 게임 필터 체크박스 이벤트
    const gameFilter = document.getElementById('gameFilter');
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
    
    // 전체 선택 버튼
    const selectAllBtn = document.getElementById('selectAll');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            const checkboxes = gameFilter.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(cb => {
                cb.checked = true;
                state.selectedGames.add(cb.value);
            });
            updateView();
        });
    }
    
    // 전체 해제 버튼
    const selectNoneBtn = document.getElementById('selectNone');
    if (selectNoneBtn) {
        selectNoneBtn.addEventListener('click', () => {
            const checkboxes = gameFilter.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(cb => {
                cb.checked = false;
            });
            state.selectedGames.clear();
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
        // games.json의 모든 게임들 추가
        games.forEach(game => {
            allGameIds.add(game.id);
        });
        // updates.json의 모든 게임들 추가
        state.updates.forEach(update => {
            allGameIds.add(update.game_id);
        });
        // Steam 게임 카테고리도 추가
        allGameIds.add('steam_all');
        // Switch 게임 카테고리도 추가
        allGameIds.add('switch_all');
        state.selectedGames = allGameIds;
        console.log('Selected games count:', state.selectedGames.size);
        
        // 게임 필터 생성 (데이터 로드 후)
        console.log('Creating game filter...');
        populateGameFilter(games);
        
        // 체크박스들을 모두 선택된 상태로 설정
        setTimeout(() => {
            const checkboxes = document.querySelectorAll('#gameFilter input[type="checkbox"]');
            console.log('Found checkboxes:', checkboxes.length);
            checkboxes.forEach(cb => {
                cb.checked = true;
            });
        }, 200);
        
        const updateView = () => {
            const filtered = filterUpdates(state.updates);
            render(filtered, gameMap);
        };
        bindControls(updateView);
        setupCalendar(gameMap);
        updateView();
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
    updates.forEach(u => {
        const game = gameMap.get(u.game_id);
        const isNew = String(u.game_id || '').startsWith('steam_') || String(u.game_id || '').startsWith('coming_');
        // 게임 이름 우선순위: games.json의 name > updates.json의 name > game_id
        const title = game?.name || (u.name && u.name.trim() ? u.name : null) || String(u.game_id || '');
        
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
            const desc = String(u.description || '').toLowerCase();
            const link = String(u.url || '').toLowerCase();
            if (desc.includes('방송') || link.includes('youtube.com') || link.includes('youtu.be') || desc.includes('라이브')) {
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
        const typeColor = (t => ({
            update: '#0d6efd',
            broadcast: '#6f42c1',
            release: '#198754',
        })[t] || '#0d6efd')(type);

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

        const isTimed = typeof u.update_date === 'string' && u.update_date.includes('T');

        // 날짜가 다른 범위일 때만 시작/종료로 분해 (같은 날 범위는 단일 이벤트로 처리)
        const startDateOnly = (u.update_date || '').toString().slice(0, 10);
        const endDateOnly = (u.end_date || '').toString().slice(0, 10);
        if (u.end_date && endDateOnly && startDateOnly && endDateOnly !== startDateOnly) {
            // 시작일 이벤트 (단일)
            events.push({
                title,
                start: u.update_date,
                allDay: !isTimed,
                backgroundColor: typeColor,
                borderColor: typeColor,
                textColor: '#fff',
                extendedProps: { ...baseExtended, milestone: 'start' }
            });
            // 종료일 이벤트 (단일, 제목에 종료 표기)
            events.push({
                title,
                start: u.end_date,
                allDay: !(typeof u.end_date === 'string' && u.end_date.includes('T')),
                backgroundColor: typeColor,
                borderColor: typeColor,
                textColor: '#fff',
                extendedProps: { ...baseExtended, milestone: 'end' }
            });
        } else {
            // 단일 이벤트
            events.push({
                title,
                start: u.update_date,
                end: undefined, // 막대 표시 방지
                allDay: !isTimed,
                backgroundColor: typeColor,
                borderColor: typeColor,
                textColor: '#fff',
                extendedProps: { ...baseExtended }
            });
        }
    });
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
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,listMonth'
        },
        // 이벤트 정렬: 기본적으로 시간순, 동일 시간일 때 플랫폼 우선순위 (모바일/고정 게임 우선, Steam/Switch 후순위)
        eventOrder: (a, b) => {
            const pa = (a.extendedProps?.platform || '').toLowerCase();
            const pb = (b.extendedProps?.platform || '').toLowerCase();
            const weight = (p) => (p === 'steam' || p === 'switch') ? 1 : 0; // 1이면 후순위
            const dw = weight(pa) - weight(pb);
            if (dw !== 0) return dw; // Steam/Switch를 뒤로
            // 같으면 제목 사전순
            return (a.title || '').localeCompare(b.title || '');
        },
        dayMaxEventRows: 10, // 최대 10개 행까지 표시
        moreLinkClick: 'popover',
        dayMaxEvents: () => state.eventLimit, // 동적으로 이벤트 제한 적용
        height: 'auto', // 높이 자동 조정
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
            const desc = `
                <div class=\"tooltip-title\">${fullTitle}</div>
                ${headerImg}
                ${tagLine ? `<div class=\"tooltip-tags\">${tagLine}</div>` : ''}
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
