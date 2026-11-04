const API = '/api', $ = id => document.getElementById(id);
let token = null, xp = 0, hearts = 3, busy = false, scene;
let gameState = {defeated: {}, bosses: [], final_defeated: false};
const ZONES = {
  redes: {name: '🌐 Ciudad de Redes', color: 0x3b6fd1, mon: 'Sniffer', boss: 'Interceptor MITM', attack: 'Man-in-the-Middle', x: 0, y: 0},
  vulnerabilidades: {name: '🔐 Fortaleza de Seguridad', color: 0x8a4fd1, mon: 'Phisher', boss: 'Phisher Supremo', attack: 'Phishing', x: 800, y: 0},
  bd: {name: '🗄️ Cueva de Bases de Datos', color: 0x2f9e6e, mon: 'Inyector', boss: 'Inyector SQL', attack: 'SQL Injection', x: 0, y: 600},
  programacion: {name: '💻 Bosque de Programación', color: 0xd18a2f, mon: 'Bot', boss: 'Señor DDoS', attack: 'DDoS', x: 800, y: 600},
};
const level = () => Math.floor(xp / 100) + 1;

async function api(path, opts = {}) {
  const r = await fetch(API + path, {...opts, headers: {'Content-Type': 'application/json', ...(token ? {Authorization: 'Bearer ' + token} : {})}});
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : 'Revisa tus datos: usuario de 3-20 letras/números y contraseña de 8 o más caracteres.');
  return d;
}
let assessment = null;
async function openAssessment() {
  $('assessmentPanel').classList.remove('hidden');
  try {
    const summary = await api('/game/assessment/summary');
    $('assessmentSummary').textContent = Object.entries(summary).map(([topic, values]) => {
      const pre = values.pre, post = values.post;
      return `${topic}: ${pre ? `pre ${pre.percent}%` : 'sin pre-test'} · ${post ? `post ${post.percent}%` : 'sin post-test'}${pre && post ? ` · mejora ${post.percent - pre.percent} puntos` : ''}`;
    }).join(' | ') || 'Aún no hay evaluaciones terminadas.';
  } catch (e) { $('assessmentSummary').textContent = e.message; }
}
async function startAssessment(kind) {
  try {
    assessment = await api('/game/assessment/start', {
      method: 'POST',
      body: JSON.stringify({kind, topic: $('assessmentTopic').value}),
    });
    renderAssessmentQuestion();
  } catch (e) { $('assessmentStatus').textContent = e.message; }
}
function renderAssessmentQuestion() {
  const index = Object.keys(assessment.answers || {}).length;
  const question = assessment.questions[index];
  if (!question) {
    $('assessmentStatus').textContent = `✅ Evaluación terminada: ${assessment.score}/${assessment.total}.`;
    $('assessmentQuestions').textContent = '';
    openAssessment();
    return;
  }
  $('assessmentStatus').textContent = `${assessment.kind === 'pre' ? 'Pre-test' : 'Post-test'} · Pregunta ${index + 1}/${assessment.total}`;
  const container = $('assessmentQuestions');
  container.textContent = '';
  const text = document.createElement('p');
  text.textContent = question.text;
  container.appendChild(text);
  question.options.forEach((option, optionIndex) => {
    const button = document.createElement('button');
    button.className = 'opt';
    button.textContent = option;
    button.onclick = () => answerAssessment(question.id, optionIndex);
    container.appendChild(button);
  });
}
async function answerAssessment(questionId, optionIndex) {
  const buttons = [...$('assessmentQuestions').querySelectorAll('button')];
  buttons.forEach(button => { button.disabled = true; });
  try {
    const result = await api('/game/assessment/answer', {
      method: 'POST',
      body: JSON.stringify({kind: assessment.kind, topic: assessment.topic, question_id: questionId, option_index: optionIndex}),
    });
    assessment.answers = {...(assessment.answers || {}), [questionId]: true};
    assessment.score = result.score;
    if (result.completed) {
      assessment.completed = true;
      renderAssessmentQuestion();
      toast(`📈 Resultado: ${result.score}/${result.total}`);
    } else {
      renderAssessmentQuestion();
    }
  } catch (e) {
    $('assessmentStatus').textContent = e.message;
    buttons.forEach(button => { button.disabled = false; });
  }
}
function toast(t) { const e = $('toast'); e.textContent = t; e.style.display = 'block'; setTimeout(() => e.style.display = 'none', 2500); }
function hud(zone) {
  $('hHearts').textContent = '❤️'.repeat(hearts) + '🖤'.repeat(3 - hearts);
  $('hXp').textContent = `⭐ Nivel ${level()} · ${xp} XP`;
  if (zone) $('hZone').textContent = zone;
}
$('tutorialStart').onclick = () => {
  localStorage.setItem('cyberquest-tutorial', 'done');
  $('tutorialPanel').classList.add('hidden');
  toast('🎯 Misión iniciada: busca tu primer enemigo.');
};
async function openSettings() {
  try {
    const profile = await api('/game/profile');
    const settings = profile.settings || {};
    $('volumeSetting').value = settings.volume ?? 70;
    $('volumeValue').textContent = $('volumeSetting').value;
    $('difficultySetting').value = settings.difficulty || 'adaptativa';
    $('achievementsText').textContent = profile.achievements?.length
      ? `Logros: ${profile.achievements.join(', ')}`
      : 'Aún no tienes logros. Resuelve 10 retos para desbloquear el primero.';
    $('settingsPanel').classList.remove('hidden');
  } catch (e) { toast(e.message); }
}
async function showRanking() {
  try {
    const ranking = await api('/game/ranking');
    $('rankingList').innerHTML = ranking.length
      ? ranking.map((item, index) => `<div class="rank${item.username === window.currentUsername ? ' me' : ''}"><strong>${index + 1}</strong><span>${item.username}</span><strong>${item.xp} XP</strong></div>`).join('')
      : '<p>Aún no hay agentes registrados.</p>';
    $('rankingPanel').classList.remove('hidden');
  } catch (e) { toast(e.message); }
}
async function showProgress() {
  try {
    const p = await api('/game/progress');
    const zones = Object.entries(ZONES).map(([key, zone]) => {
      const defeated = p.defeated?.[key] || 0;
      const boss = (p.bosses || []).includes(key) ? 'jefe derrotado' : 'jefe pendiente';
      return `${zone.name}: ${defeated}/4 enemigos, ${boss}`;
    });
    $('progressText').textContent = `Nivel ${p.level} · ${p.xp} XP · ${p.score} puntos. ${zones.join(' · ')}${p.final_defeated ? ' · Jefe final derrotado.' : ''}`;
    $('progressPanel').classList.remove('hidden');
  } catch (e) { toast(e.message); }
}
async function auth(kind) {
  $('err').textContent = '';
  try {
    const t = await api('/auth/' + kind, {method: 'POST', body: JSON.stringify({username: $('u').value.trim(), password: $('p').value})});
    token = t.access_token; const me = await api('/auth/me'); window.currentUsername = me.username; xp = me.xp; gameState = await api('/game/progress');
    const districts = await api('/game/districts');
    districts.forEach(district => {
      if (ZONES[district.zone]) {
        ZONES[district.zone].boss = district.name;
        ZONES[district.zone].attack = district.attack;
      }
    });
    $('adminBtn').classList.toggle('hidden', me.role !== 'administrador');
    $('login').classList.add('hidden'); $('hud').classList.remove('hidden'); hud('🌍 Explora'); startGame();
    if (localStorage.getItem('cyberquest-tutorial') !== 'done') $('tutorialPanel').classList.remove('hidden');
  } catch (e) { $('err').textContent = e.message; }
}
$('bIn').onclick = () => auth('login'); $('bUp').onclick = () => auth('register');
$('progressBtn').onclick = showProgress; $('progressClose').onclick = () => $('progressPanel').classList.add('hidden');
$('settingsBtn').onclick = openSettings; $('settingsClose').onclick = () => $('settingsPanel').classList.add('hidden');
$('volumeSetting').oninput = () => $('volumeValue').textContent = $('volumeSetting').value;
$('settingsSave').onclick = async () => {
  try {
    await api('/game/profile/settings', {
      method: 'PUT',
      body: JSON.stringify({volume: Number($('volumeSetting').value), difficulty: $('difficultySetting').value, language: 'es'}),
    });
    sound = Number($('volumeSetting').value) > 0;
    localStorage.setItem('cyberquest-sound', sound ? 'on' : 'off');
    $('snd').textContent = sound ? '🔊' : '🔇';
    toast('⚙️ Ajustes guardados');
  } catch (e) { toast(e.message); }
};
$('assessmentBtn').onclick = openAssessment; $('assessmentClose').onclick = () => $('assessmentPanel').classList.add('hidden');
$('pretestBtn').onclick = () => startAssessment('pre'); $('posttestBtn').onclick = () => startAssessment('post');
$('rankingBtn').onclick = showRanking; $('rankingClose').onclick = () => $('rankingPanel').classList.add('hidden');
$('towerBtn').onclick = openTowerDefense; $('towerClose').onclick = closeTowerDefense;
$('towerStart').onclick = startTowerDefense;
$('escapeBtn').onclick = openEscapeRoom; $('escapeClose').onclick = () => $('escapePanel').classList.add('hidden');
$('escapeRoom').onchange = openEscapeRoom; $('escapeReset').onclick = resetEscapeRoom;
$('detectiveBtn').onclick = openDetective; $('detectiveClose').onclick = () => $('detectivePanel').classList.add('hidden');
$('detectiveReset').onclick = resetDetective; $('finalClose').onclick = () => $('finalPanel').classList.add('hidden');
$('finalBtn').onclick = openFinalBoss;
$('mentorBtn').onclick = () => $('mentorPanel').classList.remove('hidden');
$('mentorClose').onclick = () => $('mentorPanel').classList.add('hidden');
$('mentorAsk').onclick = askMentor;
$('adminBtn').onclick = () => $('adminPanel').classList.remove('hidden');
$('adminClose').onclick = () => $('adminPanel').classList.add('hidden');
$('adminSave').onclick = async () => {
  try {
    const data = JSON.parse($('adminJson').value);
    await api('/game/questions', {method: 'POST', body: JSON.stringify(data)});
    $('adminMsg').textContent = 'Pregunta guardada correctamente.';
    $('adminJson').value = '';
  } catch (e) { $('adminMsg').textContent = e.message; }
};
async function askMentor() {
  const answer = $('mentorAnswer');
  answer.classList.remove('hidden');
  answer.textContent = 'El Maestro IA está pensando...';
  try {
    const result = await api('/game/mentor/hint', {
      method: 'POST',
      body: JSON.stringify({
        topic: $('mentorTopic').value,
        level: Number($('mentorLevel').value),
      }),
    });
    answer.textContent = `💡 ${result.hint} Fuente: ${result.source.title} (${result.source.url}). ${result.disclaimer}`;
    answer.classList.add('pulse');
    setTimeout(() => answer.classList.remove('pulse'), 500);
  } catch (e) {
    answer.textContent = e.message;
  }
}

