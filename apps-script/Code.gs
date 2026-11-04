/**
 * 공부 기록장 서버 (Google Apps Script)
 *
 * 하는 일
 *  1. 웹앱 주소를 열면 GitHub의 app/index.html(화면)을 불러와 보여 준다. 화면을 고쳐도 재배포가 필요 없다.
 *  2. 기록은 이 구글 시트의 'kv' 탭에 저장한다. (키 | JSON | 저장 시각)
 *  3. 저장이 있으면 잠시 기다렸다가(여러 번 저장은 묶어서) GitHub Actions를 한 번 실행시킨다.
 *  4. 주소 뒤에 export=1 을 붙이면 GitHub Actions가 가져갈 수 있는 내보내기(JSON)를 준다.
 *
 * 비밀 값은 프로젝트 설정 > 스크립트 속성에 있다. (코드에는 적지 않는다)
 *  TOKEN     주소에 붙는 비밀 값(setup이 만든다)
 *  GH_TOKEN  GitHub 토큰(직접 넣는다. 이 저장소의 Actions 쓰기 권한만 줄 것)
 *  SHEET_ID  기록을 저장하는 시트(setup이 넣는다)
 */

const REPO = {owner: 'bfree0225study', repo: 'study-wall', branch: 'main', workflow: 'wall.yml'};
const SHEET_NAME = 'kv';
const QUIET_MS = 60 * 1000;   // 마지막 저장 뒤 이만큼 조용하면 GitHub에 알린다
const KEY_RE = /^(days\/\d{4}-\d{2}-\d{2}|plan\/(exams|labels|tasks|timetable|wall))$/;

const props_ = () => PropertiesService.getScriptProperties();

/* ---------- 비밀 값 확인 ---------- */

function checkKey_(k) {
  const t = props_().getProperty('TOKEN');
  if (!t || typeof k !== 'string' || k.length !== t.length) return false;
  let diff = 0;
  for (let i = 0; i < t.length; i++) diff |= t.charCodeAt(i) ^ k.charCodeAt(i);
  return diff === 0;
}
function assertKey_(k) { if (!checkKey_(k)) throw new Error('주소가 맞지 않습니다.'); }

/* ---------- 웹앱 ---------- */

function doGet(e) {
  const p = (e && e.parameter) || {};
  if (!checkKey_(p.k)) return ContentService.createTextOutput('주소가 맞지 않습니다.');
  if (p.export) {
    return ContentService.createTextOutput(JSON.stringify(exportAll_())).setMimeType(ContentService.MimeType.JSON);
  }
  const html = '<script>window.__K=' + JSON.stringify(p.k) + ';</script>' + pageHtml_();
  return HtmlService.createHtmlOutput(html)
    .setTitle('공부 기록장')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// 화면 코드는 GitHub에서 불러온다. 잠깐(1분) 기억해 두고, GitHub가 안 될 때는 마지막으로 성공한 것을 쓴다.
function pageHtml_() {
  const cache = CacheService.getScriptCache();
  const fresh = cache.get('page');
  if (fresh) return fresh;
  const url = 'https://raw.githubusercontent.com/' + REPO.owner + '/' + REPO.repo + '/' + REPO.branch + '/app/index.html';
  try {
    const res = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    if (res.getResponseCode() === 200) {
      const html = res.getContentText();
      try { cache.put('page', html, 60); cache.put('page_last', html, 21600); } catch (err) { /* 너무 크면 건너뜀 */ }
      return html;
    }
  } catch (err) { /* 아래에서 처리 */ }
  return cache.get('page_last') || '<p>화면을 불러오지 못했습니다. 잠시 뒤 새로고침해 주세요.</p>';
}

/* ---------- 시트 저장 ---------- */

function sheet_() {
  const id = props_().getProperty('SHEET_ID');
  const ss = id ? SpreadsheetApp.openById(id) : SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(['key', 'json', 'updated']);
  }
  return sh;
}

function readAll_() {
  const sh = sheet_(), n = sh.getLastRow(), out = {};
  if (n < 2) return out;
  sh.getRange(2, 1, n - 1, 2).getValues().forEach(([key, json]) => {
    if (!key || !json) return;
    try { out[key] = JSON.parse(json); } catch (err) { /* 깨진 줄은 건너뜀 */ }
  });
  return out;
}

// 화면이 부르는 함수: 전체 불러오기
function load(k) {
  assertKey_(k);
  const all = readAll_(), days = [], plan = {};
  Object.keys(all).forEach(key => {
    if (key.indexOf('days/') === 0) days.push(all[key]);
    else if (key.indexOf('plan/') === 0) plan[key.slice(5)] = all[key];
  });
  return {days: days, plan: plan};
}

// GitHub Actions가 가져가는 모양: {days: {날짜: 문서}, plan: {이름: 문서}}
function exportAll_() {
  const all = readAll_(), days = {}, plan = {};
  Object.keys(all).forEach(key => {
    if (key.indexOf('days/') === 0) days[key.slice(5)] = all[key];
    else if (key.indexOf('plan/') === 0) plan[key.slice(5)] = all[key];
  });
  return {days: days, plan: plan};
}

