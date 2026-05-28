from __future__ import annotations

from collections import Counter
from datetime import date
from functools import lru_cache
from typing import Iterable, Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .movie_data import MOVIES


CURRENT_YEAR = date.today().year
MIN_YEAR = CURRENT_YEAR - 50
DEFAULT_LIMIT = 12
DECADE_RANGES = {
    "1970s": (1970, 1979),
    "1980s": (1980, 1989),
    "1990s": (1990, 1999),
    "2000s": (2000, 2009),
    "2010s": (2010, 2019),
    "2020s": (2020, 2029),
}


def _norm(value: str) -> str:
    return value.strip().lower()


def _norm_list(values: Iterable[str] | None) -> list[str]:
    if not values:
        return []
    return [_norm(value) for value in values if value and value.strip()]


def _in_decade(year: int, decade: str | None) -> bool:
    if not decade or decade == "all":
        return True
    bounds = DECADE_RANGES.get(decade)
    return bool(bounds and bounds[0] <= year <= bounds[1])


class MovieRecommender:
    """Content-based recommender over a USA-only movie catalog."""

    def __init__(self, movies: Sequence[dict] = MOVIES) -> None:
        self.movies = [
            movie
            for movie in movies
            if movie["country"] == "USA" and MIN_YEAR <= movie["year"] <= CURRENT_YEAR
        ]
        if not self.movies:
            raise ValueError("No USA movies are available for the configured 50-year window.")

        self.movies.sort(key=lambda movie: (movie["year"], movie["rating"], movie["popularity"]), reverse=True)
        self.index_by_id = {movie["id"]: index for index, movie in enumerate(self.movies)}
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        self.documents = [self._movie_document(movie) for movie in self.movies]
        self.matrix = self.vectorizer.fit_transform(self.documents)

    def _movie_document(self, movie: dict) -> str:
        weighted_genres = " ".join(movie["genres"] * 4)
        weighted_moods = " ".join(movie["moods"] * 3)
        weighted_themes = " ".join(movie["themes"] * 2)
        cast = " ".join(movie["cast"])
        return " ".join(
            [
                movie["title"],
                str(movie["year"]),
                weighted_genres,
                movie["director"],
                cast,
                weighted_moods,
                weighted_themes,
                movie["synopsis"],
            ]
        )

    @property
    def stats(self) -> dict:
        genres = sorted({genre for movie in self.movies for genre in movie["genres"]})
        moods = sorted({mood for movie in self.movies for mood in movie["moods"]})
        years = [movie["year"] for movie in self.movies]
        return {
            "country": "USA",
            "window": {"min_year": MIN_YEAR, "max_year": CURRENT_YEAR},
            "catalog_years": {"min": min(years), "max": max(years)},
            "movie_count": len(self.movies),
            "genres": genres,
            "moods": moods,
            "decades": list(DECADE_RANGES.keys()),
        }

    def search(
        self,
        q: str = "",
        genres: Sequence[str] | None = None,
        moods: Sequence[str] | None = None,
        decade: str = "all",
        limit: int = 80,
    ) -> list[dict]:
        genre_filters = set(_norm_list(genres))
        mood_filters = set(_norm_list(moods))
        q_norm = _norm(q)

        matches: list[dict] = []
        for movie in self.movies:
            genre_values = {_norm(genre) for genre in movie["genres"]}
            mood_values = {_norm(mood) for mood in movie["moods"]}
            if genre_filters and not genre_filters.intersection(genre_values):
                continue
            if mood_filters and not mood_filters.intersection(mood_values):
                continue
            if not _in_decade(movie["year"], decade):
                continue
            if q_norm and q_norm not in self._search_blob(movie):
                continue
            matches.append(movie)

        if q_norm:
            matches.sort(
                key=lambda movie: (
                    _norm(movie["title"]).startswith(q_norm),
                    movie["rating"],
                    movie["popularity"],
                ),
                reverse=True,
            )
        else:
            matches.sort(key=lambda movie: (movie["rating"], movie["popularity"], movie["year"]), reverse=True)
        return [self._serialize(movie) for movie in matches[:limit]]

    def recommend(
        self,
        movie_id: str | None = None,
        vibe: str = "",
        genres: Sequence[str] | None = None,
        moods: Sequence[str] | None = None,
        decade: str = "all",
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict]:
        genre_filters = _norm_list(genres)
        mood_filters = _norm_list(moods)
        criteria_text = self._criteria_text(vibe, genre_filters, mood_filters, decade)

        if not movie_id and not criteria_text:
            return self._editorial(limit)

        seed_index = None
        seed_movie = None
        if movie_id:
            if movie_id not in self.index_by_id:
                raise KeyError(f"Unknown movie_id: {movie_id}")
            seed_index = self.index_by_id[movie_id]
            seed_movie = self.movies[seed_index]
            query_vector = self.matrix[seed_index]
            if criteria_text:
                query_vector = query_vector + (self.vectorizer.transform([criteria_text]) * 0.72)
        else:
            query_vector = self.vectorizer.transform([criteria_text])

        raw_scores = cosine_similarity(query_vector, self.matrix).ravel()
        scored: list[tuple[float, int, list[str]]] = []
        for index, movie in enumerate(self.movies):
            if seed_index == index:
                continue
            if decade and decade != "all" and not _in_decade(movie["year"], decade):
                continue

            score = float(raw_scores[index])
            reasons: list[str] = []

            if seed_movie:
                shared_genres = [genre for genre in seed_movie["genres"] if genre in movie["genres"]]
                shared_moods = [mood for mood in seed_movie["moods"] if mood in movie["moods"]]
                if shared_genres:
                    score += 0.08 * len(shared_genres)
                    reasons.append(f"shares {', '.join(shared_genres[:2])} with {seed_movie['title']}")
                if shared_moods:
                    score += 0.04 * len(shared_moods)
                    reasons.append(f"keeps the {shared_moods[0]} tone")

            movie_genres = {_norm(genre) for genre in movie["genres"]}
            movie_moods = {_norm(mood) for mood in movie["moods"]}
            genre_hits = [genre for genre in genre_filters if genre in movie_genres]
            mood_hits = [mood for mood in mood_filters if mood in movie_moods]

            if genre_hits:
                score += 0.11 * len(genre_hits)
                reasons.append(f"matches {', '.join(genre_hits[:2])}")
            if mood_hits:
                score += 0.09 * len(mood_hits)
                reasons.append(f"feels {', '.join(mood_hits[:2])}")
            if decade and decade != "all" and _in_decade(movie["year"], decade):
                score += 0.07
                reasons.append(f"fits the {decade}")

            score += max(movie["rating"] - 7.0, 0) * 0.018
            score += movie["popularity"] * 0.00022
            scored.append((score, index, reasons))

        scored.sort(key=lambda row: row[0], reverse=True)
        top_rows = scored[:limit]
        max_score = max((score for score, _, _ in top_rows), default=1.0)
        min_score = min((score for score, _, _ in top_rows), default=0.0)
        spread = max(max_score - min_score, 0.001)

        results = []
        for score, index, reasons in top_rows:
            normalized = (score - min_score) / spread
            match_score = int(round(82 + normalized * 17))
            results.append(self._serialize(self.movies[index], match_score=match_score, reasons=reasons[:3]))
        return results

    def discover(self) -> dict:
        shelves = [
            {
                "id": "prestige-thrillers",
                "title": "Prestige Thrillers",
                "movies": self.recommend(vibe="tense acclaimed crime psychological mystery", genres=["Thriller", "Crime"], limit=10),
            },
            {
                "id": "big-sci-fi",
                "title": "Big Sci-Fi Worlds",
                "movies": self.recommend(vibe="epic futuristic space spectacle", genres=["Sci-Fi", "Adventure"], limit=10),
            },
            {
                "id": "smart-comedies",
                "title": "Sharp Comedies",
                "movies": self.recommend(vibe="witty funny satirical warm", genres=["Comedy"], limit=10),
            },
            {
                "id": "animation-night",
                "title": "Animated With Heart",
                "movies": self.recommend(vibe="colorful emotional family inventive", genres=["Animation"], limit=10),
            },
        ]
        spotlight = self.recommend(vibe="USA iconic cinematic intense premium", limit=1)[0]
        return {"stats": self.stats, "spotlight": spotlight, "shelves": shelves}

    def _editorial(self, limit: int) -> list[dict]:
        ranked = sorted(
            self.movies,
            key=lambda movie: (movie["rating"] * 0.76) + (movie["popularity"] * 0.018) + (movie["year"] >= 2010) * 0.2,
            reverse=True,
        )
        return [
            self._serialize(
                movie,
                match_score=max(84, min(98, int(round(movie["rating"] * 9.6 + movie["popularity"] * 0.09)))),
                reasons=["highly rated USA catalog pick", "strong audience signal"],
            )
            for movie in ranked[:limit]
        ]

    def _criteria_text(self, vibe: str, genres: Sequence[str], moods: Sequence[str], decade: str) -> str:
        weighted = []
        weighted.extend(genres * 4)
        weighted.extend(moods * 3)
        if decade and decade != "all":
            weighted.append(decade)
        if vibe.strip():
            weighted.append(vibe.strip())
        return " ".join(weighted).strip()

    def _search_blob(self, movie: dict) -> str:
        return _norm(
            " ".join(
                [
                    movie["title"],
                    movie["director"],
                    " ".join(movie["cast"]),
                    " ".join(movie["genres"]),
                    " ".join(movie["moods"]),
                    " ".join(movie["themes"]),
                    movie["synopsis"],
                ]
            )
        )

    def _serialize(self, movie: dict, match_score: int | None = None, reasons: Sequence[str] | None = None) -> dict:
        payload = {
            "id": movie["id"],
            "title": movie["title"],
            "year": movie["year"],
            "country": movie["country"],
            "genres": movie["genres"],
            "director": movie["director"],
            "cast": movie["cast"],
            "moods": movie["moods"],
            "themes": movie["themes"],
            "synopsis": movie["synopsis"],
            "rating": movie["rating"],
            "popularity": movie["popularity"],
            "maturity": movie["maturity"],
            "runtime_minutes": movie["runtime_minutes"],
        }
        if match_score is not None:
            payload["match_score"] = match_score
        if reasons:
            payload["match_reasons"] = list(dict.fromkeys(reasons))
        return payload


@lru_cache(maxsize=1)
def get_recommender() -> MovieRecommender:
    return MovieRecommender()
