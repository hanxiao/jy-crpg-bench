// Run with: node --test server/test_saved_history_ui.js
// A small DOM is enough to exercise asynchronous history ownership without
// starting a game or changing any saved recording.
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, 'saved-history.js'), 'utf8');
const indexSource = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const base = 'http://127.0.0.1:8084/u/test-user/';

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return {promise, resolve, reject};
}

function response(data, status = 200, blob = {name: 'frame'}) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    blob: async () => blob,
  };
}

function fixture({enabled = true, handle, decode} = {}) {
  const mutations = [], requests = [], images = [], created = [], revoked = [];
  const listeners = new Map();
  class Element {
    constructor(tag = 'div') {
      this.tagName = tag.toUpperCase();
      this.children = [];
      this.dataset = {};
      this.style = {};
      this.attributes = {};
      this.hidden = false;
      this.disabled = false;
      this.className = '';
      this._text = '';
      this.classList = {
        add: (...names) => { this.className = [...new Set(this.className.split(' ').concat(names))].join(' ').trim(); },
        remove: (...names) => { this.className = this.className.split(' ').filter(name => !names.includes(name)).join(' '); },
        contains: name => this.className.split(' ').includes(name),
      };
    }
    set textContent(value) {
      this._text = String(value);
      this.children = [];
      mutations.push({node: this, type: 'text', value: this._text});
    }
    get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
    append(...children) {
      for (const child of children) {
        const node = typeof child === 'string' ? Object.assign(new Element('#text'), {_text: child}) : child;
        node.parentNode = this;
        this.children.push(node);
        mutations.push({node: this, type: 'append', child: node});
      }
    }
    appendChild(child) { this.append(child); return child; }
    replaceChildren(...children) { this.textContent = ''; this.append(...children); }
    setAttribute(name, value) { this.attributes[name] = String(value); }
    getAttribute(name) { return this.attributes[name] ?? null; }
    addEventListener(name, handler) { this['on' + name] = handler; }
    click() { if (!this.disabled) return this.onclick?.({target: this}); }
  }
  const ids = ['historyrows', 'historyinfo', 'historypane', 'timeline',
    'logrows', 'historyfirst', 'historyprev', 'historynext', 'historylatest', 'historypage', 'historypages', 'historyrange', 'historysize',
    'play', 'save', 'recordingfiles'];
  const elements = Object.fromEntries(ids.map(id => [id, Object.assign(new Element(), {id})]));
  class TestURL extends URL {
    static createObjectURL(blob) {
      const url = 'blob:history-test-' + created.length;
      created.push({url, blob});
      return url;
    }
    static revokeObjectURL(url) { revoked.push(url); }
  }
  class TestImage extends Element {
    constructor() { super('img'); images.push(this); }
    decode() { return decode ? decode(this, created) : Promise.resolve(); }
  }
  const sandbox = {
    document: {
      currentScript: {dataset: {historyEnabled: String(enabled)}},
      getElementById: id => {
        assert.ok(elements[id], 'unexpected DOM id: ' + id);
        return elements[id];
      },
      createElement: tag => new Element(tag),
      createTextNode: text => Object.assign(new Element('#text'), {_text: String(text)}),
    },
    location: {href: base},
    URL: TestURL,
    Image: TestImage,
    AbortController,
    DOMException,
    Event,
    setTimeout,
    clearTimeout,
    queueMicrotask,
    console,
    colorOf: () => '#ddd',
    fmt: time => String(time),
    keySpans: text => Object.assign(new Element('span'), {_text: text}),
    updateImageJump: () => {},
    fetch: (url, options = {}) => {
      const call = {url: new URL(url), options, method: options.method || 'GET'};
      requests.push(call);
      return Promise.resolve().then(() => handle(call));
    },
    addEventListener: (name, handler) => {
      if (!listeners.has(name)) listeners.set(name, []);
      listeners.get(name).push(handler);
    },
    dispatchEvent: event => {
      for (const handler of listeners.get(event.type) || []) handler(event);
    },
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  const context = vm.createContext(sandbox);
  vm.runInContext(source, context, {filename: 'saved-history.js'});
  return {
    elements, requests, mutations, images, created, revoked,
    emit: (name, detail = {}) => sandbox.dispatchEvent({type: name, ...detail}),
    clearLog: () => {
      const definition = indexSource.match(/function clearLog\(\) \{[\s\S]*?\n\}/)?.[0];
      assert.ok(definition, 'the page must define clearLog');
      Object.assign(sandbox, {
        rows: elements.logrows,
        awaitingHold: [],
        downAt: new Map(),
        lastId: 5,
        logged: 5,
        logcount: new Element(),
      });
      vm.runInContext(definition + '\nclearLog();', context, {filename: 'index.html#clearLog'});
    },
    rows: () => elements.historyrows.children.filter(node => node.className.split(' ').includes('saved-row')),
  };
}

async function settle() {
  // Flush promise continuations and one event-loop turn, without waiting for
  // production polling timers or relying on a particular number of awaits.
  await new Promise(resolve => setImmediate(resolve));
}

async function until(condition, label, state) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (condition()) return;
    await settle();
  }
  assert.fail(label + '\nrequests: ' + state.requests.map(call => call.method + ' ' + call.url.pathname + call.url.search).join('\n') +
    '\nvisible: ' + state.elements.historyrows.textContent);
}

