# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from pydantic import BaseModel


class AccountRequestPOST(BaseModel):
    email: str
    username: str


class ContractRequestPOST(BaseModel):
    contract_description: str
    interest_description: str
    email: str
    first_name: str
    last_name: str
