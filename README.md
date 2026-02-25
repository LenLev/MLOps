# Model Registry

Внутренний реестр ML-моделей. Хранит метаданные моделей и версий, управляет стадиями жизненного цикла, предоставляет API для доступа к актуальной версии

---

## Проблемы

Модели лежат в папках без структуры

- неизвестен владелец модели  
- отсутствуют метрики, информация о датасете и условиях обучения  
- версии закодированы в названиях папок, нет стандарта  
- непонятно, какая версия в продакшне  
- другие сервисы не могут получить путь к актуальной модели  
- поиск нужной модели ручной и неудобный  


---

## Требования

### Функциональные

- регистрировать модель: имя, команда, описание, теги
- добавлять версию:путь к файлам, метрики, описание, теги
- переводить версию между стадиями:staging  production archived
- получать актуальную production-версию по имени модели
- фильтровать модели по команде и тегам
- просматривать историю версий модели
- удалять модель или отдельную версию

### Нефункциональные

- минимальный стек: FastAPI + SQLite + SQLAlchemy  
- работает на одной машине, без облака  
- легко заменить SQLite на Postgres и добавить авторизацию  

---

## Архитектура

```
ML-команды
(кладут файлы в ./models/<team>/<name>/)
      |
      |  HTTP REST
      v
+---------------------+
|     FastAPI App     |
+---------------------+
      |
      v
+---------------------+     +-----------------------------+
|       SQLite        |     |        File Storage         |
|    registry.db      |     |  ./models/<team>/<model>/  |
|                     |     |       v1/  v2/  v3/ ...     |
+---------------------+     +-----------------------------+
```

- Реестр хранит метаданные: путь к файлам, метрики, стадию  
- Файлы моделей остаются на диске
Почему такой стек:

- FastAPI быстрый, автодокументация, Pydantic
-SQLite нет необходимости поднимать отдельный сервер для MVP, файл легко бекапить; при необходимости меняется на Postgres одной строкой
- SQLAlchemy ORM изолирует бизнес-логику от конкретной субд, миграции потом через alembic

Структура кода:

```
app/
main.py — точка входа, роутеры
database.py — движок SQLAlchemy, сессии
models.py — ORM-модели
schemas.py — Pydantic-схемы
crud.py — работа с БД
routers/
models.py — эндпоинты /models/...
versions.py — эндпоинты /versions/...
```

---

## Схема БД

### models

| поле | тип | |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT UNIQUE NOT NULL | уникальный slug модели |
| team | TEXT NOT NULL | команда-владелец |
| description | TEXT | |
| tags | TEXT | JSON-массив: ["nlp", "bert"] |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### model_versions

| поле | тип | описание |
|---|---|---|
| id | INTEGER PK | уникальный идентификатор |
| name | TEXT UNIQUE NOT NULL | slug модели |
| team | TEXT NOT NULL | команда-владелец |
| description | TEXT | описание модели |
| tags | TEXT | JSON-массив, напр. ["nlp","bert"] |
| created_at | DATETIME | дата создания |
| updated_at | DATETIME | дата обновления |

### model_versions

| поле | тип | описание |
|---|---|---|
| id | INTEGER PK | |
| model_id | INTEGER FK → models.id | связь с моделью, CASCADE DELETE |
| version | TEXT NOT NULL ||
| path | TEXT NOT NULL ||
| stage | TEXT | staging / production / archived |
| metrics | TEXT | JSON|
| tags | TEXT | JSON-массив |
| description | TEXT | описание версии |
| created_at | DATETIME | дата создания |
| updated_at | DATETIME | дата обновления |

Инвариант: у модели не более одной production-версии. При переводе новой версии в production предыдущая архивируется


## API

Полная документация после запуска: http://localhost:8000/docs

```bash
# зарегистрировать модель
POST /models
{"name": "sentiment-clf", "team": "mlds_1", "tags": ["nlp"]}

# добавить версию
POST /models/1/versions
{"version": "1", "path": "models/mlds_1/sentiment-clf/v1", "metrics": {"f1": 0.89}}

# перевести в production
PATCH /versions/1/stage
{"stage": "production"}

# получить актуальную production-версию по имени модели
GET /models/sentiment-clf/latest

# найти все модели команды с тегом nlp
GET /models?team=mlds_1&tag=nlp

# история версий
GET /models/1/versions

# удалить модель (и все версии)
DELETE /models/1
```

---

## Запуск

```bash
pip install -r requirements.txt
python run.py
```

Swagger: http://localhost:8000/docs

---

## 7. Структура проекта

```
ML2/
README.md
requirements.txt
run.py
registry.db
app/
  main.py
  database.py
  models.py
  schemas.py
  crud.py
  routers/
      models.py
      versions.py
  models/
  .gitkeep
```
