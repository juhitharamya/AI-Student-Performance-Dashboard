"""
ML service — sklearn-backed student performance analysis.

Algorithms used:
  • K-Means (n=4)          — cluster students into performance tiers
  • Linear Regression      — predict marks when multiple score columns exist
  • Logistic Regression    — pass/fail probability per student
  • Z-score fallback       — used for small samples (n < 5)
"""

from __future__ import annotations
import statistics
from typing import Any


# ── Grade/category helpers ────────────────────────────────────────────────────

def _letter_grade(score: float) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 55: return "C"
    if score >= 40: return "D"
    return "F"


def _performance_category(grade: str, cluster: str) -> str:
    if grade == "A":                    return "Excellent"
    if grade == "B":                    return "Good"
    if grade in ("C", "D"):             return "Average"
    if cluster == "At Risk" or grade == "F": return "At Risk"
    return "Average"


def _cluster_label_from_center(score: float, centers: list[float]) -> str:
    """Map a score to a cluster label based on 4 sorted K-Means centroids."""
    sorted_c = sorted(centers)
    idx = min(range(len(sorted_c)), key=lambda i: abs(sorted_c[i] - score))
    labels = ["At Risk", "Below Average", "Above Average", "High Performer"]
    return labels[idx]


def _zscore_cluster(score: float, mean: float, stdev: float) -> str:
    z = (score - mean) / stdev if stdev > 0 else 0
    if z > 1.0:  return "High Performer"
    if z > 0.0:  return "Above Average"
    if z > -1.0: return "Below Average"
    return "At Risk"


def _risk_score(score: float, mean: float, stdev: float) -> int:
    z = (score - mean) / stdev if stdev > 0 else 0
    return max(0, min(100, int(50 - z * 20)))


# ── Roll-number detection ─────────────────────────────────────────────────────

def _find_roll_col(headers: list[str]) -> str | None:
    for h in headers:
        if str(h).strip().lower() in ("roll", "roll_no", "rollno", "roll no", "id", "student_id", "reg", "reg_no"):
            return h
    return None


# ── Main API ──────────────────────────────────────────────────────────────────

def predict(student_marks: list[dict]) -> dict:
    """
    Single-column analysis (name + marks).
    Returns per-student predictions + class insights.
    """
    return _predict_single(student_marks)


def predict_multi(
    student_marks: list[dict],
    all_rows: list[dict],
    headers: list[str],
) -> dict:
    """
    Multi-column analysis — uses Linear Regression and Logistic Regression.
    `student_marks` is the standard [{name, marks}] list (last numeric col used as target).
    `all_rows` are the full row dicts.
    `headers` is the full header list.
    """
    return _predict_with_sklearn(student_marks, all_rows, headers)


# ── Single-column path ────────────────────────────────────────────────────────

