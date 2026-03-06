# Database (SQLite / Postgres / Supabase)

## Default (dev): SQLite
- File: `database/sqlite/database.db`
- Leave `DATABASE_URL` unset to use SQLite.

## Local Postgres (Docker)
1) Start Postgres: `cd backend; docker compose up -d`
2) Set `DATABASE_URL` in `backend/.env`:
   - `postgresql+psycopg://postgres:postgres@localhost:5432/student_dashboard`
3) Migrate: `alembic -c database/alembic.ini upgrade head`

## Supabase (hosted Postgres)
1) Create a Supabase project.
2) Copy the **Postgres connection string** from Supabase (Project Settings → Database).
3) Put it in `backend/.env` as `DATABASE_URL`.

Recommended format:
- `postgresql+psycopg://postgres:<PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres?sslmode=require`

Then run migrations:
- `alembic -c database/alembic.ini upgrade head`

To view data:
- Supabase **Table Editor** / **SQL Editor**, or connect with `psql` using the same connection string.

