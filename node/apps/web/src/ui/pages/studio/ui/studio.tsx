"use client";
import { useStudioController } from "../model/studio.controller";
const labels = {
  queued: "В очереди",
  running: "Обрабатываем",
  succeeded: "Готово",
  failed: "Ошибка",
};
export function Studio() {
  const c = useStudioController();

  return (
    <main>
      <header>
        <span className="brand">FRAME / LAB</span>
        <span className="badge">IMAGE PLAYGROUND</span>
      </header>
      <section className="intro">
        <p className="eyebrow">МЕНЬШЕ ВЕС. ТОТ ЖЕ ХАРАКТЕР.</p>
        <h1>
          Изображения,
          <br />
          <span>в нужной форме.</span>
        </h1>
        <p>Измени размер и формат. Мы сохраним пропорции — тебе останется скачать результат.</p>
      </section>
      <div className="workspace">
        <form onSubmit={c.onSubmit} className="panel">
          <h2>
            <span className="step">01</span> Подготовить изображение
          </h2>
          <label className="upload">
            <span className="upload-symbol">↥</span>
            <strong>{c.file?.name ?? "Выбрать изображение"}</strong>
            <span>PNG, JPEG или WebP · до 10 МиБ и 16 Мп</span>
            <input
              aria-label="Изображение"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(e) => c.selectFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <div className="fields">
            <label>
              Макс. ширина
              <input
                type="number"
                min="1"
                max="4096"
                required
                value={c.width}
                onChange={(e) => c.changeWidth(Number(e.target.value))}
              />
            </label>
            <label>
              Макс. высота
              <input
                type="number"
                min="1"
                max="4096"
                required
                value={c.height}
                onChange={(e) => c.changeHeight(Number(e.target.value))}
              />
            </label>
            <label>
              Формат
              <select
                value={c.format}
                onChange={(e) => c.changeFormat(e.target.value as typeof c.format)}
              >
                <option value="webp">WebP</option>
                <option value="png">PNG</option>
                <option value="jpeg">JPEG</option>
              </select>
            </label>
          </div>
          <p className="hint">
            Изображение впишется в эти размеры. Прозрачность при конвертации в JPEG заменится белым
            фоном.
          </p>
          {c.error && (
            <p role="alert" className="error">
              {c.error}
            </p>
          )}
          <button disabled={c.submit.isPending || !c.file}>
            {c.submit.isPending ? "Отправляем…" : "Обработать изображение"} <span>↗</span>
          </button>
        </form>
        <section className="panel history">
          <h2>
            <span className="step">02</span> Результаты
          </h2>
          {c.jobs.isPending ? (
            <p className="empty">Загружаем историю…</p>
          ) : c.jobs.error ? (
            <p role="alert" className="error">
              Сервис временно недоступен.
            </p>
          ) : !c.jobs.data?.length ? (
            <div className="empty">
              <span>▧</span>
              <p>Здесь появятся твои изображения.</p>
              <small>Первый результат начинается с загрузки.</small>
            </div>
          ) : (
            <ul>
              {c.jobs.data.map((job) => (
                <li key={job.id}>
                  <div>
                    <strong>
                      {job.width} × {job.height} <span className="format">{job.format}</span>
                    </strong>
                    <small>
                      {job.id.slice(0, 8)} · {labels[job.status]}
                    </small>
                    {job.error && <p className="error">{job.error}</p>}
                  </div>
                  {job.status === "succeeded" && (
                    <a href={`/api/jobs/${job.id}/result`} download>
                      Скачать ↙
                    </a>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
      <footer>
        FRAME / LAB<span>Учебная студия обработки изображений</span>
      </footer>
    </main>
  );
}
