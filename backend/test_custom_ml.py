"""Validation script for custom Machine Learning algorithms."""

import numpy as np
from app.ml import KMeans, LinearRegression, LogisticRegression
from app.services.ml_service import predict, predict_multi

def test_kmeans():
    print("--- Testing Custom K-Means ---")
    # Synthetic marks
    X = np.array([30, 35, 45, 80, 85, 90, 55, 60, 65]).reshape(-1, 1)
    km = KMeans(n_clusters=3)
    km.fit(X)
    print("Centroids computed:")
    print(km.cluster_centers_)
    print("Labels computed for students:")
    print(km.labels_)
    print("Inertia:", km.inertia_)
    assert km.cluster_centers_ is not None
    assert len(km.labels_) == len(X)
    print("K-Means PASS.\n")

def test_linear_regression():
    print("--- Testing Custom Linear Regression ---")
    # X: [Midterm_1, Midterm_2]
    # y: Final marks (Midterm_1 * 0.4 + Midterm_2 * 0.6)
    X = np.array([
        [50, 60],
        [80, 90],
        [40, 30],
        [90, 95],
        [70, 80]
    ])
    y = np.array([56.0, 86.0, 34.0, 93.0, 76.0])
    
    lr = LinearRegression()
    lr.fit(X, y)
    print("Intercept (bias):", lr.intercept_)
    print("Weights:", lr.weights_)
    print("R^2 score:", lr.score(X, y))
    
    # Test prediction
    test_X = np.array([[60, 70]])
    pred = lr.predict(test_X)
    print(f"Prediction for input [60, 70] (expected 66.0): {pred[0]:.2f}")
    assert abs(pred[0] - 66.0) < 0.1
    print("Linear Regression PASS.\n")

def test_logistic_regression():
    print("--- Testing Custom Logistic Regression ---")
    # X: Midterm marks (0-100)
    # y: Pass/Fail (>=40 is Pass (1), else Fail (0))
    X = np.array([20, 25, 30, 35, 50, 70, 85, 90]).reshape(-1, 1)
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    
    clf = LogisticRegression(learning_rate=0.1, max_iter=2000)
    clf.fit(X, y)
    print("Weights after gradient descent:", clf.weights)
    print("Intercept after gradient descent:", clf.intercept)
    
    # Check predictions
    probs = clf.predict_proba(X)
    print("Probabilities:")
    for score, prob in zip(X.flatten(), probs):
        print(f"  Score: {score} -> Pass Probability: {prob * 100:.2f}%")
    
    assert probs[0] < 0.5  # Low score should fail
    assert probs[-1] > 0.5  # High score should pass
    print("Logistic Regression PASS.\n")

def test_ml_service_integration():
    print("--- Testing ml_service Integration ---")
    students = [
        {"name": "Alice", "marks": 85.0},
        {"name": "Bob", "marks": 35.0},
        {"name": "Charlie", "marks": 60.0},
        {"name": "David", "marks": 92.0},
        {"name": "Eva", "marks": 52.0}
    ]
    res = predict(students)
    print("Single column service predictions:")
    for p in res["predictions"]:
        print(f"  {p['name']}: predicted_grade={p['predicted_grade']} cluster={p['cluster']} risk={p['risk_score']} prob={p['pass_probability']}%")
    
    # Multi column service predictions
    rows = [
        {"name": "Alice", "Midterm": 80, "Endterm": 85},
        {"name": "Bob", "Midterm": 30, "Endterm": 35},
        {"name": "Charlie", "Midterm": 55, "Endterm": 60},
        {"name": "David", "Midterm": 90, "Endterm": 92},
        {"name": "Eva", "Midterm": 50, "Endterm": 52}
    ]
    res_multi = predict_multi(students, rows, ["name", "Midterm", "Endterm"])
    print("Multi column service predictions:")
    for p in res_multi["predictions"]:
         print(f"  {p['name']}: predicted_marks={p['predicted_marks']} grade={p['predicted_grade']} cluster={p['cluster']}")
    
    print("ml_service Integration PASS.\n")

if __name__ == "__main__":
    test_kmeans()
    test_linear_regression()
    test_logistic_regression()
    test_ml_service_integration()
    print("ALL ML TESTS PASSED SUCCESSFULLY!")
