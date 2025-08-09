# Django Codebase — Dual-Schema Setup (Auth & Application)

This project is a Django codebase configured to use **two PostgreSQL schemas** in a single database for clean isolation: one schema for **authorization** and another for the **application domain**. It also ships with a **predefined logger**, a **centralized configuration loader**, and a **predefined (placeholder) SQLAlchemy engine hook** you can extend.

> **Why two schemas?**  
> To keep authentication (users, permissions, sessions, etc.) separate from application data. This can simplify access control, backups, and migrations, and helps reduce blast radius.

---

## Features

- **Predefined logger** with daily file rotation pattern and consistent log format — logs are written under `./logs/`.  
- **Centralized configuration** via `config/config.ini` + `.env` (for secrets like DB credentials).  
- **Custom user model** (`accounts_app.User`) to extend auth fields cleanly.  
- **Two Postgres schemas** in the **same database**:
  - `auth_realm` for Django auth, admin, contenttypes and `accounts_app`.
  - `application_realm` for app data.
- **Database Routers** to ensure reads/writes and migrations target the right schema in the right order.
- **DRF-ready endpoints** (optional) for user CRUD; enable if you plan to use REST APIs.

---

## Project Structure (high level)

```
django_main/
  settings.py
  urls.py
  wsgi.py
accounts_app/
  models.py
  views.py
  serializers.py         # if present
helper/
  configuration.py
  logger_setup.py
config/
  config.ini             # your project-wide (non-secret) config
logs/
  ...                    # created automatically at runtime
```

> Your exact layout may differ slightly; the important files are referenced below.

---

## Requirements

- Python 3.11+
- PostgreSQL 13+ (single database with two schemas: `auth_realm`, `application_realm`)
- Recommended packages (add to `requirements.txt`):
  - `Django>=5.2`
  - `psycopg3`
  - `python-dotenv`
  - `djangorestframework` (only if you use the REST APIs)

---

## Configuration

### 1) Environment variables (`.env`)

Store secrets in `.env` at the project root:

```
db_username=postgres
db_password=postgres
```

> These are used by the configuration loader to avoid committing secrets.

### 2) App config (`config/config.ini`)

Example `config/config.ini`:

```ini
[database_connection]
host = 127.0.0.1
database_name = my_database
```

- The code reads this file to resolve non-secret parameters (like host & db name).
- Secrets (username/password) come from `.env`.

---

## Database Setup

Create **one PostgreSQL database** with **two schemas**:

```sql
CREATE SCHEMA IF NOT EXISTS auth_realm;
CREATE SCHEMA IF NOT EXISTS application_realm;
```

Grant permissions as appropriate to your DB user.

---

## Django Settings — Key Bits

- **Custom user model**: `AUTH_USER_MODEL = "accounts_app.User"`
- **Multiple DBs** in `DATABASES`:
  - `auth_realm` uses `OPTIONS: "-c search_path=auth_realm,public"`
  - `application_realm` uses `OPTIONS: "-c search_path=application_realm,public"`
- **Routers** (order matters):
  ```python
  DATABASE_ROUTERS = [
      "django_main.AuthRouter.AuthRouter",
      "django_main.ApplicationRouter.ApplicationRouter",
  ]
  ```

Make sure your default database points to the same PostgreSQL instance (same NAME/HOST/PORT), since you’re using separate **schemas** not separate databases.

> If you plan to use the **REST API** views, add `'rest_framework'` to `INSTALLED_APPS`.

---

## Migrations (IMPORTANT — run in this order)

Run **exactly** in the order below to ensure auth-related tables land in `auth_realm` first, followed by application tables:

```bash
# 1) Auth & user models
python manage.py migrate --database=auth_realm

# 2) Application models
python manage.py migrate --database=application_realm

# 3) Final sync (for anything un-routed / multi-app dependencies)
python manage.py migrate
```

> If you change routers or add new apps, re-check where their migrations should land.

**Tip:** If you ever need to reset, clear the DB tables/schemas and delete migration files in your apps (except `__init__.py`), then re-run `makemigrations` + the sequence above.

---

## Running Locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Make sure schemas exist in Postgres, and .env + config/config.ini are in place.
python manage.py migrate --database=auth_realm
python manage.py migrate --database=application_realm
python manage.py migrate

# Create an admin user (will go into auth_realm)
python manage.py createsuperuser

python manage.py runserver
```

Navigate to `http://127.0.0.1:8000/`

---

## Logging

- Logs are written into `./logs/` automatically.
- Each logger gets a file named like `<LOGGER_NAME>_YYYYMMDD.log`.
- Default format: `'%(asctime)s - %(levelname)s - [%(module)s] - %(message)s'`

You can create/get loggers per module, e.g.:

```python
from helper.logger_setup import setup_logger
logger = setup_logger("accounts_app")
logger.info("Hello from accounts_app")
```

---

## Configuration Loader

A tiny abstraction lives in `helper/configuration.py` that:

- Verifies `config/config.ini` exists and sections/keys are present.
- Fetches settings via `get_parameter(section, key)`.
- Reads secrets from environment via `get_environmental("db_username")` / `get_environmental("db_password")`.
- Emits clear log messages if anything is missing.

This keeps settings centralized and avoids sprinkling `os.getenv` all over the codebase.

---

## Database Routers (How It Works)

- **AuthRouter** routes apps: `admin`, `contenttypes`, `auth`, and `accounts_app` to `auth_realm` for both reads and writes; it also ensures their **migrations** only run against `auth_realm`.
- **ApplicationRouter** routes other application reads/writes to `application_realm`.

> Router order matters — keep `AuthRouter` *before* `ApplicationRouter` in `DATABASE_ROUTERS`.

---

## REST API (Optional)

If you enable DRF, you can use the included user endpoints:

- `POST /api/users/` — create a user
- `GET /api/users/me` — get current user
- `PUT /api/users/me` — update current user (partial)
- `DELETE /api/users/me` — delete current user

Make sure to:

1. `pip install djangorestframework`
2. Add `'rest_framework'` to `INSTALLED_APPS`.
3. Wire URLs accordingly.

---

## Custom User Model

The custom user model extends `AbstractUser` and makes `email` unique, while adding optional profile fields. Update forms/serializers/admin as needed and always reference the user model via `settings.AUTH_USER_MODEL` to avoid circular imports.

---

## Notes & Gotchas

- **Order of migrations** is critical — follow the sequence above.
- **Routers** only guide Django where to read/write/migrate. Your Postgres **schemas must exist** upfront.
- Using a custom user model? Define it **before the first migration** (already set here).
- If you introduce new apps, decide which schema they belong to and adjust routers accordingly.

---

## Next Steps 

- Add more Usermanagement API