def _predict_single(student_marks: list[dict]) -> dict:
    if not student_marks:
        return {"predictions": [], "class_insights": {}, "lr_available": False, "has_multi_column": False}

    scores = [m["marks"] for m in student_marks]
    mean = statistics.mean(scores)
    stdev = statistics.stdev(scores) if len(scores) > 1 else 0.0

    # K-Means clustering (if enough data)
    centers: list[float] = []
    if len(scores) >= 4:
        try:
            import numpy as np
            from sklearn.cluster import KMeans
            X = np.array(scores).reshape(-1, 1)
            km = KMeans(n_clusters=4, n_init=10, random_state=42)
            km.fit(X)
            centers = [float(c[0]) for c in km.cluster_centers_]
        except Exception:
            pass

    # Logistic Regression for pass/fail probability
    lr_probs: dict[str, float] = {}
    if len(scores) >= 5:
        try:
            import numpy as np
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler
            X = np.array(scores).reshape(-1, 1)
            y = [1 if s >= 40 else 0 for s in scores]
            if len(set(y)) > 1:
                scaler = StandardScaler()
                Xs = scaler.fit_transform(X)
                clf = LogisticRegression(random_state=42, max_iter=500)
                clf.fit(Xs, y)
                proba = clf.predict_proba(Xs)[:, 1]
                for i, m in enumerate(student_marks):
                    lr_probs[m["name"]] = round(float(proba[i]) * 100, 1)
        except Exception:
            pass

    # Build sorted predictions
    sorted_marks = sorted(student_marks, key=lambda m: m["marks"], reverse=True)
    predictions = []
    for rank, m in enumerate(sorted_marks, 1):
        s = m["marks"]
        if centers:
            cluster = _cluster_label_from_center(s, centers)
        else:
            cluster = _zscore_cluster(s, mean, stdev)
        grade = _letter_grade(s)
        predictions.append({
            "name": m["name"],
            "roll_no": m.get("roll_no", ""),
            "marks": s,
            "predicted_grade": grade,
            "cluster": cluster,
            "performance_category": _performance_category(grade, cluster),
            "risk_score": _risk_score(s, mean, stdev),
            "z_score": round((s - mean) / stdev, 2) if stdev > 0 else 0.0,
            "pass_probability": lr_probs.get(m["name"]),
            "predicted_marks": None,
            "rank": rank,
        })

    return _build_result(predictions, scores, lr_available=False, has_multi=False)


# ── Multi-column path (sklearn full pipeline) ─────────────────────────────────

def _predict_with_sklearn(
    student_marks: list[dict],
    all_rows: list[dict],
    headers: list[str],
) -> dict:
    if not student_marks:
        return {"predictions": [], "class_insights": {}, "lr_available": False, "has_multi_column": True}

    # Find numeric columns
    numeric_cols = []
    for h in headers:
        try:
            vals = [float(r[h]) for r in all_rows if r.get(h) is not None and str(r.get(h, "")).strip() != ""]
            if vals:
                numeric_cols.append(h)
        except (TypeError, ValueError):
            pass

    target_col = numeric_cols[-1] if numeric_cols else None
    feature_cols = numeric_cols[:-1] if len(numeric_cols) > 1 else []

    scores = [m["marks"] for m in student_marks]
    mean = statistics.mean(scores)
    stdev = statistics.stdev(scores) if len(scores) > 1 else 0.0

    # K-Means
    centers: list[float] = []
    if len(scores) >= 4:
        try:
            import numpy as np
            from sklearn.cluster import KMeans
            X = np.array(scores).reshape(-1, 1)
            km = KMeans(n_clusters=min(4, len(scores)), n_init=10, random_state=42)
            km.fit(X)
            centers = [float(c[0]) for c in km.cluster_centers_]
        except Exception:
            pass

    # Linear Regression — predict target from feature cols
    lr_preds: dict[str, float] = {}
    lr_available = False
    if feature_cols and target_col and len(all_rows) >= 5:
        try:
            import numpy as np
            from sklearn.linear_model import LinearRegression
            Xf = np.array([[float(r.get(c, 0) or 0) for c in feature_cols] for r in all_rows])
            y = np.array([float(r.get(target_col, 0) or 0) for r in all_rows])
            reg = LinearRegression()
            reg.fit(Xf, y)
            preds = reg.predict(Xf)
            roll_col = _find_roll_col(headers)
            name_col = next((h for h in headers if h.lower() in ("name", "student", "student_name")), headers[0])
            for i, row in enumerate(all_rows):
                name = str(row.get(name_col, f"Student {i+1}")).strip()
                lr_preds[name] = round(float(preds[i]), 1)
            lr_available = True
        except Exception:
            pass

    # Logistic Regression for pass/fail
    lr_probs: dict[str, float] = {}
    if len(scores) >= 5:
        try:
            import numpy as np
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler
            X = np.array(scores).reshape(-1, 1)
            y = [1 if s >= 40 else 0 for s in scores]
            if len(set(y)) > 1:
                scaler = StandardScaler()
                Xs = scaler.fit_transform(X)
                clf = LogisticRegression(random_state=42, max_iter=500)
                clf.fit(Xs, y)
                proba = clf.predict_proba(Xs)[:, 1]
                for i, m in enumerate(student_marks):
                    lr_probs[m["name"]] = round(float(proba[i]) * 100, 1)
        except Exception:
            pass

    sorted_marks = sorted(student_marks, key=lambda m: m["marks"], reverse=True)
    predictions = []
    for rank, m in enumerate(sorted_marks, 1):
        s = m["marks"]
        cluster = _cluster_label_from_center(s, centers) if centers else _zscore_cluster(s, mean, stdev)
        grade = _letter_grade(s)
        predictions.append({
            "name": m["name"],
            "roll_no": m.get("roll_no", ""),
            "marks": s,
            "predicted_grade": grade,
            "cluster": cluster,
            "performance_category": _performance_category(grade, cluster),
            "risk_score": _risk_score(s, mean, stdev),
            "z_score": round((s - mean) / stdev, 2) if stdev > 0 else 0.0,
            "pass_probability": lr_probs.get(m["name"]),
            "predicted_marks": lr_preds.get(m["name"]),
            "rank": rank,
        })

    return _build_result(predictions, scores, lr_available=lr_available, has_multi=len(numeric_cols) > 1)


