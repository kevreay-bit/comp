import { useMemo, useState, useEffect } from 'react';
import { useRaffles } from './hooks/useRaffles.js';
import RaffleCard from './components/RaffleCard.jsx';
import './styles/app.css';

const TIME_FILTERS = {
  all: { label: 'Any time', predicate: () => true },
  '24h': {
    label: 'Ending within 24h',
    predicate: (raffle) => raffle.timeRemainingMs <= 24 * 60 * 60 * 1000
  },
  '1h': {
    label: 'Ending within 1h',
    predicate: (raffle) => raffle.timeRemainingMs <= 60 * 60 * 1000
  }
};

const ODDS_FILTERS = {
  all: { label: 'All odds', predicate: () => true },
  favorable: {
    label: 'Favorable (≥ 25%)',
    predicate: (raffle) => raffle.odds >= 0.25
  },
  great: {
    label: 'Great (≥ 50%)',
    predicate: (raffle) => raffle.odds >= 0.5
  }
};

const SORTERS = {
  'deadline-asc': {
    label: 'Soonest deadline',
    compare: (a, b) => a.deadlineMs - b.deadlineMs
  },
  'deadline-desc': {
    label: 'Latest deadline',
    compare: (a, b) => b.deadlineMs - a.deadlineMs
  },
  'odds-desc': {
    label: 'Best odds',
    compare: (a, b) => b.odds - a.odds
  },
  'odds-asc': {
    label: 'Longest shots',
    compare: (a, b) => a.odds - b.odds
  },
  'title-asc': {
    label: 'Title A → Z',
    compare: (a, b) => a.title.localeCompare(b.title)
  }
};

function computeOdds(raffle) {
  const entries = Number(raffle.entries ?? 0);
  const maxEntries = Number(raffle.maxEntries ?? 0);
  if (maxEntries > 0) {
    const remaining = Math.max(maxEntries - entries, 0);
    return remaining / maxEntries;
  }
  if (entries <= 0) {
    return 1;
  }
  return 1 / entries;
}

function App() {
  const { raffles, loading, error, refetch } = useRaffles();
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('deadline-asc');
  const [oddsFilter, setOddsFilter] = useState('all');
  const [timeFilter, setTimeFilter] = useState('all');
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const tick = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(tick);
  }, []);

  const enhancedRaffles = useMemo(() => {
    const currentTime = now.getTime();
    return raffles.map((raffle) => {
      const deadlineMs = new Date(raffle.deadline).getTime();
      const timeRemainingMs = Math.max(deadlineMs - currentTime, 0);
      const odds = computeOdds(raffle);
      return {
        ...raffle,
        deadlineMs,
        timeRemainingMs,
        odds
      };
    });
  }, [raffles, now]);

  const bestOddsValue = useMemo(() => {
    return enhancedRaffles.reduce((acc, raffle) => Math.max(acc, raffle.odds), 0);
  }, [enhancedRaffles]);

  const soonestDeadline = useMemo(() => {
    return enhancedRaffles
      .filter((raffle) => raffle.timeRemainingMs > 0)
      .reduce((acc, raffle) => Math.min(acc, raffle.timeRemainingMs), Infinity);
  }, [enhancedRaffles]);

  const filteredRaffles = useMemo(() => {
    const oddsPredicate = ODDS_FILTERS[oddsFilter]?.predicate ?? ODDS_FILTERS.all.predicate;
    const timePredicate = TIME_FILTERS[timeFilter]?.predicate ?? TIME_FILTERS.all.predicate;

    const normalizedSearch = searchTerm.trim().toLowerCase();
    return enhancedRaffles.filter((raffle) => {
      const title = (raffle.title ?? '').toLowerCase();
      const matchesSearch = title.includes(normalizedSearch);
      return matchesSearch && oddsPredicate(raffle) && timePredicate(raffle);
    });
  }, [enhancedRaffles, oddsFilter, timeFilter, searchTerm]);

  const sortedRaffles = useMemo(() => {
    const sorter = SORTERS[sortBy]?.compare ?? SORTERS['deadline-asc'].compare;
    return [...filteredRaffles].sort(sorter);
  }, [filteredRaffles, sortBy]);

  return (
    <div className="app-shell">
      <header className="header">
        <div className="header__titles">
          <h1>Raffle Control Center</h1>
          <p className="header__subtitle">
            Monitor live raffles, spot the best odds, and never miss a closing deadline.
          </p>
        </div>
        <div className="header__actions">
          <button className="refresh-button" type="button" onClick={refetch} disabled={loading}>
            Refresh
          </button>
        </div>
      </header>

      <section className="toolbar">
        <label className="toolbar__item search">
          <span>Search</span>
          <input
            type="search"
            placeholder="Search raffle titles"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
        </label>
        <label className="toolbar__item">
          <span>Sort by</span>
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            {Object.entries(SORTERS).map(([key, { label }]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="toolbar__item">
          <span>Odds</span>
          <select value={oddsFilter} onChange={(event) => setOddsFilter(event.target.value)}>
            {Object.entries(ODDS_FILTERS).map(([key, { label }]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="toolbar__item">
          <span>Deadline</span>
          <select value={timeFilter} onChange={(event) => setTimeFilter(event.target.value)}>
            {Object.entries(TIME_FILTERS).map(([key, { label }]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </section>

      {error ? <div className="banner banner--error">{error}</div> : null}

      <section className="dashboard">
        {loading && raffles.length === 0 ? (
          <div className="empty-state">Loading raffles…</div>
        ) : sortedRaffles.length === 0 ? (
          <div className="empty-state">No raffles match your filters.</div>
        ) : (
          <div className="raffle-grid">
            {sortedRaffles.map((raffle) => (
              <RaffleCard
                key={raffle.id}
                raffle={raffle}
                isBestOdds={raffle.odds === bestOddsValue && bestOddsValue > 0}
                isClosingSoon={
                  (Number.isFinite(soonestDeadline) && raffle.timeRemainingMs === soonestDeadline) ||
                  raffle.timeRemainingMs <= 60 * 60 * 1000
                }
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default App;
