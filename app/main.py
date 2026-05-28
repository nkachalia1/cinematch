from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .recommender import DEFAULT_LIMIT, get_recommender


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="CineMatch USA",
    version="1.0.0",
    description="A content-based machine learning recommender for USA movies from the past 50 years.",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    model = get_recommender()
    return {"status": "ok", "model": "tfidf-cosine-content-recommender", "stats": model.stats}


@app.get("/api/stats")
def stats() -> dict:
    return get_recommender().stats


@app.get("/api/discover")
def discover() -> dict:
    return get_recommender().discover()


@app.get("/api/movies")
def movies(
    q: str = "",
    genres: str = "",
    moods: str = "",
    decade: str = "all",
    limit: int = Query(80, ge=1, le=200),
) -> dict:
    model = get_recommender()
    results = model.search(q=q, genres=_csv(genres), moods=_csv(moods), decade=decade, limit=limit)
    return {"count": len(results), "movies": results}


@app.get("/api/recommend")
def recommend(
    movie_id: str | None = None,
    vibe: str = "",
    genres: str = "",
    moods: str = "",
    decade: str = "all",
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=24),
) -> dict:
    model = get_recommender()
    try:
        results = model.recommend(
            movie_id=movie_id,
            vibe=vibe,
            genres=_csv(genres),
            moods=_csv(moods),
            decade=decade,
            limit=limit,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "count": len(results),
        "query": {
            "movie_id": movie_id,
            "vibe": vibe,
            "genres": _csv(genres),
            "moods": _csv(moods),
            "decade": decade,
        },
        "movies": results,
    }