let towerQuestion = null;
async function openTowerDefense() {
  try {
    const state = await api('/game/tower-defense/state');
    renderTowerState(state);
    $('towerPanel').classList.remove('hidden');
  } catch (e) { toast(e.message); }
}
function closeTowerDefense() {
  $('towerPanel').classList.add('hidden');
  $('towerQuiz').classList.add('hidden');
}
function renderTowerState(state) {
  $('towerHp').style.width = `${state.server_hp}%`;
  $('towerStatus').textContent = state.completed
    ? `✅ Servidor protegido. Puntuación: ${state.score}.`
    : `${state.active ? `Oleada ${state.wave + 1} de ${state.total_waves}` : 'Partida lista'} · ${state.server_hp}/100 integridad`;
  $('towerAttack').textContent = state.current_attack
    ? `Ataque entrante: ${state.current_attack}. ${state.current_tip}`
    : 'Responde preguntas para desplegar defensas educativas.';
  $('towerStart').textContent = state.active ? 'Continuar partida' : state.completed ? 'Jugar de nuevo' : 'Iniciar partida';
  const catalog = state.defense_catalog || {};
  $('towerDefense').innerHTML = Object.entries(catalog).map(([key, defense]) =>
    `<option value="${key}">${defense.name} · nivel ${state.defenses?.[key] || 0}</option>`).join('');
}
async function startTowerDefense() {
  try {
    const state = await api('/game/tower-defense/start', {method: 'POST'});
    renderTowerState(state);
    await nextTowerQuestion();
  } catch (e) { $('towerFeedback').textContent = e.message; }
}
async function nextTowerQuestion() {
  try {
    const state = await api('/game/tower-defense/state');
    if (!state.active) {
      renderTowerState(state);
      $('towerQuiz').classList.add('hidden');
      toast(state.completed ? '🏆 ¡Servidor protegido!' : '💥 El servidor fue derribado.');
      return;
    }
    const questions = await api(`/game/questions?zone=redes&min_difficulty=${Math.min(3, 1 + Math.floor(state.wave / 2))}&count=1`);
    towerQuestion = questions[0];
    renderTowerState(state);
    $('towerQuestion').textContent = towerQuestion.text;
    $('towerOpts').innerHTML = '';
    towerQuestion.options.forEach((option, index) => {
      const button = document.createElement('button');
      button.className = 'opt'; button.textContent = option;
      button.onclick = () => answerTowerQuestion(index);
      $('towerOpts').appendChild(button);
    });
    $('towerFeedback').textContent = '';
    $('towerQuiz').classList.remove('hidden');
  } catch (e) { $('towerFeedback').textContent = e.message; }
}
async function answerTowerQuestion(index) {
  const buttons = [...$('towerOpts').children];
  buttons.forEach(button => { button.disabled = true; });
  try {
    const result = await api('/game/tower-defense/answer', {
      method: 'POST',
      body: JSON.stringify({
        question_id: towerQuestion.id,
        option_index: index,
        defense: $('towerDefense').value,
      }),
    });
    buttons[result.correct_index].classList.add('ok');
    if (!result.correct) buttons[index].classList.add('bad');
    xp = result.total_xp; renderTowerState(result);
    $('towerFeedback').textContent = `${result.correct ? '✅ Correcto.' : '❌ Incorrecto.'} ${result.explanation} ${result.damage ? `Daño al servidor: ${result.damage}.` : ''} ${result.xp_gained ? `+${result.xp_gained} XP.` : ''}`;
    if (result.completed || result.wave >= result.total_waves || result.server_hp <= 0) {
      $('towerQuiz').classList.add('hidden');
      toast(result.completed ? '🏆 ¡Defensa completada!' : '💥 El servidor cayó.');
    } else {
      setTimeout(nextTowerQuestion, 1600);
    }

  } catch (e) {
    $('towerFeedback').textContent = e.message;
    buttons.forEach(button => { button.disabled = false; });
  }
}

