/* MXA MCQ: local-first answer persistence, batched idempotent server saves.
 * The server remains authoritative for exam duration, accepted answers and marking.
 * Do not store correct answers or student credentials here.
 */
(() => {
  'use strict';
  const form = document.getElementById('examForm');
  const status = document.getElementById('mxaSaveStatus');
  const configNode = document.getElementById('mxa-mcq-config');
  const answersNode = document.getElementById('mxa-server-answers');
  if (!form || !status || !configNode || !answersNode) return;
  const cfg = JSON.parse(configNode.textContent);
  const serverAnswers = JSON.parse(answersNode.textContent);
  const storageKey = `mxa_mcq_v2_${cfg.user}_${cfg.exam}_${cfg.result}`;
  const csrf = form.querySelector('input[name=csrfmiddlewaretoken]').value;
  const radios = [...form.querySelectorAll('input[type="radio"].exam-input')];
  const answers = {};
  const confirmed = {};
  let revisionCounter = 0;
  let pendingSubmit = false;
  let sending = false;
  let submitting = false;
  let saveTimer = null;
  let localAvailable = true;
  let attemptClosed = false;
  let answerConflict = false;
  const valid = {};
  for (const radio of radios) {
    const qid = radio.name.replace('question_', '');
    (valid[qid] ??= new Set()).add(String(radio.value));
  }

  function report(message, level='warning') {
    status.className = `alert alert-${level}`;
    status.textContent = message;
  }
  function persist() {
    try {
      localStorage.setItem(storageKey, JSON.stringify({answers, revisionCounter, pendingSubmit}));
      localAvailable = true;
    } catch (e) {
      localAvailable = false;
      report('Browser storage unavailable. Keep this page open and stay online to save answers.', 'danger');
    }
  }
  for (const entry of serverAnswers) {
    const qid = String(entry.question_id);
    const cid = String(entry.choice_id);
    if (valid[qid]?.has(cid)) {
      const revision = Number(entry.revision) || 0;
      answers[qid] = {choice_id: cid, revision};
      confirmed[qid] = {choice_id: cid, revision};
      revisionCounter = Math.max(revisionCounter, revision);
    }
  }
  try {
    const local = JSON.parse(localStorage.getItem(storageKey) || 'null');
    if (local?.answers) {
      revisionCounter = Math.max(revisionCounter, Number(local.revisionCounter) || 0);
      for (const [qid, item] of Object.entries(local.answers)) {
        if (!valid[qid]?.has(String(item.choice_id))) continue;
        const revision = Number(item.revision) || 0;
        if (!answers[qid] || revision > answers[qid].revision) {
          answers[qid] = {choice_id: String(item.choice_id), revision};
        }
      }
      pendingSubmit = Boolean(local.pendingSubmit);
    }
  } catch(e) {
    report('Could not read locally saved answers. Server-saved answers are restored.', 'warning');
  }
  for (const radio of radios) {
    const qid = radio.name.replace('question_', '');
    if (answers[qid]?.choice_id === String(radio.value)) radio.checked = true;
  }
  function setRevisionInputs() {
    form.querySelectorAll('input[data-mxa-revision]').forEach(el => el.remove());
    for (const [qid, a] of Object.entries(answers)) {
      const field = document.createElement('input');
      field.type='hidden'; field.dataset.mxaRevision='1';
      field.name=`revision_${qid}`; field.value=String(a.revision);
      form.appendChild(field);
    }
  }
  function pending() {
    return Object.entries(answers).filter(([qid,a]) =>
      !confirmed[qid] || confirmed[qid].revision < a.revision || confirmed[qid].choice_id !== a.choice_id
    ).map(([qid,a]) => ({question_id:Number(qid), choice_id:Number(a.choice_id),revision:a.revision}));
  }
  function updateStatus() {
    if (answerConflict) return report('Answer conflict with another tab/device. Reload and verify before submitting.', 'danger');
    if (submitting) return report('Submitting answers to MXA server...', 'info');
    if (attemptClosed) return report('Exam submitted or time expired. Open exam list to view status.', 'warning');
    const n = pending().length;
    if (n === 0) return report('All selected answers saved on MXA server.', 'success');
    if (!navigator.onLine) return report(`${n} answer(s) stored on this device, awaiting internet connection. Do not clear browser data.`, 'warning');
    report(`${n} answer(s) saved on device, synchronizing with MXA server...`, 'warning');
  }
  const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
  function scheduleSave(delay=2500) {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(sync, delay);
  }
  for (const radio of radios) {
    radio.addEventListener('change', () => {
      if (!radio.checked || submitting) return;
      const qid = radio.name.replace('question_', '');
      const previous = answers[qid];
      if (previous?.choice_id === String(radio.value)) return;
      revisionCounter++;
      answers[qid] = {choice_id:String(radio.value), revision:revisionCounter};
      persist(); setRevisionInputs(); updateStatus(); scheduleSave();
    });
  }

  async function sync() {
    if (sending || submitting || attemptClosed || !navigator.onLine) return;
    const batch = pending();
    if (!batch.length) return;
    sending = true;
    const controller = new AbortController();
    const abort = setTimeout(() => controller.abort(), 9000);
    try {
      const response = await fetch(cfg.autosave, {
        method:'POST', credentials:'same-origin',
        headers:{'Content-Type':'application/json', 'X-CSRFToken':csrf},
        body: JSON.stringify({answers: batch}), signal:controller.signal,
      });
      if (response.status === 409) {
        attemptClosed = true;
        report('Exam submitted or time expired. Reopen it from your exam list to see its status.', 'danger');
        return;
      }
      if (!response.ok) throw Error('Server not available');
      const payload = await response.json();
      if (!payload.saved) throw Error('Save not confirmed');
      // Only mark server-acknowledged choices as saved. An older browser tab
      // must not falsely claim that its answer overwrote a newer revision.
      for (const entry of payload.confirmed || []) {
        const qid = String(entry.question_id);
        const revision = Number(entry.client_revision) || 0;
        confirmed[qid] = {
          choice_id: String(entry.selected_choice_id_snapshot), revision,
        };
        // A different device may have a newer saved answer; alert rather
        // than automatically overwriting it with this device's old state.
        if (answers[qid] && answers[qid].revision < revision &&
            answers[qid].choice_id !== confirmed[qid].choice_id) {
          attemptClosed = true;
          answerConflict = true;
          report('Answer conflict: another tab or device saved newer answers. Reload this page and verify before submitting.', 'danger');
        }
      }
    } catch(e) {
      report('Network problem: selected answers remain on this device and will retry.', 'warning');
    } finally {
      clearTimeout(abort);
      sending=false;
      updateStatus();
      if (!attemptClosed && pending().length && navigator.onLine) scheduleSave(5000);
    }
  }

  async function submitForm(expired=false) {
    if (submitting) return;
    if (answerConflict) { updateStatus(); return; }
    if (!expired && !confirm('Submit this examination? You cannot change answers after submission.')) return;
    pendingSubmit=true; persist(); setRevisionInputs();
    if (!navigator.onLine) {
      report(expired ? 'Time has ended. Internet is required to transmit unsaved answers. Reconnect immediately; late answers may not be accepted.' :
        'You are offline. Your answers remain on this device. Reconnect to submit.', 'danger');
      return;
    }
    submitting=true; updateStatus();
    const controller = new AbortController();
    const abort = setTimeout(() => controller.abort(), 20000);
    try {
      // The full answer set accompanies the final POST; no dependency on autosave completing first.
      const response = await fetch(form.action, {
        method:'POST', credentials:'same-origin', body:new FormData(form),
        signal: controller.signal,
      });
      if (response.ok && response.url.includes('/result/')) {
        localStorage.removeItem(storageKey);
        window.location.assign(response.url);
        return;
      }
      throw Error('Final submission not confirmed');
    } catch (e) {
      submitting=false;
      report('Submission not confirmed. Your answers are still on this device. Reconnect and retry; exam deadlines are enforced by the server.', 'danger');
      persist();
    } finally {
      clearTimeout(abort);
    }
  }
  form.addEventListener('submit', e => {
    e.preventDefault();
    submitForm(false);
  });
  window.mxaTimeExpired = () => submitForm(true);
  window.addEventListener('online', () => {
    updateStatus(); scheduleSave(0);
    if (pendingSubmit) setTimeout(() => submitForm(true), 1500);
  });
  window.addEventListener('offline', updateStatus);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) scheduleSave(0);
  });
  // No constant polling: only changes trigger database writes.
  window.setInterval(() => {
    if (pending().length) sync();
  }, 12000);
  persist(); setRevisionInputs(); updateStatus();
  if (pending().length) scheduleSave(700);
  if (pendingSubmit && navigator.onLine) setTimeout(() => submitForm(true), 1300);
})();
