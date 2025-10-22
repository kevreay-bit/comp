import PropTypes from 'prop-types';

function formatTimeRemaining(ms) {
  if (!Number.isFinite(ms) || ms <= 0) {
    return 'Closed';
  }
  const totalSeconds = Math.floor(ms / 1000);
  const days = Math.floor(totalSeconds / (24 * 3600));
  const hours = Math.floor((totalSeconds % (24 * 3600)) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const parts = [];
  if (days) parts.push(`${days}d`);
  if (days || hours) parts.push(`${hours}h`);
  parts.push(`${minutes}m`);
  parts.push(`${seconds}s`);
  return parts.join(' ');
}

function formatOdds(odds) {
  if (!Number.isFinite(odds)) return '—';
  const pct = Math.max(0, Math.min(odds * 100, 100));
  return `${pct.toFixed(1)}%`;
}

function RaffleCard({ raffle, isBestOdds, isClosingSoon }) {
  const progress = raffle.maxEntries
    ? Math.min(100, Math.round(((raffle.entries ?? 0) / raffle.maxEntries) * 100))
    : null;

  return (
    <article
      className={`raffle-card${isBestOdds ? ' raffle-card--best-odds' : ''}${
        isClosingSoon ? ' raffle-card--closing-soon' : ''
      }`}
    >
      <div className="raffle-card__header">
        <div>
          <h2>{raffle.title}</h2>
          {raffle.subtitle ? <p className="raffle-card__subtitle">{raffle.subtitle}</p> : null}
        </div>
        <div className="raffle-card__tags">
          {isBestOdds ? <span className="tag tag--success">Best odds</span> : null}
          {isClosingSoon ? <span className="tag tag--warning">Closing soon</span> : null}
        </div>
      </div>

      {raffle.imageUrl ? (
        <img className="raffle-card__image" src={raffle.imageUrl} alt="" loading="lazy" />
      ) : null}

      <p className="raffle-card__description">{raffle.description}</p>

      <dl className="raffle-card__meta">
        <div>
          <dt>Time remaining</dt>
          <dd>{formatTimeRemaining(raffle.timeRemainingMs)}</dd>
        </div>
        <div>
          <dt>Chance to win</dt>
          <dd>{formatOdds(raffle.odds)}</dd>
        </div>
        <div>
          <dt>Entries</dt>
          <dd>
            {raffle.entries ?? 0}
            {raffle.maxEntries ? ` / ${raffle.maxEntries}` : null}
          </dd>
        </div>
      </dl>

      {progress !== null ? (
        <div
          className="raffle-card__progress"
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <div className="raffle-card__progress-bar" style={{ width: `${progress}%` }} />
          <span className="raffle-card__progress-label">{progress}% full</span>
        </div>
      ) : null}

      <footer className="raffle-card__footer">
        <button type="button" className="raffle-card__cta">
          View details
        </button>
      </footer>
    </article>
  );
}

RaffleCard.propTypes = {
  raffle: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    title: PropTypes.string.isRequired,
    subtitle: PropTypes.string,
    description: PropTypes.string,
    imageUrl: PropTypes.string,
    entries: PropTypes.number,
    maxEntries: PropTypes.number,
    timeRemainingMs: PropTypes.number.isRequired,
    odds: PropTypes.number.isRequired
  }).isRequired,
  isBestOdds: PropTypes.bool,
  isClosingSoon: PropTypes.bool
};

RaffleCard.defaultProps = {
  isBestOdds: false,
  isClosingSoon: false
};

export default RaffleCard;
