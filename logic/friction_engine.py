"""
friction_engine.py  -  LearnSense AI's rule-based logic
=========================================================
IMPORTANT: This is a RULE-BASED prototype. It is NOT a trained machine-learning
model. Every number below is chosen by us (the group) and is EXPERIMENTAL.
It has not been validated on real learners.

How the Experimental Friction Index (0-100) is built
----------------------------------------------------
Four signals, each converted to a fraction between 0 and 1,
then multiplied by its weight. The weights add up to 100.

  1. Time signal        (weight 30)
        ratio = actual_time / expected_time
        fraction = (ratio - 1), kept between 0 and 1
        -> on time or faster = 0, double the expected time (or more) = 1

  2. Unsuccessful-attempt signal (weight 30)
        fraction = unsuccessful_attempts / attempts
        -> share of attempts that did not work

  3. Hint signal        (weight 20)
        fraction = hints / 5, kept at most 1
        -> 5 or more hints = full weight

  4. Repeated-attempt signal (weight 20)
        fraction = (attempts - 1) / 5, kept between 0 and 1
        -> first-try success = 0, 6 or more attempts = full weight

  Index = sum(weight x fraction), then rounded and clamped to 0..100.
"""

# ---- Settings (kept in one place so students can explain & change them) ----
WEIGHTS = {"time": 30, "unsuccessful": 30, "hints": 20, "attempts": 20}
HINTS_FOR_FULL_SIGNAL = 5      # 5 hints -> hint signal is maxed out
ATTEMPTS_FOR_FULL_SIGNAL = 6   # 6 attempts -> repeated-attempt signal is maxed out

# Thresholds used to say "this signal was detected"
TIME_RATIO_THRESHOLD = 1.5     # took 1.5x the expected time or more
FAIL_RATE_THRESHOLD = 0.5      # half or more attempts unsuccessful (and at least 2)
HINT_THRESHOLD = 3             # 3 or more hints requested
CHECKIN_INDEX_THRESHOLD = 75   # high index -> suggest teacher check-in

# Limits to keep inputs sensible
MAX_MINUTES = 600
MAX_COUNT = 100


class InputError(ValueError):
    """Raised when the user's inputs are not valid."""


def _clamp(value, low, high):
    """Keep a number between low and high."""
    return max(low, min(high, value))


def validate_session(data):
    """Check the raw inputs and return clean numbers. Raises InputError if wrong."""
    if not isinstance(data, dict):
        raise InputError("Session data must be sent as a set of named values.")

    fields = {
        "expected_time": "Expected task time",
        "actual_time": "Actual task time",
        "attempts": "Number of attempts",
        "unsuccessful": "Unsuccessful attempts",
        "hints": "Hints requested",
    }
    clean = {}
    for key, label in fields.items():
        raw = data.get(key)
        if raw is None or str(raw).strip() == "":
            raise InputError(f"{label} is required.")
        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise InputError(f"{label} must be a number.")
        if value != value or value in (float("inf"), float("-inf")):
            raise InputError(f"{label} must be a normal number.")
        if value < 0:
            raise InputError(f"{label} cannot be negative.")
        clean[key] = value

    if clean["expected_time"] <= 0:
        raise InputError("Expected task time must be greater than 0.")
    if clean["expected_time"] > MAX_MINUTES or clean["actual_time"] > MAX_MINUTES:
        raise InputError(f"Time values cannot be more than {MAX_MINUTES} minutes.")
    for key in ("attempts", "unsuccessful", "hints"):
        if clean[key] != int(clean[key]):
            raise InputError("Attempts, unsuccessful attempts and hints must be whole numbers.")
        clean[key] = int(clean[key])
        if clean[key] > MAX_COUNT:
            raise InputError(f"Counts cannot be more than {MAX_COUNT}.")
    if clean["unsuccessful"] > clean["attempts"]:
        raise InputError("Unsuccessful attempts cannot be more than total attempts.")
    return clean


def calculate_components(s):
    """Return the time ratio, fail rate, the 4 signal fractions (0..1) and their points."""
    ratio = s["actual_time"] / s["expected_time"]
    time_fraction = _clamp(ratio - 1, 0, 1)

    fail_rate = (s["unsuccessful"] / s["attempts"]) if s["attempts"] > 0 else 0
    hint_fraction = _clamp(s["hints"] / HINTS_FOR_FULL_SIGNAL, 0, 1)
    attempt_fraction = _clamp((s["attempts"] - 1) / (ATTEMPTS_FOR_FULL_SIGNAL - 1), 0, 1)

    fractions = {
        "time": time_fraction,
        "unsuccessful": _clamp(fail_rate, 0, 1),
        "hints": hint_fraction,
        "attempts": attempt_fraction,
    }
    points = {k: round(fractions[k] * WEIGHTS[k], 1) for k in fractions}
    return ratio, fail_rate, fractions, points


def friction_index(s):
    """Final Experimental Friction Index: always a whole number from 0 to 100."""
    _, _, fractions, _ = calculate_components(s)
    total = sum(fractions[k] * WEIGHTS[k] for k in fractions)
    return int(_clamp(round(total), 0, 100))