async function openEscapeRoom() {
  try {
    const room = $('escapeRoom').value;
    const state = await api(`/game/escape-room/${room}`);
    renderEscapeRoom(state);
    $('escapePanel').classList.remove('hidden');
  } catch (e) { toast(e.message); }
}
function renderEscapeRoom(state) {
  $('escapeIntro').textContent = state.intro;
  $('escapeStatus').textContent = state.completed
    ? `🏆 Sala completada · ${state.score} puntos · ${state.hints_used} pistas usadas`
    : `Retos resueltos: ${state.solved}/${state.total} · Puntuación: ${state.score}`;
  $('escapeChallenges').innerHTML = state.challenges.map(challenge => `
    <div class="challenge${challenge.solved ? ' solved' : ''}">
      <strong>${challenge.solved ? '✅' : '🔒'} ${challenge.title}</strong>
      <p>${challenge.prompt}</p>
      <pre>${challenge.code}</pre>
      <div id="escape-options-${challenge.id}"></div>
      ${challenge.solved ? '<p>Reto resuelto.</p>' : `<button class="ghost" onclick="requestEscapeHint('${challenge.id}')">💡 Pista (-5 puntos)</button>`}
      <p id="escape-feedback-${challenge.id}"></p>
    </div>`).join('');
  state.challenges.forEach(challenge => {
    if (challenge.solved) return;
    const container = $(`escape-options-${challenge.id}`);
    challenge.options.forEach((option, index) => {
      const button = document.createElement('button');
      button.className = 'opt'; button.textContent = option;
      button.onclick = () => answerEscapeChallenge(challenge.id, index);
      container.appendChild(button);
    });
  });
}
async function answerEscapeChallenge(challengeId, optionIndex) {
  const room = $('escapeRoom').value;
  const feedback = $(`escape-feedback-${challengeId}`);
  try {
    const result = await api('/game/escape-room/answer', {
      method: 'POST',
      body: JSON.stringify({room, challenge_id: challengeId, option_index: optionIndex}),
    });
    xp = result.total_xp;
    renderEscapeRoom(result);
    $(`escape-feedback-${challengeId}`).textContent =
      `${result.correct ? '✅ Correcto.' : '❌ Incorrecto.'} ${result.explanation} ${result.xp_gained ? `+${result.xp_gained} XP.` : ''}`;
    if (result.completed) toast('🏆 ¡Escapaste de la sala!');
  } catch (e) { feedback.textContent = e.message; }
}
async function requestEscapeHint(challengeId) {
  try {
    const result = await api('/game/escape-room/hint', {
      method: 'POST',
      body: JSON.stringify({room: $('escapeRoom').value, challenge_id: challengeId}),
    });
    toast(`💡 ${result.hint}`);
    await openEscapeRoom();
  } catch (e) { toast(e.message); }
}
async function resetEscapeRoom() {
  try {
    const state = await api(`/game/escape-room/${$('escapeRoom').value}/reset`, {method: 'POST'});
    renderEscapeRoom(state);
  } catch (e) { toast(e.message); }
}

