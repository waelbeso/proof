# Deploy Proof on Render | تشغيل Proof على Render

Proof is prepared for a simple demo deployment using the repository's `render.yaml` Blueprint.

## Quick deployment

1. Sign in to Render.
2. Open **Blueprints** and choose **New Blueprint Instance**.
3. Connect the GitHub repository: `waelbeso/proof`.
4. Render will detect `render.yaml`.
5. Apply the Blueprint.

Render will create:

- `proof-demo` — free Python web service.
- `proof-demo-db` — free PostgreSQL database.

The build process automatically runs:

```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed_topics
python manage.py seed_demo
```

The demo dataset contains synthetic users, claims, evidence, community positions, votes, and topic-specific credibility scores. Demo claims are visibly marked with `[DEMO]`.

After deployment finishes, open the `.onrender.com` URL shown by Render.

## Notes

- The free web service is intended for testing and may spin down when idle.
- Render's free PostgreSQL database is temporary and currently expires after 30 days unless upgraded.
- Source Verification background jobs are not enabled in the free demo Blueprint because a separate background worker would be required. The seeded demo evidence already contains source metadata so the Evidence UX remains visible.
- New user registration, claims, positions, follows, evidence, and voting remain usable in the demo.

## Admin account

If you want Django Admin access, open a Render Shell for the web service and run:

```bash
python manage.py createsuperuser
```
