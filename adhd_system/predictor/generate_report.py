import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable, PageBreak
)
from datetime import datetime


BLUE        = colors.HexColor("#3B82F6")
LIGHT_BLUE  = colors.HexColor("#EFF6FF")
RED         = colors.HexColor("#EF4444")
LIGHT_RED   = colors.HexColor("#FEF2F2")
GREEN       = colors.HexColor("#22C55E")
LIGHT_GREEN = colors.HexColor("#F0FDF4")
TEAL        = colors.HexColor("#10B981")
LIGHT_TEAL  = colors.HexColor("#ECFDF5")
ORANGE      = colors.HexColor("#F97316")
PURPLE      = colors.HexColor("#8B5CF6")
DARK        = colors.HexColor("#1E293B")
GRAY        = colors.HexColor("#64748B")
LIGHT_GRAY  = colors.HexColor("#F1F5F9")
WHITE       = colors.white


THRESHOLDS = {
    "InattentionScore":   {"low": 3,  "high": 6,  "max": 5,  "label": "Inattention"},
    "ImpulsivityScore":   {"low": 3,  "high": 6,  "max": 5,  "label": "Impulsivity"},
    "HyperactivityScore": {"low": 2,  "high": 4,  "max": 5,  "label": "Hyperactivity"},
    "Daydreaming":        {"low": 1,  "high": 2,  "max": 3,  "label": "Daydreaming"},
    "RSD":                {"low": 1,  "high": 2,  "max": 3,  "label": "Rejection Sensitivity"},
    "SleepHours":         {"low": 6,  "high": 9,  "max": 12, "label": "Sleep Hours",      "invert": True},
    "ScreenTime":         {"low": 2,  "high": 5,  "max": 12, "label": "Screen Time (hrs)"},
    "AcademicScore":      {"low": 40, "high": 70, "max": 100,"label": "Academic Score",   "invert": True},
    "ComorbidAnxiety":    {"low": 0,  "high": 0,  "max": 1,  "label": "Anxiety"},
    "ComorbidDepression": {"low": 0,  "high": 0,  "max": 1,  "label": "Depression"},
    "FamilyHistoryADHD":  {"low": 0,  "high": 0,  "max": 1,  "label": "Family History"},
}

SCORE_KEYS    = ["InattentionScore", "ImpulsivityScore", "HyperactivityScore", "Daydreaming", "RSD"]
LIFESTYLE_KEYS = ["SleepHours", "ScreenTime", "AcademicScore"]
BINARY_KEYS   = ["ComorbidAnxiety", "ComorbidDepression", "FamilyHistoryADHD"]

TIME_GAME_TARGETS = [2000, 3000, 5000, 4000, 3000]


def _buf_to_rl_image(fig, width_cm=14):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    img = Image(buf)
    aspect = img.imageHeight / img.imageWidth
    w = width_cm * cm
    img.drawWidth  = w
    img.drawHeight = w * aspect
    return img

def _risk_color(value, threshold_key):
    t = THRESHOLDS[threshold_key]
    invert = t.get("invert", False)
    low, high = t["low"], t["high"]
    if invert:
        if value >= high: return "#22C55E"
        if value >= low:  return "#F97316"
        return "#EF4444"
    else:
        if value <= low:  return "#22C55E"
        if value <= high: return "#F97316"
        return "#EF4444"


def _chart_symptom_scores(user_data):
    keys       = SCORE_KEYS
    labels     = [THRESHOLDS[k]["label"] for k in keys]
    values     = [float(user_data.get(k, 0)) for k in keys]
    maxes      = [5, 5, 5, 3, 3]   
    bar_colors = [_risk_color(v, k) for v, k in zip(values, keys)]

    fig, ax = plt.subplots(figsize=(8, 3.5))
    y = np.arange(len(labels))
    ax.barh(y, maxes,  color="#E2E8F0", height=0.5, zorder=1)
    ax.barh(y, values, color=bar_colors, height=0.5, zorder=2)
    for i, (v, m) in enumerate(zip(values, maxes)):
        ax.text(m + 0.1, i, f"{v}/{m}", va='center', fontsize=9, color="#1E293B")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlim(0, max(maxes) + 1.5)
    ax.set_xlabel("Score", fontsize=9)
    ax.set_title("Core ADHD Symptom Scores", fontsize=12, fontweight='bold', pad=10)
    ax.spines[['top','right','left']].set_visible(False)
    ax.xaxis.set_ticks_position('bottom')
    patches = [
        mpatches.Patch(color="#22C55E", label="Low risk"),
        mpatches.Patch(color="#F97316", label="Moderate risk"),
        mpatches.Patch(color="#EF4444", label="High risk"),
    ]
    ax.legend(handles=patches, loc='lower right', fontsize=8, framealpha=0.7)
    fig.tight_layout()
    return _buf_to_rl_image(fig)


