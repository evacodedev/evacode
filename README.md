# Evacode

Интернет-магазин корейской косметики. Репозиторий является **monorepo**: Django API, Nuxt-витрина и Docker-инфраструктура находятся здесь в одном Git-репозитории.

## Содержание

- [Стек](#стек)
- [Архитектура](#архитектура)
- [Структура репозитория](#структура-репозитория)
- [Требования](#требования)
- [Переменные окружения](#переменные-окружения)
- [Запуск для разработки](#запуск-для-разработки)
- [Запуск production-версии](#запуск-production-версии)
- [Работа с Docker](#работа-с-docker)
- [Django и API](#django-и-api)
- [Разработка frontend](#разработка-frontend)
- [Обновление и Git-процесс](#обновление-и-git-процесс)
- [Диагностика](#диагностика)

Инструкция по переносу действующего VPS со старого репозитория с Git-сабмодулем: [MIGRATION_TO_NEW_REPOSITORY.md](MIGRATION_TO_NEW_REPOSITORY.md).

## Стек

| Область | Технологии |
| --- | --- |
| Frontend | Nuxt 3, Vue 3, Pinia, Vite, Bootstrap 5, Sass, Bun |
| Backend | Python 3.11, Django 5, Django REST Framework, Gunicorn |
| Данные | PostgreSQL, Django migrations |
| Инфраструктура | Docker Compose, Nginx, Let's Encrypt/Certbot |
| Интеграции | Business.Ru, Telegram Bot API, YooKassa, Toss Payments |

## Архитектура

```text
Пользователь
    |
    v
Nginx :80/:443
    |-- /              -> Nuxt SSR frontend (контейнер frontend:3000)
    |-- /api/, /admin/ -> Django API (контейнер server:8000)
    |-- /static/       -> Docker volume static
    `-- /media/        -> Docker volume media

Django API
    |-- core    -> контент сайта: баннеры, доставка, контакты, отзывы, валюты
    |-- market  -> каталог, категории, остатки, заявки/заказы, Business.Ru, Telegram
    `-- finance -> счета и callbacks платежей Toss Payments/YooKassa

PostgreSQL <- Django migrations и данные каталога
```

Frontend получает публичные данные через REST API. Базовый URL API задается переменной `BASE_API_URL`; Nuxt передает ее в `runtimeConfig.public.apiBase`.

## Структура репозитория

```text
.
├── src/                         # Django-проект
│   ├── evacode_backend/          # settings, корневые URL, WSGI/ASGI
│   ├── core/                     # контентные сущности и REST API
│   ├── market/                   # каталог, импорт Business.Ru, checkout
│   └── finance/                  # платежные модели и callbacks
├── evacode.org/                  # Nuxt frontend
│   ├── pages/                    # маршруты Nuxt
│   ├── components/               # UI-компоненты
│   ├── store/                    # Pinia stores
│   ├── public/                   # изображения и видео
│   └── assets/                   # Sass, шрифты, CSS
├── dockerfiles/                  # Dockerfile backend и Nginx-конфигурация
├── docker-compose.yml            # production-стек
├── docker-compose.dev.yml        # backend/БД/Nginx для разработки
├── .env.template                 # шаблон backend-конфигурации
└── init-letsencrypt.sh           # первичная настройка Let's Encrypt
```

`evacode.org` — обычная папка, а не Git-сабмодуль. Изменения frontend и backend коммитятся и пушатся из корня этого репозитория.

## Требования

- Docker Engine и Docker Compose v2;
- Bun 1.x для локального запуска frontend;
- Git;
- открытые порты `80` и `443` для production;
- домен, указывающий на VPS, если используется HTTPS.

Проверка инструментов:

```bash
docker --version
docker compose version
bun --version
```

## Переменные окружения

Секреты не хранятся в Git. Корневые `.env` и `.env2`, а также `evacode.org/.env` игнорируются через `.gitignore`.

### Backend и PostgreSQL

Создайте файлы из шаблона:

```bash
cp .env.template .env
cp .env.template .env2
```

Основные переменные:

| Переменная | Назначение | Примечание |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | секрет Django | обязательна в production |
| `DJANGO_DEBUG_MODE` | режим отладки | `false` в production |
| `DB_TYPE` | драйвер БД | для Docker: `postgres` |
| `POSTGRES_DB` | имя БД | используется PostgreSQL и Django |
| `POSTGRES_USER` | пользователь БД | используется PostgreSQL и Django |
| `POSTGRES_PASSWORD` | пароль БД | используется PostgreSQL и Django |
| `DB_HOST` | хост PostgreSQL | `.env`: `db`; `.env2`: `localhost` для production-сервиса импорта |
| `DB_PORT` | порт PostgreSQL | обычно `5432` |
| `DJANGO_STATIC_ROOT` | каталог собранной статики | production: `/www/data/static` |
| `DJANGO_MEDIA_ROOT` | каталог пользовательских медиа | production: `/www/data/media` |
| `DJANGO_SUPERUSER_*` | учетная запись администратора | нужны для `createsuperuser --noinput` |

### Внешние интеграции

| Переменная | Используется для |
| --- | --- |
| `APP_ID`, `API_SECRET` | импорт категорий и товаров из Business.Ru |
| `BOT_TOKEN`, `CHAT_ID` | уведомления о заказах в Telegram |
| `TOSS_SECRET_KEY` | подтверждение и отмена платежей Toss Payments |
| `YOOKASSA_SHOP_ID`, `YOOKASSA_API_TOKEN` | YooKassa |
| `BACKEND_PUBLIC_URL` | публичный адрес backend для платежных callback URL |

`YOOKASSA_SHOP_ID` и `YOOKASSA_API_TOKEN` используются кодом, поэтому добавьте их в `.env`, если YooKassa включена, хотя их пока нет в `.env.template`.

### Frontend

Создайте `evacode.org/.env`:

```bash
cp evacode.org/.env.example evacode.org/.env
```

Для локальной разработки с Nginx из `docker-compose.dev.yml`:

```dotenv
BASE_API_URL=http://localhost/api
SITE_URL=http://localhost:3000
```

Для production укажите публичный HTTPS-адрес:

```dotenv
BASE_API_URL=https://www.evacode.org/api
SITE_URL=https://www.evacode.org
```

Nuxt читает эти значения во время запуска/сборки. Подготовьте `evacode.org/.env` **до** выполнения `docker compose build frontend`.

## Запуск для разработки

В разработке backend, PostgreSQL и Nginx работают в Docker, а Nuxt запускается локально с hot reload.

### 1. Подготовьте окружение

```bash
cp .env.template .env
cp .env.template .env2
cp evacode.org/.env.example evacode.org/.env
```

Заполните `.env`. В `.env2` измените только хост базы:

```dotenv
DB_HOST=localhost
```

### 2. Запустите backend, БД и Nginx

Из корня репозитория:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Команда запускает:

- PostgreSQL на `localhost:5432`;
- Django development server на `localhost:8000`;
- Nginx на `localhost:80`, который проксирует `/api/`, `/admin/`, `/media/` и `/static/`.

### 3. Запустите frontend

В отдельном терминале:

```bash
cd evacode.org
bun install
bun run dev
```

Откройте `http://localhost:3000`.

Полезные адреса в development:

| Адрес | Назначение |
| --- | --- |
| `http://localhost:3000` | Nuxt frontend |
| `http://localhost:8000/admin/` | Django admin напрямую |
| `http://localhost:8000/api/swagger/` | Swagger API напрямую |
| `http://localhost/api/` | API через Nginx |

Остановка development-стека:

```bash
docker compose -f docker-compose.dev.yml down
```

Не добавляйте `-v`, если хотите сохранить локальную PostgreSQL-базу.

## Запуск production-версии

Production Compose запускает PostgreSQL, Gunicorn, Nginx, Nuxt и сервис синхронизации каталога.

### Перед первым запуском

1. Подготовьте `.env`, `.env2` и `evacode.org/.env`.
2. Для `.env` укажите `DB_HOST=db`; для `.env2` укажите `DB_HOST=localhost`.
3. Настройте DNS-записи `evacode.org` и `www.evacode.org` на IP сервера.
4. Подготовьте TLS-сертификаты в `data/certbot/conf` либо включите и настройте Certbot.

Nginx ожидает сертификаты по путям:

```text
data/certbot/conf/live/www.evacode.org/fullchain.pem
data/certbot/conf/live/www.evacode.org/privkey.pem
```

Сервис Certbot сейчас закомментирован в `docker-compose.yml`, поэтому автоматическое продление сертификатов не выполняется. До запуска HTTPS убедитесь, что сертификаты существуют и действительны.

### Сборка и запуск

```bash
docker compose up -d --build
docker compose ps
```

Просмотр логов первого запуска:

```bash
docker compose logs -f --tail=100 server frontend nginx
```

Production URL:

```text
https://www.evacode.org
```

## Работа с Docker

### Обновить только frontend

После изменения файлов в `evacode.org/`:

```bash
docker compose up -d --build frontend
docker compose logs -f --tail=100 frontend
```

### Обновить backend

После изменения Python-кода, зависимостей или Dockerfile:

```bash
docker compose up -d --build server
docker compose logs -f --tail=100 server
```

### Миграции и администратор

```bash
docker compose exec server python manage.py makemigrations
docker compose exec server python manage.py migrate
docker compose exec server python manage.py createsuperuser
docker compose exec server python manage.py shell
```

### Синхронизация каталога

В production сервис `update_database` запускает команду `updatedata`. Она сразу получает актуальный токен Business.Ru, синхронизирует категории и товары, затем повторяет этот цикл **каждые 5 минут**.

```bash
docker compose logs -f update_database
```

Команда работает в бесконечном цикле и сама по себе не завершается. `restart: always` в `docker-compose.yml` восстанавливает сервис после неожиданного завершения или перезапуска Docker, а не задаёт расписание. Не используйте `docker compose run --rm update_database python manage.py updatedata` для разового импорта: этот запуск также будет работать непрерывно.

Чтобы вручную перезапустить синхронизацию после изменения настроек Business.Ru:

```bash
docker compose restart update_database
```

### Данные и место на диске

Постоянные Docker volumes:

- `evacode-pgdata` — PostgreSQL;
- `evacode-static` — собранная статика;
- `evacode-media` — загружаемые медиафайлы.

Диагностика занятого Docker-места:

```bash
docker system df
docker system df -v
df -h
```

Безопасная очистка неиспользуемых контейнеров, сетей и build cache:

```bash
docker system prune -f
```

`docker volume prune` и `docker compose down -v` могут удалить базу и медиа. Используйте их только после резервной копии.

## Django и API

Корневые маршруты определены в `src/evacode_backend/urls.py`.

| URL | Назначение |
| --- | --- |
| `/admin/` | Django admin |
| `/api/core/` | баннеры, контакты, доставка, отзывы, страницы, валюты |
| `/api/market/` | товары, категории, оформление заказа, импорт каталога |
| `/api/invoice/` | callback-страницы Toss Payments |
| `/api/token/` | получение JWT access/refresh токенов |
| `/api/refresh_token/` | обновление JWT access токена |
| `/api/swagger/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/ckeditor/` | загрузка контента CKEditor |

Основные API-модули:

- `core`: контент, которым удобно управлять через Django admin;
- `market`: каталог, категории, остатки, Telegram-уведомления и endpoint `/api/market/checkout/`;
- `finance`: возврат пользователя после оплаты и подтверждение Toss Payments.

Backend-тесты:

```bash
docker compose exec server python manage.py test
```

Во frontend `package.json` пока не содержит отдельной test-команды. Минимальная проверка перед деплоем:

```bash
cd evacode.org
bun run build
```

## Разработка frontend

Nuxt маршрутизирует страницы из `evacode.org/pages/`, а компоненты автоматически импортируются из `evacode.org/components/`.

- Для новых страниц используйте `pages/`.
- Для переиспользуемых UI-блоков используйте `components/`.
- Для общего клиентского состояния используйте Pinia в `store/`.
- Для запросов к backend используйте `useRuntimeConfig().public.apiBase`, а не жестко заданный URL.
- Публичные статические файлы размещайте в `evacode.org/public/`.

После изменения frontend для production пересоберите только сервис `frontend`:

```bash
docker compose up -d --build frontend
```

## Обновление и Git-процесс

Это единый репозиторий: не нужно выполнять `git submodule update` и не нужно отдельно пушить `evacode.org`.

Типовой процесс:

```bash
git switch main
git pull --ff-only
git switch -c feat/short-description

# изменить backend, frontend или инфраструктуру
git status
git add README.md src/evacode_backend/settings.py
git commit -m "docs: describe local development workflow"
git push -u origin feat/short-description
```

Не коммитьте `.env`, `.env2`, сертификаты, базы данных, Docker volumes и `node_modules`.

## Диагностика

### Frontend не получает API

1. Проверьте `BASE_API_URL` в `evacode.org/.env`.
2. Убедитесь, что backend работает: `curl http://localhost:8000/api/core/delivery/`.
3. Если используется адрес `http://localhost/api`, убедитесь, что запущен Nginx из development Compose.

### Backend не подключается к PostgreSQL

Проверьте `DB_TYPE=postgres`, имя БД, пользователя и пароль. Для контейнера `server` должен быть `DB_HOST=db`; `localhost` внутри контейнера не означает контейнер PostgreSQL.

### Nginx не стартует в production

Проверьте, что TLS-сертификаты расположены по путям из раздела [Запуск production-версии](#запуск-production-версии), и посмотрите логи:

```bash
docker compose logs --tail=100 nginx
```

### Заказ не приходит в Telegram

Проверьте `BOT_TOKEN`, `CHAT_ID` и логи backend:

```bash
docker compose logs -f --tail=100 server
```

## Резервное копирование

Перед обновлением production рекомендуется сохранить дамп PostgreSQL:

```bash
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > evacode-backup.sql
```

Восстановление выполняйте только после проверки дампа и при остановленном приложении:

```bash
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' < evacode-backup.sql
```

Храните дампы и секреты вне репозитория.
