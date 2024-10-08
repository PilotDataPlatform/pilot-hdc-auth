# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID


class User(dict):
    """Realm user model."""

    @property
    def id(self) -> UUID:
        return UUID(self['id'])

    @property
    def username(self) -> str:
        return self['username']

    @property
    def email(self) -> str:
        return self['email']


class Role(dict):
    """Realm role model."""

    @property
    def id(self) -> UUID:
        return UUID(self['id'])

    @property
    def name(self) -> str:
        return self['name']
