import { useEffect, useRef } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router'

const navLinkClassName = 'rounded-sm py-1 underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-(--color-accent) aria-[current=page]:text-(color:--color-accent) aria-[current=page]:underline'

export default function Layout() {
  const { pathname } = useLocation()
  const mainRef = useRef<HTMLElement>(null)
  const previousPathname = useRef(pathname)

  useEffect(() => {
    const heading = mainRef.current?.querySelector('h1')
    if (!heading?.textContent) return

    document.title = `${heading.textContent} · Lumen Diary`

    if (previousPathname.current !== pathname) {
      previousPathname.current = pathname
      heading.focus()
    }
  }, [pathname])

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-(--color-border) bg-(--color-surface)">
        <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
          <Link to="/" className="rounded-sm text-lg font-semibold focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-(--color-accent)">
            Lumen Diary
          </Link>

          <nav aria-label="Основная навигация" className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
            <NavLink to="/" end className={navLinkClassName}>
              Новый день
            </NavLink>
            <NavLink to="/archive" end className={navLinkClassName}>
              Архив
            </NavLink>
          </nav>
        </div>
      </header>

      <main ref={mainRef} className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 py-8 sm:px-6">
        <Outlet />
      </main>

      <footer className="border-t border-(--color-border) text-sm text-(color:--color-text-muted)">
        <div className="mx-auto w-full max-w-5xl px-4 py-4 sm:px-6">
          Genesis Hackathon 2026 · ArtTech
        </div>
      </footer>
    </div>
  )
}