def _chart_go_nogo(game_data):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.5))

    sizes   = [
        game_data.get('correct_go', 0),
        game_data.get('missed_go', 0),
        game_data.get('correct_inhibit', 0),
        game_data.get('commission_errors', 0),
    ]
    if sum(sizes) == 0:
        ax1.text(0.5, 0.5, 'Game not played', ha='center', va='center',
                 transform=ax1.transAxes, fontsize=11, color='gray')
        ax1.axis('off')
        ax1.set_title("Response Accuracy", fontsize=11, fontweight='bold')
    else:
        clrs    = ['#22C55E', '#F97316', '#3B82F6', '#EF4444']
        labels  = ['Correct Go', 'Missed Go', 'Correct Inhibit', 'Commission Errors']
        explode = [0, 0.05, 0, 0.05]
        wedges, texts, autotexts = ax1.pie(
            sizes, labels=labels, colors=clrs, explode=explode,
            autopct=lambda p: f'{p:.0f}%' if p > 0 else '',
            startangle=90, textprops={'fontsize': 8}
        )
        for at in autotexts:
            at.set_fontsize(8)
        ax1.set_title("Response Accuracy", fontsize=11, fontweight='bold')

    rts = game_data.get('reaction_times', [])
    if rts:
        ax2.hist(rts, bins=min(15, len(rts)), color='#3B82F6', edgecolor='white', alpha=0.85)
        ax2.axvline(np.mean(rts), color='#EF4444', linewidth=1.5,
                    linestyle='--', label=f'Mean: {np.mean(rts):.0f} ms')
        ax2.legend(fontsize=8)
    else:
        ax2.text(0.5, 0.5, 'No RT data', ha='center', va='center',
                 transform=ax2.transAxes, fontsize=10, color='gray')
    ax2.set_xlabel("Reaction Time (ms)", fontsize=9)
    ax2.set_ylabel("Count", fontsize=9)
    ax2.set_title("Reaction Time Distribution", fontsize=11, fontweight='bold')
    ax2.spines[['top','right']].set_visible(False)
    fig.suptitle("Go / No-Go Game Performance", fontsize=12, fontweight='bold')
    fig.tight_layout()
    return _buf_to_rl_image(fig, width_cm=15)


