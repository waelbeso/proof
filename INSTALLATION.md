# Proof Installation Guide | دليل تثبيت Proof

This document contains the practical installation steps for the current Proof MVP v0.5.

---

## 1. Recommended setup: Docker

Docker is the easiest way to run the full system because Proof currently uses four services:

1. Django web application.
2. PostgreSQL database.
3. Redis broker.
4. Celery background worker.

### Requirements

Install:

- Docker Desktop on Windows/macOS, or Docker Engine on Linux.
- Docker Compose v2.

Check:

```bash
docker --version
docker compose version
```

### Clone

```bash
git clone https://github.com/waelbeso/Proof.git
cd Proof
```

### Configure

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

For local development, the example database values work with the included Docker Compose file. Change `DJANGO_SECRET_KEY` before any serious deployment.

### Start

```bash
docker compose up --build
```

Open:

```text
http://127.0.0.1:8000/
```

### Create admin

In another terminal:

```bash
docker compose exec web python manage.py createsuperuser
```

Admin panel:

```text
http://127.0.0.1:8000/admin/
```

### Verify services

```bash
docker compose ps
```

You should see `web`, `db`, `redis`, and `worker` running.

Health endpoint:

```text
http://127.0.0.1:8000/health/
```

Expected JSON:

```json
{"status":"ok","service":"proof"}
```

### Stop

```bash
docker compose down
```

To also remove the PostgreSQL development volume:

```bash
docker compose down -v
```

---

## 2. Lightweight setup: Python + SQLite

This is useful when working on the UI or Django code without PostgreSQL.

### Requirements

- Python 3.12+
- pip

### Create virtual environment

```bash
python -m venv .venv
```

Activate on Linux/macOS:

```bash
source .venv/bin/activate
```

Activate on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Initialize

```bash
python manage.py migrate
python manage.py seed_topics
python manage.py createsuperuser
```

### Run

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

When `POSTGRES_HOST` is not defined, Proof automatically uses a local SQLite database at `db.sqlite3`.

---

## 3. Background source verification

Source Verification Lite runs as a Celery task.

If you run the full Docker stack, the worker is already included.

If you run Django locally, start Redis separately and configure:

```env
REDIS_URL=redis://localhost:6379/0
```

Then run:

```bash
celery -A proof worker -l info
```

Without the worker, users can still create claims and evidence, but source URLs may remain pending instead of being inspected automatically.

---

## 4. Useful Django commands

Run migrations:

```bash
python manage.py migrate
```

Seed bilingual topics:

```bash
python manage.py seed_topics
```

Create admin:

```bash
python manage.py createsuperuser
```

Run tests:

```bash
python manage.py test
```

Run development server:

```bash
python manage.py runserver
```

---

## 5. Common problems

### Port 8000 already in use

Run Django on another port:

```bash
python manage.py runserver 8001
```

Or modify the Docker port mapping.

### PostgreSQL port 5432 already in use

If another PostgreSQL instance is already using host port 5432, remove or change the `5432:5432` host mapping in `docker-compose.yml`. The Proof containers communicate internally using the service name `db`, so publishing PostgreSQL to the host is not required for normal app operation.

### Redis port 6379 already in use

The same principle applies to Redis. The containers communicate internally using `redis`.

### Evidence source remains pending

Check that the Celery worker is running:

```bash
docker compose logs worker
```

or locally:

```bash
celery -A proof worker -l info
```

### Reset local Docker database

Warning: this deletes local development data.

```bash
docker compose down -v
docker compose up --build
```

---

## العربية — ملخص سريع

أسهل طريقة لتشغيل Proof هي Docker:

```bash
cp .env.example .env
docker compose up --build
```

ثم افتح:

```text
http://127.0.0.1:8000/
```

ولإنشاء مدير:

```bash
docker compose exec web python manage.py createsuperuser
```

التشغيل عبر Docker يشغل تلقائيًا Django وPostgreSQL وRedis وCelery، وبالتالي تعمل ميزة فحص روابط الأدلة أيضًا.

للتطوير الخفيف بدون Docker يمكن استخدام Python + SQLite:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_topics
python manage.py runserver
```

على Windows استبدل أمر تفعيل البيئة بـ:

```powershell
.venv\Scripts\Activate.ps1
```
