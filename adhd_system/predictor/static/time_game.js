// ─────────────────────────────────────────────────────────────────────────────
// TIME ESTIMATION GAME — time_game.js
//
// Research basis:
//   Toplak, M. E., Dockstader, C., & Tannock, R. (2006).
//   "Temporal information processing in ADHD: Findings to date and new methods."
//   Journal of Neuroscience Methods, 151(1), 15–30.
//
//   ADHD individuals consistently UNDERESTIMATE time — they release the button
//   too early because their internal clock runs faster. The deviation score
//   (how far off from target) maps to HyperactivityScore.
// ─────────────────────────────────────────────────────────────────────────────

// ── Targets for each of the 5 rounds (in milliseconds) ──────────────────────
const ROUND_TARGETS = [2000, 3000, 5000, 4000, 3000];
// Average of ROUND_TARGETS = 3400ms — varied to prevent rhythm exploitation

let currentRound = 0;
let holdStartTime = null;
let isHolding = false;
let roundResults = [];   // [{target, actual, error, errorPct}]
let gamePhase = 'idle';  // idle | memorize | hold | feedback | done
let memorizeTimer = null;
let memorizeStart = null;
let memorizeRAF = null;

// ── DOM refs ──────────────────────────────────────────────────────────────────
const startBtn = document.getElementById('startBtn');
const instructions = document.getElementById('instructions');
const roundDots = document.getElementById('roundDots');
const targetDisplay = document.getElementById('targetDisplay');
const targetSeconds = document.getElementById('targetSeconds');
const memorizeBar = document.getElementById('memorizeBar');
const memorizeBarFill = document.getElementById('memorizeBarFill');
const holdWrapper = document.getElementById('holdWrapper');
const holdBtn = document.getElementById('holdBtn');
const feedbackCard = document.getElementById('feedbackCard');
const feedbackTitle = document.getElementById('feedbackTitle');
const feedbackDetail = document.getElementById('feedbackDetail');
const statusText = document.getElementById('status');

// ── Helpers ───────────────────────────────────────────────────────────────────
function setStatus(msg) { statusText.innerText = msg; }

function updateDots() {
  for (let i = 0; i < 5; i++) {
    const dot = document.getElementById(`dot${i}`);
    dot.className = 'round-dot';
    if (i < currentRound) dot.classList.add('done');
    else if (i === currentRound) dot.classList.add('active');
  }
}

function showFeedback(target, actual) {
  const error = actual - target;          // positive = too late, negative = too early
  const errorPct = (error / target) * 100;
  const absErr = Math.abs(error);

  feedbackCard.className = 'feedback-card';
  let emoji, titleText, detailText;

  if (absErr <= target * 0.10) {
    // Within 10% — excellent
    feedbackCard.classList.add('good');
    emoji = '✅';
    titleText = 'Excellent timing!';
    detailText = `You held for ${(actual / 1000).toFixed(2)}s — only ${(absErr / 1000).toFixed(2)}s off.`;
  } else if (error < 0) {
    // Released too early — ADHD-associated pattern
    feedbackCard.classList.add('too-early');
    emoji = '⚡';
    titleText = 'Released too early';
    detailText = `You held for ${(actual / 1000).toFixed(2)}s — ${(absErr / 1000).toFixed(2)}s shorter than target.`;
  } else {
    // Released too late
    feedbackCard.classList.add('too-late');
    emoji = '⏳';
    titleText = 'Released a bit late';
    detailText = `You held for ${(actual / 1000).toFixed(2)}s — ${(absErr / 1000).toFixed(2)}s longer than target.`;
  }

  feedbackTitle.innerText = `${emoji} ${titleText}`;
  feedbackDetail.innerText = detailText;
  feedbackCard.style.display = 'block';

  return { target, actual, error, errorPct };
}

// ── Animate memorize bar ──────────────────────────────────────────────────────
function animateMemorizeBar(durationMs) {
  memorizeStart = Date.now();
  memorizeBarFill.style.width = '0%';
  memorizeBarFill.style.transition = 'none';

  function tick() {
    const elapsed = Date.now() - memorizeStart;
    const pct = Math.min((elapsed / durationMs) * 100, 100);
    memorizeBarFill.style.width = pct + '%';
    if (pct < 100) memorizeRAF = requestAnimationFrame(tick);
  }
  memorizeRAF = requestAnimationFrame(tick);
}

// ── Game flow ─────────────────────────────────────────────────────────────────

function startGame() {
  startBtn.style.display = 'none';
  instructions.style.display = 'none';
  roundDots.style.display = 'flex';
  currentRound = 0;
  roundResults = [];
  updateDots();
  beginRound();
}

