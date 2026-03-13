let currentColor;
let gameRunning = false;
let clickable = false;
let totalGreen = 0;
let missedGreen = 0;
let totalRed = 0;
let clickedRed = 0;
let stimulusStartTime;
let reactionTimes = [];

const box = document.getElementById("box");
const statusText = document.getElementById("status");
const startBtn = document.getElementById("startBtn");
const instructionBox = document.getElementById("instructions");

function startGame() {
    startBtn.style.display = "none";
    instructionBox.style.display = "none";

    totalGreen = 0;
    missedGreen = 0;
    totalRed = 0;
    clickedRed = 0;
    reactionTimes = [];

    gameRunning = true;
    statusText.innerText = "Assessing... Stay Focused";
    statusText.style.color = "var(--text-main)";

    nextStimulus();
    // Test duration: 30 seconds
    setTimeout(endGame, 30000);
}

function nextStimulus() {
    if (!gameRunning) return;

    box.style.display = "none";
    clickable = false;

    setTimeout(() => {
        if (!gameRunning) return;

        // 70% green (attention test), 30% red (impulsivity test)
        currentColor = Math.random() < 0.7 ? "green" : "red";

        box.style.backgroundColor = currentColor === "green" ? "#10b981" : "#ef4444";
        box.style.boxShadow = `0 0 40px ${currentColor === "green"
            ? "rgba(16, 185, 129, 0.4)"
            : "rgba(239, 68, 68, 0.4)"}`;

        box.style.display = "block";
        stimulusStartTime = Date.now();
        clickable = true;

        if (currentColor === "green") totalGreen++;
        else totalRed++;

        // Stimulus visible for 1 second
        setTimeout(() => {
            if (clickable && gameRunning) {
                if (currentColor === "green") {
                    missedGreen++;
                }
                nextStimulus();
            }
        }, 1000);

    }, Math.random() * 1000 + 800);
}

box.onclick = () => {
    if (!clickable || !gameRunning) return;

    const reactionTime = Date.now() - stimulusStartTime;
    clickable = false;
    box.style.display = "none";

    if (currentColor === "green") {
        // Only log RT for correct Go responses
        reactionTimes.push(reactionTime);
    } else if (currentColor === "red") {
        clickedRed++;
    }

    nextStimulus();
};

// ─────────────────────────────────────────────────────────────
// REACTION TIME ANALYSIS
// Research basis: ADHD is associated with slower mean RT AND
// higher RT variability (SD). Variability is considered the
// stronger cognitive marker. (Hervey et al., 2004;
// Epstein et al., 2003)
// ─────────────────────────────────────────────────────────────

/**
 * Returns mean of an array. Returns null if empty.
 */
function mean(arr) {
    if (arr.length === 0) return null;
    return arr.reduce((a, b) => a + b, 0) / arr.length;
}

/**
 * Returns standard deviation of an array. Returns null if < 2 values.
 */
function stdDev(arr) {
    if (arr.length < 2) return null;
    const m = mean(arr);
    const variance = arr.reduce((sum, val) => sum + Math.pow(val - m, 2), 0) / arr.length;
    return Math.sqrt(variance);
}

/**
 * Scores inattention (0–5) using BOTH omission error rate AND reaction time.
 *
 * Omission errors  → missed green boxes      → pure attention failures
 * Slow mean RT     → delayed responses        → sluggish attention engagement
 * High RT variability (SD) → inconsistent RT → hallmark of ADHD attention dysregulation
 *
 * Each component contributes equally (weighted 1/3 each).
 * Final score is rounded to nearest integer in 0–5 range.
 */
