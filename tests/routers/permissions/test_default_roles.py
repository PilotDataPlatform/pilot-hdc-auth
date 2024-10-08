# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import sqlalchemy
from sqlalchemy.orm import Session

from app.models.permissions import CasbinRule


class TestDefaultRoles:
    def test_default_roles_create(self, test_client, db):
        engine = sqlalchemy.create_engine(db.get_connection_url())
        session = Session(bind=engine)
        session.query(CasbinRule).delete()
        session.commit()
        fake_rule = {
            'ptype': 'p',
            'v0': 'admin',
            'v1': 'greenroom',
            'v2': 'project',
            'v3': 'view',
            'v4': 'pilotdefault',
        }
        new_rule = CasbinRule(**fake_rule)
        session.add(new_rule)
        session.commit()

        payload = {'project_code': 'test_project'}
        response = test_client.post('/v1/defaultroles', json=payload)

        assert response.status_code == 200
        rule = session.query(CasbinRule).filter(CasbinRule.v4 == 'test_project').first()
        assert rule.v0 == 'admin'
        assert rule.v1 == 'greenroom'
        assert rule.v2 == 'project'
        assert rule.v3 == 'view'
        session.query(CasbinRule).delete()
        session.commit()
        session.close()

    def test_default_roles_create_mutliple(self, test_client, db):
        engine = sqlalchemy.create_engine(db.get_connection_url())
        session = Session(bind=engine)
        session.query(CasbinRule).delete()
        session.commit()
        for _i in range(0, 3):
            fake_rule = {
                'ptype': 'p',
                'v0': 'admin',
                'v1': 'greenroom',
                'v2': 'project',
                'v3': 'view',
                'v4': 'pilotdefault',
            }
            new_rule = CasbinRule(**fake_rule)
            session.add(new_rule)
            session.commit()
        fake_rule = {
            'ptype': 'p',
            'v0': 'admin',
            'v1': 'greenroom',
            'v2': 'project',
            'v3': 'view',
            'v4': 'anotherproject',
        }
        new_rule = CasbinRule(**fake_rule)
        session.add(new_rule)
        session.commit()

        payload = {'project_code': 'test_project'}
        response = test_client.post('/v1/defaultroles', json=payload)

        assert response.status_code == 200
        rule = session.query(CasbinRule).filter(CasbinRule.v4 == 'test_project')
        assert rule.count() == 3
        rule = rule.first()
        assert rule.v0 == 'admin'
        assert rule.v1 == 'greenroom'
        assert rule.v2 == 'project'
        assert rule.v3 == 'view'
        session.query(CasbinRule).delete()
        session.commit()
        session.close()