async function openDetective() {
  try {
    const state = await api('/game/detective/state');
    renderDetective(state);
    $('detectivePanel').classList.remove('hidden');
  } catch (e) { toast(e.message); }
}
function renderDetective(state) {
  $('detectiveIntro').textContent = state.intro;
  $('detectiveStatus').textContent = state.completed
    ? `🏆 Investigación completa · ${state.score} puntos`
    : `Pistas analizadas: ${state.solved}/${state.total} · Puntuación: ${state.score}`;
  $('detectiveChallenges').innerHTML = state.challenges.map(challenge => `
    <div class="challenge${challenge.solved ? ' solved' : ''}">
      <strong>${challenge.solved ? '✅' : '🔎'} ${challenge.title}</strong>
      <small style="display:block;opacity:.8">${challenge.source}</small>
      <pre>${challenge.snippet}</pre>
      <p>${challenge.prompt}</p><div id="detective-options-${challenge.id}"></div>
      <p id="detective-feedback-${challenge.id}">${challenge.solved ? `Evidencia: ${challenge.evidence}` : ''}</p>
    </div>`).join('');
  state.challenges.forEach(challenge => {
    if (challenge.solved) return;
    const container = $(`detective-options-${challenge.id}`);
    challenge.options.forEach((option, index) => {
      const button = document.createElement('button');
      button.className = 'opt'; button.textContent = option;
      button.onclick = () => answerDetective(challenge.id, index);
      container.appendChild(button);
    });
  });
}
async function answerDetective(challengeId, optionIndex) {
  try {
    const result = await api('/game/detective/answer', {
      method: 'POST', body: JSON.stringify({challenge_id: challengeId, option_index: optionIndex}),
    });
    xp = result.total_xp; renderDetective(result);
    toast(`${result.correct ? '✅ Evidencia confirmada.' : '❌ Interpretación incorrecta.'} ${result.explanation}`);
    if (result.completed) toast('🏆 ¡Ya puedes abrir el caso final!');
  } catch (e) { toast(e.message); }
}
async function resetDetective() {
  try { renderDetective(await api('/game/detective/reset', {method: 'POST'})); }
  catch (e) { toast(e.message); }
}
async function openFinalBoss() {
  try {
    const state = await api('/game/final-boss/state');
    $('finalStatus').textContent = state.defeated
      ? '🏆 Caso resuelto.'
      : state.unlocked
        ? `Evidencias reunidas: ${state.evidence_count}/${state.required_evidence}.`
        : 'Completa los cuatro jefes y la investigación del modo detective.';
    $('finalPrompt').textContent = state.unlocked && !state.defeated ? state.prompt : '';
    $('finalOptions').innerHTML = '';
    state.options.forEach((option, index) => {
      const button = document.createElement('button');
      button.className = 'opt'; button.textContent = option;
      button.onclick = () => answerFinal(index);
      $('finalOptions').appendChild(button);
    });
    $('finalPanel').classList.remove('hidden');
  } catch (e) { toast(e.message); }
}
async function answerFinal(optionIndex) {
  try {
    const result = await api('/game/final-boss/answer', {
      method: 'POST', body: JSON.stringify({option_index: optionIndex}),
    });
    xp = result.total_xp;
    $('finalFeedback').textContent = `${result.correct ? '✅ ¡Caso resuelto!' : '❌ Aún no.'} ${result.explanation}`;
    if (result.correct) { gameState.final_defeated = true; win(); }
    else await openFinalBoss();
  } catch (e) { $('finalFeedback').textContent = e.message; }
}

