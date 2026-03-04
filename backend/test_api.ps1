$BASE = "http://localhost:8000/api/v1"
$pass = $true

function Test-Endpoint {
    param($Label, $Status, $Expected, $Body)
    if ($Status -eq $Expected) {
        Write-Host "[PASS] $Label" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] $Label (got $Status, expected $Expected)" -ForegroundColor Red
        $script:pass = $false
    }
}

function Invoke-API {
    param($Method, $Url, $Headers, $Body, $Form)
    try {
        if ($Form) {
            $response = Invoke-WebRequest -Method $Method -Uri $Url -Headers $Headers -Form $Form -ErrorAction Stop
        } elseif ($Body) {
            $response = Invoke-WebRequest -Method $Method -Uri $Url -Headers $Headers -ContentType "application/json" -Body $Body -ErrorAction Stop
        } else {
            $response = Invoke-WebRequest -Method $Method -Uri $Url -Headers $Headers -ErrorAction Stop
        }
        return $response
    } catch {
        return $_.Exception.Response
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  AI Student Performance Dashboard API Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# ── Health Check ─────────────────────────────────────────────────────────────
Write-Host "--- Health ---" -ForegroundColor Yellow
$r = Invoke-WebRequest -Uri "$BASE/../health" -ErrorAction Stop
Test-Endpoint "GET /health" $r.StatusCode 200
Write-Host "  Response: $($r.Content)"

# ── Faculty Login ─────────────────────────────────────────────────────────────
Write-Host "`n--- Authentication ---" -ForegroundColor Yellow
$body = '{"email":"sarah@university.edu","password":"faculty123","role":"faculty"}'
$r = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop
Test-Endpoint "POST /auth/login (faculty)" $r.StatusCode 200
$data = $r.Content | ConvertFrom-Json
$FACULTY_TOKEN = $data.access_token
Write-Host "  Name: $($data.name), Role: $($data.role)"

# ── Auth Me ───────────────────────────────────────────────────────────────────
$fHeaders = @{Authorization = "Bearer $FACULTY_TOKEN"}
$r = Invoke-WebRequest -Uri "$BASE/auth/me" -Headers $fHeaders -ErrorAction Stop
Test-Endpoint "GET /auth/me" $r.StatusCode 200
$me = $r.Content | ConvertFrom-Json
Write-Host "  User: $($me.name), Role: $($me.role), Email: $($me.email)"

# ── Wrong password (negative test) ───────────────────────────────────────────
$body2 = '{"email":"sarah@university.edu","password":"WRONG","role":"faculty"}'
try {
    $r2 = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -ContentType "application/json" -Body $body2 -ErrorAction Stop
    Test-Endpoint "POST /auth/login (bad password)" $r2.StatusCode 401
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Test-Endpoint "POST /auth/login (bad password)" $code 401
}

# ── Faculty Stats ─────────────────────────────────────────────────────────────
Write-Host "`n--- Faculty Endpoints ---" -ForegroundColor Yellow
$r = Invoke-WebRequest -Uri "$BASE/faculty/stats" -Headers $fHeaders -ErrorAction Stop
Test-Endpoint "GET /faculty/stats" $r.StatusCode 200
$stats = $r.Content | ConvertFrom-Json
Write-Host "  Students: $($stats.total_students), Avg: $($stats.avg_performance)%, Pass: $($stats.pass_rate)%"

# ── Faculty Uploads List ──────────────────────────────────────────────────────
$r = Invoke-WebRequest -Uri "$BASE/faculty/uploads" -Headers $fHeaders -ErrorAction Stop
Test-Endpoint "GET /faculty/uploads" $r.StatusCode 200
$uploads = $r.Content | ConvertFrom-Json
Write-Host "  Files count: $($uploads.files.Count)"
$FIRST_ID = $uploads.files[0].id

# ── Upload a CSV file ────────────────────────────────────────────────────────
$csvContent = "name,marks`nAlice,88`nBob,76`nCharlie,91"
$tmpFile = [System.IO.Path]::GetTempFileName() + ".csv"
$csvContent | Out-File -FilePath $tmpFile -Encoding utf8

$form = @{
    file = Get-Item $tmpFile
    subject = "Data Structures"
}
$r = Invoke-WebRequest -Uri "$BASE/faculty/uploads" -Method POST -Headers $fHeaders -Form $form -ErrorAction Stop
Test-Endpoint "POST /faculty/uploads (upload CSV)" $r.StatusCode 201
$newFile = $r.Content | ConvertFrom-Json
Write-Host "  Uploaded: id=$($newFile.id), name=$($newFile.name), subject=$($newFile.subject)"
$NEW_FILE_ID = $newFile.id

Remove-Item $tmpFile -Force

# ── Delete the uploaded file ──────────────────────────────────────────────────
$r = Invoke-WebRequest -Uri "$BASE/faculty/uploads/$NEW_FILE_ID" -Method DELETE -Headers $fHeaders -ErrorAction Stop
Test-Endpoint "DELETE /faculty/uploads/{id}" $r.StatusCode 200
$del = $r.Content | ConvertFrom-Json
Write-Host "  Delete result: $($del.message)"

# ── Faculty Analytics ─────────────────────────────────────────────────────────
$r = Invoke-WebRequest -Uri "$BASE/faculty/analytics" -Headers $fHeaders -ErrorAction Stop
Test-Endpoint "GET /faculty/analytics" $r.StatusCode 200
$an = $r.Content | ConvertFrom-Json
Write-Host "  student_marks count: $($an.student_marks.Count)"
Write-Host "  performance_trend count: $($an.performance_trend.Count)"
Write-Host "  grade_distribution count: $($an.grade_distribution.Count)"

# ── Analytics with filters ────────────────────────────────────────────────────
$r = Invoke-WebRequest -Uri "$BASE/faculty/analytics?department=Computer Science&year=3rd Year" -Headers $fHeaders -ErrorAction Stop
Test-Endpoint "GET /faculty/analytics?filters" $r.StatusCode 200

# ── Faculty Average ───────────────────────────────────────────────────────────
$avgBody = "{`"file_ids`": [`"$FIRST_ID`", `"2`"]}"
$r = Invoke-WebRequest -Uri "$BASE/faculty/average" -Method POST -Headers $fHeaders -ContentType "application/json" -Body $avgBody -ErrorAction Stop
Test-Endpoint "POST /faculty/average" $r.StatusCode 200
$avg = $r.Content | ConvertFrom-Json
Write-Host "  avg_score=$($avg.avg_score)%, pass_rate=$($avg.pass_rate)%, highest=$($avg.highest_score)"

# ── Filter Options ────────────────────────────────────────────────────────────
$r = Invoke-WebRequest -Uri "$BASE/faculty/filter-options" -Headers $fHeaders -ErrorAction Stop
Test-Endpoint "GET /faculty/filter-options" $r.StatusCode 200
$fo = $r.Content | ConvertFrom-Json
Write-Host "  Departments: $($fo.departments -join ', ')"

# ── Student Login ─────────────────────────────────────────────────────────────
Write-Host "`n--- Student Endpoints ---" -ForegroundColor Yellow
$sBody = '{"email":"alex@university.edu","password":"student123","role":"student"}'
$r = Invoke-WebRequest -Uri "$BASE/auth/login" -Method POST -ContentType "application/json" -Body $sBody -ErrorAction Stop
Test-Endpoint "POST /auth/login (student)" $r.StatusCode 200
$sData = $r.Content | ConvertFrom-Json
$STUDENT_TOKEN = $sData.access_token
$sHeaders = @{Authorization = "Bearer $STUDENT_TOKEN"}
Write-Host "  Student: $($sData.name)"

# ── Student Dashboard ─────────────────────────────────────────────────────────
$r = Invoke-WebRequest -Uri "$BASE/student/dashboard" -Headers $sHeaders -ErrorAction Stop
Test-Endpoint "GET /student/dashboard" $r.StatusCode 200
$dash = $r.Content | ConvertFrom-Json
Write-Host "  Name: $($dash.profile.name), CGPA: $($dash.profile.cgpa)"
Write-Host "  Subjects: $($dash.subject_performance.Count)"
Write-Host "  Activity items: $($dash.recent_activity.Count)"

# ── Role protection test (student tries to hit faculty route) ─────────────────
Write-Host "`n--- Auth Guards ---" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "$BASE/faculty/stats" -Headers $sHeaders -ErrorAction Stop
    Test-Endpoint "Student blocked from /faculty/stats" $r.StatusCode 403
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Test-Endpoint "Student blocked from /faculty/stats" $code 403
}

try {
    $r = Invoke-WebRequest -Uri "$BASE/student/dashboard" -Headers $fHeaders -ErrorAction Stop
    Test-Endpoint "Faculty blocked from /student/dashboard" $r.StatusCode 403
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Test-Endpoint "Faculty blocked from /student/dashboard" $code 403
}

try {
    $r = Invoke-WebRequest -Uri "$BASE/faculty/stats" -ErrorAction Stop
    Test-Endpoint "Unauthenticated blocked from /faculty/stats" $r.StatusCode 401
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Test-Endpoint "Unauthenticated blocked from /faculty/stats" $code 401
}

# ── Logout ────────────────────────────────────────────────────────────────────
Write-Host "`n--- Logout ---" -ForegroundColor Yellow
$r = Invoke-WebRequest -Uri "$BASE/auth/logout" -Method POST -Headers $fHeaders -ErrorAction Stop
Test-Endpoint "POST /auth/logout" $r.StatusCode 200

# ── Summary ──────────────────────────────────────────────────────────────────
Write-Host "`n========================================" -ForegroundColor Cyan
if ($pass) {
    Write-Host "  ALL TESTS PASSED " -ForegroundColor Green
} else {
    Write-Host "  SOME TESTS FAILED" -ForegroundColor Red
}
Write-Host "========================================`n" -ForegroundColor Cyan
