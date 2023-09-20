# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime

from common import LoggerFactory
from pytz import timezone

logger = LoggerFactory('execution_time').get_logger()


def mask_email(email):
    sections = email.split('@')
    first = ''.join(['*' for i in sections[0][0:-2]])
    second = ''.join([i if i == '.' else '*' for i in sections[1]])
    return sections[0][0] + first + sections[0][-1] + '@' + second


def get_formatted_datetime(tz):
    cet = timezone(tz)
    now = datetime.now(cet)
    return now.strftime('%Y-%m-%d, %-I:%M%p (%Z)')