// ---- Combate por preguntas ----
let mon = null, monHp = 0, q = null;
async function nextQuestion() {
  $('qExp').classList.add('hidden'); $('qNext').classList.add('hidden'); $('qFlee').classList.remove('hidden');
  try { q = (await api(`/game/questions?zone=${qz()}${mon.boss ? '&min_difficulty=2' : ''}&count=1`))[0]; } catch (e) { toast(e.message); return endQuiz(); }
  $('qText').textContent = q.text; $('qOpts').innerHTML = '';
  $('qJokers').classList.remove('hidden');
  q.options.forEach((o, i) => {
    const b = document.createElement('button'); b.className = 'opt'; b.textContent = o; b.onclick = () => answer(i); $('qOpts').appendChild(b);
  });
}
async function answer(i) {
  const btns = [...$('qOpts').children]; btns.forEach(b => b.disabled = true); $('qFlee').classList.add('hidden');
  const r = await api(`/game/questions/${q.id}/answer`, {method: 'POST', body: JSON.stringify({option_index: i})});
  btns[r.correct_index].classList.add('ok'); if (!r.correct) btns[i].classList.add('bad'); r.correct ? sfx.ok() : sfx.bad();
  const before = level(); xp = r.total_xp;
  if (r.correct) { monHp--; $('qHp').style.width = (monHp / mon.maxHp * 100) + '%'; scene.cameras.main.flash(120, 45, 220, 120); } else { hearts--; scene.cameras.main.shake(180, .006); }
  $('qExp').textContent = (r.correct ? '✅ ¡Correcto! ' : '❌ ¡Casi! ') + r.explanation + (r.xp_gained ? `  (+${r.xp_gained} XP)` : '');
  $('qExp').classList.remove('hidden'); $('qNext').classList.remove('hidden'); hud();
  if (level() > before) toast(`🎉 ¡Subiste al nivel ${level()}!`);
  $('qNext').onclick = () => {
    if (monHp <= 0) { endQuiz(); defeated(mon); }
    else if (hearts <= 0) { hearts = 3; hud(); toast('😴 Descansa un momento y vuelve a intentarlo'); scene.player.setPosition(800, 690); endQuiz(); }
    else nextQuestion();
  };
}
async function useJoker(joker) {
  try {
    const result = await api(`/game/profile/joker/${joker}${joker === 'eliminate' ? `?question_id=${q.id}` : ''}`, {method: 'POST'});
    if (joker === 'eliminate') {
      result.blocked_indices.forEach(index => {
        const button = $('qOpts').children[index];
        if (button) { button.disabled = true; button.classList.add('ghost'); }
      });
      toast(`🃏 Comodín usado. Restan ${result.remaining}.`);
    } else {
      const mentor = await api('/game/mentor/hint', {
        method: 'POST',
        body: JSON.stringify({topic: qz() === 'vulnerabilidades' ? 'seguridad' : qz(), level: 1}),
      });
      $('qExp').textContent = `💡 ${mentor.hint} Fuente: ${mentor.source.title}`;
      $('qExp').classList.remove('hidden');
      toast(`🃏 Comodín usado. Restan ${result.remaining}.`);
    }
  } catch (e) { toast(e.message); }
}
function endQuiz() { $('quiz').classList.add('hidden'); busy = false; scene.cool = scene.time.now + 1200; }
$('qFlee').onclick = () => { const p = scene.player; p.x += p.x > mon.x ? 40 : -40; p.y += p.y > mon.y ? 40 : -40; endQuiz(); };
$('jokerEliminate').onclick = () => useJoker('eliminate');
$('jokerHint').onclick = () => useJoker('hint');
function startQuiz(m) {
  if (m.final) { openFinalBoss(); return; }
  busy = true; mon = m; monHp = m.maxHp; scene.player.setVelocity(0);
  scene.cameras.main.flash(180, 90, 220, 255);
  const district = ZONES[m.zone];
  $('qMon').textContent = `${district.name} · ${m.boss ? `${m.label} (${district.attack})` : `¡Aparece ${m.label}!`}`;
  $('qHp').style.width = '100%';
  $('quiz').classList.remove('hidden'); nextQuestion();
}

