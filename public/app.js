const raffleGrid = document.getElementById('raffle-grid');
const status = document.getElementById('status');
const sortSelect = document.getElementById('sort');
const maxOddsRange = document.getElementById('odds');
const maxOddsValue = document.getElementById('odds-value');
const endsBeforeInput = document.getElementById('ends-before');
const searchInput = document.getElementById('search');

const POLL_INTERVAL = 10_000;
let pollHandle;
let lastResponse = [];

const formatPercent = (value) => `${value.toFixed(1)}%`;

function buildQuery() {
  const params = new URLSearchParams();
  const sort = sortSelect.value;
  if (sort) {
    params.set('sort', sort);
  }

  const maxOdds = Number(maxOddsRange.value);
  if (!Number.isNaN(maxOdds) && maxOdds < Number(maxOddsRange.max)) {
    params.set('max_odds', maxOdds.toString());
  }

  if (endsBeforeInput.value) {
    const isoString = new Date(endsBeforeInput.value).toISOString();
    if (isoString) {
      params.set('ends_before', isoString);
    }
  }

  return params.toString();
}

async function fetchRaffles() {
  const query = buildQuery();
  const endpoint = query ? `/api/raffles?${query}` : '/api/raffles';
  status.textContent = 'Loading raffles…';
  try {
    const response = await fetch(endpoint);
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    const payload = await response.json();
    lastResponse = payload.data;
    renderRaffles(applySearchFilter(payload.data));
    const refreshTime = new Date(payload.meta.generatedAt).toLocaleTimeString();
    status.textContent = `Showing ${payload.meta.count} of ${payload.meta.total} raffles • Updated ${refreshTime}`;
  } catch (error) {
    console.error(error);
    status.textContent = 'Unable to load raffles. Please try again later.';
  }
}

function applySearchFilter(list) {
  const searchTerm = searchInput.value.trim().toLowerCase();
  if (!searchTerm) {
    return list;
  }
  return list.filter((raffle) =>
    raffle.name.toLowerCase().includes(searchTerm) ||
    raffle.description.toLowerCase().includes(searchTerm)
  );
}

function renderRaffles(raffles) {
  raffleGrid.innerHTML = '';
  if (!raffles.length) {
    raffleGrid.innerHTML = '<p class="empty">No raffles match your filters.</p>';
    return;
  }

  const minOdds = Math.min(...raffles.map((raffle) => raffle.odds));
  const soonestDeadline = raffles
    .map((raffle) => new Date(raffle.deadline))
    .sort((a, b) => a - b)[0];
  const urgentThreshold = Date.now() + 1000 * 60 * 60 * 3; // within 3 hours

  raffles.forEach((raffle) => {
    const card = document.createElement('article');
    card.className = 'raffle-card';

    const isBestOdds = Math.abs(raffle.odds - minOdds) < 0.001;
    const deadlineDate = new Date(raffle.deadline);
    const isUrgent = deadlineDate.getTime() === soonestDeadline.getTime() || deadlineDate.getTime() <= urgentThreshold;

    if (isBestOdds) {
      card.classList.add('highlight-odds');
    }
    if (isUrgent) {
      card.classList.add('highlight-deadline');
    }

    card.innerHTML = `
      <div>
        <h2>${raffle.name}</h2>
        <p>${raffle.description}</p>
      </div>
      <div class="raffle-meta">
        <span class="badge badge-odds">Odds ${formatPercent(raffle.odds)}</span>
        <span class="badge badge-deadline">Ends ${new Date(raffle.deadline).toLocaleString()}</span>
        <span class="badge">Prize: ${raffle.prize}</span>
      </div>
      <small>Updated ${new Date(raffle.updatedAt).toLocaleTimeString()}</small>
    `;

    raffleGrid.appendChild(card);
  });
}

function startPolling() {
  stopPolling();
  pollHandle = setInterval(fetchRaffles, POLL_INTERVAL);
}

function stopPolling() {
  if (pollHandle) {
    clearInterval(pollHandle);
    pollHandle = undefined;
  }
}

// Input events
sortSelect.addEventListener('change', fetchRaffles);
maxOddsRange.addEventListener('input', () => {
  maxOddsValue.textContent = formatPercent(Number(maxOddsRange.value));
});
maxOddsRange.addEventListener('change', fetchRaffles);
endsBeforeInput.addEventListener('change', fetchRaffles);
searchInput.addEventListener('input', () => {
  renderRaffles(applySearchFilter(lastResponse));
});

document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    stopPolling();
  } else {
    fetchRaffles();
    startPolling();
  }
});

maxOddsValue.textContent = formatPercent(Number(maxOddsRange.value));
fetchRaffles();
startPolling();