function isOpen(call) { return call.method === 'GET' && call.url.pathname.endsWith('/api/replay'); }
function isSteps(call) { return call.url.pathname.endsWith('/steps'); }
function isFrame(call) { return call.url.pathname.endsWith('/frame'); }
function tokenOf(call) { return call.url.pathname.split('/api/replay/')[1]?.split('/')[0]; }
function deleted(state) { return state.requests.filter(call => call.method === 'DELETE').map(tokenOf); }
function indices(state) { return state.rows().map(row => Number(row.dataset.step)); }
function step(number, who = 'new-rec') { return {t: number, act: 'KEY', on: 'up', who, ok: true}; }

function standard(call, token = 'new', total = 20, customStep) {
  if (isOpen(call)) return response({token, started: token, steps: total});
  if (call.method === 'DELETE') return response({});
  if (isSteps(call)) {
    const start = Number(call.url.searchParams.get('start'));
    const count = Number(call.url.searchParams.get('count'));
    return response({steps: Array.from({length: Math.min(count, Math.max(0, total - start))},
      (_, offset) => customStep ? customStep(start + offset) : step(start + offset))});
  }
  if (isFrame(call)) return response({}, 200, {name: tokenOf(call)});
  assert.fail('unexpected request ' + call.url);
}

test('explicitly disabled history leaves the unified timeline without replay requests', async () => {
  const state = fixture({enabled: false, handle: () => assert.fail('disabled history requested the API')});
  await settle();
  assert.equal(state.elements.historypane.hidden, false);
  assert.equal(state.elements.logrows.hidden, false);
  for (const id of ['play', 'save', 'recordingfiles']) {
    assert.equal(state.elements[id].hidden, true, id + ' reads endpoints this server does not have');
  }
  state.emit('historyinvalidate');
  await settle();
  assert.equal(state.requests.length, 0);
});

test('an ordinary endpoint 404 remains a visible history error', async () => {
  const state = fixture({handle: () => response({}, 404)});
  await until(() => state.elements.historyrows.textContent.includes('历史'), 'history error did not appear', state);
  assert.equal(state.elements.historypane.hidden, false);
  assert.equal(state.elements.logrows.hidden, true);
  assert.match(state.elements.historyrows.textContent, /不可用|失败|重试/);
  assert.equal(state.elements.historylatest.disabled, false);
});

