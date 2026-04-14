# Деплой Genomic Prediction API

## Koyeb

| Параметр | Значение |
|---|---|
| RAM | 512 МБ |
| vCPU | 0.1 |
| SSD | 2 ГБ |
| До засыпания | ❌ Не засыпает (scale-to-zero после 1ч) |
| Просыпание | 1-5 сек |
| Карта | ✅ Требуется для верификации |
| Free DB | PostgreSQL (1 ГБ, 5 ч/мес compute) |
| Custom Domain | Бесплатно |

> **Требуется кредитная карта** для верификации. Списание — $0. Бесплатно в пределах Free tier.

---

## Шаг 1: Регистрация

1. Откройте [koyeb.com](https://www.koyeb.com)
2. Нажмите **Start Free** → **Continue with GitHub**
3. Авторизуйтесь через GitHub
4. Привяжите карту (требуется, но списывается $0)

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

### Вариант A: Через web-интерфейс (рекомендуется)

1. Войдите в [dashboard.koyeb.com](https://dashboard.koyeb.com)
2. Нажмите **Create Service**
3. Подключите GitHub-репозиторий:
   - Выберите organization
   - Выберите репозиторий `breedi-genomic-api`
4. Настройте:
   | Поле | Значение |
   |---|---|
   | Name | `genomic-api` |
   | Builder | Dockerfile |
   | Branch | `main` |
   | Port | `8000` |
   | Region | `Frankfurt` (ближе к РФ) |
5. Нажмите **Deploy**

Первичный билд занимает 3-5 минут. После — сервис доступен по URL: `https://genomic-api.koyeb.app`

### Вариант B: Через Koyeb CLI

```bash
# Установка CLI
brew install koyeb/cli/koyeb  # macOS
# или
curl -L https://install.koyeb.dev | sh  # Linux

# Авторизация
koyeb login

# Деплой
koyeb service create \
  --name genomic-api \
  --github-owner your-username \
  --github-repo breedi-genomic-api \
  --builder dockerfile \
  --port 8000
```

---

## Проверка

| Endpoint | URL |
|---|---|
| Health | `https://genomic-api.koyeb.app/health` |
| Swagger UI | `https://genomic-api.koyeb.app/docs` |
| ReDoc | `https://genomic-api.koyeb.app/redoc` |

### Тест health

```bash
curl https://genomic-api.koyeb.app/health
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
curl -X POST https://genomic-api.koyeb.app/predict-gev \
  -H "Content-Type: application/json" \
  -d '{
    "animal_id": "cow_001",
    "snp_dosages": [0,1,2,0,1,2,0,1,2,0,1]
  }'
```

> dummy-модель ожидает 10 000 SNP. Если число другое — вернёт 400 ошибку.

**Тест с 10 000 SNP (полный пример):**

```bash
python3 -c "
import json, urllib.request
dosages = [i % 3 for i in range(10000)]
data = json.dumps({'animal_id': 'cow_123', 'snp_dosages': dosages}).encode()
req = urllib.request.Request('https://genomic-api.koyeb.app/predict-gev', data=data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req)
print(json.dumps(json.loads(resp.read()), indent=2))
"
```

Ожидаемый ответ:

```json
{
  "animal_id": "cow_123",
  "gebv": 1.3184,
  "accuracy": 0.72,
  "percentile": 90.56
}
```

---

## Управление

### Передеплой

При пуше в main-ветку:
1. Koyeb автоматически делает deploy
2. Или вручную: **Redeploy**

### Остановка

В dashboard:
1. Выберите сервис **genomic-api**
2. **Settings** → **Deactivate** — сервис останавливается

---

## Ограничения Free tier

| Ограничение | Значение |
|---|---|
| RAM | 512 МБ |
| vCPU | 0.1 |
| SSD | 2 ГБ |
| Scale-to-zero | После 1 часа idle |
| Cold start | 1-5 сек |
| Количество сервисов | 1 |
| Free PostgreSQL | 1 ГБ, 5 ч/мес |

> Для продакшна рекомендуется платный план: Starter от $10/мес.

---

## Устранение проблем

### Сервис не запускается

1. Проверьте логи: **Logs** в dashboard
2. Типичные ошибки:
   - `port not found` — убедитесь `EXPOSE 8000` в Dockerfile
   - `model not found` — проверьте `app/assets/model.joblib` exists
   - `python not found` — убедитесь `ENV PATH` настроен в Dockerfile

### 503 Service Unavailable

Модель не загружена. Проверьте файл `app/assets/model.joblib`:

```bash
ls -la app/assets/model.joblib
# Должен быть > 0 байт
```

### Cold start медленный

Это редкость на Koyeb — обычно 1-5 сек. Если медленно:
1. Проверьте регион (Frankfurt ближе к РФ)
2. Размер образа — меньше = быстрее

---

## Сравнение с Render

| Параметр | Koyeb | Render |
|---|---|---|
| RAM | 512 МБ | 512 МБ |
| Sleep | После 1ч idle | После 15 мин idle |
| Wake time | 1-5 сек | 30-50 сек |
| SSD | 2 ГБ | ❌ Нет |
| Free DB | PostgreSQL | PostgreSQL (90 дней) |

### Когда выбрать Koyeb:
- Нужен быстрый отклик
- Не хотите UptimeRobot
- SSD для модели

### Когда выбрать Render:
- Нужна бесплатная БД на 90 дней
- Много часов (750/мес)

---

## Чеклист перед деплоем

- [ ] Модель сгенерирована: `app/assets/model.joblib` exists
- [ ] Health-чек проходит локально: `uv run uvicorn app.main:app --reload`
- [ ] Код запушен в GitHub (main branch)
- [ ] GitHub-репозиторий подключён к Koyeb