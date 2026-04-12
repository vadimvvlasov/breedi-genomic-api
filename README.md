# Breedi Genomic Prediction API

REST API сервис для расчёта геномной оценки племенной ценности (**GEBV**) на базе модели **RR-BLUP** (Ridge Regression BLUP).

## Обзор

Сервис принимает ДНК-данные животных — дозировки SNP-маркеров, закодированные как **0, 1 или 2** (число альтернативных аллелей в локусе), — и возвращает:

| Поле | Описание |
|---|---|
| `gebv` | Genomic Estimated Breeding Value — сумма взвешенных SNP-эффектов |
| `accuracy` | Оценка точности предсказания (correlation GEBV ↔ истинная племенная ценность) |
| `percentile` | Процентиль животного относительно референсной популяции |

Модель RR-BLUP математически эквивалентна **GBLUP** и оценивает аддитивный эффект каждого SNP-маркера независимо — стандартный подход в современных геномных пайплайнах.

## Структура проекта

```
├── app/
│   ├── main.py           # FastAPI приложение, роуты
│   ├── models.py         # Pydantic-схемы запросов и ответов
│   ├── inference.py      # Логика RR-BLUP (загрузка модели, inference)
│   └── assets/
│       └── model.joblib  # Предобученные веса SNP-эффектов
├── tests/                # pytest-тесты
├── scripts/
│   └── generate_dummy_model.py  # Генерация dummy-модели для разработки
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

## Быстрый старт

### Локальный запуск (uv)

```bash
# Установка зависимостей
uv sync --all-extras

# Генерация dummy-модели (для разработки)
uv run python scripts/generate_dummy_model.py

# Запуск сервера
uv run uvicorn app.main:app --reload
```

Сервер доступен по адресу [http://localhost:8000](http://localhost:8000).  
Swagger-документация — [http://localhost:8000/docs](http://localhost:8000/docs).

### Docker

```bash
docker compose up --build
```

Сервер запустится на `http://localhost:8000`.

| Действие | Команда |
|---|---|
| Запуск в фоне | `docker compose up -d --build` |
| Логи | `docker compose logs -f` |
| Остановка | `docker compose down` |
| Подменить модель | Раскомментируйте строку `volumes` в `docker-compose.yml` и положите свой `model.joblib` в корень проекта |

## API

### `GET /health`

Проверка работоспособности сервиса.

```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "dummy-v0.1.0"
}
```

### `POST /predict-gev`

Расчёт GEBV по SNP-данным.

**Request:**

```json
{
  "animal_id": "cow_123",
  "snp_dosages": [0, 1, 2, 0, 1, 2, ...]
}
```

| Поле | Тип | Описание |
|---|---|---|
| `animal_id` | string | Идентификатор животного |
| `snp_dosages` | list[int] | Дозировки SNP-маркеров (**0, 1 или 2**). Длина должна совпадать с числом маркеров модели |

**Response:**

```json
{
  "animal_id": "cow_123",
  "gebv": 1.3184,
  "accuracy": 0.72,
  "percentile": 90.56
}
```

## Формат модели

Файл `app/assets/model.joblib` должен содержать сериализованный `dict`:

```python
{
    "snp_effects": np.ndarray,   # shape (n_snps,) — аддитивные эффекты SNP
    "accuracy": float,           # точность предсказания
    "ref_mean": float,           # среднее GEBV референсной популяции
    "ref_std": float,            # стандартное отклонение GEBV
    "version": str,              # опционально: версия модели
}
```

Для генерации тестовой модели:

```bash
uv run python scripts/generate_dummy_model.py
```

## Тесты

```bash
uv run pytest -v
```

## Формула расчёта

GEBV вычисляется как скалярное произведение вектора SNP-эффектов и вектора дозировок:

$$\text{GEBV} = \sum_{i=1}^{n} \beta_i \cdot x_i$$

где $\beta_i$ — аддитивный эффект $i$-го SNP, $x_i \in \{0, 1, 2\}$ — дозировка аллеля.
