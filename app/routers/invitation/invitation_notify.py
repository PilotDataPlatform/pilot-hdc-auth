# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import base64

from common import LoggerFactory

from app.components.identity.crud import IdentityCRUD
from app.config import ConfigSettings
from app.models.sql_invitation import InvitationModel
from app.services.notifier_services.email_service import SrvEmail

_logger = LoggerFactory(
    'api_invitation',
    level_default=ConfigSettings.LOG_LEVEL_DEFAULT,
    level_file=ConfigSettings.LOG_LEVEL_FILE,
    level_stdout=ConfigSettings.LOG_LEVEL_STDOUT,
    level_stderr=ConfigSettings.LOG_LEVEL_STDERR,
).get_logger()


async def send_emails(
    invitation_entry: InvitationModel, project: dict, account_in_ad: bool, identity_crud: IdentityCRUD
):
    _logger.info('Called send_emails')
    email_sender = SrvEmail()

    inviter_entry = await identity_crud.get_user_by_username(invitation_entry.invited_by)

    template_kwargs = {
        'inviter_email': inviter_entry['email'],
        'inviter_name': inviter_entry['username'],
        'support_email': ConfigSettings.EMAIL_SUPPORT,
        'support_url': ConfigSettings.EMAIL_PROJECT_SUPPORT_URL,
        'admin_email': ConfigSettings.EMAIL_ADMIN,
        'url': ConfigSettings.INVITATION_URL_LOGIN,
        'login_url': ConfigSettings.INVITATION_URL_LOGIN,
        'user_email': invitation_entry.email,
        'domain': ConfigSettings.DOMAIN_NAME,
        'helpdesk_email': ConfigSettings.EMAIL_HELPDESK,
        'platform_name': ConfigSettings.PROJECT_NAME,
        'register_url': ConfigSettings.EMAIL_PROJECT_REGISTER_URL,
        'register_link': ConfigSettings.INVITATION_REGISTER_URL.format(
            invitation_code=invitation_entry.invitation_code
        ),
    }

    subject = 'Invitation to join the'
    if project:
        subject = f'{subject} {project["name"]} project'
        if account_in_ad:
            template = 'invitation/ad_existing_invite_project.html'
        else:
            template = 'invitation/invite_project_register.html'
        template_kwargs['project_name'] = project['name']
        template_kwargs['project_code'] = project['code']
        template_kwargs['project_role'] = invitation_entry.project_role
    else:
        subject = f'{subject} {ConfigSettings.PROJECT_NAME}'
        if not account_in_ad:
            template = 'invitation/invite_without_project_register.html'
        else:
            template = 'invitation/ad_existing_invite_without_project.html'

        if invitation_entry.platform_role == 'admin':
            platform_role = 'Platform Administrator'
        else:
            platform_role = 'Platform User'
        template_kwargs['platform_role'] = platform_role

    attachment = []
    if not account_in_ad:
        if ConfigSettings.INVITE_ATTACHMENT:
            with open(ConfigSettings.INVITE_ATTACHMENT, 'rb') as f:
                data = base64.b64encode(f.read()).decode()
                attachment = [{'name': ConfigSettings.INVITE_ATTACHMENT_NAME, 'data': data}]

    email_sender.send(
        subject,
        invitation_entry.email,
        ConfigSettings.EMAIL_SUPPORT,
        msg_type='html',
        template=template,
        template_kwargs=template_kwargs,
        attachments=attachment,
    )
