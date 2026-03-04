import sys; sys.path.insert(0, '.')
from app.services.faculty_service import _extract_marks
from app.services.ml_service import predict_multi

rows = [
    {'S.No': 1, 'Roll No': '23Q91A6601', 'Student Name': 'Akhila Reddy',    'Assignment': 16, 'Descriptive': 23, 'Bit (20)': 15, 'PPT (30)': 24, 'Total (100)': 78},
    {'S.No': 2, 'Roll No': '23Q91A6602', 'Student Name': 'Bhavya Sri',      'Assignment': 17, 'Descriptive': 24, 'Bit (20)': 16, 'PPT (30)': 25, 'Total (100)': 82},
    {'S.No': 3, 'Roll No': '23Q91A6603', 'Student Name': 'Charan Kumar',    'Assignment': 18, 'Descriptive': 25, 'Bit (20)': 17, 'PPT (30)': 26, 'Total (100)': 86},
    {'S.No': 4, 'Roll No': '23Q91A6604', 'Student Name': 'Divya Teja',      'Assignment': 19, 'Descriptive': 26, 'Bit (20)': 18, 'PPT (30)': 27, 'Total (100)': 90},
    {'S.No': 5, 'Roll No': '23Q91A6605', 'Student Name': 'Eshwar Rao',      'Assignment': 15, 'Descriptive': 27, 'Bit (20)': 14, 'PPT (30)': 28, 'Total (100)': 84},
    {'S.No': 6, 'Roll No': '23Q91A6606', 'Student Name': 'Farhana Begum',   'Assignment': 16, 'Descriptive': 28, 'Bit (20)': 15, 'PPT (30)': 29, 'Total (100)': 88},
    {'S.No': 7, 'Roll No': '23Q91A6607', 'Student Name': 'Goutham Krishna', 'Assignment': 17, 'Descriptive': 29, 'Bit (20)': 16, 'PPT (30)': 23, 'Total (100)': 85},
    {'S.No': 8, 'Roll No': '23Q91A6608', 'Student Name': 'Harika Devi',     'Assignment': 18, 'Descriptive': 22, 'Bit (20)': 17, 'PPT (30)': 24, 'Total (100)': 81},
    {'S.No': 9, 'Roll No': '23Q91A6609', 'Student Name': 'Irfan Ali',       'Assignment': 19, 'Descriptive': 23, 'Bit (20)': 18, 'PPT (30)': 25, 'Total (100)': 85},
    {'S.No':10, 'Roll No': '23Q91A6610', 'Student Name': 'Jyothi Lakshmi',  'Assignment': 15, 'Descriptive': 24, 'Bit (20)': 14, 'PPT (30)': 26, 'Total (100)': 79},
]
headers = list(rows[0].keys())
student_marks = _extract_marks(rows)
result = predict_multi(student_marks, rows, headers)

print(f'has_multi_column={result["has_multi_column"]}')
print(f'lr_available={result["lr_available"]}')
print('PREDICTIONS:')
for p in result['predictions']:
    print(f"{p['rank']}. {p['name']} - marks={p['marks']} pred={p['predicted_marks']} grade={p['predicted_grade']} cluster={p['cluster']} risk={p['risk_score']}")
