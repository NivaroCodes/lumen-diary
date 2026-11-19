import { Link } from 'react-router'

const entrySections = [
  {
    id: 'day-text',
    title: 'Текст',
    description: 'Здесь можно будет рассказать, как прошёл день и что запомнилось.',
  },
  {
    id: 'day-photos',
    title: 'Фотографии',
    description: 'Здесь можно будет загрузить фотографии этого дня.',
  },
  {
    id: 'day-music',
    title: 'Музыка',
    description: 'Здесь можно будет добавить ссылку на композицию и кратко описать её.',
  },
]

export default function CreateDayPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 tabIndex={-1} className="text-3xl font-bold sm:text-4xl">Новый день</h1>
        <p className="max-w-prose text-(color:--color-text-muted)">
          Соберите воспоминания о дне. Текст, фотографии и музыка станут основой вашей открытки.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {entrySections.map(({ id, title, description }) => (
          <section
            key={id}
            aria-labelledby={id}
            className="space-y-2 rounded-(--radius-md) border border-(--color-border) bg-(--color-surface) p-4 sm:p-5"
          >
            <h2 id={id} className="text-lg font-semibold">{title}</h2>
            <p className="text-sm text-(color:--color-text-muted)">{description}</p>
          </section>
        ))}
      </div>

      <div className="space-y-2">
        <button
          type="button"
          disabled
          aria-describedby="create-postcard-status"
          className="w-full rounded-(--radius-sm) border border-(--color-border) bg-(--color-surface) px-4 py-2.5 text-sm font-medium text-(color:--color-text-muted) disabled:cursor-not-allowed sm:w-auto"
        >
          Создать открытку
        </button>
        <p id="create-postcard-status" className="text-sm text-(color:--color-text-muted)">
          Создание открытки пока недоступно.
        </p>
        <Link
          to="/memory/demo-01"
          className="inline-block rounded-sm text-(color:--color-accent) underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-(--color-accent)"
        >
          Посмотреть демо-воспоминание
        </Link>
      </div>
    </div>
  )
}
