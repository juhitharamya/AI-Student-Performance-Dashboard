"""
ML service — sklearn-backed student performance analysis.

Algorithms used:
  • K-Means (n=4)          — cluster students into performance tiers
  • Linear Regression      — predict total marks from multiple subject cols
  • Logistic Regression    — pass/fail probability per student
  • Z-score fallback       — used for small samples (n < 4)
"""

from __future__ import annotations
import logging
import statistics
from typing import Any

logger = logging.getLogger(__name__)

# Column aliases that should NEVER be used as ML features
_NON_FEATURE_ALIASES = {
    "name", "student", "student_name", "student name", "sname",
    "roll", "roll_no", "rollno", "roll no", "reg", "reg_no", "id",
    "student_id", "regno", "roll number", "sno", "s.no", "serial",
}


# ── Grade/category helpers ────────────────────────────────────────────────────

def _letter_grade(score: float) -> str:
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 55: return "C"
    if score >= 40: return "D"
    return "F"


def _performance_category(grade: str, cluster: str) -> str:
    if grade == "A":                     return "Excellent"
    if grade == "B":                     return "Good"
    if grade in ("C", "D"):              return "Average"
    if cluster == "At Risk" or grade == "F": return "At Risk"
    return "Average"


def _cluster_label_from_center(score: float, centers: list[float]) -> str:
    """Map a score to a cluster label based on sorted K-Means centroids."""
    sorted_c = sorted(centers)
    idx = min(range(len(sorted_c)), key=lambda i: abs(sorted_c[i] - score))
    labels = ["At Risk", "Below Average", "Above Average", "High Performer"]
    return labels[min(idx, len(labels) - 1)]


def _zscore_cluster(score: float, mean: float, stdev: float) -> str:
    z = (score - mean) / stdev if stdev > 0 else 0
    if z > 1.0:  return "High Performer"
    if z > 0.0:  return "Above Average"
    if z > -1.0: return "Below Average"
    return "At Risk"


def _risk_score(score: float, mean: float, stdev: float) -> int:
    z = (score - mean) / stdev if stdev > 0 else 0
    return max(0, min(100, int(50 - z * 20)))


def _is_non_feature(h: str) -> bool:
    return str(h).strip().lower() in _NON_FEATURE_ALIASES


# ── Main API ──────────────────────────────────────────────────────────────────

def predict(student_marks: list[dict]) -> dict:
    """Single-column analysis (name + marks). Returns per-student predictions + class insights."""
    return _predict_single(student_marks)


