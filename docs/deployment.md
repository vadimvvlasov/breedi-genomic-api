# Деплой Genomic Prediction API

## Сравнительная таблица бесплатных платформ

| Платформа | RAM | vCPU | Хранилище | Docker | Карта | Sleep |
|---|---|---|---|---|---|---|
| **Koyeb** | 512 МБ | 0.1 | 2 ГБ SSD | ✅ | Нет | Да |
| **Google Cloud Run** | до 8 ГБ | до 4 | — | ✅ (OCI) | Да | Scale-to-zero |
| **Oracle Cloud Always Free** | до 24 ГБ | до 4 OCPU | 200 ГБ | ✅ | Да | Нет |
| **Render** | 512 МБ | shared | — | частично | Нет | Да |
| **Railway** | до 8 ГБ | до 8 | — | ✅ | Да | Ограничено кредитом |

> Для лёгкой модели (<50 МБ) оптимален **Koyeb**. Для тяжёлой модели — **Oracle Cloud** или **Google Cloud Run**.

---

## Koyeb

1. Зарегистрируйтесь на [koyeb.com](https://www.koyeb.com) (GitHub-аккаунт).
2. Push-те код в GitHub-репозиторий.
3. В Koyeb: **Create Service** → **GitHub** → выберите репозиторий.
4. Укажите:
   - **Builder**: Dockerfile
   - **Branch**: `main`
   - **Port**: `8000`
   - **Region**: `Frankfurt` (ближе к РФ)
5. Нажмите **Deploy**.

После сборки сервис доступен по адресу `https://<app-name>.koyeb.app`.

**Ограничение:** 512 МБ RAM — достаточно для модели с < 50 000 SNP.

---

## Google Cloud Run

### Шаг 1: билд и push образа

```bash
# Авторизуйтесь в gcloud
gcloud auth login
gcloud auth configure-docker

# Соберите и запушьте
docker build -t gcr.io/$PROJECT_ID/genomic-api:latest .
docker push gcr.io/$PROJECT_ID/genomic-api:latest
```

### Шаг 2: создание сервиса

```bash
gcloud run deploy genomic-api \
  --image gcr.io/$PROJECT_ID/genomic-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars UVICORN_WORKERS=2
```

### Бесплатные лимиты

| Ресурс | Бесплатно в месяц |
|---|---|
| Запросы | 2 млн |
| vCPU-время | 180 000 сек |
| Память | 360 000 GiB-сек |

> Нужен billing-аккаунт (привязка карты), но в пределах лимитов — $0.
> Scale-to-zero: при отсутствии запросов контейнер не работает и не списывает ресурсы.

---

## Oracle Cloud Always Free

### Нюанс: ARM-архитектура

Oracle Free Tier предоставляет Ampere A1 (ARM64). Для совместимости собирайте образ:

```bash
docker buildx build --platform linux/arm64 -t genomic-api:arm64 .
```

Если вы на x86-машине, нужен `docker buildx` с поддержкой эмуляции (работает автоматически через QEMU, но билд займёт больше времени).

### Шаг 1: push в OCIR

```bash
docker tag genomic-api:arm64 <region>.ocir.io/<namespace>/genomic-api:latest
docker push <region>.ocir.io/<namespace>/genomic-api:latest
```

### Шаг 2: создание Compute Instance

1. В OCI Console: **Compute** → **Instances** → **Create instance**
2. Выберите **Ampere A1** (ARM), профиль Always Free
3. Image — Ubuntu/Oracle Linux
4. При создании подключитесь по SSH и запустите контейнер:

```bash
# Установка Docker на VM
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Запуск
docker pull <region>.ocir.io/<namespace>/genomic-api:latest
docker run -d -p 8000:8000 --restart unless-stopped \
  --name genomic-api \
  <region>.ocir.io/<namespace>/genomic-api:latest
```

> **Always Free лимиты:** до 4 OCPU, 24 ГБ RAM, 200 ГБ хранилище. Этого хватит для модели с миллионами SNP.

---

## Чеклист перед деплоем

- [ ] Файл `model.joblib` лежит в `app/assets/`
- [ ] Формат модели — dict с ключами: `snp_effects`, `accuracy`, `ref_mean`, `ref_std`
- [ ] Число SNP в модели совпадает с ожидаемым входным размером (`len(snp_effects)`)
- [ ] `pyproject.toml` и `uv.lock` актуальны (`uv sync && uv lock`)
- [ ] `Dockerfile` корректно копирует `pyproject.toml` и `uv.lock`
- [ ] Health-чек проходит: `GET /health` → `{"status": "healthy", "model_loaded": true}`
- [ ] Для Oracle Cloud — образ собран под `linux/arm64`
- [ ] Для Google Cloud Run — привязан billing-аккаунт
