# Student Management Portal

A college project using HTML, CSS, JavaScript, Python and MySQL.

## Folder structure

- `frontend/` — browser pages, styles and JavaScript
- `backend/` — Python HTTP server, database connector, admin setup and SQL schema

## Requirements

- Python 3.10+
- MySQL Server
- Install Python dependency: `pip install -r backend/requirements.txt`

## Database setup

1. Start MySQL.
2. Run `backend/schema.sql` in MySQL Workbench or MySQL CLI.
3. Configure database environment variables if needed:
   - `DB_HOST` (default `127.0.0.1`)
   - `DB_USER` (default `root`)
   - `DB_PASSWORD` (default empty)
   - `DB_NAME` (default `student_portal`)

## Create the first administrator

From the project root run:

```bash
python backend/create_admin.py
```

Choose a username and a password of at least 12 characters.

## Run locally

From the project root run:

```bash
python backend/server.py
```

Open **http://127.0.0.1:8000** in your browser.

## Main features

- Administrator login and logout
- Dashboard statistics
- Add, view, search, edit and delete students
- Daily attendance entry and records
- Subject-wise marks entry and records
- Combined attendance and marks report
- Print report

## Important deployment note

The supplied server is a small standard-library development server intended for local demonstration. It binds to `127.0.0.1`, and its same-origin check is configured for local use. Do not expose it directly to the public internet. For a public GitHub-linked deployment, adapt the server for a production WSGI/ASGI host, HTTPS, secure cookies, environment-based host/origin configuration and a managed MySQL database. GitHub stores the source code; it does not run this Python/MySQL application by itself.

## Security notes

- Never commit real database passwords or production secrets.
- Use a dedicated MySQL user instead of the MySQL root account.
- Use HTTPS and Secure cookies in production.
- Back up the database before demonstrations or data changes.