def _chart_time_game(time_game_data):
    rounds  = time_game_data.get('rounds', [])
    if not rounds:
        fig, ax = plt.subplots(figsize=(9, 3))
        ax.text(0.5, 0.5, 'Time game not played', ha='center', va='center',
                transform=ax.transAxes, fontsize=12, color='gray')
        ax.axis('off')
        fig.tight_layout()
        return _buf_to_rl_image(fig, width_cm=14)

    n       = len(rounds)
    targets = [r['target_ms'] / 1000 for r in rounds]   # convert to seconds
    actuals = [r['actual_ms'] / 1000 for r in rounds]
    errors  = [r['actual_ms'] - r['target_ms'] for r in rounds]  # ms, signed
    r_labels = [f"Round {i+1}" for i in range(n)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.5))

    x = np.arange(n)
    w = 0.35
    ax1.bar(x - w/2, targets, w, label='Target',  color='#3B82F6', alpha=0.85)
    ax1.bar(x + w/2, actuals, w, label='Actual',  color='#10B981', alpha=0.85)
    ax1.set_xticks(x)
    ax1.set_xticklabels(r_labels, fontsize=8)
    ax1.set_ylabel("Duration (seconds)", fontsize=9)
    ax1.set_title("Target vs Actual Hold Time", fontsize=11, fontweight='bold')
    ax1.legend(fontsize=8)
    ax1.spines[['top','right']].set_visible(False)

    bar_colors = ['#EF4444' if e < 0 else '#F97316' for e in errors]
    ax2.bar(x, errors, color=bar_colors, alpha=0.85)
    ax2.axhline(0, color='#1E293B', linewidth=1)
    ax2.set_xticks(x)
    ax2.set_xticklabels(r_labels, fontsize=8)
    ax2.set_ylabel("Deviation (ms)", fontsize=9)
    ax2.set_title("Timing Deviation per Round", fontsize=11, fontweight='bold')

    early_count = sum(1 for e in errors if e < 0)
    note = f"Released early {early_count}/{n} rounds"
    ax2.text(0.98, 0.97, note, transform=ax2.transAxes,
             ha='right', va='top', fontsize=8,
             color='#EF4444' if early_count > n/2 else '#64748B')

    patches = [
        mpatches.Patch(color="#EF4444", label="Too early (ADHD pattern)"),
        mpatches.Patch(color="#F97316", label="Too late"),
    ]
    ax2.legend(handles=patches, fontsize=7, loc='lower right')
    ax2.spines[['top','right']].set_visible(False)

    fig.suptitle("Time Perception Game Performance", fontsize=12, fontweight='bold')
    fig.tight_layout()
    return _buf_to_rl_image(fig, width_cm=15)


def _chart_radar(user_data):
    cats   = ["Inattention", "Impulsivity", "Hyperactivity", "Daydreaming", "RSD"]
    keys   = ["InattentionScore", "ImpulsivityScore", "HyperactivityScore", "Daydreaming", "RSD"]
    maxes  = [5, 5, 5, 3, 3]
    user_v = [float(user_data.get(k, 0)) / m for k, m in zip(keys, maxes)]
    adhd_v = [0.78, 0.72, 0.80, 0.75, 0.70]

    N      = len(cats)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    user_v += [user_v[0]];  adhd_v += [adhd_v[0]];  angles += [angles[0]]
    cat_angles = angles[:-1]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.plot(angles, user_v, 'o-', linewidth=2, color='#3B82F6', label='You')
    ax.fill(angles, user_v, alpha=0.2, color='#3B82F6')
    ax.plot(angles, adhd_v, 's--', linewidth=1.5, color='#EF4444', label='Typical ADHD')
    ax.fill(angles, adhd_v, alpha=0.1, color='#EF4444')
    ax.set_xticks(cat_angles)
    ax.set_xticklabels(cats, fontsize=9)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=7)
    ax.set_title("Your Profile vs Typical ADHD", fontsize=11, fontweight='bold', pad=18)
    ax.legend(loc='lower right', fontsize=9, bbox_to_anchor=(1.35, -0.05))
    fig.tight_layout()
    return _buf_to_rl_image(fig, width_cm=10)


def _chart_binary_factors(user_data):
    keys       = BINARY_KEYS
    labels     = [THRESHOLDS[k]["label"] for k in keys]
    values     = [user_data.get(k, 0) for k in keys]
    bar_colors = ["#EF4444" if v else "#22C55E" for v in values]

    fig, ax = plt.subplots(figsize=(6, 2))
    y = np.arange(len(labels))
    ax.barh(y, [1]*len(labels), color="#E2E8F0", height=0.4)
    ax.barh(y, values, color=bar_colors, height=0.4)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlim(0, 1.4)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['No', 'Yes'])
    ax.set_title("Risk Factors Present", fontsize=11, fontweight='bold', pad=8)
    ax.spines[['top','right','left']].set_visible(False)
    for i, v in enumerate(values):
        ax.text(1.05, i, "YES" if v else "NO", va='center', fontsize=10,
                fontweight='bold', color="#EF4444" if v else "#22C55E")
    fig.tight_layout()
    return _buf_to_rl_image(fig, width_cm=10)


