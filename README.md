# hermes-plugin-run-profile-endpoint

Плагин-мост `POST /api/v1/run-profile`. Внешние оркестраторы (n8n,
LangGraph, MC pipeline, curl) отдают единицу работы Гермесу и получают
ответ.

## Зачем

```
external system ──POST /api/v1/run-profile──▶ handle_run_profile()
                                                     │
                                                     ▼
                                          create_bridge_task() —
                                          kanban-доска bridge-runs
                                                     │
                                                     ▼
                                          диспетчер Гермеса спавнит
                                          worker с указанным profile
                                                     │
                                                     ▼
                                          worker делает работу,
                                          вызывает kanban_complete()
                                                     │
                                                     ▼
                                          handle_run_profile возвращает
                                          результат вызывающему
```

Sync mode (по умолчанию) — блокирует до `timeout_sec` секунд опроса.
Async mode — сразу возвращает `{run_id}`, клиент опрашивает
`GET /api/v1/run-profile/<run_id>` пока не терминальное состояние.

## Состояние: СПЯЩИЙ

Файл `run_profile_endpoint.py` определяет aiohttp handlers, но
**нигде не подключены к серверу**:

- Upstream `gateway/platforms/api_server.py` создаёт собственный
  `web.Application(...)` для `/v1/messages`
- Раньше наш overlay-`hermes_cli/kanban_db.py` подцеплял routes
  через middleware при старте api_server
- При переходе на release tag `v2026.5.29.2` мы дропнули старый
  overlay (`refactor(overlay): дроп 81 устаревшего upstream-snapshot`)
  и wire-up отвалился

Endpoint `POST /api/v1/run-profile` в runtime **не существует**.

## Пути восстановления

### 1. Upstream PR (чистый)

Добавить в `gateway/platforms/api_server.py:start()` событие или
методику `register_routes(routes_or_callable)` через которую плагины
поставляют свои RouteDef. Тогда наш плагин в `__init__.py` делает:

```python
from hermes.api_server_hooks import register_routes
from . import run_profile_endpoint as ep
register_routes([
    aiohttp_web.post("/api/v1/run-profile", ep.handle_run_profile),
    aiohttp_web.get("/api/v1/run-profile/{run_id}", ep.handle_get_run_profile),
])
```

### 2. Monkey-patch плагин `hermes-plugin-aiohttp-route-bootstrap`

Wrap `api_server.start()`. После создания `_app` сканирует все плагины
которые определяют `get_routes()`, добавляет их в `_app.router`.

Преимущество: не нужен upstream PR.
Недостаток: фрагильно если upstream переименует `start()` или `_app`.

### 3. Side-channel (отдельный aiohttp сервер)

Плагин стартует собственный aiohttp на другом порту (например :8643),
регистрирует там routes. UI клиент бьёт туда. Не зависит от upstream.

Преимущество: ноль upstream-cooperation.
Недостаток: ещё один процесс, ещё один порт, потеря единого API.

## Конфиг

```yaml
plugins:
  enabled:
    - run-profile-endpoint
```

При загрузке плагин залогирует:

```
INFO run-profile-endpoint: loaded (dormant — handlers готовы, ждёт wire-up в gateway/platforms/api_server.py)
```

## Mount

Уже подмонтировано через супер-репо `sources/hermes-plugins-collection`.
