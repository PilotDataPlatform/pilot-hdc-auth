# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import logging
from contextlib import AbstractContextManager
from typing import Any

from common.logging.logging import Logger

logger: Logger = logging.getLogger('pilot.auth')


class AuditLog(AbstractContextManager):
    """Context manager for audit log."""

    def __init__(self, message: str, **kwds: Any) -> None:
        self.message = message
        self.kwds = kwds

    def __enter__(self) -> None:
        logger.audit(f'Attempting to {self.message}.', **self.kwds)

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        if exc_type is not None:
            logger.audit(f'Received an unexpected error while attempting to {self.message}.', **self.kwds)
            return

        logger.audit(f'Successfully managed to {self.message}.', **self.kwds)
