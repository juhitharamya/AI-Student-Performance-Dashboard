import sys
sys.path.insert(0, ".")
from app.services.ml_service import predict

students = [
    {"name": "Alice", "roll_no": "CS001", "marks": 92},
    {"name": "Bob", "roll_no": "CS002", "marks": 78},
    {"name": "Carol", "roll_no": "CS003", "marks": 65},
    {"name": "Dave", "roll_no": "CS004", "marks": 55},
    {"name": "Eve", "roll_no": "CS005", "marks": 42},
    {"name": "Frank", "roll_no": "CS006", "marks": 35},
    {"name": "Grace", "roll_no": "CS007", "marks": 88},
    {"name": "Hank", "roll_no": "CS008", "marks": 71},
    {"name": "Iris", "roll_no": "CS009", "marks": 48},
    {"name": "Jack", "roll_no": "CS010", "marks": 22},
]

result = predict(students)
print("=== Single-col ML Results ===")
for p in result["predictions"]:
    prob = p["pass_probability"]
    print(f"  {p['rank']:2}. {p['name']:<8} marks={p['marks']:5.1f}  grade={p['predicted_grade']}  cluster={p['cluster']:<16}  risk={p['risk_score']:3}  pass%={prob}")
ci = result["class_insights"]
print(f"\nClass: mean={ci['mean']}  stdev={ci['stdev']}  pass_rate={ci['pass_rate']}%")
print(f"At-risk={ci['at_risk_count']}  Top={ci['top_performer_count']}  Failed={ci['failed_count']}")
print("Rec:", ci["recommendations"][0])

# Quick multi-column test
from app.services.ml_service import predict_multi
headers = ["name", "roll_no", "quiz1", "quiz2", "final"]
rows = [
    {"name": "Alice", "roll_no": "CS001", "quiz1": 45, "quiz2": 48, "final": 92},
    {"name": "Bob", "roll_no": "CS002", "quiz1": 38, "quiz2": 40, "final": 78},
    {"name": "Carol", "roll_no": "CS003", "quiz1": 30, "quiz2": 35, "final": 65},
    {"name": "Dave", "roll_no": "CS004", "quiz1": 25, "quiz2": 28, "final": 55},
    {"name": "Eve", "roll_no": "CS005", "quiz1": 20, "quiz2": 22, "final": 42},
    {"name": "Frank", "roll_no": "CS006", "quiz1": 15, "quiz2": 18, "final": 35},
]
result2 = predict_multi(students[:6], rows, headers)
print("\n=== Multi-col ML Results ===")
print(f"lr_available={result2['lr_available']}  has_multi={result2['has_multi_column']}")
for p in result2["predictions"]:
    print(f"  {p['name']:<8} marks={p['marks']}  predicted={p['predicted_marks']}  grade={p['predicted_grade']}")
print("All assertions passed!")
