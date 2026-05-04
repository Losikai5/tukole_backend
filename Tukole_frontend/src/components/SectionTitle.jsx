export function SectionTitle({ eyebrow, title, description, action }) {
  return (
    <div className="section-title">
      <div>
        {eyebrow ? <p className="section-title__eyebrow">{eyebrow}</p> : null}
        <h2>{title}</h2>
        {description ? <p className="section-title__description">{description}</p> : null}
      </div>
      {action ? <div className="section-title__action">{action}</div> : null}
    </div>
  )
}
