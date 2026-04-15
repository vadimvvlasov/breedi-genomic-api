# Деплой на Fly.io

## Цены и лимиты

| Параметр | Значение |
|---|---|
| Минимальный план | $5/мес (включает $5 кредита) |
| VM shared-cpu-1x 256MB | $1.94/мес |
| VM shared-cpu-1x 1GB | $5.70/мес |

Для этого API хватит 256MB — весит ~50MB.

---

## Быстрый старт

```bash
# 1. Установить CLI
brew install flyctl  # macOS
# или https://fly.io/docs/flyctl/install/

# 2. Авторизоваться
fly auth login

# 3. Запустить
fly launch --name genomic-api
```

Ответь на вопросы:
- Region: `Frankfurt`
- Dockerfile detected: **Yes**

Деплой:

```bash
fly deploy
```

---

## Проверка

```bash
curl https://genomic-api.fly.dev/health
# {"status":"healthy","model_loaded":true,"model_version":"dummy-v0.1.0"}
```

---

## Частые проблемы

| Ошибка | Причина | Решение |
|---|---|---|
| 503 | Нет модели | Проверить `app/assets/model.joblib` в репозитории |
| 502 | port mismatch | Проверить `internal_port = 8000` в fly.toml |

---

## Команды

```bash
fly deploy          # Передеплой
fly logs           # Логи
fly scale memory 512  # Увеличить RAM до 512MB
```