# ── Shared result builder ─────────────────────────────────────────────────────

def _build_result(predictions: list[dict], scores: list[float], lr_available: bool, has_multi: bool) -> dict:
    mean = statistics.mean(scores)
    stdev = statistics.stdev(scores) if len(scores) > 1 else 0.0
    pass_rate = round(100 * sum(1 for s in scores if s >= 40) / len(scores), 1)

    cluster_counts: dict[str, int] = {}
    for p in predictions:
        cluster_counts[p["cluster"]] = cluster_counts.get(p["cluster"], 0) + 1

    at_risk = [p for p in predictions if p["cluster"] == "At Risk"]
    top = [p for p in predictions if p["cluster"] == "High Performer"]
    failed = [p for p in predictions if p["predicted_grade"] == "F"]
    topper = max(predictions, key=lambda p: p["marks"]) if predictions else None
    lowest = min(predictions, key=lambda p: p["marks"]) if predictions else None

    recommendations: list[str] = []
    if at_risk:
        recommendations.append(
            f"{len(at_risk)} student(s) ({', '.join(p['name'] for p in at_risk[:3])}) "
            f"are critically at risk — consider immediate intervention."
        )
    if pass_rate < 70:
        recommendations.append(
            f"Pass rate is {pass_rate}% — below the 70% benchmark. "
            f"Review teaching strategy and exam difficulty."
        )
    if top:
        recommendations.append(
            f"{len(top)} student(s) are high performers. "
            f"Consider advanced assignments to challenge them further."
        )
    if stdev > 15:
        recommendations.append(
            f"High score variance (σ={stdev:.1f}) indicates inconsistent learning — "
            f"consider differentiated instruction."
        )
    if not recommendations:
        recommendations.append(
            f"Class performance is stable with a mean of {mean:.1f}. Keep up the good work!"
        )

    class_insights = {
        "mean": round(mean, 1),
        "stdev": round(stdev, 1),
        "pass_rate": pass_rate,
        "fail_rate": round(100 - pass_rate, 1),
        "highest": max(scores),
        "lowest": min(scores),
        "cluster_distribution": cluster_counts,
        "at_risk_count": len(at_risk),
        "top_performer_count": len(top),
        "failed_count": len(failed),
        "topper": {"name": topper["name"], "marks": topper["marks"]} if topper else None,
        "lowest_performer": {"name": lowest["name"], "marks": lowest["marks"]} if lowest else None,
        "recommendations": recommendations,
    }

    return {
        "predictions": predictions,
        "class_insights": class_insights,
        "lr_available": lr_available,
        "has_multi_column": has_multi,
    }