test('latest, first, next, and previous pages own eight rows and preserve the user-relative API path', async () => {
  let opened = 0;
  const state = fixture({handle: call => isOpen(call)
    ? response({token: 'page-' + (++opened), started: 'same-recording', steps: 20})
    : standard(call, tokenOf(call), 20)});
  async function completed(number, expected) {
    await until(() => deleted(state).length === number && !state.elements.historylatest.disabled,
      'page did not finish', state);
    assert.deepEqual(indices(state), expected);
  }
  await completed(1, [16, 17, 18, 19]);
  assert.equal(state.elements.historyrange.textContent, '17–20 / 20 张');
  state.elements.historyfirst.click();
  await completed(2, [0, 1, 2, 3, 4, 5, 6, 7]);
  assert.equal(state.elements.historyprev.disabled, true);
  state.elements.historynext.click();
  await completed(3, [8, 9, 10, 11, 12, 13, 14, 15]);
  state.elements.historyprev.click();
  await completed(4, [0, 1, 2, 3, 4, 5, 6, 7]);
  state.elements.historylatest.click();
  await completed(5, [16, 17, 18, 19]);
  assert.equal(state.elements.historynext.disabled, true);
  assert.ok(state.requests.every(call => call.url.pathname.startsWith('/u/test-user/api/replay')));
  assert.ok(state.requests.filter(isOpen).every(call => call.url.searchParams.get('recording') === 'current'));
  assert.ok(state.requests.filter(isSteps).every(call => call.url.searchParams.get('count') === '8'));
  assert.equal(new Set(deleted(state)).size, 5);
  assert.equal(state.created.length - new Set(state.revoked).size, 4, 'only the current page retains image URLs');
  state.emit('pagehide', {persisted: false});
  await settle();
  assert.ok(state.created.every(({url}) => state.revoked.includes(url)), 'pagehide releases all rendered image URLs');
});

test('a persisted activity refreshes the same feed and follows only the latest page', async () => {
  let total = 8, opened = 0;
  const state = fixture({handle: call => isOpen(call)
    ? response({token: 'live-' + (++opened), started: 'same-recording', steps: total})
    : standard(call, tokenOf(call), total)});
  await until(() => deleted(state).length === 1 && !state.elements.historylatest.disabled,
    'initial live page did not finish', state);
  total = 9;
  state.emit('activityrecorded');
  await new Promise(resolve => setTimeout(resolve, 300));
  await until(() => deleted(state).length === 2 && indices(state).join(',') === '8',
    'new persisted activity did not refresh the latest page', state);
  assert.equal(state.elements.logrows.hidden, true);
  assert.equal(state.elements.historyrange.textContent, '9–9 / 9 张');
});

test('page size can be changed without losing the current record range', async () => {
  let opened = 0;
  const state = fixture({handle: call => isOpen(call)
    ? response({token: 'size-' + (++opened), started: 'same-recording', steps: 20})
    : standard(call, tokenOf(call), 20)});
  await until(() => deleted(state).length === 1 && !state.elements.historylatest.disabled,
    'initial page did not finish', state);
  state.elements.historysize.value = '16';
  state.elements.historysize.onchange();
  await until(() => deleted(state).length === 2 && !state.elements.historylatest.disabled,
    'page-size change did not finish', state);
  assert.deepEqual(indices(state), [16, 17, 18, 19]);
  assert.equal(state.elements.historypages.textContent, '2');
  assert.equal(state.elements.historyrange.textContent, '17–20 / 20 张');
  assert.equal(state.requests.filter(isSteps).at(-1).url.searchParams.get('count'), '16');
  state.elements.historyfirst.click();
  await until(() => deleted(state).length === 3 && !state.elements.historylatest.disabled,
    'first page after size change did not finish', state);
  assert.deepEqual(indices(state), Array.from({length: 16}, (_, i) => i));
});

test('failed actions visibly retain their failure status and reason', async () => {
  const state = fixture({handle: call => standard(call, 'failed', 1,
    number => ({...step(number), ok: false, detail: 'busy'}))});
  await until(() => deleted(state).length === 1, 'failed-action page did not finish', state);
  assert.match(state.elements.historyrows.textContent, /未执行|失败/);
  assert.match(state.elements.historyrows.textContent, /busy/);
});

test('the real clearLog handler replaces the old saved history with the current recording', async () => {
  let opens = 0;
  const state = fixture({handle: call => {
    if (isOpen(call)) {
      opens++;
      return response({token: opens === 1 ? 'old' : 'fresh', started: opens === 1 ? 'old' : 'fresh', steps: 8});
    }
    return standard(call, tokenOf(call), 8, number => step(number, tokenOf(call) === 'old' ? 'old-rec' : 'new-rec'));
  }});
  await until(() => deleted(state).includes('old') && !state.elements.historylatest.disabled,
    'initial history did not finish', state);
  assert.ok(state.elements.historyrows.textContent.includes('old-rec'));
  state.elements.logrows.textContent = 'old live activity';
  state.clearLog();
  assert.equal(state.elements.logrows.textContent, '');
  assert.ok(!state.elements.historyrows.textContent.includes('old-rec'));
  await until(() => deleted(state).includes('fresh'), 'clearLog did not reload history', state);
  assert.equal(opens, 2);
  assert.ok(state.rows().every(row => row.textContent.includes('new-rec')));
  assert.ok(state.created.filter(item => item.blob.name === 'old').every(item => state.revoked.includes(item.url)));
});

