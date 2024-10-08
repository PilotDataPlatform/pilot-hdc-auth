# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

from app.components.keycloak.models import Role
from app.components.keycloak.models import User


class TestUser:
    def test_id_returns_user_id_as_uuid(self, fake):
        user_id = fake.uuid4()
        user = User({'id': user_id})

        assert user.id == UUID(user_id)

    def test_username_returns_username_property(self, fake):
        username = fake.user_name()
        user = User({'username': username})

        assert user.username == username

    def test_email_returns_email_property(self, fake):
        email = fake.email()
        user = User({'email': email})

        assert user.email == email


class TestRole:
    def test_id_returns_role_id_as_uuid(self, fake):
        role_id = fake.uuid4()
        role = Role({'id': role_id})

        assert role.id == UUID(role_id)

    def test_name_returns_name_property(self, fake):
        name = fake.word()
        role = Role({'name': name})

        assert role.name == name
