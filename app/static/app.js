const state = {
  genres: new Set(),
  moods: new Set(),
  decade: "all",
  activeSeedId: "",
  movies: [],
  discover: null,
};

const curatedGenres = [
  "Drama",
  "Comedy",
  "Sci-Fi",
  "Thriller",
  "Action",
  "Animation",
  "Horror",
  "Romance",
  "Crime",
  "Superhero",
];

const curatedMoods = [
  "tense",
  "witty",
  "epic",
  "warm",
  "gritty",
  "mind bending",
  "uplifting",
  "dark",
  "playful",
  "emotional",
];

const palettes = [
  ["#e50914", "#260608", "#f4b860"],
  ["#34d6c8", "#101820", "#f43f5e"],
  ["#ff7a18", "#1a0d06", "#ffd166"],
  ["#7dd3fc", "#06131f", "#f97316"],
  ["#a3e635", "#10170a", "#f43f5e"],
  ["#eab308", "#17120a", "#38bdf8"],
  ["#fb7185", "#19080d", "#fef3c7"],
  ["#22c55e", "#07150d", "#e50914"],
];

const elements = {
  form: document.querySelector("#recommenderForm"),
  seedSelect: document.querySelector("#seedSelect"),
  vibeInput: document.querySelector("#vibeInput"),
  genreChips: document.querySelector("#genreChips"),
  moodChips: document.querySelector("#moodChips"),
  decadeControl: document.querySelector("#decadeControl"),
  resetButton: document.querySelector("#resetButton"),
  clearSeedButton: document.querySelector("#clearSeedButton"),
  resultsGrid: document.querySelector("#resultsGrid"),
  resultsTitle: document.querySelector("#resultsTitle"),
  matchStatus: document.querySelector("#matchStatus"),
  selectedSeed: document.querySelector("#selectedSeed"),
  selectedSeedTitle: document.querySelector("#selectedSeedTitle"),
  selectedSeedMeta: document.querySelector("#selectedSeedMeta"),
  shelves: document.querySelector("#shelves"),
  heroStats: document.querySelector("#heroStats"),
  spotlight: document.querySelector("#spotlight"),
  spotlightPoster: document.querySelector("#spotlightPoster"),
  spotlightTitle: document.querySelector("#spotlightTitle"),
  spotlightMeta: document.querySelector("#spotlightMeta"),
  spotlightSynopsis: document.querySelector("#spotlightSynopsis"),
};

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function hashValue(value) {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(index);
    hash |= 0;
  }
  return Math.abs(hash);
}

function paletteFor(movie) {
  return palettes[hashValue(movie.id) % palettes.length];
}

function initials(title) {
  const words = title.replace(/[^a-zA-Z0-9 ]/g, " ").split(" ").filter(Boolean);
  return words.slice(0, 3).map((word) => word[0]).join("");
}

function setPosterVars(node, movie) {
  const [a, b, c] = paletteFor(movie);
  node.style.setProperty("--poster-a", a);
  node.style.setProperty("--poster-b", b);
  node.style.setProperty("--poster-c", c);
}

function runtime(movie) {
  const hours = Math.floor(movie.runtime_minutes / 60);
  const minutes = movie.runtime_minutes % 60;
  return `${hours}h ${minutes}m`;
}

function movieById(movieId) {
  return state.movies.find((movie) => movie.id === movieId) || null;
}

function movieCard(movie, compact = false) {
  const reasons = movie.match_reasons || movie.moods?.slice(0, 2) || [];
  const score = movie.match_score || Math.round(movie.rating * 10);
  const genreText = movie.genres.slice(0, compact ? 2 : 3).join(" / ");
  const castText = movie.cast.slice(0, 2).join(", ");

  return `
    <article
      class="movie-card"
      data-movie-id="${escapeHtml(movie.id)}"
      role="button"
      tabindex="0"
      aria-label="Recommend movies like ${escapeHtml(movie.title)}"
    >
      <div class="poster-art">
        <span>${escapeHtml(initials(movie.title))}</span>
      </div>
      <div class="movie-body">
        <h3>${escapeHtml(movie.title)}</h3>
        <div class="movie-meta">
          <span>${movie.year}</span>
          <span>${escapeHtml(movie.maturity)}</span>
          <span>${runtime(movie)}</span>
        </div>
        <div class="movie-meta">
          <span>${escapeHtml(genreText)}</span>
        </div>
        <p class="synopsis">${escapeHtml(movie.synopsis)}</p>
        <div class="reason-list">
          ${reasons.map((reason) => `<span>${escapeHtml(reason)}</span>`).join("")}
        </div>
        <div class="score-pill">
          <span>${score}%</span>
          <progress max="100" value="${score}" aria-label="${score}% match"></progress>
        </div>
        ${
          compact
            ? ""
            : `<div class="movie-meta"><span>${escapeHtml(movie.director)}</span><span>${escapeHtml(castText)}</span></div>
               <button class="ghost-button seed-button" type="button" data-seed="${escapeHtml(movie.id)}">Use as seed</button>`
        }
      </div>
    </article>
  `;
}

