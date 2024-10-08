# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import httpx

from app.config import ConfigSettings


class SrvEmail:
    def send(
        self,
        subject: str,
        receiver: str,
        sender: str,
        content: str = '',
        msg_type: str = 'plain',
        template: str = None,
        template_kwargs: dict = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Summary:
            The api is used to request a emailing sending operation
            by input payload

        Parameter:
            - subject(string): The subject of email
            - receiver(string): The reciever email
            - sender(string): The sender email
            - content(string): default="", The email content
            - msg_type(string): default="plain", the message type for email
            - template(string): default=None, email service support some predefined template
            - template_kwargs(dict): default={}, the parameters for the template structure

        Return:
            200 updated
        """
        if attachments is None:
            attachments = []

        if not template_kwargs:
            template_kwargs = {}

        url = ConfigSettings.NOTIFY_SERVICE + 'email/'
        payload = {
            'subject': subject,
            'sender': sender,
            'receiver': [receiver],
            'msg_type': msg_type,
            'attachments': attachments,
        }
        if content:
            payload['message'] = content
        if template:
            payload['template'] = template
            payload['template_kwargs'] = template_kwargs
        res = httpx.post(url=url, json=payload)
        return json.loads(res.text)
