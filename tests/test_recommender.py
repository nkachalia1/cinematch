from app.recommender import MIN_YEAR, MovieRecommender


def test_catalog_is_usa_only_and_within_50_year_window():
    model = MovieRecommender()

    assert model.movies
    assert all(movie["country"] == "USA" for movie in model.movies)
    assert min(movie["year"] for movie in model.movies) >= MIN_YEAR


def test_recommendations_exclude_seed_and_find_related_titles():
    model = MovieRecommender()

    results = model.recommend(movie_id="star-wars-a-new-hope", limit=8)
    result_ids = {movie["id"] for movie in results}

    assert "star-wars-a-new-hope" not in result_ids
    assert {"the-empire-strikes-back", "star-trek", "guardians-galaxy"}.intersection(result_ids)
    assert all("match_score" in movie for movie in results)


def test_filters_can_target_mood_genre_and_decade():
    model = MovieRecommender()

    results = model.recommend(vibe="funny clever", genres=["Comedy"], moods=["witty"], decade="1990s", limit=6)

    assert results
    assert all(1990 <= movie["year"] <= 1999 for movie in results[:3])
    assert any("Comedy" in movie["genres"] for movie in results)


def test_search_returns_cast_and_title_matches():
    model = MovieRecommender()

    by_title = model.search(q="Matrix", limit=3)
    by_cast = model.search(q="Denzel", limit=5)

    assert by_title[0]["id"] == "the-matrix"
    assert any("Denzel Washington" in movie["cast"] for movie in by_cast)
