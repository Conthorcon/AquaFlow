# Deploy the web application to Vercel

Only app.py runs on Vercel. Run ai_server.py separately with HTTPS and the same AI_API_KEY. See ai-server.md.

## 1. Database and secrets

Create a PostgreSQL database. Prefer the provider's pooled connection URL for serverless hosting. Install web dependencies locally:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require"
$env:SECRET_KEY="replace-with-a-long-random-secret"
```

postgres:// and postgresql:// URLs are normalized to the psycopg driver. Passwords containing reserved URL characters must be URL-encoded. Do not commit credentials. `.env.example` is documentation only; the app does not load `.env` automatically.

## 2. Initialize the target database once

```powershell
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app create-admin
```

The second command prompts for username and password (minimum 12 characters). It never replaces an existing user. No default admin is created on startup. Existing local users remain unchanged.

`init-db` creates missing tables; it does not alter existing schemas or transfer SQLite records. The PostgreSQL database starts empty. Back up and migrate existing data separately if needed; do not delete the SQLite file. Importing app.py never runs schema creation or seeding.

## 3. Vercel project

Push the source to GitHub and import the repository in Vercel. Choose the root containing app.py and requirements.txt. Let Vercel detect Flask. The checked-in vercel.json sets the build command and function duration; do not set the build command to python app.py.

Set these Environment Variables in Vercel for each intended environment:

| Variable | Value |
| --- | --- |
| DATABASE_URL | PostgreSQL connection URL |
| SECRET_KEY | Stable random secret for sessions |
| AI_SERVER_URL | Public HTTPS URL of the separate AI server |
| AI_API_KEY | Same secret as on the AI server |
| AI_TIMEOUT_SECONDS | 180 |

Use a separate database for Preview if previews should not modify production data. Redeploy after changing variables. Vercel supplies VERCEL=1; the app then refuses local SQLite or a missing SECRET_KEY and enables secure session cookies.

The build runs build_vercel.py, copying web/static into public/static. Templates stay in web/templates and existing /static URLs stay valid. Do not manually maintain a second copy of assets. .vercelignore excludes models, AI source, local databases and environments; requirements.txt contains only web dependencies. Function duration is 240 seconds; verify the project supports that value. Uploads are still subject to Vercel request-size limits even if the AI server accepts larger files.

## 4. Verify

Check /login, login with the account created above, then test /sale, dashboard charts, CSV import, OCR and chatbot. AI_SERVER_URL must not be localhost on Vercel. AI timeout does not cancel an inference already running on the other server.

The date helper in src/database/date_sql.py compiles to SQLite strftime locally and PostgreSQL to_char in deployment. It deliberately preserves the old +7-hour display offset; historical naive timestamps are not converted. Review timezone conventions before migrating historical data from machines in different timezones. Chatbot still returns SQLite-oriented SQL text; it does not execute SQL against PostgreSQL.

## Local development

Unset DATABASE_URL to use the existing SQLite database. For a new local database, run init-db and create-admin first. Set a stable local SECRET_KEY to keep sessions across restarts.

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --port 4849 --no-reload
.\.venv\Scripts\python.exe -m unittest evaluation.test_deployment -v
.\.venv\Scripts\python.exe -m unittest evaluation.chatbot.test_ai_boundary -v
```

Deployment tests use an isolated in-memory SQLite database and compile PostgreSQL SQL. They do not replace integration testing against the actual PostgreSQL service.

Reference: https://vercel.com/docs/frameworks/backend/flask
