import { Link, useParams } from 'react-router'

export default function MemoryPage() {
  const { id } = useParams<'id'>()
  const isDemo = id === 'demo-01'

  return (
    <article aria-labelledby="memory-title" className="space-y-6">
      <div className="space-y-2">
        <h1 id="memory-title" tabIndex={-1} className="text-3xl font-bold sm:text-4xl">
          {isDemo ? 'Демо-воспоминание' : 'Воспоминание дня'}
        </h1>
        {isDemo && (
          <p className="text-(color:--color-text-muted)">Это демонстрационный пример. Он не сохранён в архиве.</p>
        )}
        <dl className="text-sm text-(color:--color-text-muted)">
          <div className="flex flex-wrap gap-x-2">
            <dt className="font-medium">Дата записи</dt>
            <dd>Пока недоступна</dd>
          </div>
          {id && (
            <div className="flex flex-wrap gap-x-2">
              <dt className="font-medium">ID записи</dt>
              <dd className="min-w-0 break-all">{id}</dd>
            </div>
          )}
        </dl>
      </div>

      <div className="grid items-start gap-6 md:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
        <figure className="grid aspect-[4/5] w-full max-w-[22rem] place-items-center justify-self-center rounded-(--radius-lg) border border-dashed border-(--color-border) bg-(--color-surface) p-4 text-center md:justify-self-start">
          <figcaption className="text-sm text-(color:--color-text-muted)">
            Здесь появится открытка дня
          </figcaption>
        </figure>

        <div className="space-y-4">
          <section aria-labelledby="memory-music-title" className="space-y-2 rounded-(--radius-md) border border-(--color-border) bg-(--color-surface) p-4">
            <h2 id="memory-music-title" className="text-lg font-semibold">Музыка</h2>
            <p id="memory-music-status" className="text-sm text-(color:--color-text-muted)">
              Проигрыватель пока недоступен.
            </p>
            <button
              type="button"
              disabled
              aria-describedby="memory-music-status"
              className="rounded-(--radius-sm) border border-(--color-border) px-3 py-2 text-sm text-(color:--color-text-muted) disabled:cursor-not-allowed"
            >
              Воспроизвести
            </button>
          </section>

          <section aria-labelledby="memory-explanation-title" className="space-y-2 rounded-(--radius-md) border border-(--color-border) bg-(--color-surface) p-4">
            <h2 id="memory-explanation-title" className="text-lg font-semibold">Почему так</h2>
            <p className="text-sm text-(color:--color-text-muted)">
              Здесь появится объяснение, как текст, фотография и музыка повлияли на открытку.
            </p>
          </section>
        </div>
      </div>

      <Link
        to="/"
        className="inline-block rounded-sm text-(color:--color-accent) underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-(--color-accent)"
      >
        Вернуться к созданию дня
      </Link>
    </article>
  )
}
