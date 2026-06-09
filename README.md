# Weekly Backend

FastAPI + SQLAlchemy (async) + PostgreSQL — бэкенд приложения Weekly.

## Запуск

```bash
# 1. зависимости
pip install -r requirements.txt

# 2. конфигурация
cp .env.dist .env   # затем заполнить значения (см. ниже)

# 3. запуск dev-сервера (порт 6767)
python -m app.main
# либо
uvicorn app.main:app --reload --port 6767
```

Схема БД создаётся автоматически при старте (`Base.metadata.create_all`), миграции не используются.

## Настройка `.env`

Скопируй `.env.dist` в `.env` и заполни. **Обязательные** переменные не имеют значений по умолчанию — без них приложение не стартует.

### База данных (обязательно)

| Переменная | Описание | Пример |
|---|---|---|
| `DB_HOST` | Хост PostgreSQL | `127.0.0.1` |
| `DB_PORT` | Порт PostgreSQL | `5432` |
| `DB_NAME` | Имя БД | `weekly_db` |
| `DB_USER` | Пользователь | `user` |
| `DB_PASSWORD` | Пароль | `password` |

### Сервер и аутентификация

| Переменная | Описание | По умолчанию |
|---|---|---|
| `port` | Порт сервера | `6767` |
| `host` | Адрес привязки | `0.0.0.0` |
| `RANDOM_SECRET` | Секрет для подписи JWT (задать свой!) | `secret` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access-токена, мин | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Время жизни refresh-токена, дней | `30` |

### S3-хранилище (для аватаров)

| Переменная | Описание | По умолчанию |
|---|---|---|
| `S3_ACCESS_KEY` | Access key (**обязательно**) | — |
| `S3_SECRET_KEY` | Secret key (**обязательно**) | — |
| `S3_ENDPOINT_URL` | Endpoint S3-совместимого хранилища | `https://s3.komaru-best.cfd` |
| `S3_BUCKET` | Бакет | `weekly` |
| `S3_PUBLIC_URL` | Публичный базовый URL файлов | `https://s3.komaru-best.cfd/weekly` |
| `DEFAULT_AVATAR_URL` | URL аватара по умолчанию | `…/avatars/default.png` |

### Уведомления, почта, капча, AI

| Переменная | Описание | По умолчанию |
|---|---|---|
| `FIREBASE_CREDENTIALS_PATH` | Путь к JSON service-account Firebase (FCM) | `""` |
| `YANDEX_CAPTCHA_SECRET_KEY` | Серверный ключ Yandex SmartCaptcha | `""` |
| `CAPTCHA_ENABLED` | Включить проверку капчи | `true` |
| `EMAIL_CODE_ENABLED` | Подтверждение email кодом | `false` |
| `RESEND_API_KEY` | API-ключ Resend (отправка писем) | `""` |
| `RESEND_FROM_EMAIL` | Адрес отправителя | `noreply@weekly.komaru-best.cfd` |
| `ANTHROPIC_API_KEY` | Ключ Anthropic (AI-функции) | `""` |
| `ANTHROPIC_BASE_URL` | Base URL Anthropic-совместимого API | `https://gate.trinity.tg/aurora` |

### Deep Links / Android App Links

Используются роутером `app/routers/deeplinks.py` (`/.well-known/assetlinks.json`, `/tasks`, `/promo`).

| Переменная | Описание | По умолчанию |
|---|---|---|
| `ANDROID_PACKAGE_NAME` | Package name Android-приложения | `com.livesgood.weekly_app` |
| `ANDROID_SHA256_FINGERPRINTS` | SHA-256 отпечатки сертификатов подписи, через запятую. При выходе в Google Play добавить отпечаток Play App Signing | отпечаток release-ключа |
| `APP_SCHEME` | Кастомная схема приложения | `weekly` |
| `APP_DOWNLOAD_URL` | Куда вести, если приложение не установлено | `https://t.me/weekly_app` |

> Отпечаток SHA-256 release-ключа получается командой:
> ```bash
> keytool -list -v -keystore release.keystore -alias <alias>
> ```

## Деплой (VDS)

Образ собирается автоматически при push в `main` (GitHub Actions → GHCR:
`ghcr.io/l1vesgood/weekly-backend:latest`). На сервере:

```bash
cd ~/services/weekly-backend && ./upd.sh
```

`upd.sh` делает `docker pull` свежего образа и перезапускает контейнер
(`--network host`, `--env-file .env`). Перед домен проксируется nginx
(`weekly.komaru-best.cfd` → `127.0.0.1:6767`).

## Архитектура

- `app/models.py` — ORM-модели (`User`, `Task`, `RefreshToken`)
- `app/schemas/` — Pydantic-схемы (camelCase в ответах)
- `app/dao/` — слой доступа к данным (async SQLAlchemy)
- `app/routers/` — роутеры FastAPI, монтируются под `/api` (кроме `deeplinks` — в корень)
- `app/services/` — внешние интеграции (S3, FCM, email)
- `app/utils/auth_utils.py` — JWT, хеширование паролей, зависимости `get_current_user` / `admin_only`