test('leaving the page releases a late opening token without rendering or reopening', async () => {
  const pending = deferred();
  const state = fixture({handle: call => isOpen(call) ? pending.promise : standard(call)});
  await until(() => state.requests.some(isOpen), 'opening did not start', state);
  state.emit('pagehide', {persisted: false});
  state.emit('historyinvalidate');
  pending.resolve(response({token: 'departed', started: 'old', steps: 8}));
  await until(() => deleted(state).includes('departed'), 'late token was not released', state);
  await settle();
  assert.equal(state.requests.filter(isOpen).length, 1);
  assert.equal(state.rows().length, 0);
  assert.equal(state.requests.filter(call => isSteps(call) || isFrame(call)).length, 0);
});

for (const openingStage of ['fetch', 'json']) {
  test('invalidation waits for the old opening ' + openingStage + ' and token DELETE before reopening', async () => {
    const old = deferred(), oldDelete = deferred();
    let opens = 0;
    const state = fixture({handle: call => {
      if (isOpen(call)) {
        opens++;
        if (opens === 1) return openingStage === 'fetch' ? old.promise : {...response({}), json: () => old.promise};
        return standard(call, 'fresh', 8);
      }
      if (call.method === 'DELETE' && tokenOf(call) === 'old') return oldDelete.promise;
      assert.notEqual(tokenOf(call), 'old', 'an invalidated opening must not request old steps or frames');
      return standard(call, 'fresh', 8);
    }});
    await until(() => opens === 1, 'old opening did not start', state);
    if (openingStage === 'fetch') state.clearLog();
    else state.emit('historyinvalidate');
    state.emit('historyinvalidate');
    await settle();
    assert.equal(opens, 1, 'a pending unknown token must not overlap another open');
    const metadata = {token: 'old', started: 'old', steps: 16};
    old.resolve(openingStage === 'fetch' ? response(metadata) : metadata);
    await until(() => deleted(state).includes('old'), 'old token was not released', state);
    await settle();
    assert.equal(opens, 1, 'the replacement must wait for DELETE completion');
    oldDelete.resolve(response({}));
    await until(() => deleted(state).includes('fresh') && state.rows().length === 8,
      'fresh history was not loaded after invalidation', state);
    assert.equal(opens, 2, 'repeated invalidations coalesce into one fresh open');
    assert.deepEqual(deleted(state), ['old', 'fresh']);
    assert.ok(state.rows().every(row => row.textContent.includes('new-rec')));
  });
}

