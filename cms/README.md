# This is a House Gallery — FastAPI Headless CMS

A self-hosted, headless content platform for
[thisisahousegallery.com](https://thisisahousegallery.com). It serves multiple
artist frontends from one content API. See the design spec at
[`../../docs/headless-cms-design.md`](../../docs/headless-cms-design.md) in the
repo root.

This is the headless CMS implementing the design spec — content models with
the multi-tenant seam and the public read-only `/v1` API.

## Getting started

### 1. Install dependencies

```bash
uv sync
```

### 2. Apply migrations

```bash
uv run alembic upgrade head
```

### 3. Run the dev server

```bash
uv run uvicorn app.main:app --reload
```

- Interactive API docs (Swagger) at http://localhost:8000/docs
- SQLAdmin admin at http://localhost:8000/admin
- Health check at http://localhost:8000/healthz

## API

Public read-only v1 routes (also visible in `/docs` Swagger):

```
GET /v1/site-settings          Site title, tagline, nav, contact, socials
GET /v1/exhibitions            List of exhibitions
GET /v1/exhibitions/{slug}     Exhibition detail (artists/artworks/photos)
GET /v1/artists                List of artists
GET /v1/artists/{slug}         Artist detail (+ artworks)
GET /v1/artworks               List (optional ?artist=&tag=&exhibition= filters)
GET /v1/artworks/{slug}        Artwork detail (artists/images/tags)
GET /v1/images/{image_id}      Image detail (+ rendition URLs)
GET /v1/tags                   List of tags
```

Use `env -u PYTHONPATH uv run ...` (or the project `.venv/Scripts/python.exe`)
if your shell's `PYTHONPATH` points at another venv.

## Environment

Copy `.env.example` to `.env` and adjust as needed.

## Database and backups

The database is a single SQLite file, `cms.db` (created by the migrations).
[Litestream](https://litestream.io) replicates it continuously to the
`housegallery-cms` S3 bucket under `litestream/`; see `litestream.yml`.

```bash
litestream replicate -config litestream.yml       # run alongside the CMS
litestream restore -config litestream.yml cms.db  # rebuild from S3
```

### Moving data off the old Postgres

One-off, run on the machine that holds the Postgres container:

```bash
uv sync --extra migrate
uv run alembic upgrade head            # creates an empty cms.db
uv run python -m scripts.copy_postgres_to_sqlite \
    postgresql+psycopg://cms:cms@localhost:5432/cms sqlite:///./cms.db
```

It refuses a non-empty target and compares row counts at the end.