def predict_multi(
    student_marks: list[dict],
    all_rows: list[dict],
    headers: list[str],
) -> dict:
    """
    Multi-column analysis — uses Linear Regression and Logistic Regression.
    `student_marks` is [{name, marks}] list used for clustering/logistic.
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

    # K-Means clustering
    centers: list[float] = []
    if len(scores) >= 4:
        try:
            import numpy as np
            from sklearn.cluster import KMeans
            X = np.array(scores, dtype=float).reshape(-1, 1)
            n_clusters = min(4, len(scores))
            km = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
            km.fit(X)
            centers = [float(c[0]) for c in km.cluster_centers_]
            logger.debug("KMeans centers: %s", centers)
        except Exception as e:
            logger.warning("KMeans failed, using z-score fallback: %s", e)

    # Logistic Regression for pass/fail probability
    lr_probs: dict[str, float] = {}
    if len(scores) >= 5:
        try:
            import numpy as np
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler
            X = np.array(scores, dtype=float).reshape(-1, 1)
            y = [1 if s >= 40 else 0 for s in scores]
            if len(set(y)) > 1:  # need both classes
                scaler = StandardScaler()
                Xs = scaler.fit_transform(X)
                clf = LogisticRegression(random_state=42, max_iter=500)
                clf.fit(Xs, y)
                proba = clf.predict_proba(Xs)[:, 1]
                for i, m in enumerate(student_marks):
                    lr_probs[m["name"]] = round(float(proba[i]) * 100, 1)
                logger.debug("Logistic Regression pass probabilities computed for %d students", len(lr_probs))
            else:
                logger.debug("LogReg skipped — all students in same pass/fail class")
        except Exception as e:
            logger.warning("LogisticRegression failed: %s", e)

    # Build predictions sorted by marks desc
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

    # Identify numeric feature columns — exclude name/roll/id cols
    feature_cols = []
    target_col = None
    for h in headers:
        if _is_non_feature(h):
            continue
        try:
            vals = [
                float(str(r.get(h, "")).replace(",", ""))
                for r in all_rows
                if r.get(h) is not None and str(r.get(h, "")).strip() != ""
            ]
            if len(vals) >= max(3, len(all_rows) * 0.5):  # column must be ≥50% populated
                feature_cols.append(h)
        except (TypeError, ValueError):
            pass

    # Last numeric column = target (total/final), rest = features
    target_col = feature_cols[-1] if feature_cols else None
    input_cols = feature_cols[:-1] if len(feature_cols) > 1 else []

    scores = [m["marks"] for m in student_marks]
    mean = statistics.mean(scores)
    stdev = statistics.stdev(scores) if len(scores) > 1 else 0.0

    # K-Means on final marks
    centers: list[float] = []
    if len(scores) >= 4:
        try:
            import numpy as np
            from sklearn.cluster import KMeans
            X = np.array(scores, dtype=float).reshape(-1, 1)
            n_clusters = min(4, len(scores))
            km = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
            km.fit(X)
            centers = [float(c[0]) for c in km.cluster_centers_]
        except Exception as e:
            logger.warning("KMeans failed in multi-col path: %s", e)

    # Linear Regression — predict target from input feature columns
    lr_preds: dict[str, float] = {}
    lr_available = False
    if input_cols and target_col and len(all_rows) >= 5:
        try:
            import numpy as np
            from sklearn.linear_model import LinearRegression

            def safe_float(v: Any) -> float:
                try:
                    return float(str(v).replace(",", ""))
                except (TypeError, ValueError):
                    return 0.0

            Xf = np.array([[safe_float(r.get(c)) for c in input_cols] for r in all_rows])
            y = np.array([safe_float(r.get(target_col)) for r in all_rows])

            reg = LinearRegression()
            reg.fit(Xf, y)
            preds = reg.predict(Xf)

            # Map prediction back to student name
            name_col = next(
                (h for h in headers if str(h).strip().lower() in
                 ("name", "student", "student_name", "student name")),
                headers[0],
            )
            for i, row in enumerate(all_rows):
                name = str(row.get(name_col, f"Student {i+1}")).strip()
                lr_preds[name] = round(float(preds[i]), 1)

            lr_available = True
            logger.debug(
                "LinearRegression fitted. Features: %s → Target: %s. R² on train: %.3f",
                input_cols, target_col, reg.score(Xf, y)
            )
        except Exception as e:
            logger.warning("LinearRegression failed: %s", e)

    # Logistic Regression for pass probability
    lr_probs: dict[str, float] = {}
    if len(scores) >= 5:
        try:
            import numpy as np
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler
            X = np.array(scores, dtype=float).reshape(-1, 1)
            y = [1 if s >= 40 else 0 for s in scores]
            if len(set(y)) > 1:
                scaler = StandardScaler()
                Xs = scaler.fit_transform(X)
                clf = LogisticRegression(random_state=42, max_iter=500)
                clf.fit(Xs, y)
                proba = clf.predict_proba(Xs)[:, 1]
                for i, m in enumerate(student_marks):
                    lr_probs[m["name"]] = round(float(proba[i]) * 100, 1)
        except Exception as e:
            logger.warning("LogisticRegression failed in multi-col path: %s", e)

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

    return _build_result(predictions, scores, lr_available=lr_available, has_multi=len(feature_cols) > 1)


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
        names = ", ".join(p["name"] for p in at_risk[:3])
        extra = f" (+{len(at_risk) - 3} more)" if len(at_risk) > 3 else ""
        recommendations.append(
            f"{len(at_risk)} student(s) ({names}{extra}) are critically at risk — consider immediate intervention."
        )
    if pass_rate < 70:
        recommendations.append(
            f"Pass rate is {pass_rate}% — below the 70% benchmark. "
            f"Review teaching strategy and exam difficulty."
        )
    if top:
        recommendations.append(
            f"{len(top)} high-performer(s) identified. "
            f"Consider advanced assignments to maintain their engagement."
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
