"""run-profile-endpoint — мост к внешним оркестраторам через POST /api/v1/run-profile.

Состояние: dormant. Handlers готовы (handle_run_profile, handle_get_run_profile),
но регистрация на aiohttp app происходит где-то снаружи. В текущем upstream
release tag нет hook'а у api_server для подключения плагин-routes — wire-up
ждёт upstream PR или отдельного monkey-patch плагина.

Sys.modules sideload: код когда-то лежал на пути gateway.run_profile_endpoint
(через overlay COPY в /opt/hermes/gateway/). Сохраняем доступность по тому же
имени на случай если будущий wire-up landed по старому import-пути.
"""

from __future__ import annotations

import logging
import sys

from . import run_profile_endpoint as _module

sys.modules.setdefault("gateway.run_profile_endpoint", _module)

# Re-export public surface
from .run_profile_endpoint import (  # noqa: E402,F401
    ensure_bridge_board,
    create_bridge_task,
    get_task_snapshot,
    wait_for_terminal,
    handle_run_profile,
    handle_get_run_profile,
)

logger = logging.getLogger(__name__)
logger.info(
    "run-profile-endpoint: loaded (dormant — handlers готовы, "
    "ждёт wire-up в gateway/platforms/api_server.py)"
)
