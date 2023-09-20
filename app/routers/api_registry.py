# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import FastAPI

from app.routers import ops_admin
from app.routers import ops_user
from app.routers import user_account_management
from app.routers.api_user_create import api_user_create
from app.routers.event import event
from app.routers.health import health
from app.routers.invitation import external
from app.routers.invitation import invitation
from app.routers.permissions import default_roles
from app.routers.permissions import permission_metadata
from app.routers.permissions import permissions


def api_registry(app: FastAPI):
    app.include_router(ops_user.router, prefix='/v1')
    app.include_router(user_account_management.router, prefix='/v1')
    app.include_router(permissions.router, prefix='/v1')
    app.include_router(ops_admin.router, prefix='/v1')
    app.include_router(invitation.router, prefix='/v1')
    app.include_router(event.router, prefix='/v1')
    app.include_router(health.router, prefix='/v1')
    app.include_router(api_user_create.router, prefix='/v1')
    app.include_router(external.router, prefix='/v1')
    app.include_router(permission_metadata.router, prefix='/v1')
    app.include_router(default_roles.router, prefix='/v1')