// ---- Mundo (Phaser) ----
function px(s, key, w, h, draw) { const g = s.make.graphics({add: false}); draw(g); g.generateTexture(key, w, h); g.destroy(); }
function startGame() {
  new Phaser.Game({type: Phaser.AUTO, parent: 'game', pixelArt: true, backgroundColor: '#12172b',
    scale: {mode: Phaser.Scale.RESIZE, width: '100%', height: '100%'}, physics: {default: 'arcade'}, scene: {create, update}});
}
function create() {
  scene = this;
  px(this, 'player', 16, 16, g => { g.fillStyle(0x5a3a1a).fillRect(4, 1, 8, 3); g.fillStyle(0xffd0a0).fillRect(4, 4, 8, 4);
    g.fillStyle(0x111111).fillRect(5, 5, 1, 2).fillRect(10, 5, 1, 2); g.fillStyle(0x2f6fe0).fillRect(3, 8, 10, 5);
    g.fillStyle(0x333366).fillRect(4, 13, 3, 3).fillRect(9, 13, 3, 3); });
  for (const [k, z] of Object.entries(ZONES)) {
    px(this, 'g_' + k, 16, 16, g => { g.fillStyle(z.color).fillRect(0, 0, 16, 16); g.fillStyle(0x000000, .12).fillRect(3, 4, 2, 2).fillRect(11, 10, 2, 2).fillRect(8, 1, 2, 2); });
    px(this, 'm_' + k, 16, 16, g => { g.fillStyle(0xffffff).fillRect(3, 3, 10, 10).fillRect(2, 5, 12, 6).fillRect(4, 13, 2, 2).fillRect(10, 13, 2, 2);
      g.fillStyle(0xff4d6d, .55).fillRect(3, 3, 10, 2); g.fillStyle(0x111111).fillRect(5, 6, 2, 3).fillRect(9, 6, 2, 3).fillRect(6, 11, 4, 1); });
    this.add.tileSprite(z.x, z.y, 800, 600, 'g_' + k).setOrigin(0);
    this.add.text(z.x + 400, z.y + 30, z.name, {fontSize: '22px', fontStyle: 'bold', color: '#fff', stroke: '#000', strokeThickness: 4}).setOrigin(.5);
    this.add.text(z.x + 400, z.y + 58, `Jefe: ${z.boss} · Ataque: ${z.attack}`, {fontSize: '12px', color: '#dce6ff', stroke: '#000', strokeThickness: 3}).setOrigin(.5);
  }
  this.physics.world.setBounds(0, 0, 1600, 1200);
  this.player = this.physics.add.sprite(800, 600, 'player').setCollideWorldBounds(true).setDepth(5);
  this.mons = this.physics.add.group();
  this.left = Object.fromEntries(Object.keys(ZONES).map(k => [k, Math.max(0, 4 - (gameState.defeated?.[k] || 0))]));
  this.bossesDown = gameState.bosses?.length || 0;
  for (const [k, z] of Object.entries(ZONES)) for (let i = 0; i < 4; i++) {
    if (i >= this.left[k]) break;
    const m = this.mons.create(z.x + 110 + Math.random() * 580, z.y + 100 + Math.random() * 400, 'm_' + k).setTint(0xffffff).setImmovable(true);
    m.zone = k; m.label = z.mon; m.maxHp = 2; this.tweens.add({targets: m, y: m.y - 6, yoyo: true, repeat: -1, duration: 700 + i * 120});
  }
  for (const [k, z] of Object.entries(ZONES)) {
    if (this.left[k] === 0 && !(gameState.bosses || []).includes(k)) spawn(z.x + 400, z.y + 300, k, z.boss, 4, true, false);
  }
  if (this.bossesDown === 4 && !gameState.final_defeated) spawn(800, 600, 'redes', 'el Rey del Ciberespacio', 5, true, true);
  this.cameras.main.setBounds(0, 0, 1600, 1200).startFollow(this.player, true, .1, .1);
  const fit = () => this.cameras.main.setZoom(Math.max(2, Math.min(4, this.scale.width / 400))); fit(); this.scale.on('resize', fit);
  this.keys = this.input.keyboard.addKeys('W,A,S,D,UP,DOWN,LEFT,RIGHT'); this.cool = 0; this.target = null;
  this.input.on('pointerdown', p => { if (!busy) this.target = {x: p.worldX, y: p.worldY}; });
  this.physics.add.overlap(this.player, this.mons, (p, m) => { if (!busy && this.time.now > this.cool) startQuiz(m); });
}
function update() {
  const p = this.player, k = this.keys, sp = 95; if (busy) return p.setVelocity(0);
  let vx = (k.RIGHT.isDown || k.D.isDown) - (k.LEFT.isDown || k.A.isDown), vy = (k.DOWN.isDown || k.S.isDown) - (k.UP.isDown || k.W.isDown);
  if (vx || vy) this.target = null;
  else if (this.target) { const dx = this.target.x - p.x, dy = this.target.y - p.y, d = Math.hypot(dx, dy); if (d > 4) { vx = dx / d; vy = dy / d; } else this.target = null; }
  const n = Math.hypot(vx, vy) || 1; p.setVelocity(vx / n * sp * (vx || vy ? 1 : 0), vy / n * sp * (vx || vy ? 1 : 0));
  for (const [key, z] of Object.entries(ZONES)) if (p.x >= z.x && p.x < z.x + 800 && p.y >= z.y && p.y < z.y + 600) { if (this.zone !== key) { this.zone = key; hud(z.name); } }
}