function getInattentionScore(omissionRate, meanRT, rtSD) {
    // --- Component 1: Omission error rate (0–5) ---
    let omissionScore;
    if (omissionRate <= 0.05)       omissionScore = 0;
    else if (omissionRate <= 0.15)  omissionScore = 1;
    else if (omissionRate <= 0.30)  omissionScore = 2;
    else if (omissionRate <= 0.50)  omissionScore = 3;
    else if (omissionRate <= 0.70)  omissionScore = 4;
    else                            omissionScore = 5;

    // --- Component 2: Mean reaction time (0–5) ---
    // Normal RT for healthy adults: ~250–400ms
    // Slow RT (>600ms) is associated with inattention
    let rtMeanScore = 0;
    if (meanRT !== null) {
        if (meanRT <= 300)       rtMeanScore = 0;
        else if (meanRT <= 400)  rtMeanScore = 1;
        else if (meanRT <= 500)  rtMeanScore = 2;
        else if (meanRT <= 650)  rtMeanScore = 3;
        else if (meanRT <= 800)  rtMeanScore = 4;
        else                     rtMeanScore = 5;
    }

    // --- Component 3: RT variability / standard deviation (0–5) ---
    // Low SD (~50–80ms) = consistent attention
    // High SD (>200ms)  = highly variable, ADHD marker
    let rtSDScore = 0;
    if (rtSD !== null) {
        if (rtSD <= 60)        rtSDScore = 0;
        else if (rtSD <= 100)  rtSDScore = 1;
        else if (rtSD <= 150)  rtSDScore = 2;
        else if (rtSD <= 200)  rtSDScore = 3;
        else if (rtSD <= 280)  rtSDScore = 4;
        else                   rtSDScore = 5;
    }

    // Weighted average: variability weighted slightly higher as it's
    // the stronger ADHD marker per Hervey et al. (2004)
    const weighted = (omissionScore * 0.30) + (rtMeanScore * 0.30) + (rtSDScore * 0.40);
    return Math.min(5, Math.round(weighted));
}

function getImpulsivityScore(commissionRate) {
    if (commissionRate <= 0.05)       return 0;
    else if (commissionRate <= 0.15)  return 1;
    else if (commissionRate <= 0.30)  return 2;
    else if (commissionRate <= 0.50)  return 3;
    else if (commissionRate <= 0.70)  return 4;
    else                              return 5;
}

function endGame() {
    gameRunning = false;
    box.style.display = "none";

    const omissionRate    = totalGreen > 0 ? missedGreen / totalGreen : 0;
    const commissionRate  = totalRed   > 0 ? clickedRed  / totalRed   : 0;

    const meanRT = mean(reactionTimes);
    const rtSD   = stdDev(reactionTimes);

    const inScore = getInattentionScore(omissionRate, meanRT, rtSD);
    const imScore = getImpulsivityScore(commissionRate);

    // Pass data back to parent form
    if (window.opener && !window.opener.closed) {
        try {
            window.opener.document.getElementById("InattentionScore").value  = inScore;
            window.opener.document.getElementById("ImpulsivityScore").value  = imScore;
            window.opener.document.getElementById("total_trials").value      = totalGreen + totalRed;
            window.opener.document.getElementById("correct_go").value        = totalGreen - missedGreen;
            window.opener.document.getElementById("missed_go").value         = missedGreen;
            window.opener.document.getElementById("correct_inhibit").value   = totalRed - clickedRed;
            window.opener.document.getElementById("commission_errors").value = clickedRed;
            window.opener.document.getElementById("reaction_times").value    = JSON.stringify(reactionTimes);

            // Show completion status in parent
            const statusDiv = window.opener.document.getElementById("game-completion-status");
            if (statusDiv) statusDiv.style.display = "block";

            const parentBtn = window.opener.document.querySelector("button[onclick='openGame()']");
            if (parentBtn) {
                parentBtn.innerText = "Assessment Complete ✓";
                parentBtn.style.color = "#10b981";
                parentBtn.style.borderColor = "#10b981";
            }
        } catch (e) {
            console.error("Could not update parent window:", e);
        }
    }

    statusText.innerText = "Assessment Complete";
    statusText.style.color = "#10b981";

    const summary = document.createElement("div");
    summary.style.cssText = "margin-top:20px; color:var(--text-muted); font-size:0.85rem;";
    summary.innerHTML = `<p>Test finished successfully. Closing in 3 seconds...</p>`;
    box.parentNode.appendChild(summary);

    setTimeout(() => window.close(), 3000);
}