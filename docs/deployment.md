# Деплой Genomic Prediction API

## Render

| Параметр | Значение |
|---|---|
| RAM | 512 МБ |
| vCPU | shared |
| Бесплатные часы | 750/мес (обнуляются 1-го числа) |
| До засыпания | 15 мин idle |
| Просыпание | 30-50 сек |
| Карта | Не требуется |
| Custom Domain | Бесплатно с SSL |

> Платформа не требует кредитную карту. Достаточно GitHub-аккаунта.

---

## Шаг 1: Регистрация

1. Откройте [render.com](https://render.com)
2. Нажмите **Start Free** → **Continue with GitHub**
3. Авторизуйтесь через GitHub
4. Подтвердите email

---

## Шаг 2: Подготовка модели

Перед деплоем убедитесь, что модель существует:

```bash
# Локально: генерация dummy-модели (если её нет)
uv run python scripts/generate_dummy_model.py

# Проверка: должен появиться файл app/assets/model.joblib
ls -la app/assets/
```

Формат модели:

```python
{
    "snp_effects": np.ndarray,     # shape (n_snps,) — аддитивные эффекты
    "accuracy": float,               # точность предсказания
    "ref_mean": float,              # среднее GEBV популяции
    "ref_std": float,              # стандартное отклонение
    "version": str,                # версия модели (опционально)
}
```

---

## Шаг 3: Деплой

### Вариант A: Через web-интерфейс

1. Войдите в [dashboard.render.com](https://dashboard.render.com)
2. Нажмите **New** → **Web Service**
3. Подключите GitHub-репозиторий:
   - Выберите organization
   - Выберите репозиторий `breedi-genomic-api`
4. Настройте:
   | Поле | Значение |
   |---|---|
   | Name | `genomic-api` |
   | Root Directory | (по умолчанию) |
   | Build Command | (пусто — использует Dockerfile) |
   | Start Command | (пусто — из Dockerfile) |
5. Нажмите **Advanced**:
   | Поле | Значение |
   |---|---|
   | Port | `8000` |
   | Instance Type | **Free** |
6. Нажмите **Deploy**

Первичный билд занимает 2-5 минут. После — сервис доступен по URL: `https://genomic-api.onrender.com`

### Вариант B: Через CLI

```bash
# Установка CLI
brew install render-cli/render/render

# Авторизация
render auth login

# Деплой
render web create \
  --name genomic-api \
  --sourcePath . \
  --buildCommand "docker build -t genomic-api ." \
  --startCommand "docker run -p 8000:8000 genomic-api"
```

---

## Шаг 4: Избежание засыпания (опционально)

На Free tier сервис засыпает после 15 мин бездействия. Чтобы не заснул — используйте UptimeRobot для пинга.

### Регистрация

1. Откройте [uptimerobot.com](https://uptimerobot.com)
2. Нажмите **Sign Up Free** → войдите через Google
3. Нажмите **Add New Monitor**

### Настройка монитора

| Поле | Значение |
|---|---|
| Monitor Type | HTTP(s) |
| Friendly Name | `genomic-api health` |
| URL (or IP) | `https://genomic-api.onrender.com/health` |
| Monitoring Interval | 5 minutes |
| Alert Contacts | (ваш email) |

Нажмите **Create Monitor**.

Теперь UptimeRobot пингует `/health` каждые 5 минут — сервис не засыпает.

> Бесплатный план: до 50 мониторов. Достаточно для одного сервиса.

---

## Проверка

| Endpoint | URL |
|---|---|
| Health | `https://genomic-api.onrender.com/health` |
| Swagger UI | `https://genomic-api.onrender.com/docs` |
| ReDoc | `https://genomic-api.onrender.com/redoc` |

### Тест health

```bash
curl https://genomic-api.onrender.com/health
```

Ожидаемый ответ:

```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "dummy-v0.1.0"
}
```

### Тест предсказания GEBV

```bash
curl -X POST https://genomic-api.onrender.com/predict-gev \
  -H "Content-Type: application/json" \
  -d '{
    "animal_id": "cow_001",
    "snp_dosages": [0,1,2,0,1,2,0,1,2,0,1]
  }'
```

> dummy-модель ожидает 10 000 SNP. Если число другое — вернёт 400 ошибку.

---

## Управление

### Логи

В dashboard Render:
1. Выберите сервис **genomic-api**
2. Перейдите на вкладку **Logs**

### Передеплой

При пуше в main-ветку:
1. Render автоматически делает deploy
2. Или вручную: **Manual Deploy** → **Deploy latest commit**

### Остановка

**Settings** → **Shutdown** — сервис останавливается, но не удаляется.

---

## Ограничения Free tier

| Ограничение | Значение |
|---|---|
| RAM | 512 МБ |
| Idle time | 15 мин → sleep |
| Cold start | 30-50 сек |
| База данных | PostgreSQL (бесплатно 90 дней) |
| Непрерывный uptime | Не гарантируется |

> Для продакшна рекомендуется платный план: Starter от $7/мес.

---

## Устранение проблем

### Сервис не запускается

1. Проверьте логи: **Logs** в dashboard
2. typical errors:
   - `port not found` — убедитесь `EXPOSE 8000` в Dockerfile
   - `model not found` — проверьте `app/assets/model.joblib` exists

### 503 Service Unavailable

Модель не загружена. Проверьте файл `app/assets/model.joblib`:

```bash
ls -la app/assets/model.joblib
# Должен быть > 0 байт
```

### Cold start медленный

Это норма для Free tier. Используйте UptimeRobot для keep-alive.

---

## Чеклист перед деплоем

- [ ] Модель сгенерирована: `app/assets/model.joblib` exists
- [ ] Health-чек проходит локально: `uv run uvicorn app.main:app --reload`
- [ ] Код запушен в GitHub (main branch)
- [ ] GitHub-репозиторий подключён к Render
- [ ] UptimeRobot настроен (опционально)