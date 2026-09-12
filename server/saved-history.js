// Complete disk-backed activity history. When the server exposes saved
// history, this is the one rendered feed: the websocket is only a change
// signal and the page owns eight disk-backed records at a time.
(() => {
  const PAGE_SIZES = [8, 16, 32, 64];
  const get = id => document.getElementById(id);
  const endpoint = path => new URL(path, location.href);
  const enabled = document.currentScript?.dataset.historyEnabled !== 'false';
  globalThis.__savedHistoryEnabled = enabled;
  let pageSize = 8, start = 0, total = 0, origin = null, busy = false, urls = [];
  let generation = 0, active = null, reload = false, reloadStart = null, disposed = false;
  let refreshTimer = null;
  const box = get('historyrows'), info = get('historyinfo'), sizeControl = get('historysize');
  sizeControl.value = String(pageSize);
  function selectHistory() {
    get('historypane').hidden = false;
    // The live websocket cache is a fallback for benchmark pages where saved
    // history is disabled. Rendering it beside this feed would duplicate the
    // same actions and make pagination look as if only half the timeline moved.
    get('logrows').hidden = enabled;
    if (typeof updateImageJump === 'function') updateImageJump();
  }
  function buttons() {
    const pages = total ? Math.ceil(total / pageSize) : 0;
    const page = total ? Math.floor(start / pageSize) + 1 : 0;
    get('historypage').value = page || '';
    get('historypages').textContent = pages || '—';
    get('historypage').disabled = busy || !pages;
    sizeControl.disabled = busy || !pages;
    get('historyfirst').disabled = get('historyprev').disabled = busy || start <= 0;
    get('historynext').disabled = busy || start + pageSize >= total;
    get('historylatest').disabled = busy;
  }
  function releaseImages() { urls.forEach(url => URL.revokeObjectURL(url)); urls = []; }
  async function request(path, signal) {
    const response = await fetch(endpoint(path), {cache:'no-store', signal});
    if (!response.ok) throw Error(response.status === 404 ? '历史截图暂不可用，请重试。' : '读取历史失败，请重试。');
    return {response, data:await response.json()};
  }
  async function load(requested = null) {
    if (active || disposed || !enabled) return;
    busy = true; buttons();
    const run = {generation, controller:new AbortController()};
    active = run;
    const signal = run.controller.signal;
    const current = () => active === run && generation === run.generation && !signal.aborted && !disposed;
    const check = () => { if (!current()) throw new DOMException('History changed', 'AbortError'); };
    let token = null;
    info.textContent = ' · 读取中';
    try {
      // Keep the opening response even after invalidation: it owns the token
      // we must close before opening the replacement snapshot. Later reads
      // can be aborted because their token is already known.
      let result = await request('api/replay?recording=current');
      token = result.data.token;
      check();
      if (!token) throw Error('历史读取未能开始，请重试。');
      while (result.response.status === 202 || result.data.indexing) {
        const progress = result.data.total ? Math.min(100, Math.floor(100 * result.data.scanned / result.data.total)) : null;
        info.textContent = ' · 正在读取磁盘历史' + (progress !== null ? ` ${progress}%` : '');
        await new Promise(resolve => setTimeout(resolve, 600));
        check();
        result = await request(`api/replay/${encodeURIComponent(token)}`, signal);
        check();
      }
      const meta = result.data;
      if (!Number.isSafeInteger(meta.steps) || meta.steps < 0) throw Error('历史记录数量无法识别。');
      if (origin !== null && origin !== meta.started) requested = null;
      origin = meta.started; total = meta.steps;
      const pages = total ? Math.ceil(total / pageSize) : 0;
      const requestedPage = requested === null || requested === undefined
        ? pages
        : Math.floor(Math.max(0, requested) / pageSize) + 1;
      const pageNumber = pages ? Math.max(1, Math.min(pages, requestedPage)) : 0;
      // Every page is aligned to the selected page-size boundary. The last
      // page may be shorter when the total is not an exact multiple.
      start = pageNumber ? (pageNumber - 1) * pageSize : 0;
      const path = `api/replay/${encodeURIComponent(token)}/steps?start=${start}&count=${pageSize}`;
      const {data:page} = await request(path, signal);
      check();
      if (!Array.isArray(page.steps)) throw Error('历史截图列表无法读取。');
      releaseImages(); box.textContent = '';
      info.textContent = ' · ' + total.toLocaleString();
      get('historyrange').textContent = total ? `${start+1}–${start+page.steps.length} / ${total} 张` : '0 张';
      const imageRows = [];
      // The page is already chronological. Keep older actions above newer ones
      // so the timeline reads from top to bottom.
      for (let offset = 0; offset < page.steps.length; offset++) {
        const step = page.steps[offset], index = start + offset;
        const row = document.createElement('article'); row.className = 'saved-row'; row.dataset.step = index;
        const details = document.createElement('div'); details.className = 'saved-meta';
        const who = document.createElement('span'); who.className = 'saved-who'; who.textContent = step.who || 'agent'; who.title = who.textContent; who.style.color = colorOf(who.textContent);
        const when = document.createElement('span'); when.textContent = `#${index+1} · ${fmt(step.t)}`;
        details.append(who, when);
        const action = document.createElement('div'); action.className = 'saved-action';
        const verb = document.createElement('span'); verb.className = 'verb';
        verb.textContent = ({GET:'截图',KEY:'按键',KEYS:'按键',WAIT:'等待'})[step.act] || step.act;
        action.append(verb);
        if (step.act === 'KEY' || step.act === 'KEYS') action.append(keySpans(step.on || ''));
        else if (step.act !== 'GET') action.append(document.createTextNode(step.on || ''));
        row.append(details, action);
        if (step.ok === false || step.detail) {
          const result = document.createElement('div');
          result.className = step.ok === false ? 'saved-result' : 'saved-detail';
          result.textContent = (step.ok === false ? '未执行 / 失败' : '')
            + (step.detail ? (step.ok === false ? ' · ' : '') + step.detail : '');
          row.append(result);
        }
        box.append(row); imageRows.push({row, index});
      }
      if (!page.steps.length) { const text = document.createElement('div'); text.className = 'history-empty'; text.textContent = '暂无已保存的历史截图'; box.append(text); }
      for (let i = 0; i < imageRows.length; i += 2) {
        await Promise.all(imageRows.slice(i,i+2).map(async ({row,index}) => {
          try {
            const response = await fetch(endpoint(`api/replay/${encodeURIComponent(token)}/frame?step=${index}`), {cache:'no-store',signal});
            check();
            if (!response.ok) throw Error();
            const blob = await response.blob();
            check();
            const url = URL.createObjectURL(blob); urls.push(url);
            const link = document.createElement('a'); link.className = 'saved-shot'; link.href = url; link.target = '_blank'; link.rel = 'noopener'; link.title = '打开完整画面 · 从磁盘录像按步骤还原';
            const image = new Image(); image.src = url; image.alt = `历史截图 ${index+1}`; image.dataset.step = index;
            link.append(image); row.append(link); await image.decode();
            check();
          } catch(error) {
            if (!current()) throw error;
            const text = document.createElement('div'); text.className = 'history-empty'; text.textContent = '截图暂时无法加载，请重试'; row.append(text);
          }
        }));
      }
      check();
      const timeline = get('timeline');
      if (timeline) timeline.scrollTop = 0;
    } catch(error) {
      if (current()) { releaseImages(); info.textContent=''; box.textContent=''; const text=document.createElement('div'); text.className='history-empty'; text.textContent=error.message; box.append(text); }
    } finally {
      if (token) await fetch(endpoint(`api/replay/${encodeURIComponent(token)}`), {method:'DELETE',keepalive:true}).catch(()=>{});
      active = null; busy = false;
      if (reload && !disposed) { const requested = reloadStart; reload = false; reloadStart = null; load(requested); }
      else buttons();
    }
  }
  function invalidate() {
    if (!enabled || disposed) return;
    const requested = origin !== null ? start : null;
    generation++;
    active?.controller.abort();
    releaseImages(); box.textContent = '';
    start = total = 0;
    info.textContent = ' · 读取中'; get('historyrange').textContent = '';
    if (active) { reload = true; reloadStart = requested; }
    else load(requested);
  }
  function scheduleRefresh() {
    if (!enabled || disposed || refreshTimer !== null) return;
    refreshTimer = setTimeout(() => {
      refreshTimer = null;
      // Keep an old page stable while it is being inspected. If the user was
      // on the last page, follow the new last page so live activity becomes
      // part of the same paginated feed immediately.
      const requested = total && start + pageSize < total ? start : null;
      if (active) {
        reload = true;
        reloadStart = requested;
      } else {
        load(requested);
      }
    }, 250);
  }
  get('historyfirst').onclick = () => load(0);
  get('historyprev').onclick = () => load(Math.max(0,start-pageSize));
  get('historynext').onclick = () => load(start+pageSize);
  get('historylatest').onclick = () => load();
  const jump = () => {
    const pages = total ? Math.ceil(total / pageSize) : 0;
    const page = Number.parseInt(get('historypage').value, 10);
    if (pages && Number.isInteger(page)) load(Math.max(0, Math.min(pages, page) - 1) * pageSize);
  };
  get('historypage').onchange = jump;
  get('historypage').onkeydown = event => { if (event.key === 'Enter') { event.preventDefault(); jump(); } };
  sizeControl.onchange = () => {
    const next = Number.parseInt(sizeControl.value, 10);
    if (!PAGE_SIZES.includes(next) || next === pageSize) {
      sizeControl.value = String(pageSize);
      return;
    }
    pageSize = next;
    load(start);
  };
  addEventListener('historyinvalidate', invalidate);
  addEventListener('activityrecorded', scheduleRefresh);
  addEventListener('pagehide', event => {
    if (!event.persisted) {
      disposed = true; reload = false; generation++;
      if (refreshTimer !== null) { clearTimeout(refreshTimer); refreshTimer = null; }
      active?.controller.abort(); releaseImages();
    }
  });
  // Playback, export and the recordings menu read the same endpoints the
  // history pane does, so where the server has none they are hidden too.
  if (!enabled) for (const id of ['play', 'save', 'recordingfiles']) get(id).hidden = true;
  selectHistory();
  if (enabled) load();
})();
