# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import random

from fastapi_sqlalchemy import db
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base

from app.config import ConfigSettings

Base = declarative_base()


def generate_id():
    gid = random.randint(ConfigSettings.LDAP_GID_LOWER_BOUND, ConfigSettings.LDAP_GID_UPPER_BOUND)
    while db.session.query(LdapIdModel).filter_by(id=gid).first() is not None:
        gid = random.randint(ConfigSettings.LDAP_GID_LOWER_BOUND, ConfigSettings.LDAP_GID_UPPER_BOUND)
    return gid


class LdapIdModel(Base):
    __tablename__ = 'ldap_id'
    __table_args__ = {'schema': ConfigSettings.RDS_SCHEMA_PREFIX + '_ldap'}
    id = Column(Integer(), unique=True, primary_key=True, default=generate_id)
    group_name = Column(String())
