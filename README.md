# Proof — Evidence-First Social Network

**Current version:** MVP v0.5 — Evidence UX  
**Backend:** Python / Django 6  
**UI:** Arabic RTL + English LTR  
**API:** Django REST Framework

> Proof is a social network built around **claims and evidence**, not generic posts and engagement alone.

**Proof** is designed for discussions where people should be able to see what is being claimed, what evidence supports or contradicts it, how confident participants are, and how credible contributors have been within a specific topic.

---

## العربية

### ما هي Proof؟

Proof منصة اجتماعية يكون فيها العنصر الأساسي **ادعاء Claim** بدل المنشور التقليدي.

كل ادعاء يمكن أن يحتوي على:

- أدلة **مؤيدة** أو **مناقضة** أو **سياقية**.
- روابط للمصادر مع فحص أولي لبيانات المصدر.
- موقف المستخدم من الادعاء: صحيح / خطأ / غير متأكد.
- درجة ثقة من 0 إلى 100%.
- توقعات قابلة للحسم في وقت لاحق.
- درجة مصداقية للمستخدم **حسب الموضوع**، وليس رقمًا عامًا واحدًا.

الفكرة الأساسية هي أن Proof لا يحاول مكافأة أعلى صوت أو أكثر منشور حصل على تفاعل، بل يحاول جعل **الأدلة والمصداقية وتنوع وجهات النظر** جزءًا من بنية المنصة نفسها.

### ما الذي يميز Proof عن شبكة اجتماعية تقليدية؟

في الشبكات التقليدية غالبًا تكون الوحدة الأساسية هي المنشور ثم تأتي التعليقات والإعجابات بعده.

في Proof البنية هي:

```text
Claim
 ├── Evidence supporting it
 ├── Evidence contradicting it
 ├── Context evidence
 ├── Community positions + confidence
 └── Topic-specific credibility history
```

لذلك السؤال الأساسي ليس فقط: **من قال هذا؟** بل أيضًا: **ما الدليل؟ وما قوة المصدر؟ وما سجل الشخص في هذا المجال؟**

### الخصائص الحالية — v0.5

- واجهة عربية RTL وإنجليزية LTR.
- تبديل اللغة من داخل المنصة.
- تسجيل حساب / تسجيل دخول.
- Global Feed وFollowing Feed.
- إنشاء Claims.
- Evidence مؤيد / مناقض / سياق.
- التصويت على فائدة الدليل.
- Community Position مع Confidence من 0–100%.
- Profiles وFollow / Unfollow.
- Credibility Score حسب الموضوع.
- Leaderboard.
- Feed Ranking Engine لا يعتمد على التفاعل الخام فقط.
- Source Verification Lite لاستخراج بيانات المصدر الأساسية وفحص الرابط.
- REST API.
- PostgreSQL + Redis + Celery عند التشغيل عبر Docker.

### فلسفة الـFeed

ترتيب الـFeed يعتمد حاليًا على مجموعة إشارات محدودة وقابلة للفهم، منها:

- جودة وكمية الأدلة.
- وجود أدلة من أكثر من جانب.
- حداثة الادعاء.
- مصداقية الكاتب في الموضوع.
- النقاش المفيد المدعوم بأدلة.
- قدر محدود من التفاعل.
- فرصة ظهور للحسابات الجديدة.
- منع احتكار نفس الكاتب أو نفس الموضوع لأول الشاشة.

الهدف ليس تعظيم الوقت الذي يقضيه المستخدم داخل التطبيق، بل رفع احتمال ظهور **نقاش يستحق القراءة**.

### Source Verification Lite

عند إضافة رابط كمصدر للدليل، Celery Worker يحاول:

- منع روابط localhost والشبكات الخاصة كحماية أولية من SSRF.
- فتح روابط HTTP/HTTPS العامة فقط.
- استخراج عنوان الصفحة.
- استخراج الناشر أو اسم الموقع إن توفر.
- استخراج تاريخ النشر إن توفر.
- تسجيل الدومين النهائي.
- حساب **Provenance Quality Score** أولي بناءً على HTTPS واكتمال بيانات المصدر.

> هذه الدرجة **ليست Fact Check** ولا تعني أن محتوى المصدر صحيح، ولا أنها حكم نهائي على موثوقية الناشر.

---

## English

### What is Proof?

Proof is an **evidence-first social network** where the primary object is a **claim**, not a generic post.

A claim can contain:

- Supporting, contradicting, or contextual evidence.
- Source links with lightweight source metadata inspection.
- Community positions: true / false / unsure.
- Confidence from 0 to 100%.
- Time-bound predictions that can later be resolved.
- Topic-specific credibility for contributors.

