export function StatCard({ label, value, detail, accent = 'sun' }) {
  return (
    <article className={`stat-card stat-card--${accent}`}>
      <p className="stat-card__label">{label}</p>
      <h3>{value}</h3>
      <p className="stat-card__detail">{detail}</p>
    </article>
  )
}
