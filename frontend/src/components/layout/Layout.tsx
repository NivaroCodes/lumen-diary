import { useEffect, useRef } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router'

export default function Layout() {
  const { pathname } = useLocation()
  const mainRef = useRef<HTMLElement>(null)
  const previousPathname = useRef(pathname)

  useEffect(() => {
    const heading = mainRef.current?.querySelector('h1')
    if (!heading?.textContent) return

    document.title = `${heading.getAttribute('aria-label') ?? heading.textContent} · Lumen Diary`

    if (previousPathname.current !== pathname) {
      previousPathname.current = pathname
      heading.focus({ preventScroll: true })
      window.scrollTo({ top: 0 })
    }
  }, [pathname])

  return (
    <div className="site">
      <a href="#main" className="skip-link">К содержанию</a>
      <header className="site-header">
        <div className="site-bar">
          <Link to="/" className="site-mark" viewTransition>Lumen Diary</Link>
          <nav aria-label="Основная навигация" className="site-nav">
            <NavLink to="/" end viewTransition>Новый день</NavLink>
            <NavLink to="/archive" end viewTransition>Архив</NavLink>
          </nav>
        </div>
      </header>

      <main id="main" ref={mainRef} className="site-main">
        <Outlet />
      </main>

      <footer className="site-footer">
        <div className="site-bar">
          <p>Команда Kernel, Genesis Hackathon 2026, трек ArtTech</p>
          <p>Записи и фото хранятся только на этом компьютере.</p>
        </div>
      </footer>
    </div>
  )
}