def interpret(index):
    """Plain, supportive wording for each band. No labels about ability or motivation."""
    if index < 25:
        return ("Smooth progress",
                "The session signals show little friction. The task appears to have matched the learner's current stage.")
    if index < 50:
        return ("Some friction",
                "A few signals suggest the task was a little tricky. Light support may help.")
    if index < 75:
        return ("Noticeable friction",
                "Several signals suggest the task was difficult this time. Targeted support is recommended.")
    return ("Strong friction signals",
            "Many signals point to difficulty with this task. This describes the session, not the learner. "
            "Supportive help and a teacher check-in are recommended.")


def detect_signals(s):
    """List which signals crossed their threshold, with a plain explanation."""
    ratio, fail_rate, _, _ = calculate_components(s)
    signals = []
    if ratio >= TIME_RATIO_THRESHOLD:
        signals.append({
            "key": "time",
            "title": "Long completion time",
            "detail": f"Task took {s['actual_time']:g} min against {s['expected_time']:g} min expected "
                      f"({ratio:.1f}x the expected time).",
        })
    if s["unsuccessful"] >= 2 and fail_rate >= FAIL_RATE_THRESHOLD:
        signals.append({
            "key": "unsuccessful",
            "title": "Many unsuccessful attempts",
            "detail": f"{s['unsuccessful']} of {s['attempts']} attempts did not work "
                      f"({fail_rate * 100:.0f}% unsuccessful).",
        })
    if s["hints"] >= HINT_THRESHOLD:
        signals.append({
            "key": "hints",
            "title": "Frequent hint requests",
            "detail": f"{s['hints']} hints were requested.",
        })
    return signals


# What each signal means and which support we suggest (used for explanations)
_SUPPORT = {
    "time": {
        "suggestion": "Try a simpler explanation or a worked example",
        "why_matters": "Taking much longer than expected can mean the idea needs to be shown in a clearer or smaller way first.",
        "why_support": "A worked example lets the learner see the full thinking process once, then try again with more confidence.",
    },
    "unsuccessful": {
        "suggestion": "Use guided practice with feedback after each try",
        "why_matters": "Repeated unsuccessful attempts can mean the same misunderstanding is being repeated without feedback.",
        "why_support": "Guided practice gives quick correction after each attempt, so mistakes are not repeated.",
    },
    "hints": {
        "suggestion": "Break the problem into smaller steps",
        "why_matters": "Asking for many hints can mean the problem feels too large to start or continue alone.",
        "why_support": "Smaller steps make each part easier to attempt and can reduce the need for hints over time.",
    },
}


def build_recommendations(s, index, signals):
    """Create explainable recommendations that match the detected signals."""
    recs = []
    for sig in signals:
        info = _SUPPORT[sig["key"]]
        recs.append({
            "suggestion": info["suggestion"],
            "signal_detected": f"{sig['title']}: {sig['detail']}",
            "why_it_matters": info["why_matters"],
            "why_this_support": info["why_support"],
        })

    # Continuing difficulty -> teacher check-in
    if len(signals) >= 2 or index >= CHECKIN_INDEX_THRESHOLD:
        if signals:
            names = ", ".join(sig["title"].lower() for sig in signals)
            detected = (f"Difficulty continues across the signals above ({names}); "
                        f"experimental friction index is {index}/100.")
        else:
            detected = f"Experimental friction index is {index}/100."
        recs.append({
            "suggestion": "Arrange a short teacher check-in",
            "signal_detected": detected,
            "why_it_matters": "When several signals appear together, self-study tools alone may not be enough.",
            "why_this_support": "A teacher can listen, find the exact point of confusion, and adjust the support. "
                                "Teacher judgement always comes before this tool's output.",
        })

    if not recs:
        recs.append({
            "suggestion": "Continue to the next learning task",
            "signal_detected": "No signal crossed its threshold.",
            "why_it_matters": "Few friction signals suggest the task matched the learner's current stage.",
            "why_this_support": "No extra support is needed now. A slightly more challenging task can be offered.",
        })
    return recs


