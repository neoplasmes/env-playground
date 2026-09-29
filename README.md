# Image playground

Учебная обработка изображений и воспроизводимый кластер в Cloud.ru Evolution.
Next.js принимает файл через BFF, Rust сохраняет задание в SQLite, Python выполняет
преобразование через Pillow. Браузер опрашивает состояние и скачивает результат.

Поддерживаются PNG, JPEG и WebP: вход до 10 МиБ и 16 мегапикселей, выход вписывается
в прямоугольник до 4096×4096 с сохранением пропорций. Анимация отклоняется,
ориентация EXIF учитывается, метаданные удаляются. В окружении максимум 50 заданий.
Это ограниченный playground: удаления отдельных заданий и отдельных аккаунтов пока нет.

## Что делать сейчас

1. Файл `.secrets/local.env` уже подготовлен командой `moon run infra:prepare`.
   Заполни `TF_VAR_auth_key_id`, `TF_VAR_auth_secret` и `TF_VAR_admin_cidr`.
   Последнее значение — твой внешний IPv4 с `/32`, например `203.0.113.10/32`.
   Значения секретов заключай в одинарные кавычки: это shell-файл.
2. В Cloud.ru нужен API-ключ сервисного аккаунта с правами управления Compute и
   сетями проекта `d644930d-f129-41bc-a1f2-4715cff2b478`.
   Ключ и secret вводи только локально, не в чат и не в Git.
3. Проверь в личном кабинете оставшиеся бонусы, срок их действия и начисления.
   Квоты уже подтверждены; повторно запрашивать их не нужно.
4. Затем выполни каталог и план из раздела ниже. Создание ВМ — отдельная команда.

## Инструменты и локальная разработка

Языковые зависимости и lockfiles лежат в `node/`, `python/`, `rust/`.
Версии инструментов закреплены в `.prototools`; команды проекта запускаются через moon.
На текущем компьютере установлен отдельный набор инструментов в `.cache/proto`:

```bash
source node/activate.sh
moon run playground:check
moon run playground:test
moon run playground:format
```