// ---- Jefes, sonido y final ----
const qz = () => mon.final ? Object.keys(ZONES)[Math.floor(Math.random() * 4)] : mon.zone;
function spawn(x, y, zone, label, hp, boss, final) {
  const m = scene.mons.create(x, y, 'm_' + zone).setImmovable(true).setScale(boss ? 2.4 : 1).setDepth(3);
  Object.assign(m, {zone, label, maxHp: hp, boss, final}); if (final) m.setTint(0xffd166);
  scene.tweens.add({targets: m, y: y - 8, yoyo: true, repeat: -1, duration: 600});
}
function defeated(m) {
  const s = scene; m.destroy(); sfx.win();
  if (m.final) { openFinalBoss(); return; }
  const progress = {zone: m.zone, boss: !!m.boss};
  api('/game/progress/defeat', {method: 'POST', body: JSON.stringify(progress)}).then(result => {
    xp = result.total_xp;
    toast(`¡Derrotaste a ${m.label}! +${result.reward_xp} XP 🏆`);
  }).catch(e => toast(e.message));
  if (m.boss) {
    gameState.bosses = [...(gameState.bosses || []), m.zone];
    if (++s.bossesDown === 4) { spawn(800, 600, 'redes', 'el Rey del Ciberespacio', 5, true, true); toast('👑 ¡El jefe final apareció en el centro del mapa!'); }
    return;
  }
  gameState.defeated[m.zone] = (gameState.defeated[m.zone] || 0) + 1;
  if (--s.left[m.zone] === 0) { const z = ZONES[m.zone]; spawn(z.x + 400, z.y + 300, m.zone, z.boss, 4, true, false); toast(`⚠️ ¡${z.boss} apareció! Responde preguntas sobre ${z.attack}.`); }
}
async function win() {
  busy = true;
  try {
    const stats = await api('/game/final-stats');
    const topics = Object.entries(stats.by_topic).map(([topic, value]) => `${topic}: ${value.correct}/${value.total} (${value.percent}%)`).join(' · ');
    $('wXp').textContent = `Nivel ${stats.level} · ${stats.xp} XP · ${stats.score} puntos. ${topics || 'Sin respuestas registradas.'} Logros: ${stats.achievements.length || 0}.`;
  } catch (e) {
    $('wXp').textContent = `Nivel ${level()} · ${xp} XP`;
  }
  $('win').classList.remove('hidden');
}
$('wOk').onclick = () => { $('win').classList.add('hidden'); busy = false; };
let sound = localStorage.getItem('cyberquest-sound') !== 'off', actx;
function beep(f, d = .12, type = 'square') {
  if (!sound) return;
  try { actx = actx || new AudioContext(); const o = actx.createOscillator(), g = actx.createGain(); o.type = type; o.frequency.value = f; g.gain.value = .05;
    o.connect(g); g.connect(actx.destination); o.start(); g.gain.exponentialRampToValueAtTime(.0001, actx.currentTime + d); o.stop(actx.currentTime + d); } catch (e) {}
}
const sfx = {ok: () => { beep(660); setTimeout(() => beep(880), 110); }, bad: () => beep(160, .25, 'sawtooth'),
  win: () => [523, 659, 784, 1046].forEach((f, i) => setTimeout(() => beep(f, .2), i * 140))};
$('snd').textContent = sound ? '🔊' : '🔇';
$('snd').onclick = () => { sound = !sound; localStorage.setItem('cyberquest-sound', sound ? 'on' : 'off'); $('snd').textContent = sound ? '🔊' : '🔇'; };