// 화면이 부르는 함수: 저장. ops = [{key: 'days/2026-11-05', doc: {...}}]
function save(k, ops) {
  assertKey_(k);
  if (!Array.isArray(ops) || !ops.length || ops.length > 50) throw new Error('저장 요청이 올바르지 않습니다.');
  ops.forEach(op => {
    if (!op || !KEY_RE.test(op.key) || !op.doc || typeof op.doc !== 'object' || JSON.stringify(op.doc).length > 40000) {
      throw new Error('저장 항목이 올바르지 않습니다.');
    }
  });
  writeOps_(ops);
  return true;
}

function writeOps_(ops) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const sh = sheet_(), n = sh.getLastRow(), now = new Date().toISOString();
    const keys = n >= 2 ? sh.getRange(2, 1, n - 1, 1).getValues().map(r => r[0]) : [];
    ops.forEach(op => {
      const json = JSON.stringify(op.doc), i = keys.indexOf(op.key);
      if (i >= 0) {
        sh.getRange(i + 2, 1, 1, 3).setValues([[op.key, json, now]]);
      } else {
        sh.appendRow([op.key, json, now]);
        keys.push(op.key);
      }
    });
    props_().setProperty('DIRTY', String(Date.now()));
  } finally {
    lock.releaseLock();
  }
}

/* ---------- GitHub Actions 실행 요청 (저장을 묶어서 한 번) ---------- */

// 1분마다 도는 트리거. 저장이 있었고 1분 넘게 조용하면 GitHub에 알린다.
function flush() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) return;
  try {
    const p = props_(), dirty = p.getProperty('DIRTY');
    if (!dirty || Date.now() - Number(dirty) < QUIET_MS) return;
    const result = dispatch_();
    if (result.ok) p.deleteProperty('DIRTY');
    else p.setProperty('DIRTY', String(Date.now() + 4 * 60 * 1000));   // 실패하면 5분쯤 뒤에 다시
  } finally {
    lock.releaseLock();
  }
}

function dispatch_() {
  const p = props_(), token = p.getProperty('GH_TOKEN');
  if (!token) { p.setProperty('LAST_ERROR', 'GH_TOKEN이 없습니다.'); return {ok: false}; }
  const url = 'https://api.github.com/repos/' + REPO.owner + '/' + REPO.repo + '/actions/workflows/' + REPO.workflow + '/dispatches';
  try {
    const res = UrlFetchApp.fetch(url, {
      method: 'post',
      contentType: 'application/json',
      headers: {Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'},
      payload: JSON.stringify({ref: REPO.branch}),
      muteHttpExceptions: true
    });
    const code = res.getResponseCode();
    if (code === 204) { p.deleteProperty('LAST_ERROR'); return {ok: true}; }
    p.setProperty('LAST_ERROR', code + ' ' + res.getContentText().slice(0, 300));
    return {ok: false, code: code};
  } catch (err) {
    p.setProperty('LAST_ERROR', String(err).slice(0, 300));
    return {ok: false};
  }
}

/* ---------- 처음 한 번 실행하는 함수들 ---------- */

// 1) setup: 비밀 값 만들기, 시트 연결, 1분 트리거 만들기
function setup() {
  const p = props_();
  p.setProperty('SHEET_ID', SpreadsheetApp.getActiveSpreadsheet().getId());
  if (!p.getProperty('TOKEN')) p.setProperty('TOKEN', Utilities.getUuid().replace(/-/g, ''));
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'flush')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('flush').timeBased().everyMinutes(1).create();
  sheet_();
  Logger.log('준비가 끝났습니다. 다음은 웹앱으로 배포한 뒤 showUrl을 실행하세요.');
}

// 2) 배포 뒤 실행: 기록장 주소와 GitHub 비밀값에 넣을 값을 보여 준다
function showUrl() {
  const base = ScriptApp.getService().getUrl(), token = props_().getProperty('TOKEN');
  Logger.log('기록장 주소(북마크): ' + base + '?k=' + token);
  Logger.log('GitHub 비밀값 APPS_SCRIPT_URL: ' + base);
  Logger.log('GitHub 비밀값 APPS_SCRIPT_TOKEN: ' + token);
}

// 3) GitHub 토큰을 넣은 뒤 실행: 지금 바로 GitHub에 이미지 만들기를 요청해 본다
function runNow() {
  const r = dispatch_();
  Logger.log(r.ok ? 'GitHub에 요청했습니다. 1분쯤 뒤 저장소의 Actions 탭에서 확인하세요.'
                  : '실패: ' + (props_().getProperty('LAST_ERROR') || '알 수 없음'));
}

// 확인용: 지금 상태를 보여 준다
function status() {
  const p = props_();
  Logger.log('저장된 항목 수: ' + Object.keys(readAll_()).length);
  Logger.log('GitHub에 알릴 저장 대기: ' + (p.getProperty('DIRTY') ? '있음' : '없음'));
  Logger.log('GH_TOKEN: ' + (p.getProperty('GH_TOKEN') ? '들어 있음' : '없음'));
  Logger.log('마지막 오류: ' + (p.getProperty('LAST_ERROR') || '없음'));
}
