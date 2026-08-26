# Переход на монорепозиторий на VPS

Это руководство переносит production-сервер со старого репозитория, где `evacode.org` был Git-сабмодулем, на монорепозиторий [`pomaho/evacode`](https://github.com/pomaho/evacode). В новом репозитории frontend и backend находятся в одной рабочей копии.

Цель миграции: после перехода обновлять весь проект из одной папки командами `git pull --ff-only origin main` и `docker compose up -d --build`.

## Что сохраняется

- PostgreSQL-данные в Docker volume `evacode-pgdata`;
- Django media в volume `evacode-media`;
- собранная статика в volume `evacode-static`;
- секреты и настройки из `.env`, `.env2` и `evacode.org/.env`;
- TLS-сертификаты из `data/certbot`, если они хранятся в папке проекта.

Старую рабочую копию не нужно удалять: она остаётся резервным вариантом для быстрого отката.

## Перед началом

1. Убедитесь, что все нужные изменения запушены в ветку `main` репозитория `pomaho/evacode`.
2. Подключитесь к VPS по SSH.
3. Узнайте абсолютный путь старого проекта. Далее он обозначен как `OLD_DIR`.
4. Выберите соседнюю пустую папку для монорепозитория. Далее она обозначена как `NEW_DIR`.

Пример для проекта в `/opt`:

```bash
export OLD_DIR=/opt/evacode_backend
export NEW_DIR=/opt/evacode
```

Замените эти значения на реальные пути сервера. Не выполняйте команды из инструкции вслепую, если старый проект расположен в другом месте.

## 1. Проверьте старую конфигурацию

Проверьте, что файлы настроек существуют:

```bash
find "$OLD_DIR" -maxdepth 2 -type f \( -name '.env' -o -name '.env2' \)
```

Для production обычно нужны:

```text
$OLD_DIR/.env
$OLD_DIR/.env2
$OLD_DIR/evacode.org/.env
```

Проверьте Docker volumes. Имена должны быть видны в выводе:

```bash
docker volume ls | rg 'evacode-(pgdata|static|media)'
```

Если `rg` не установлен, используйте:

```bash
docker volume ls | grep -E 'evacode-(pgdata|static|media)'
```

## 2. Клонируйте монорепозиторий рядом со старым

Не меняйте `remote` и не удаляйте сабмодуль в старой рабочей копии. Новый клон позволяет проверить запуск и вернуться назад без восстановления из бэкапа.

```bash
git clone https://github.com/pomaho/evacode.git "$NEW_DIR"
cd "$NEW_DIR"
git status --short --branch
```

Ожидаемый результат: рабочая копия на ветке `main` без незакоммиченных файлов.

## 3. Перенесите только секреты и TLS-данные

Файлы окружения игнорируются Git, поэтому их необходимо перенести вручную:

```bash
cp -p "$OLD_DIR/.env" "$NEW_DIR/.env"
[ -f "$OLD_DIR/.env2" ] && cp -p "$OLD_DIR/.env2" "$NEW_DIR/.env2"
[ -f "$OLD_DIR/evacode.org/.env" ] && cp -p "$OLD_DIR/evacode.org/.env" "$NEW_DIR/evacode.org/.env"
```

Если используются сертификаты, которые лежат в `data/certbot`, перенесите их отдельно:

```bash
[ -d "$OLD_DIR/data/certbot" ] && {
  mkdir -p "$NEW_DIR/data/certbot"
  cp -a "$OLD_DIR/data/certbot/." "$NEW_DIR/data/certbot/"
}
```

Не переносите целиком старую папку и не копируйте `.git`, `evacode.org/.git`, `node_modules`, `.venv` или Docker-контейнеры. Они либо относятся к старому репозиторию, либо должны быть созданы заново.

## 4. Проверьте конфигурацию нового проекта

```bash
cd "$NEW_DIR"
docker compose config --quiet
```

Проверьте значения в файлах окружения:

- в `.env` переменная `DB_HOST` должна быть `db`;
- в `.env2` переменная `DB_HOST` должна быть `localhost`;
- в `evacode.org/.env` должны быть production URL, например `https://www.evacode.org/api` и `https://www.evacode.org`;
- если используется YooKassa, в `.env` должны быть `YOOKASSA_SHOP_ID` и `YOOKASSA_API_TOKEN`.

## 5. Переключите контейнеры на новую рабочую копию

Сначала остановите старый Compose-стек. **Не добавляйте `-v`**, иначе Docker удалит volumes с базой и медиафайлами.

```bash
cd "$OLD_DIR"
docker compose down
```

Соберите и запустите сервисы из новой папки:

```bash
cd "$NEW_DIR"
docker compose up -d --build
docker compose ps
docker compose logs -f --tail=100 server frontend nginx
```

Проверьте сайт, Django Admin и создание тестового заказа. Для проверки состояния контейнеров используйте `docker compose ps`.

## Последующие обновления

Обычное обновление всех сервисов:

```bash
cd "$NEW_DIR"
git pull --ff-only origin main
docker compose up -d --build
```

Если менялся только frontend:

```bash
cd "$NEW_DIR"
git pull --ff-only origin main
docker compose up -d --build frontend
```

## Откат

Если новый запуск не работает, вернитесь к старой рабочей копии. Volumes остаются общими, поэтому база и медиа не пропадут.

```bash
cd "$NEW_DIR"
docker compose down

cd "$OLD_DIR"
docker compose up -d --build
docker compose ps
```

Не используйте `docker compose down -v`, `docker volume prune` или `docker system prune --volumes` во время миграции: эти команды могут удалить production-данные.