function applyPosterPalettes(container, movies) {
  container.querySelectorAll(".movie-card").forEach((card, index) => {
    const movie = movies[index];
    const poster = card.querySelector(".poster-art");
    if (movie && poster) setPosterVars(poster, movie);
  });
}

function markSelectedCards() {
  document.querySelectorAll(".movie-card").forEach((card) => {
    const isSelected = Boolean(state.activeSeedId) && card.dataset.movieId === state.activeSeedId;
    card.classList.toggle("selected", isSelected);
    if (isSelected) {
      card.setAttribute("aria-current", "true");
    } else {
      card.removeAttribute("aria-current");
    }
  });
}

function updateSelectedSeed(seedMovie = null) {
  const movie = seedMovie || movieById(state.activeSeedId);
  if (!movie) {
    elements.selectedSeed.hidden = true;
    elements.resultsTitle.textContent = "Recommended Matches";
    markSelectedCards();
    return;
  }

  elements.selectedSeed.hidden = false;
  elements.selectedSeedTitle.textContent = movie.title;
  elements.selectedSeedMeta.textContent = `${movie.year} | ${movie.genres.slice(0, 3).join(" / ")} | ${movie.rating.toFixed(1)} rating`;
  elements.resultsTitle.textContent = `Because You Picked ${movie.title}`;
  markSelectedCards();
}

function renderSkeleton(container, count = 8) {
  container.innerHTML = Array.from({ length: count }, () => '<div class="skeleton"></div>').join("");
}

function renderChips() {
  elements.genreChips.innerHTML = curatedGenres
    .map((genre) => `<button type="button" class="chip" data-kind="genres" data-value="${genre}">${genre}</button>`)
    .join("");
  elements.moodChips.innerHTML = curatedMoods
    .map((mood) => `<button type="button" class="chip" data-kind="moods" data-value="${mood}">${mood}</button>`)
    .join("");
}

function updateStats(stats) {
  elements.heroStats.innerHTML = `
    <span>${stats.movie_count} USA titles</span>
    <span>${stats.catalog_years.min}-${stats.catalog_years.max}</span>
    <span>${stats.genres.length} genres</span>
    <span>TF-IDF model</span>
  `;
}

function populateSeedSelect(movies) {
  const options = movies
    .slice()
    .sort((a, b) => a.title.localeCompare(b.title))
    .map((movie) => `<option value="${escapeHtml(movie.id)}">${escapeHtml(movie.title)} (${movie.year})</option>`)
    .join("");
  elements.seedSelect.insertAdjacentHTML("beforeend", options);
}

function setSpotlight(movie) {
  setPosterVars(elements.spotlightPoster, movie);
  elements.spotlightPoster.innerHTML = `<span>${escapeHtml(initials(movie.title))}</span>`;
  elements.spotlightTitle.textContent = movie.title;
  elements.spotlightMeta.textContent = `${movie.year} | ${movie.genres.slice(0, 3).join(" / ")} | ${movie.rating.toFixed(1)} model prior`;
  elements.spotlightSynopsis.textContent = movie.synopsis;
}

function renderResults(movies) {
  if (!movies.length) {
    elements.resultsGrid.innerHTML = '<div class="empty-state">No matches in this slice. Reset one filter and try again.</div>';
    return;
  }
  elements.resultsGrid.innerHTML = movies.map((movie) => movieCard(movie)).join("");
  applyPosterPalettes(elements.resultsGrid, movies);
  markSelectedCards();
}

function renderShelves(shelves) {
  elements.shelves.innerHTML = shelves
    .map(
      (shelf) => `
        <section class="shelf-row" aria-label="${escapeHtml(shelf.title)}">
          <h3>${escapeHtml(shelf.title)}</h3>
          <div class="shelf-scroll">
            ${shelf.movies.map((movie) => movieCard(movie, true)).join("")}
          </div>
        </section>
      `,
    )
    .join("");

  elements.shelves.querySelectorAll(".shelf-row").forEach((row, shelfIndex) => {
    applyPosterPalettes(row, shelves[shelfIndex].movies);
  });
  markSelectedCards();
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return response.json();
}

