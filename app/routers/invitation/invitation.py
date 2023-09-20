# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import math

from common import LoggerFactory
from fastapi import APIRouter
from fastapi import Depends
from fastapi_sqlalchemy import db
from fastapi_utils.cbv import cbv

from app.commons.project_services import get_project_by_code
from app.commons.psql_services.invitation import create_invite
from app.commons.psql_services.invitation import query_invites
from app.commons.psql_services.user_event import create_event
from app.commons.psql_services.user_event import update_event
from app.components.identity.crud import IdentityCRUD
from app.components.identity.dependencies import get_identity_crud
from app.config import ConfigSettings
from app.models.api_response import APIResponse
from app.models.api_response import EAPIResponseCode
from app.models.invitation import InvitationListPOST
from app.models.invitation import InvitationPOST
from app.models.invitation import InvitationPOSTResponse
from app.models.invitation import InvitationPUT
from app.models.sql_invitation import InvitationModel
from app.resources.error_handler import APIException
from app.routers.invitation.invitation_notify import send_emails
from app.services.data_providers.identity_client import get_identity_client

router = APIRouter()

_API_TAG = 'Invitation'


@cbv(router)
class Invitation:
    identity_crud: IdentityCRUD = Depends(get_identity_crud)

    _logger = LoggerFactory(
        'api_invitation',
        level_default=ConfigSettings.LOG_LEVEL_DEFAULT,
        level_file=ConfigSettings.LOG_LEVEL_FILE,
        level_stdout=ConfigSettings.LOG_LEVEL_STDOUT,
        level_stderr=ConfigSettings.LOG_LEVEL_STDERR,
    ).get_logger()

    @router.post(
        '/invitations', response_model=InvitationPOSTResponse, summary='Creates an new invitation', tags=[_API_TAG]
    )
    async def create_invitation(self, data: InvitationPOST):  # noqa:C901
        self._logger.info('Called create_invitation')
        res = APIResponse()
        email = data.email
        relation_data = data.relationship
        inviter_project_role = data.inviter_project_role

        project = None
        if relation_data:
            project = await get_project_by_code(relation_data.get('project_code'))
            query = {'project_code': project['code'], 'email': email}
            if query_invites(query):
                res.result = 'Invitation for this user already exists'
                res.code = EAPIResponseCode.conflict
                return res.json_response()

        admin_client = await self.identity_crud.create_operations_admin()
        if await admin_client.get_user_by_email(email):
            self._logger.info('User already exists in platform')
            res.result = '[ERROR] User already exists in platform'
            res.code = EAPIResponseCode.bad_request
            return res.json_response()

        if project:
            if inviter_project_role not in ['platform_admin', 'admin']:
                raise APIException(error_msg='Permission Denied', status_code=EAPIResponseCode.forbidden.value)
            if inviter_project_role == 'admin' and not ConfigSettings.ALLOW_EXTERNAL_REGISTRATION:
                raise APIException(error_msg='Permission Denied', status_code=EAPIResponseCode.forbidden.value)

        account_in_ad = False
        if ConfigSettings.ENABLE_ACTIVE_DIRECTORY:
            IdentityClient = get_identity_client()
            with IdentityClient() as client:
                account_in_ad = client.user_exists(email)
                if account_in_ad:
                    client.add_user_to_group(email, ConfigSettings.AD_USER_GROUP)
                    if data.platform_role == 'admin':
                        client.add_user_to_group(email, ConfigSettings.AD_ADMIN_GROUP)
                    elif relation_data:
                        client.add_user_to_group(email, ConfigSettings.LDAP_PREFIX + '-' + project['code'])

        model_data = {
            'email': email,
            'invited_by': data.invited_by,
            'project_role': relation_data.get('project_role'),
            'platform_role': data.platform_role,
            'status': 'sent',
        }
        if project:
            model_data['project_code'] = project['code']
        invitation_entry = create_invite(model_data)

        event_detail = {
            'operator': invitation_entry.invited_by,
            'event_type': 'INVITE_TO_PROJECT' if invitation_entry.project_code else 'INVITE_TO_PLATFORM',
            'detail': {
                'invitation_id': str(invitation_entry.id),
                'platform_role': invitation_entry.platform_role,
            },
        }
        if project:
            event_detail['detail']['project_role'] = invitation_entry.project_role
            event_detail['detail']['project_code'] = project['code']
        await create_event(event_detail, identity_crud=self.identity_crud)
        await send_emails(invitation_entry, project, account_in_ad, self.identity_crud)
        res.result = 'success'
        return res.json_response()

    @router.get(
        '/invitation/check/{email}',
        response_model=InvitationPOSTResponse,
        summary="This method allow to get user's detail on the platform.",
        tags=[_API_TAG],
    )
    async def check_user(self, email: str, project_code: str = ''):
        self._logger.info('Called check_user')
        res = APIResponse()
        admin_client = await self.identity_crud.create_operations_admin()
        user_info = await admin_client.get_user_by_email(email)
        project = None
        if not user_info:
            invite = (
                db.session.query(InvitationModel)
                .filter(InvitationModel.email == email, InvitationModel.status.in_(['pending', 'sent']))
                .first()
            )
            if invite:
                res.result = {
                    'name': '',
                    'email': invite.email,
                    'status': 'invited',
                    'role': invite.platform_role,
                    'relationship': {},
                }
                return res.json_response()
            raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg='User not found in keycloak')
        if project_code:
            project = await get_project_by_code(project_code)

        roles = await self.identity_crud.get_user_realm_roles(user_info['id'])
        platform_role = 'member'
        project_role = ''
        for role in roles:
            if 'platform-admin' == role['name']:
                platform_role = 'admin'
            if project and project['code'] == role['name'].split('-')[0]:
                project_role = role['name'].split('-')[1]
        res.result = {
            'name': user_info['username'],
            'email': user_info['email'],
            'status': user_info['attributes'].get('status', ['pending'])[0],
            'role': platform_role,
            'relationship': {},
        }
        if project and project_role:
            res.result['relationship'] = {
                'project_code': project['code'],
                'project_role': project_role,
            }
        return res.json_response()

    @router.post(
        '/invitation-list', response_model=InvitationPOSTResponse, summary='list invitations from psql', tags=[_API_TAG]
    )
    def invitation_list(self, data: InvitationListPOST):
        self._logger.info('Called invitation_list')
        res = APIResponse()
        query = {}
        for field in ['project_code', 'status', 'invitation_code']:
            if data.filters.get(field):
                query[field] = data.filters[field]
        try:
            invites = db.session.query(InvitationModel).filter_by(**query)
            for field in ['email', 'invited_by']:
                if data.filters.get(field):
                    invites = invites.filter(getattr(InvitationModel, field).like('%' + data.filters[field] + '%'))
            if data.order_type == 'desc':
                sort_param = getattr(InvitationModel, data.order_by).desc()
            else:
                sort_param = getattr(InvitationModel, data.order_by).asc()
            count = invites.count()
            invites = invites.order_by(sort_param).offset(data.page * data.page_size).limit(data.page_size).all()
        except Exception as e:
            error_msg = f'Error querying invite for listing in psql: {str(e)}'
            self._logger.error(error_msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

        res.result = [i.to_dict() for i in invites]
        res.page = data.page
        res.num_of_pages = math.ceil(count / data.page_size)
        res.total = count
        return res.json_response()

    @router.put(
        '/invitation/{invite_id}',
        response_model=InvitationPOSTResponse,
        summary='update a single invite',
        tags=[_API_TAG],
    )
    async def invitation_update(self, invite_id: str, data: InvitationPUT):
        self._logger.info('Called invitation_update')
        res = APIResponse()
        update_data = {}
        if data.status:
            update_data['status'] = data.status

        query = {'id': invite_id}
        if data.status == 'complete':
            invite = db.session.query(InvitationModel).filter_by(**query).first()
            admin_client = await self.identity_crud.create_operations_admin()
            user = await admin_client.get_user_by_email(invite.email)
            update_event({'invitation_id': invite_id}, {'target_user': user['username'], 'target_user_id': user['id']})
        try:
            db.session.query(InvitationModel).filter_by(**query).update(update_data)
            db.session.commit()
        except Exception as e:
            error_msg = f'Error updating invite in psql: {str(e)}'
            self._logger.error(error_msg)
            raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
        res.result = 'success'
        return res.json_response()