В новом checkout: установи proto по [официальной инструкции](https://moonrepo.dev/docs/proto/install),
затем `proto upgrade 0.62.3`, `proto install`. Используй активацию своего proto;
`activate.sh` выше предназначен именно для инструментов в локальном `.cache`.
Общие Node-инструменты (commitlint и браузерные тесты Playwright) находятся
в `node/`. Проверки: `moon run playground:node-check` и
`moon run playground:browser-test`; подключение Git hook:
`moon run playground:node-hooks` после установки зависимостей. Инструменты агентов
настраиваются отдельно по [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md).

Для нативной сборки Rust нужен C-компилятор и заголовки libc, поскольку SQLite
собирается вместе с приложением. На Ubuntu: `sudo apt install build-essential`.
Для контейнерного запуска нужен Docker с Compose и BuildKit.

```bash
moon run playground:up        # собрать и запустить; открыть http://localhost:3000
moon run playground:down      # остановить; локальные данные остаются в Docker volume
moon run playground:smoke     # HTTP-проверка трёх сервисов с временной БД без Docker
```

Для разработки в трёх терминалах: `moon run image-processor:dev`,
`moon run image-api:dev`, `moon run web:dev`. Порты: 8081, 8080, 3000.
Облачная Basic Auth в локальном Compose не используется: он слушает только localhost.

Фронт проверяется **oxlint**, форматируется **oxfmt**. ESLint не устанавливается.
JS-плагин `@stylistic/eslint-plugin` подключён к oxlint, как поддерживает его
[механизм JS plugins](https://oxc.rs/docs/guide/usage/linter/js-plugins).
Правило из `~/qualification_work` требует пустую строку перед `return`, `throw`,
`break`, `continue`, когда это не первый оператор блока.

Для Python аналог проверяет `return`, `raise`, `break`, `continue` через AST;
для Rust — `return`, `break`, `continue` через tree-sitter. Rust tail expressions
и непрозрачное содержимое макросов не проверяются. `moon run repo-style:check`
проверяет, `moon run repo-style:fix` вставляет строки. Сначала запускай стандартные
форматтеры через `playground:format`: они разбивают несколько операторов на одной строке.
Проверка padding входит в обычные проверки и Woodpecker.

## Создать облако

```bash
moon run infra:catalog
```

Каталог читает доступные образы и конфигурации ВМ, не создавая ресурсов.
Выбери доступную зону, Ubuntu и размеры машин. В `.secrets/local.env` можно добавить
`TF_VAR_zone`, `TF_VAR_image_name`, `TF_VAR_control_plane_flavor`, `TF_VAR_worker_flavor`.
Значения `gen-2-4`, `gen-4-8`, `ubuntu-24.04` в конфиге — исходные кандидаты;
их доступность в твоём аккаунте должен подтвердить каталог.

Стартовый размер: control-plane 2 vCPU / 4 ГиБ и worker 4 vCPU / 8 ГиБ.
Создаются два загрузочных SSD на 30 и 50 ГБ, два публичных IPv4, VPC, подсеть и security group.
HTTP/HTTPS открыты снаружи, SSH и Kubernetes API — только для указанного `/32`.
У второго узла собственный IP для доступа в интернет: отдельный NAT не нужен.

Посчитай выбранные ВМ, диски, оба IPv4 и исходящий трафик в калькуляторе/консоли
Cloud.ru. Из суммы бонусов нельзя вывести срок работы без текущего тарифа.
Бюджетное уведомление само по себе не выключает кластер.

```bash
moon run infra:init
moon run infra:plan          # сохранить и посмотреть .local/create.tfplan
moon run infra:apply         # создать именно просмотренный план; начнётся тарификация
moon run infra:cluster       # установить k3s и сохранить .secrets/kubeconfig
```

Terraform state хранится на твоём компьютере в `.local/terraform.tfstate`, вне
удаляемого кластера. Сохраняй зашифрованную резервную копию `.local` и `.secrets`.
Не запускай облачные изменения с нескольких компьютеров: пока backend локальный.
При изменении ключей или параметров создавай новый plan. Kubeconfig даёт права
администратора и также является секретом.

## Подключить GitHub, HTTPS и Woodpecker

После создания ВМ `infra:cluster` покажет callback вида
`https://ci.<IP-с-дефисами>.sslip.io/authorize`.

1. Создай GitHub OAuth App: Homepage URL — этот адрес без `/authorize`,
   Authorization callback URL — полный адрес с `/authorize`.
2. Запиши Client ID и secret в `WOODPECKER_GITHUB_CLIENT` и `WOODPECKER_GITHUB_SECRET`.
   В `ACME_EMAIL` укажи email для Let's Encrypt.
3. Для GHCR создай токен с `write:packages` и `read:packages`, запиши его в
   `REGISTRY_TOKEN`; `REGISTRY_USER=neoplasmes`. Для чтения PR и статусов нужен
   отдельный `GITHUB_TOKEN` с доступом на чтение contents, pull requests и commit statuses
   этого репозитория. Clone поддерживает и приватный репозиторий: токен передаётся
   через окружение Git, а не записывается в его remote URL.
4. Выполни `moon run infra:platform`. Скрипт устанавливает cert-manager,
   Woodpecker server/agent и BuildKit; секретные значения не печатаются.
5. Войди в Woodpecker через GitHub и активируй `neoplasmes/env-playground`.
   Путь конфигурации — `.woodpecker/`. Запуски из fork требуют ручного одобрения,
   автоматические preview создаются только для PR из этого же репозитория.

Первый образ инструментов собирается с твоего компьютера, поскольку новый CI
ещё не может собрать сам себя. В отдельном терминале авторизуй Docker в GHCR:

```bash
set -a
source .secrets/local.env
set +a
printf '%s' "$REGISTRY_TOKEN" | docker login ghcr.io -u "$REGISTRY_USER" --password-stdin
moon run infra:toolchain-push
```

Далее добавь в Woodpecker следующие **repository secrets**. Для всех разреши
**только событие `cron`**, отключив остальные события, включая `push` и `pull_request`.
Pipeline-фильтр в YAML не заменяет фильтр самого секрета.
Доступ к изменению cron/настроек CI должен быть только у доверенных участников.

| Имя в Woodpecker | Значение |
| --- | --- |
| `github_read_token` | `GITHUB_TOKEN` |
| `registry_token` | `REGISTRY_TOKEN` |
| `deploy_kubeconfig` | содержимое `.secrets/deploy-kubeconfig.json` |
| `buildkit_ca` | содержимое `.secrets/buildkit/ca.pem` |
| `buildkit_cert` | содержимое `.secrets/buildkit/client.pem` |
| `buildkit_key` | содержимое `.secrets/buildkit/client.key` |
| `playground_domain` | `<IP-с-дефисами>.sslip.io`, без `https://` |

Создай cron с именем **`reconcile`**, веткой **`master`**, расписанием `@every 5m`.
Он запускает доверенный код доставки из master. В GitHub защити master и запрети
несогласованные изменения CI-файлов. Настройки секретов описаны в
[документации Woodpecker](https://woodpecker-ci.org/docs/usage/secrets),
расписание — в [документации cron](https://woodpecker-ci.org/docs/usage/cron).

Проверки PR выполняются без deploy-секретов. Следующий запуск reconcile берёт
успешно проверенный SHA, собирает образы через BuildKit и устанавливает Helm chart
из master. При изменении SHA во время сборки устаревшая версия не разворачивается.
Приложения получают digest образа, а не изменяемый тег. Agent выполняет один workflow
за раз; не увеличивай параллелизм без добавления блокировки доставки.

## Окружения и удаление

| Адрес | Окружение |
| --- | --- |
| `ci.<IP>.sslip.io` | Woodpecker |
| `dev.<IP>.sslip.io` | Последний проверенный master, после очередного reconcile |
| `prod.<IP>.sslip.io` | Ручное продвижение образов из dev: `moon run infra:promote` |
| `pr-42.<IP>.sslip.io` | Preview PR №42 |

Здесь `<IP>` — адрес с дефисами. Максимум три preview; остальные ждут свободного
места. Используются заранее созданные namespace `preview-1..3`, чтобы deploy-токен
не имел права создавать namespace и менять кластерные роли. PR сохраняет свой слот.
Закрытый/слитый/draft PR очищается при следующем reconcile, вместе с PVC заданиями;
сам пустой namespace и его служебные секреты остаются. Эта же очистка работает после простоя CI.

Приложения защищены общей Basic Auth: пользователь `playground`, пароль в
`.secrets/playground-password`. Namespace имеют квоты, NetworkPolicy и отдельные БД.
Сервисные аккаунты приложений и CI-задач не получают Kubernetes API token.
Это один учебный кластер без HA; `prod` здесь не означает промышленную надёжность.
Rootless BuildKit требует Unconfined seccomp/AppArmor, но не получает host socket
или cluster-admin. Его API защищён клиентскими сертификатами, действующими год.

```bash
moon run infra:destroy-plan   # посмотреть полный список удаляемого
moon run infra:destroy        # удалить ВМ, диски, IPv4 и сети из Terraform state
```

Полный teardown удаляет **все изображения, историю заданий и БД Woodpecker** вместе
с дисками. GHCR-образы, GitHub OAuth App, файлы на твоём компьютере остаются.
У GHCR пока нет автоматической очистки старых образов. После destroy проверь,
что в облачном кабинете не осталось ресурсов этого playground и начислений за них.
Сломавшийся destroy запускай повторно; не удаляй state, чтобы «починить» ошибку.

При пересоздании IP может поменяться: обнови OAuth callback, адрес Woodpecker,
webhook в GitHub и CI secrets. Заново выполни cluster/platform и активируй репозиторий.
SSH host key тоже поменяется; удаляй запись только этого IP из `.local/known_hosts`
после проверки, что это новая ВМ. `local-path` PVC привязан к узлу и не переживает
его удаление; резервирование данных и миграция между узлами пока не реализованы.

## Проверенный статус

Локально проверены oxlint/oxfmt/TypeScript, Ruff/ty, Clippy, тесты Python/Rust/фронта,
правило padding, логика preview, Terraform validate и Helm lint/template.
Также прошёл HTTP smoke: загрузка через BFF, идемпотентность задания, обработка
и скачивание результата в PNG/JPEG/WebP. Браузерный E2E также прошёл: преобразование и скачивание WebP, отказ для
слишком большого файла и обработка повреждённого изображения.
Cloud.ru apply, установка платформы и работа webhooks требуют твоих credentials
и ещё не выполнялись. Полная сборка Docker пока заблокирована: Docker daemon
не может скачать слой с Docker Hub по IPv6 (`network is unreachable`).
Публичный образ GHCR успешно прочитан с отдельным `DOCKER_CONFIG`; сохранённую
Docker-авторизацию и настройки daemon на компьютере не меняли.