function beginRound() {
  gamePhase = 'memorize';
  feedbackCard.style.display = 'none';
  holdWrapper.style.display = 'none';

  const target = ROUND_TARGETS[currentRound];
  targetSeconds.innerText = (target / 1000).toFixed(0);
  targetDisplay.style.display = 'block';

  setStatus(`Round ${currentRound + 1} of 5 — memorize this duration`);
  updateDots();

  // Show the target for (target) ms so user gets a feel for how long it is
  memorizeBar.style.display = 'block';
  animateMemorizeBar(target);

  memorizeTimer = setTimeout(() => {
    cancelAnimationFrame(memorizeRAF);
    memorizeBar.style.display = 'none';
    targetDisplay.style.display = 'none';
    gamePhase = 'hold';
    setStatus('Now hold the button for exactly that long!');
    holdWrapper.style.display = 'flex';
  }, target);
}

// ── Hold button events ────────────────────────────────────────────────────────

function onHoldStart(e) {
  e.preventDefault();
  if (gamePhase !== 'hold') return;
  isHolding = true;
  holdStartTime = Date.now();
  holdBtn.classList.add('holding');
  holdBtn.innerText = 'Holding...';
  setStatus('Release when you think the time is up!');
}

function onHoldEnd(e) {
  e.preventDefault();
  if (!isHolding || gamePhase !== 'hold') return;
  isHolding = false;
  holdBtn.classList.remove('holding');
  holdBtn.innerText = 'Hold';

  const actual = Date.now() - holdStartTime;
  const target = ROUND_TARGETS[currentRound];
  const result = showFeedback(target, actual);
  roundResults.push(result);

  gamePhase = 'feedback';
  holdWrapper.style.display = 'none';

  currentRound++;
  if (currentRound < ROUND_TARGETS.length) {
    updateDots();
    setStatus('Next round coming up...');
    setTimeout(beginRound, 1800);
  } else {
    // Mark all dots done
    for (let i = 0; i < 5; i++) {
      document.getElementById(`dot${i}`).className = 'round-dot done';
    }
    setTimeout(endGame, 1800);
  }
}

holdBtn.addEventListener('mousedown', onHoldStart);
holdBtn.addEventListener('mouseup', onHoldEnd);
holdBtn.addEventListener('mouseleave', onHoldEnd);
holdBtn.addEventListener('touchstart', onHoldStart, { passive: false });
holdBtn.addEventListener('touchend', onHoldEnd, { passive: false });

// ── Scoring logic ─────────────────────────────────────────────────────────────
// Maps mean absolute error percentage to 0–5 HyperactivityScore
// Research: ADHD → underestimate time → higher deviation
// Normal deviation: ~10–20% | ADHD deviation: often >40%
function getHyperactivityScore(results) {
  if (!results.length) return 0;

  const meanAbsErrPct = results.reduce((s, r) => s + Math.abs(r.errorPct), 0) / results.length;

  // Bias: count rounds where released TOO EARLY (ADHD hallmark — impulsive release)
  const earlyCount = results.filter(r => r.error < 0).length;
  const earlyBias = earlyCount / results.length;   // 0–1

  // Base score from deviation magnitude
  let baseScore;
  if (meanAbsErrPct <= 10) baseScore = 0;
  else if (meanAbsErrPct <= 20) baseScore = 1;
  else if (meanAbsErrPct <= 35) baseScore = 2;
  else if (meanAbsErrPct <= 55) baseScore = 3;
  else if (meanAbsErrPct <= 75) baseScore = 4;
  else baseScore = 5;

  // Bonus: consistent early release bumps score up (impulsivity signal)
  // If >60% of rounds were released early, add 1 point
  const bonus = earlyBias >= 0.6 ? 1 : 0;

  return Math.min(5, baseScore + bonus);
}

// ── End game ──────────────────────────────────────────────────────────────────
function endGame() {
  gamePhase = 'done';
  feedbackCard.style.display = 'none';

  const hyperScore = getHyperactivityScore(roundResults);

  // Send score to parent window (index.html)
  if (window.opener && !window.opener.closed) {
    try {
      window.opener.document.getElementById('HyperactivityScore').value = hyperScore;

      // Send full round data for the PDF report per-round table
      const roundsPayload = roundResults.map((r, i) => ({
        target_ms: ROUND_TARGETS[i],
        actual_ms: r.actual,
      }));
      window.opener.document.getElementById('time_game_rounds').value = JSON.stringify(roundsPayload);

      // Show completion badge on parent page
      const timeGameStatus = window.opener.document.getElementById('time-game-completion-status');
      if (timeGameStatus) timeGameStatus.style.display = 'block';

      const timeBtn = window.opener.document.querySelector("button[onclick='openTimeGame()']");
      if (timeBtn) {
        timeBtn.innerText = 'Time Test Complete ✓';
        timeBtn.style.color = '#10b981';
        timeBtn.style.borderColor = '#10b981';
      }
    } catch (e) {
      console.error('Could not update parent window:', e);
    }
  }

  setStatus('Assessment complete!');

  const summary = document.createElement('div');
  summary.style.cssText = 'margin-top:20px; color:var(--text-muted); font-size:0.85rem;';
  summary.innerHTML = '<p>Test finished successfully. Closing in 3 seconds...</p>';
  holdWrapper.parentNode.appendChild(summary);

  setTimeout(() => window.close(), 3000);
}