# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from app.config import ConfigSettings


def test_get_external_is_true_200(test_client, monkeypatch):
    monkeypatch.setattr(ConfigSettings, 'ALLOW_EXTERNAL_REGISTRATION', True)
    response = test_client.get('/v1/invitations/external')
    assert response.status_code == 200
    assert response.json()['result']['allow_external_registration'] is True


def test_get_external_is_false_200(test_client, monkeypatch):
    monkeypatch.setattr(ConfigSettings, 'ALLOW_EXTERNAL_REGISTRATION', False)
    response = test_client.get('/v1/invitations/external')
    assert response.status_code == 200
    assert response.json()['result']['allow_external_registration'] is False