def analyse_session(data):
    """MAIN FUNCTION: validate -> calculate -> detect -> recommend. Returns a dictionary."""
    s = validate_session(data)
    ratio, fail_rate, fractions, points = calculate_components(s)
    index = friction_index(s)
    signals = detect_signals(s)
    title, message = interpret(index)

    breakdown = [
        {"key": "time", "label": "Completion time", "weight": WEIGHTS["time"],
         "points": points["time"],
         "how": f"Actual/expected = {ratio:.2f}. Fraction = ({ratio:.2f} - 1) limited to 0-1 = {fractions['time']:.2f}."},
        {"key": "unsuccessful", "label": "Unsuccessful attempts", "weight": WEIGHTS["unsuccessful"],
         "points": points["unsuccessful"],
         "how": f"{s['unsuccessful']} unsuccessful out of {s['attempts']} attempts = {fractions['unsuccessful']:.2f}."},
        {"key": "hints", "label": "Hints requested", "weight": WEIGHTS["hints"],
         "points": points["hints"],
         "how": f"{s['hints']} hints / {HINTS_FOR_FULL_SIGNAL} (limited to 1) = {fractions['hints']:.2f}."},
        {"key": "attempts", "label": "Repeated attempts", "weight": WEIGHTS["attempts"],
         "points": points["attempts"],
         "how": f"({s['attempts']} - 1) / {ATTEMPTS_FOR_FULL_SIGNAL - 1} (limited to 0-1) = {fractions['attempts']:.2f}."},
    ]

    return {
        "inputs": s,
        "friction_index": index,
        "band": title,
        "interpretation": message,
        "breakdown": breakdown,
        "signals": signals,
        "recommendations": build_recommendations(s, index, signals),
        "disclaimer": "Experimental rule-based index. Not a trained model and not validated on real learners. "
                      "It describes one learning session, not a learner's ability or motivation.",
    }


# ---- Demonstration scenarios shown as buttons on the LearnSense page ----
SCENARIOS = [
    {"id": "smooth", "name": "Smooth session",
     "description": "Task finished near the expected time on the first try.",
     "inputs": {"expected_time": 8, "actual_time": 7, "attempts": 1, "unsuccessful": 0, "hints": 0}},
    {"id": "slow", "name": "Slow but steady",
     "description": "Took longer than expected, but attempts were mostly fine.",
     "inputs": {"expected_time": 10, "actual_time": 17, "attempts": 2, "unsuccessful": 1, "hints": 1}},
    {"id": "hints", "name": "Needs smaller steps",
     "description": "Finished in a reasonable time but needed many hints.",
     "inputs": {"expected_time": 12, "actual_time": 14, "attempts": 3, "unsuccessful": 1, "hints": 4}},
    {"id": "stuck", "name": "Repeated unsuccessful tries",
     "description": "Several attempts, most of which did not work.",
     "inputs": {"expected_time": 6, "actual_time": 9, "attempts": 5, "unsuccessful": 4, "hints": 1}},
    {"id": "high", "name": "High friction example",
     "description": "Long time, many failed attempts and many hints together.",
     "inputs": {"expected_time": 6, "actual_time": 14, "attempts": 4, "unsuccessful": 4, "hints": 3}},
]


def _quiz_value(name, raw):
    """Check a quiz score typed by the user (must be 0 to 10)."""
    try:
        v = float(raw)
    except (TypeError, ValueError):
        raise InputError(f"{name} must be a number from 0 to 10.")
    if not 0 <= v <= 10:
        raise InputError(f"{name} must be between 0 and 10.")
    return v


def compare_before_after(before, after, quiz_before=None, quiz_after=None):
    """
    PROPOSED FEATURE (not validated): compare two sessions around a support step.
    Returns changes for time, attempts, hints, friction index and (optional) quiz.
    """
    b = analyse_session(before)
    a = analyse_session(after)

    def change(label, bv, av, unit="", lower_is_better=True):
        diff = round(av - bv, 1)
        if diff == 0:
            note = "No change"
        else:
            improved = (diff < 0) if lower_is_better else (diff > 0)
            note = "Moved in a helpful direction" if improved else "Moved the other way"
        return {"label": label, "before": bv, "after": av, "unit": unit, "change": diff, "note": note}

    rows = [
        change("Time taken", b["inputs"]["actual_time"], a["inputs"]["actual_time"], "min"),
        change("Attempts", b["inputs"]["attempts"], a["inputs"]["attempts"]),
        change("Unsuccessful attempts", b["inputs"]["unsuccessful"], a["inputs"]["unsuccessful"]),
        change("Hint requests", b["inputs"]["hints"], a["inputs"]["hints"]),
        change("Friction index", b["friction_index"], a["friction_index"], "/100"),
    ]
    if quiz_before not in (None, "") and quiz_after not in (None, ""):
        qb = _quiz_value("Quiz before", quiz_before)
        qa = _quiz_value("Quiz after", quiz_after)
        rows.append(change("Quiz score", qb, qa, "/10", lower_is_better=False))

    index_diff = a["friction_index"] - b["friction_index"]
    if index_diff < 0:
        summary = ("The after-support session shows fewer friction signals. With one pair of sessions "
                   "this cannot show that the support caused the change.")
        next_step = "Offer the next task at the same level, then a slightly harder one if the signals stay low."
    elif index_diff == 0:
        summary = "Friction signals look similar before and after support."
        next_step = "Try a different kind of support, or arrange a teacher check-in."
    else:
        summary = "The after-support session shows more friction signals."
        next_step = "Pause new content and arrange a teacher check-in to understand what is blocking progress."
    return {"rows": rows, "before_index": b["friction_index"], "after_index": a["friction_index"],
            "summary": summary, "next_step": next_step,
            "disclaimer": "PROPOSED feature. It has not been tested experimentally and gives no proof "
                          "that support caused any change."}