def _chart_lifestyle(user_data):
    keys       = LIFESTYLE_KEYS
    labels     = [THRESHOLDS[k]["label"] for k in keys]
    values     = [user_data.get(k, 0) for k in keys]
    maxes      = [THRESHOLDS[k]["max"] for k in keys]
    bar_colors = [_risk_color(v, k) for v, k in zip(values, keys)]

    fig, axes = plt.subplots(1, 3, figsize=(8, 3))
    for ax, label, value, max_val, color in zip(axes, labels, values, maxes, bar_colors):
        ax.bar([label], [value],   color=color,    width=0.4)
        ax.bar([label], [max_val], color="#E2E8F0", width=0.4, zorder=0)
        ax.set_ylim(0, max_val * 1.25)
        ax.set_title(label, fontsize=9, fontweight='bold')
        ax.text(0, value + max_val * 0.02, f"{value}", ha='center', fontsize=11, fontweight='bold')
        ax.spines[['top','right','left']].set_visible(False)
        ax.set_xticks([])
    fig.suptitle("Lifestyle Indicators", fontsize=12, fontweight='bold')
    fig.tight_layout()
    return _buf_to_rl_image(fig, width_cm=14)


def _symptom_interpretation(user_data, prediction, game_data, time_game_data):
    inatt  = float(user_data.get("InattentionScore", 0))
    impuls = float(user_data.get("ImpulsivityScore", 0))
    hyper  = float(user_data.get("HyperactivityScore", 0))
    sleep  = user_data.get("SleepHours", 0)
    screen = user_data.get("ScreenTime", 0)
    acad   = user_data.get("AcademicScore", 0)
    anxiety    = user_data.get("ComorbidAnxiety", 0)
    depression = user_data.get("ComorbidDepression", 0)
    family     = user_data.get("FamilyHistoryADHD", 0)

    commission      = game_data.get("commission_errors", 0)
    total           = game_data.get("total_trials", 1)
    missed_go       = game_data.get("missed_go", 0)
    rts             = game_data.get("reaction_times", [])
    mean_rt         = int(np.mean(rts)) if rts else None
    commission_rate = commission / total if total else 0
    missed_rate     = missed_go / total if total else 0

    items = []

    sym_parts = []
    for score, label, threshold in [(inatt, "inattention", 3.0), (impuls, "impulsivity", 3.0), (hyper, "hyperactivity", 2.0)]:
        if score >= threshold * 2:
            sym_parts.append(f"{label.capitalize()} score ({score}/5) is high.")
        elif score >= threshold:
            sym_parts.append(f"{label.capitalize()} score ({score}/5) is moderate.")
        else:
            sym_parts.append(f"{label.capitalize()} score ({score}/5) is low.")
    items.append(("Core Symptom Scores", " ".join(sym_parts)))

    game_parts = []
    if commission_rate > 0.20:
        game_parts.append(f"Commission errors on {commission_rate*100:.0f}% of No-Go trials — a key impulsivity marker.")
    else:
        game_parts.append(f"Commission error rate ({commission_rate*100:.0f}%) was within normal range.")
    if missed_rate > 0.25:
        game_parts.append(f"Missed {missed_rate*100:.0f}% of Go targets, suggesting inattention.")
    else:
        game_parts.append(f"Responded correctly to {100-missed_rate*100:.0f}% of Go targets.")
    if mean_rt:
        if mean_rt > 600:
            game_parts.append(f"Average reaction time ({mean_rt} ms) was slower than typical.")
        elif mean_rt < 250:
            game_parts.append(f"Average reaction time ({mean_rt} ms) was very fast, suggesting impulsive responding.")
        else:
            game_parts.append(f"Average reaction time ({mean_rt} ms) was in the normal range.")
    items.append(("Go / No-Go Game Interpretation", " ".join(game_parts)))

    time_parts = []
    rounds = time_game_data.get('rounds', [])
    if rounds:
        errors     = [r['actual_ms'] - r['target_ms'] for r in rounds]
        abs_errors = [abs(e) for e in errors]
        mean_err   = np.mean(abs_errors)
        early_count = sum(1 for e in errors if e < 0)
        mean_err_pct = np.mean([abs(r['actual_ms'] - r['target_ms']) / r['target_ms'] * 100 for r in rounds])

        if mean_err_pct <= 10:
            time_parts.append(f"Excellent time perception — average deviation was only {mean_err:.0f} ms ({mean_err_pct:.0f}% of target).")
        elif mean_err_pct <= 30:
            time_parts.append(f"Moderate timing accuracy — average deviation was {mean_err:.0f} ms ({mean_err_pct:.0f}% of target).")
        else:
            time_parts.append(f"Poor timing accuracy — average deviation was {mean_err:.0f} ms ({mean_err_pct:.0f}% of target), which is above the normal range.")

        if early_count >= 4:
            time_parts.append(
                f"Critically, {early_count} out of {len(rounds)} rounds were released early — "
                f"consistently underestimating time is the hallmark ADHD pattern in temporal processing tasks "
                f"(Toplak et al., 2006)."
            )
        elif early_count >= 2:
            time_parts.append(f"{early_count} of {len(rounds)} rounds were released early, suggesting a mild tendency to underestimate time.")
        else:
            time_parts.append(f"No strong early-release bias was observed — time perception appears relatively intact.")

        time_parts.append(f"This score contributed to the Hyperactivity dimension of the assessment.")
    else:
        time_parts.append("Time perception game was not completed. Hyperactivity score was derived from the questionnaire instead.")

    items.append(("Time Perception Game Interpretation", " ".join(time_parts)))

    life_parts = []
    if sleep < 6:
        life_parts.append(f"Sleep of {sleep} hrs is low — can amplify ADHD symptoms.")
    elif sleep > 9:
        life_parts.append(f"Sleep of {sleep} hrs is above average.")
    else:
        life_parts.append(f"Sleep duration ({sleep} hrs) is in the healthy range.")
    if screen > 5:
        life_parts.append(f"Screen time of {screen} hrs/day is high, associated with attention difficulties.")
    else:
        life_parts.append(f"Screen time ({screen} hrs/day) appears manageable.")
    if acad < 50:
        life_parts.append(f"Academic score of {acad} is low, may reflect attention-related learning impact.")
    elif acad >= 70:
        life_parts.append(f"Academic score of {acad} is good.")
    else:
        life_parts.append(f"Academic score is average ({acad}).")
    items.append(("Lifestyle & Academic Indicators", " ".join(life_parts)))

    risk_parts = []
    if family:     risk_parts.append("Family history of ADHD increases genetic predisposition.")
    if anxiety:    risk_parts.append("Comorbid anxiety was reported — frequently co-occurs with ADHD.")
    if depression: risk_parts.append("Comorbid depression was noted — common in individuals with ADHD.")
    if not (family or anxiety or depression):
        risk_parts.append("No additional biological or psychological risk factors were reported.")
    items.append(("Additional Risk Factors", " ".join(risk_parts)))

    if prediction == 1:
        conclusion = (
            "Based on combined analysis of symptom scores, Go/No-Go game performance, "
            "time perception results, lifestyle indicators, and risk factors, the model "
            "identified a pattern consistent with ADHD. This does not constitute a clinical "
            "diagnosis. Please consult a licensed psychiatrist or psychologist for formal evaluation."
        )
    else:
        conclusion = (
            "Your overall pattern did not meet the threshold the model associates with ADHD. "
            "This does not rule out ADHD — only a qualified clinician can provide a formal assessment. "
            "If you have concerns, speaking with a healthcare professional is always a good step."
        )
    items.append(("How the Conclusion Was Reached", conclusion))
    return items