The central product rule is simple: **engagement alone should not determine visibility or credibility**.

### Current MVP features

- Arabic RTL + English LTR interface.
- Language switching.
- Authentication and registration.
- Global and following feeds.
- Claims and evidence.
- Evidence usefulness voting.
- Community positions with confidence.
- Profiles and follow relationships.
- Topic-specific credibility.
- Topic leaderboards.
- Explainable feed ranking.
- Source Verification Lite.
- REST API.
- Docker development stack with PostgreSQL, Redis, Django and Celery.

---

# Installation / التثبيت

## Option 1 — Docker Compose (recommended)

Requirements:

- Docker
- Docker Compose

Clone the repository and enter the project directory:

```bash
git clone https://github.com/waelbeso/Proof.git
cd Proof
```

Create the environment file:

```bash
cp .env.example .env
```

Start the complete development stack:

```bash
docker compose up --build
```

The application will be available at:

```text
http://127.0.0.1:8000/
```

Create an administrator account:

```bash
docker compose exec web python manage.py createsuperuser
```

The Docker stack starts:

- `web` — Django application
- `db` — PostgreSQL 17
- `redis` — Redis
- `worker` — Celery worker for background jobs such as source verification

The web container automatically runs migrations and loads the default bilingual topics on startup.

Stop the stack:

```bash
docker compose down
```

Delete the development database volume as well:

```bash
docker compose down -v
```

---

## Option 2 — Local development with SQLite

Requirements:

- Python 3.12+
- `pip`

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

Linux / macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the database tables:

```bash
python manage.py migrate
```

Load the default Arabic/English topics:

```bash
python manage.py seed_topics
```

Create an admin user:

```bash
python manage.py createsuperuser
```

Run Django:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

### Running source verification locally

The main site can run with SQLite without Redis/Celery, but automatic source verification requires Redis and a Celery worker.

Example worker command after Redis is running:

```bash
celery -A proof worker -l info
```

If the worker is not running, the core social features still work, but evidence URLs may remain unverified/pending.

---

# Environment variables

Copy `.env.example` to `.env` and adjust values as required.

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=proof
POSTGRES_USER=proof
POSTGRES_PASSWORD=proof
POSTGRES_HOST=db
POSTGRES_PORT=5432
REDIS_URL=redis://redis:6379/0
```

**Do not use the example secret or development settings in production.**

---

# Main routes

| Route | Purpose |
|---|---|
| `/` | Ranked feed |
| `/claims/new/` | Create a claim |
| `/claims/<id>/` | Claim, evidence and community positions |
| `/leaderboard/` | Credibility leaderboard |
| `/u/<username>/` | User profile |
| `/login/` | Login |
| `/register/` | Registration |
| `/admin/` | Django Admin |
| `/health/` | Health endpoint |
| `/lang/ar/` | Arabic UI |
| `/lang/en/` | English UI |

---

# REST API

Token authentication:

```text
POST /api/auth/token/
```

Core endpoints:

```text
GET       /api/topics/
GET|POST  /api/claims/
GET       /api/claims/{id}/evidence/
GET|POST  /api/evidence/
POST      /api/evidence/{id}/vote/
GET|POST  /api/positions/
GET|POST  /api/following/
GET       /api/feed/
GET       /api/leaderboard/?topic=economics
POST      /api/claims/{id}/resolve/   # admin only
```

---

# Project structure

```text
proof/                  Django project settings, URLs and Celery setup
core/                   Main social network domain
  models.py             Claims, evidence, positions, credibility and follows
  services/feed.py      Feed ranking policy
  services/scoring.py   Topic credibility calculations
  services/source_verification.py
  templates/core/       Bilingual web UI
  static/core/          CSS and JavaScript
api/                    Django REST Framework API
core/migrations/        Database migrations
tests/                  Feed, scoring, source verification and web tests
Dockerfile
docker-compose.yml
requirements.txt
```

---

# Development status

Proof v0.5 is an **MVP / experimental codebase**. It is suitable for product testing and continued development, but it has not yet been hardened for public production deployment.

Before production, the project will need additional work around areas such as deployment security, secrets management, static/media hosting, rate limiting, abuse controls, monitoring, backups, and production-grade web serving.

---

## Version history

- **v0.2** — bilingual Arabic/English product foundation.
- **v0.3** — explainable Feed Ranking Engine.
- **v0.4** — Source Verification Lite.
- **v0.5** — improved Evidence UX and clearer provenance presentation.
