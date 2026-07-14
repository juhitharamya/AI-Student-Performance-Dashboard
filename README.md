# AI Student Performance Dashboard

An intelligent, full-stack student performance tracking and predictive analytics system designed for academic institutions. The application parses student records, generates rich visual insights, and uses machine learning to identify at-risk students and predict academic grades.

---

## 🌟 Key Features
*   **Faculty Dashboard:** KPI cards for average performance, pass rates, student count, and document uploads.
*   **AI Performance Predictor:** A machine learning model (Scikit-Learn) that predicts student grades, pass probabilities, and risk categories based on mid-term marks and historical performance.
*   **File Upload & Parsing:** Support for Excel spreadsheets (`.xlsx`) and PDF transcripts (`.pdf`) using python parsing engines (`openpyxl` & `pdfplumber`).
*   **Interactive Visual Analytics:** Grade distributions (pie charts), section comparisons (bar charts), and monthly class averages (line charts) built with **Recharts**.
*   **Student View:** Individual dashboards with attendance percentages, CGPA tracking, class rankings, and radar charts comparing personal scores to the class average.
*   **Secure Authentication:** Role-based access control (Admin, Faculty, Student) secured via JWT tokens.

---

## 🛠️ Technology Stack (FART Stack)
*   **Frontend:** React (v19), Vite, TypeScript, Tailwind CSS, Recharts, Framer Motion
*   **Backend:** Python 3.12+, FastAPI, Uvicorn, SQLAlchemy, Pandas, NumPy, Scikit-Learn
*   **Database:** PostgreSQL (Supabase) in production, SQLite for local fallback
*   **Deployment:** Vercel (Frontend & Serverless Backend Functions)

---

## 🚀 How to Run Locally

### 1. Install Frontend Dependencies
```bash
npm run install:frontend
```

### 2. Configure Environment variables
Create a `.env` file inside the `backend/` directory:
```env
DATABASE_URL=sqlite:///database.db
SECRET_KEY=your-secret-key
```

### 3. Start Development Servers
Run the single root orchestrator command to launch both the React frontend and FastAPI backend:
```bash
npm run dev
```
*   Frontend: `http://localhost:5173`
*   Backend API Docs: `http://localhost:8000/docs`

---

## ☁️ Deployment on Vercel
The repository is pre-configured to build and run 100% on Vercel as a single application:

1.  **Add Database Columns (Supabase SQL Editor):**
    ```sql
    ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS file_data TEXT;
    ALTER TABLE student_list_files ADD COLUMN IF NOT EXISTS file_data TEXT;
    ```
2.  **Push your project to GitHub.**
3.  **Import to Vercel:** Set framework preset to **Other**, Root Directory to `/`, Build Command to `npm run build`, and Output Directory to `frontend/dist`.
4.  **Set Environment Variables:** Add `DATABASE_URL` (Supabase Postgres URI) and `SECRET_KEY`.