def generate_adhd_report(user_data: dict, game_data: dict, prediction: int,
                         user_name: str = "User",
                         time_game_data: dict = None) -> bytes:
    
    if time_game_data is None:
        time_game_data = {}

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )

    styles    = getSampleStyleSheet()
    sec_style = ParagraphStyle('SectionHead', parent=styles['Heading2'],
                               fontSize=13, textColor=BLUE, spaceBefore=14, spaceAfter=4)
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                fontSize=10, textColor=DARK, leading=16,
                                alignment=TA_JUSTIFY, spaceAfter=6)
    caption_style = ParagraphStyle('Caption', parent=styles['Normal'],
                                   fontSize=8, textColor=GRAY, alignment=TA_CENTER)
    small_bold = ParagraphStyle('SmallBold', parent=styles['Normal'],
                                fontSize=9, textColor=DARK, fontName='Helvetica-Bold')

    story = []

    result_text = "ADHD INDICATORS DETECTED" if prediction == 1 else "NO ADHD INDICATORS DETECTED"
    banner_data = [[
        Paragraph("<font size='20'><b>ADHD Assessment Report</b></font>", styles['Normal']),
        Paragraph(
            f"<font color='{'#EF4444' if prediction==1 else '#22C55E'}' size='11'><b>{result_text}</b></font><br/>"
            f"<font size='9' color='#64748B'>Generated: {datetime.now().strftime('%d %B %Y')}</font>",
            styles['Normal']
        )
    ]]
    banner = Table(banner_data, colWidths=[10*cm, 7*cm])
    banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), LIGHT_GRAY),
        ('ROWPADDING', (0,0),(-1,-1), 12),
        ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
        ('ALIGN',      (1,0),(1,0),   'RIGHT'),
        ('LEFTPADDING',(0,0),(0,-1),  14),
    ]))
    story.append(banner)
    story.append(Spacer(1, 10))

    info_items = [("Name", user_name), ("Age", str(user_data.get("Age","—"))),
                  ("Gender", user_data.get("Gender","—")), ("Education", user_data.get("EducationStage","—"))]
    info_data  = [[Paragraph(f"<b>{k}</b><br/>{v}", small_bold) for k, v in info_items]]
    info_table = Table(info_data, colWidths=[4.25*cm]*4)
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), LIGHT_BLUE),
        ('ROWPADDING', (0,0),(-1,-1), 8),
        ('ALIGN',      (0,0),(-1,-1), 'CENTER'),
        ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
        ('BOX',        (0,0),(-1,-1), 0.5, BLUE),
        ('INNERGRID',  (0,0),(-1,-1), 0.5, BLUE),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))

    disc = Table([[Paragraph(
        "<b>⚠ Important Disclaimer:</b> This report is generated by a machine learning model "
        "for educational purposes only. It is <b>not</b> a clinical diagnosis. Consult a licensed "
        "healthcare professional for formal evaluation.", body_style
    )]], colWidths=[17*cm])
    disc.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), colors.HexColor("#FFFBEB")),
        ('BOX',       (0,0),(-1,-1), 0.8, colors.HexColor("#F59E0B")),
        ('ROWPADDING',(0,0),(-1,-1), 10),
    ]))
    story.append(disc)
    story.append(Spacer(1, 16))

    # Section 1: Symptom Scores 
    story.append(Paragraph("1. Core ADHD Symptom Scores", sec_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BLUE, spaceAfter=8))
    story.append(_chart_symptom_scores(user_data))
    story.append(Paragraph(
        "Scores from Go/No-Go game (Inattention, Impulsivity) and Time Perception game (Hyperactivity). "
        "Green = low risk · Orange = moderate · Red = high.",
        caption_style))
    story.append(Spacer(1, 10))

    # Section 2: Game Performance Statistics 
    story.append(Paragraph("2. Game Performance Statistics", sec_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BLUE, spaceAfter=8))

    # Go/No-Go stats
    total_t = game_data.get('total_trials', 0)
    hit_r   = game_data.get('correct_go', 0) / max(total_t, 1) * 100
    com_r   = game_data.get('commission_errors', 0) / max(total_t, 1) * 100
    rts     = game_data.get('reaction_times', [])
    mean_rt_str = f"{int(np.mean(rts))} ms" if rts else "N/A"

    # Time game stats
    time_rounds = time_game_data.get('rounds', [])
    time_performed = len(time_rounds) > 0
    if time_performed:
        time_errors = [r['actual_ms'] - r['target_ms'] for r in time_rounds]
        time_abs_errors = [abs(e) for e in time_errors]
        time_mean_abs_err = np.mean(time_abs_errors)
        time_early_count = sum(1 for e in time_errors if e < 0)
        time_mean_err_pct = np.mean([abs(r['actual_ms'] - r['target_ms']) / r['target_ms'] * 100 for r in time_rounds])
        time_accuracy_str = f"{100-time_mean_err_pct:.0f}%"
    else:
        time_accuracy_str = "Not played"

    # Combined table
    stat_data = [
        ["Metric", "Go/No-Go", "Time Perception Game"],
        ["Total Trials / Rounds", str(total_t), f"{len(time_rounds)} rounds" if time_performed else "—"],
        ["Hit Rate / Accuracy", f"{hit_r:.0f}%", time_accuracy_str],
        ["Error Rate", f"{com_r:.0f}%", f"{time_mean_err_pct:.0f}% deviation" if time_performed else "—"],
        ["Mean Reaction Time", mean_rt_str, f"{int(time_mean_abs_err)} ms" if time_performed else "—"],
    ]
    stat_t = Table(stat_data, colWidths=[5*cm, 6*cm, 6*cm])
    stat_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), BLUE),
        ('TEXTCOLOR',  (0,0),(-1,0), WHITE),
        ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0),(-1,-1), 9),
        ('ALIGN',      (0,0),(-1,-1), 'CENTER'),
        ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
        ('ROWPADDING', (0,0),(-1,-1), 8),
        ('BACKGROUND', (0,1),(-1,-1), LIGHT_BLUE),
        ('BOX',        (0,0),(-1,-1), 0.5, BLUE),
        ('INNERGRID',  (0,0),(-1,-1), 0.5, colors.HexColor("#BFDBFE")),
    ]))
    story.append(stat_t)
    story.append(Spacer(1, 10))

    #  Subsection 2a: Go/No-Go Game 
    story.append(Paragraph("2.1 Go / No-Go Game Performance", sec_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BLUE, spaceAfter=8))
    story.append(_chart_go_nogo(game_data))
    story.append(Spacer(1, 10))

    #  Subsection 2b: Time Perception Game 
    story.append(Paragraph("2.2 Time Perception Game Performance", sec_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=TEAL, spaceAfter=8))

    rounds = time_game_data.get('rounds', [])
    if rounds:
        errors       = [r['actual_ms'] - r['target_ms'] for r in rounds]
        abs_errors   = [abs(e) for e in errors]
        mean_abs_err = np.mean(abs_errors)
        early_count  = sum(1 for e in errors if e < 0)
        mean_err_pct = np.mean([abs(r['actual_ms'] - r['target_ms']) / r['target_ms'] * 100 for r in rounds])

        tg_data = [
            ["Round", "Target (s)", "Your Hold (s)", "Deviation (ms)", "Direction"],
        ]
        for i, r in enumerate(rounds):
            dev   = r['actual_ms'] - r['target_ms']
            direc = "Too Early ⚡" if dev < 0 else ("On Time ✅" if abs(dev) <= r['target_ms']*0.1 else "Too Late ⏳")
            tg_data.append([
                f"Round {i+1}",
                f"{r['target_ms']/1000:.1f}s",
                f"{r['actual_ms']/1000:.2f}s",
                f"{dev:+.0f} ms",
                direc,
            ])
        tg_data.append([
            "Average", "—",
            f"{np.mean([r['actual_ms'] for r in rounds])/1000:.2f}s",
            f"{np.mean(errors):+.0f} ms",
            f"{early_count}/{len(rounds)} early"
        ])

        tg_table = Table(tg_data, colWidths=[2.5*cm, 3*cm, 3.5*cm, 3.5*cm, 4.5*cm])
        tg_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), TEAL),
            ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND', (0,-1),(-1,-1), LIGHT_TEAL),
            ('FONTNAME',   (0,-1),(-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 9),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('ROWPADDING', (0,0), (-1,-1), 7),
            ('BOX',        (0,0), (-1,-1), 0.5, TEAL),
            ('INNERGRID',  (0,0), (-1,-1), 0.5, colors.HexColor("#A7F3D0")),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [WHITE, LIGHT_TEAL]),
        ]))
        story.append(tg_table)
        story.append(Spacer(1, 8))
        story.append(_chart_time_game(time_game_data))
        story.append(Paragraph(
            f"Mean absolute deviation: {mean_abs_err:.0f} ms ({mean_err_pct:.0f}% of target) · "
            f"Early releases: {early_count}/{len(rounds)} rounds · "
            "Red bars = released early (ADHD-associated pattern).",
            caption_style))
    else:
        story.append(Paragraph(
            "Time perception game was not completed. Hyperactivity score was derived from the questionnaire.",
            body_style))

    story.append(Spacer(1, 10))

    # Section 3: Profile + Risk Factors 
    story.append(Paragraph("3. Profile Comparison & Risk Factors", sec_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BLUE, spaceAfter=8))
    radar_img  = _chart_radar(user_data)
    binary_img = _chart_binary_factors(user_data)
    radar_img.drawWidth  = 8.5*cm;  radar_img.drawHeight  = 8.5*cm
    binary_img.drawWidth = 8*cm;    binary_img.drawHeight = 4*cm
    two_col = Table([[radar_img, binary_img]], colWidths=[8.7*cm, 8.3*cm])
    two_col.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(-1,-1),'CENTER')]))
    story.append(two_col)
    story.append(Spacer(1, 10))

    #  Section 4: Lifestyle 
    story.append(Paragraph("4. Lifestyle Indicators", sec_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BLUE, spaceAfter=8))
    story.append(_chart_lifestyle(user_data))
    story.append(Spacer(1, 10))

    # Section 5: Detailed Interpretation 
    story.append(Paragraph("5. Detailed Interpretation", sec_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BLUE, spaceAfter=8))

    for heading, body in _symptom_interpretation(user_data, prediction, game_data, time_game_data):
        is_conclusion = "Conclusion" in heading or "Reached" in heading
        is_time       = "Time Perception" in heading
        bg     = (LIGHT_RED   if (is_conclusion and prediction==1)
                  else LIGHT_GREEN if (is_conclusion and prediction==0)
                  else LIGHT_TEAL  if is_time
                  else LIGHT_GRAY)
        border = (RED   if (is_conclusion and prediction==1)
                  else GREEN if (is_conclusion and prediction==0)
                  else TEAL  if is_time
                  else GRAY)
        t = Table([
            [Paragraph(f"<b>{heading}</b>", small_bold)],
            [Paragraph(body, body_style)],
        ], colWidths=[17*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(-1,0), bg),
            ('ROWPADDING', (0,0),(-1,-1), 8),
            ('BOX',        (0,0),(-1,-1), 0.8, border),
            ('LINEBELOW',  (0,0),(-1,0),  0.5, border),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This report was generated automatically by a machine learning based ADHD screening tool. "
        "It is intended for informational purposes only and does not replace professional medical advice, "
        "diagnosis, or treatment.",
        ParagraphStyle('Footer', parent=styles['Normal'],
                       fontSize=7.5, textColor=GRAY, alignment=TA_CENTER)
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()


if __name__ == "__main__":
    sample_user = {
        'Age': 22, 'Gender': 'Male', 'EducationStage': 'University',
        'InattentionScore': 3.8, 'ImpulsivityScore': 4.2, 'HyperactivityScore': 4,
        'Daydreaming': 2, 'RSD': 2, 'SleepHours': 5.5, 'ScreenTime': 7,
        'ComorbidAnxiety': 1, 'ComorbidDepression': 0, 'FamilyHistoryADHD': 1,
        'Medication': 'No', 'SchoolSupport': 'None', 'AcademicScore': 52,
    }
    sample_game = {
        'total_trials': 60, 'correct_go': 28, 'missed_go': 7,
        'correct_inhibit': 17, 'commission_errors': 8,
        'reaction_times': [320,410,290,510,380,450,310,490,360,420,
                           280,530,370,480,300,440,390,520,340,460],
    }
    sample_time_game = {
        'rounds': [
            {'target_ms': 2000, 'actual_ms': 1540},   
            {'target_ms': 3000, 'actual_ms': 2210},   
            {'target_ms': 5000, 'actual_ms': 4100},   
            {'target_ms': 4000, 'actual_ms': 3650},   
            {'target_ms': 3000, 'actual_ms': 3180},   
        ]
    }
    pdf_bytes = generate_adhd_report(
        sample_user, sample_game, prediction=1,
        user_name="Alex", time_game_data=sample_time_game
    )
    with open("/mnt/user-data/outputs/adhd_report_sample.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("Report saved.")