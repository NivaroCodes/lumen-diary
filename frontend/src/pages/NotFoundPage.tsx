import { Link } from 'react-router'

export default function NotFoundPage() {
  return (
    <div style={{ paddingTop: 24 }}>
      <h1 tabIndex={-1} className="page-title">Такой страницы нет</h1>
      <p className="page-lede">Возможно, ссылка устарела. Начните новый день или найдите прошлый в архиве.</p>
      <p style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 24 }}>
        <Link to="/" className="btn btn-solid" viewTransition>Записать день</Link>
        <Link to="/archive" className="btn" viewTransition>Открыть архив</Link>
      </p>
    </div>
  )
}
