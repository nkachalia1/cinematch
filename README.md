# CineMatch

[CineMatch Link](https://cinematch-usa.onrender.com/)

A machine learning movie recommender for USA films from the past 50 years. The app pairs a FastAPI backend with a polished streaming-style frontend and is ready to deploy as a Render web service.

## What It Does

- Recommends USA or USA-led films from 1976 onward.
- Uses a content-based ML pipeline: TF-IDF text vectors plus cosine similarity.
- Lets users click any movie card to use it as the recommendation seed.
- Also supports free-text vibe, genre chips, mood chips, decade controls, and the reference-title dropdown.
- Returns explainable match reasons and match scores.
- Serves the static frontend and API from one FastAPI app for simple deployment.

## ML Approach

Each movie is represented as a weighted document built from title, year, genres, director, cast, moods, themes, and synopsis. Genres and moods are repeated in the document so they carry more signal. The recommender vectorizes the catalog with `TfidfVectorizer(ngram_range=(1, 2))`, scores candidates with cosine similarity, then applies transparent boosts for selected genres, moods, and decades.

This is intentionally content-based rather than collaborative filtering so the project works without user accounts or private viewing histories.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`.

On Windows you can also run:

```powershell
.\scripts\run_local.ps1
```

## Tests

```bash
pytest
```

## API

- `GET /health` - service and model status.
- `GET /api/stats` - catalog metadata, genres, moods, and active 50-year window.
- `GET /api/movies?q=&genres=&moods=&decade=&limit=` - searchable catalog.
- `GET /api/recommend?movie_id=&vibe=&genres=&moods=&decade=&limit=` - ML-ranked recommendations, including the selected `seed_movie` when a seed is provided.
- `GET /api/discover` - spotlight title and curated shelves for the homepage.

## Render Deployment

This repo includes `render.yaml` for Render Blueprints.

Manual Render settings:

- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

After pushing to GitHub, create a new Render Web Service or Blueprint from the repository. Render will expose the app at its `onrender.com` URL.

## Project Notes

- The dataset is a curated demo catalog kept in code for transparency and easy review.
- Poster art is deterministic CSS-generated key art, avoiding external image dependencies and poster licensing issues.