for (const stage of ['steps', 'frame', 'blob', 'decode']) {
  test('stale ' + stage + ' completion cannot restore old rows after invalidation', async () => {
    const pending = deferred();
    let opens = 0, held = false;
    const state = fixture({
      handle: call => {
        if (isOpen(call)) {
          opens++;
          return response({token: opens === 1 ? 'old' : 'fresh', started: opens === 1 ? 'old' : 'fresh', steps: opens === 1 ? 16 : 8});
        }
        if (tokenOf(call) === 'old') {
          if (stage === 'steps' && isSteps(call)) {
            held = true;
            return {...response({}), json: () => pending.promise};
          }
          if (isFrame(call) && !held && (stage === 'frame' || stage === 'blob')) {
            held = true;
            return stage === 'frame' ? pending.promise : {...response({}), blob: () => pending.promise};
          }
          return standard(call, 'old', 16, number => step(number, 'old-rec'));
        }
        return standard(call, 'fresh', 8);
      },
      decode: (image, created) => {
        if (stage === 'decode' && !held && created.find(item => item.url === image.src)?.blob.name === 'old') {
          held = true;
          return pending.promise;
        }
        return Promise.resolve();
      },
    });
    await until(() => held, 'the deferred ' + stage + ' stage was not reached', state);
    state.emit('historyinvalidate');
    const invalidatedAt = state.mutations.length;
    await settle();
    assert.ok(!state.elements.historyrows.textContent.includes('old-rec'), 'invalidation immediately clears the old page');
    if (stage === 'steps') pending.resolve({steps: Array.from({length: 8}, (_, offset) => step(8 + offset, 'old-rec'))});
    else if (stage === 'frame') pending.resolve(response({}, 200, {name: 'old'}));
    else if (stage === 'blob') pending.resolve({name: 'old'});
    else pending.resolve();
    await until(() => deleted(state).includes('fresh') && !state.elements.historylatest.disabled,
      'fresh history did not finish', state);
    assert.deepEqual(indices(state), [0, 1, 2, 3, 4, 5, 6, 7]);
    assert.ok(state.rows().every(row => row.textContent.includes('new-rec')));
    assert.equal(state.elements.historyrange.textContent, '1–8 / 8 张');
    const staleAppends = state.mutations.slice(invalidatedAt).filter(change =>
      change.type === 'append' && change.node === state.elements.historyrows && change.child.textContent.includes('old-rec'));
    assert.equal(staleAppends.length, 0, 'a stale step list must never be appended after invalidation');
    assert.deepEqual(deleted(state), ['old', 'fresh']);
    assert.ok(state.created.filter(item => item.blob.name === 'old').every(item => state.revoked.includes(item.url)),
      'old blob URLs must be revoked, including those completing after invalidation');
    state.emit('pagehide', {persisted: false});
    await settle();
    assert.ok(state.created.every(item => state.revoked.includes(item.url)));
  });
}

for (const stage of ['frame', 'blob', 'decode']) {
  test('a late old ' + stage + ' cannot change a replacement page that has already rendered', async () => {
    const pending = deferred();
    let opens = 0, oldFrames = 0, held = false, abortable = false;
    const state = fixture({
      handle: call => {
        if (isOpen(call)) {
          opens++;
          return response({token: opens === 1 ? 'old' : 'fresh', started: opens === 1 ? 'old' : 'fresh', steps: 8});
        }
        if (tokenOf(call) === 'old' && isFrame(call)) {
          oldFrames++;
          if (oldFrames === 1) {
            if (stage === 'frame') { held = true; return pending.promise; }
            if (stage === 'blob') { held = true; return {...response({}), blob: () => pending.promise}; }
            return response({}, 200, {name: 'old'});
          }
          // A browser can reject one request on abort while its sibling is
          // already decoding. That releases the old run before the sibling
          // completes, so this checks ownership after a fresh page is visible.
          abortable = true;
          return new Promise((resolve, reject) => {
            call.options.signal.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')), {once: true});
          });
        }
        return standard(call, tokenOf(call), 8, number => step(number, tokenOf(call) === 'old' ? 'old-rec' : 'new-rec'));
      },
      decode: (image, created) => {
        if (stage === 'decode' && created.find(item => item.url === image.src)?.blob.name === 'old') {
          held = true;
          return pending.promise;
        }
        return Promise.resolve();
      },
    });
    await until(() => held && abortable, 'old image requests did not reach the intended race', state);
    state.emit('historyinvalidate');
    await until(() => deleted(state).includes('fresh') && !state.elements.historylatest.disabled,
      'the aborted sibling did not permit a fresh page', state);
    const rows = [...state.rows()];
    const text = state.elements.historyrows.textContent;
    const range = state.elements.historyrange.textContent;
    if (stage === 'frame') pending.resolve(response({}, 200, {name: 'old'}));
    else if (stage === 'blob') pending.resolve({name: 'old'});
    else pending.resolve();
    await settle();
    assert.deepEqual(state.rows(), rows, 'late completion must not replace the current rows');
    assert.equal(state.elements.historyrows.textContent, text);
    assert.equal(state.elements.historyrange.textContent, range);
    assert.equal(state.elements.historylatest.disabled, false);
    assert.deepEqual(deleted(state), ['old', 'fresh']);
    assert.ok(state.created.filter(item => item.blob.name === 'old').every(item => state.revoked.includes(item.url)));
    state.emit('pagehide', {persisted: false});
    assert.ok(state.created.every(item => state.revoked.includes(item.url)));
  });
}