function recommendationParams() {
  const params = new URLSearchParams();
  const seed = elements.seedSelect.value;
  const vibe = elements.vibeInput.value.trim();
  if (seed) params.set("movie_id", seed);
  if (vibe) params.set("vibe", vibe);
  if (state.genres.size) params.set("genres", Array.from(state.genres).join(","));
  if (state.moods.size) params.set("moods", Array.from(state.moods).join(","));
  if (state.decade !== "all") params.set("decade", state.decade);
  params.set("limit", "12");
  return params;
}

async function loadRecommendations() {
  state.activeSeedId = elements.seedSelect.value;
  updateSelectedSeed();
  renderSkeleton(elements.resultsGrid, 8);
  elements.matchStatus.textContent = state.activeSeedId ? "Scoring similar titles" : "Scoring catalog";
  const data = await fetchJson(`/api/recommend?${recommendationParams().toString()}`);
  state.activeSeedId = data.seed_movie?.id || "";
  updateSelectedSeed(data.seed_movie);
  renderResults(data.movies);
  elements.matchStatus.textContent = data.seed_movie
    ? `${data.count} ML-ranked matches from ${data.seed_movie.title}`
    : `${data.count} ML-ranked matches`;
}

async function selectSeed(movieId, { scroll = true } = {}) {
  if (!movieId) return;
  const movie = movieById(movieId);
  state.activeSeedId = movieId;
  elements.seedSelect.value = movieId;
  updateSelectedSeed(movie);
  if (scroll) {
    elements.selectedSeed.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
  await loadRecommendations();
}

function toggleChip(button) {
  const set = state[button.dataset.kind];
  const value = button.dataset.value;
  if (set.has(value)) {
    set.delete(value);
    button.classList.remove("active");
    button.setAttribute("aria-pressed", "false");
  } else {
    set.add(value);
    button.classList.add("active");
    button.setAttribute("aria-pressed", "true");
  }
}

function resetControls() {
  state.genres.clear();
  state.moods.clear();
  state.decade = "all";
  state.activeSeedId = "";
  elements.seedSelect.value = "";
  elements.vibeInput.value = "";
  document.querySelectorAll(".chip.active").forEach((chip) => {
    chip.classList.remove("active");
    chip.setAttribute("aria-pressed", "false");
  });
  document.querySelectorAll(".segment").forEach((segment) => {
    segment.classList.toggle("active", segment.dataset.decade === "all");
  });
  updateSelectedSeed();
}

function bindEvents() {
  elements.form.addEventListener("submit", (event) => {
    event.preventDefault();
    loadRecommendations().catch(showError);
  });

  elements.resetButton.addEventListener("click", () => {
    resetControls();
    loadRecommendations().catch(showError);
  });

  elements.clearSeedButton.addEventListener("click", () => {
    state.activeSeedId = "";
    elements.seedSelect.value = "";
    updateSelectedSeed();
    loadRecommendations().catch(showError);
  });

  elements.seedSelect.addEventListener("change", () => {
    state.activeSeedId = elements.seedSelect.value;
    updateSelectedSeed();
    loadRecommendations().catch(showError);
  });

  document.addEventListener("click", (event) => {
    const chip = event.target.closest(".chip");
    if (chip) {
      toggleChip(chip);
      return;
    }

    const segment = event.target.closest(".segment");
    if (segment) {
      state.decade = segment.dataset.decade;
      document.querySelectorAll(".segment").forEach((node) => node.classList.toggle("active", node === segment));
      return;
    }

    const seedButton = event.target.closest(".seed-button");
    if (seedButton) {
      selectSeed(seedButton.dataset.seed).catch(showError);
      return;
    }

    const movieCardNode = event.target.closest(".movie-card");
    if (movieCardNode) {
      selectSeed(movieCardNode.dataset.movieId).catch(showError);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    if (event.target.closest("button, input, select, textarea")) return;
    const movieCardNode = event.target.closest(".movie-card");
    if (!movieCardNode) return;
    event.preventDefault();
    selectSeed(movieCardNode.dataset.movieId).catch(showError);
  });
}

function showError(error) {
  elements.matchStatus.textContent = "Something went sideways";
  elements.resultsGrid.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
}

async function init() {
  renderChips();
  renderSkeleton(elements.resultsGrid, 8);
  bindEvents();

  const [discover, catalog] = await Promise.all([
    fetchJson("/api/discover"),
    fetchJson("/api/movies?limit=200"),
  ]);

  state.discover = discover;
  state.movies = catalog.movies;
  updateStats(discover.stats);
  populateSeedSelect(catalog.movies);
  setSpotlight(discover.spotlight);
  renderShelves(discover.shelves);
  await loadRecommendations();
}

init().catch(showError);
