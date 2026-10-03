# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

IU Campus Resource Hub: a Flask + SQLite server-rendered app (Jinja2, Bootstrap 5) for booking campus resources. Roles are `student`, `staff`, `admin`. Includes an AI concierge ("Crimson") backed by Google Gemini.

## Commands

```bash
pip install -r requirements.txt
cp .env.example .env              # app runs without .env using Config defaults
python app.py                     # http://localhost:5000

python tests/run_tests.py         # full suite, verbose, with coverage (writes htmlcov/)
python -m pytest tests -q         # full suite, no coverage
python -m pytest tests/test_booking_service.py::test_name -v   # single test
python init_db.py                 # create schema + default admin in DATABASE_PATH
```

There is no linter or formatter configured.

## Architecture

Layered, all under `src/`, wired together in `app.py`:

- `controllers/` — one Flask blueprint per feature (`auth`, `resources`, `bookings`, `search`, `messages`, `reviews`, `admin`, `ai_concierge`), all registered in `app.py`. Templates live in `src/views/<feature>/` (Flask `template_folder='src/views'`, `static_folder='src/static'`).
- `services/` — business logic. Services return dicts, not exceptions: `{'success': True, 'data': {...}}` or `{'success': False, 'error': '...'}`. Controllers branch on `result['success']`; `utils/controller_helpers.handle_service_result` flashes and redirects from this shape.
- `data_access/database.py` — `get_db_connection()` context manager: raw `sqlite3` with `sqlite3.Row`, commits on exit, rolls back and raises `DatabaseError` on failure. No ORM; all SQL is hand-written with `?` parameters. `utils/query_builder.QueryBuilder` builds dynamic WHERE/JOIN/ORDER/LIMIT queries for search and listing.
- `models/user.py` — the only model; Flask-Login `User` with `is_admin()` / `is_staff()`. Everything else is plain dicts from rows.
- `utils/` — `config.Config` (all env vars, validated at startup in `app.py`), `decorators.admin_required`, `controller_helpers` (permission checks, image upload to `uploads/<subfolder>/<uuid>.<ext>`, booking categorization, admin action logging), `datetime_utils`, `html_utils.sanitize_html`, custom exceptions.

Key cross-cutting behavior:

- **Datetimes** are stored as UTC ISO strings and displayed in `Config.TIMEZONE` (America/New_York) via Jinja filters registered in `app.py` (`format_datetime_est`, `format_datetime_local`, etc.). Use `parse_datetime_aware` / `ensure_utc` rather than naive datetimes.
- **Bookings** (`services/booking_service.py`) are auto-approved on creation. Conflict detection only considers `status = 'approved'` rows with overlap `existing_start < new_end AND existing_end > new_start`. Validation uses per-resource operating hours (`operating_hours_start/end`, `is_24_hours`) plus `BOOKING_*` limits from `Config`. "In progress" is a computed display status (`get_booking_display_status`), not a stored one.
- **Messages** are grouped by `thread_id`; read state lives in the `thread_read` table. The unread count is injected into every template by a context processor in `app.py`.
- **Admin actions** are written to `admin_logs` via `log_admin_action`.
- **CSRF** is enabled globally (Flask-WTF); forms and AJAX POSTs must send the token.
- **AI concierge** (`services/ai_concierge.py`) loads `docs/context/*.md` as system context, queries the DB for grounding data, and calls Gemini (`google-generativeai`, deprecated upstream). With no `GOOGLE_GEMINI_API_KEY` it falls back to `query_concierge_fallback` (rule-based), which is what tests exercise.

## Database

- Schema source of truth: `init_db.py` (tables: `users`, `resources`, `bookings`, `messages`, `thread_read`, `reviews`, `admin_logs`). Reference doc: `docs/context/ERD_AND_SCHEMA.md`.
- `campus_resource_hub.db` and `uploads/` are committed intentionally (sample data and images; see `.gitignore`). Avoid committing incidental changes to them from local runs.
- Schema changes must be made in `init_db.py` and in the inline `CREATE TABLE` statements in test fixtures (e.g. `tests/test_booking_service.py`), which duplicate the schema.
- Seed accounts: `admin@iu.edu` / `AdminUser1!`, `staff@iu.edu` / `StaffUser1!`, `student@iu.edu` / `StudentUser1!`.

## Tests

- `DATABASE_PATH` is read from the environment on every connection (`get_database_path()`), so fixtures isolate tests by pointing `os.environ['DATABASE_PATH']` at a temp file and calling `init_database()` or creating tables inline. Follow this pattern; never run tests against the committed DB.
- Integration tests import `app` from `app.py` and use `app.test_client()`.
- `tests/ai_eval/` checks the concierge returns only real DB records.

## Docs

Product and technical specs: `docs/context/PRD_COMPLETE.md`, `API.md` (routes), `SETUP_STEPS.md`. `.prompt/dev_notes.md` is the course-required log of AI interactions (user prompt + summary of agent actions per entry); append to it when the user asks for logging.
