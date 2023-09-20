# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import ldap
import ldap.modlist as modlist
import yaml
from common import LoggerFactory

from app.commons.psql_services.ldap_id import create_ldap_id
from app.config import ConfigSettings
from app.models.base_models import EAPIResponseCode
from app.resources.error_handler import APIException

_logger = LoggerFactory(
    'ldap client',
    level_default=ConfigSettings.LOG_LEVEL_DEFAULT,
    level_file=ConfigSettings.LOG_LEVEL_FILE,
    level_stdout=ConfigSettings.LOG_LEVEL_STDOUT,
    level_stderr=ConfigSettings.LOG_LEVEL_STDERR,
).get_logger()


class LdapClient:
    """LdapClient."""

    def __init__(self) -> None:
        ldap.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)
        self.conn = None
        self.objectclass = None
        with open('ldap_query_config.yaml', 'r') as f:
            try:
                yaml_data = yaml.safe_load(f)
                self.group_dn_template = yaml_data.get('GROUP_DN_TEMPLATE')
                self.user_search_email_template = yaml_data.get('USER_SEARCH_EMAIL_TEMPLATE')
                self.user_search_username_template = yaml_data.get('USER_SEARCH_USERNAME_TEMPLATE')
                self.dc_template = yaml_data.get('DC_TEMPLATE')
            except yaml.YAMLError as e:
                raise APIException(
                    error_msg=f'Invalid yaml for ldap_query_config.yaml: {e}',
                    status_code=EAPIResponseCode.internal_error.value,
                )

    def connect(self) -> None:
        """
        Summary:
            Setup the connection with ldap by the configure file

        Return:
            None
        """
        self.conn = ldap.initialize(ConfigSettings.LDAP_URL)
        self.objectclass = [ConfigSettings.LDAP_GROUP_OBJECTCLASS.encode('utf-8')]
        self.conn.simple_bind_s(ConfigSettings.LDAP_ADMIN_DN, ConfigSettings.LDAP_ADMIN_SECRET)

    def disconnect(self) -> None:
        """
        Summary:
            disconnect from ldap

        Return:
            None
        """
        self.conn.unbind_s()

    async def __aenter__(self) -> 'LdapClient':
        self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    def format_group_dn(self, group_name: str) -> str:
        """
        Summary:
            format the dn based on config

        Parameter:
            group_name(string): the group name that will be added
                into AD

        Return:
            formated dn name(string)
        """
        group_dn = self.group_dn_template.format(
            cn=ConfigSettings.LDAP_PREFIX,
            group_name=group_name,
            ou=ConfigSettings.LDAP_OU,
            dc1=ConfigSettings.LDAP_DC1,
            dc2=ConfigSettings.LDAP_DC2,
        )
        return group_dn

    def format_group_name(self, group_name: str) -> str:
        return ConfigSettings.LDAP_PREFIX + '-' + group_name

    async def add_user_to_group(self, email: str, group_name: str) -> str:
        """
        Summary:
            adding the user to target group_dn. Note here,
            there group_dn is the result from format_group_dn function

        Parameter:
            user_dn(string): formated user dn
            user_dn(group_dn): formated group dn

        Return:
            formated dn name(string)
        """
        user = self.get_user_by_email(email)
        user_dn = user['dn']
        group_dn = self.format_group_dn(group_name)

        _logger.info(f'add user: {email}')
        _logger.info(f'add user from group dn: {group_name}')
        try:
            operation_list = [(ldap.MOD_ADD, 'member', [user_dn.encode('utf-8')])]
            self.conn.modify_s(group_dn, operation_list)
        except ldap.ALREADY_EXISTS:
            _logger.info(f'Already in group skipping group add: {group_dn}')
            return 'conflict'
        return 'success'

    async def remove_user_from_group(self, email: str, group_name: str) -> dict:
        """
        Summary:
            remove the user to target group_dn. Note here,
            there group_dn/user_dn are the result from format_group_dn function

        Parameter:
            user_dn(string): formated user dn
            user_dn(group_dn): formated group dn

        Return:
            formated dn name(string)
        """
        _logger.info(f'removed user: {email}')
        _logger.info(f'remove user from group dn: {group_name}')

        user = self.get_user_by_email(email)
        user_dn = user['dn']
        group_dn = self.format_group_dn(group_name)

        operation_list = [(ldap.MOD_DELETE, 'member', [user_dn.encode('utf-8')])]
        res = self.conn.modify_s(group_dn, operation_list)
        return res

    async def get_user_by_email(self, email: str) -> dict:
        """
        Summary:
            get the user infomation in ldap by email

        Parameter:
            email(string): user email in ldap

        Return:
            user(dict): user data
        """
        user_search = self.user_search_email_template.format(email=email)
        users_all = self.conn.search_s(
            self.dc_template.format(dc1=ConfigSettings.LDAP_DC1, dc2=ConfigSettings.LDAP_DC2),
            ldap.SCOPE_SUBTREE,
            user_search,
        )
        user_found = None
        for user_dn, entry in users_all:
            if 'mail' in entry:
                decoded_email = entry['mail'][0].decode('utf-8')
                if decoded_email == email:
                    user_found = (user_dn, entry)
        if not user_found:
            raise Exception('get_user_by_email error: User not found on AD: ' + email)
        return {
            'username': str(entry['uid'][0]),
            'first_name': str(entry['givenName'][0]),
            'last_name': str(entry['sn'][0]),
            'email': str(entry['mail'][0]),
            'dn': user_dn,
            'groups': entry.get('memberOf', []),
        }

    async def get_user_by_username(self, username: str) -> dict:
        """
        Summary:
            get the user infomation in ldap by username

        Parameter:
            username(string): user name in ldap

        Return:
            user_dn(string): user dn in ldap
            user_info(dict): the rest infomation in user eg. group
        """
        user_search = self.user_search_username_template.format(username=username)
        users = self.conn.search_s(
            self.dc_template.format(dc1=ConfigSettings.LDAP_DC1, dc2=ConfigSettings.LDAP_DC2),
            ldap.SCOPE_SUBTREE,
            user_search,
        )

        user_found = None
        for user_dn, entry in users:
            if ConfigSettings.LDAP_USER_QUERY_FIELD in entry:
                decoded_username = entry[ConfigSettings.LDAP_USER_QUERY_FIELD][0].decode('utf-8')
                if decoded_username == username:
                    user_found = (user_dn, entry)

        if not user_found:
            _logger.info(f'user {username} is not found in AD')
            return None, None
        _logger.info(f'found user by username: {user_found}')
        return {
            'username': str(entry['uid'][0]),
            'first_name': str(entry['givenName'][0]),
            'last_name': str(entry['sn'][0]),
            'email': str(entry['mail'][0]),
            'dn': user_dn,
            'groups': entry.get('memberOf', []),
        }

    async def user_exists(self, email: str) -> bool:
        try:
            self.get_user_by_email(email)
        except Exception:
            return False
        return True

    async def create_group(self, group_name: str, description: str = ''):
        group_dn = self.format_group_dn(group_name)
        user_object_class = f'{ConfigSettings.LDAP_PREFIX}-{group_name}'.encode('utf-8')
        attrs = {'objectclass': self.objectclass, ConfigSettings.LDAP_USER_QUERY_FIELD: user_object_class}
        if description:
            attrs['description'] = description.encode('utf-8')

        if ConfigSettings.LDAP_SET_GIDNUMBER:
            ldap_id_obj = create_ldap_id(group_name)
            attrs['gidNumber'] = str(ldap_id_obj.id).encode('utf-8')

        ldif = modlist.addModlist(attrs)
        self.conn.add_s(group_dn, ldif)

    async def delete_group(self, group_name: str):
        group_dn = self.format_group_dn(group_name)
        try:
            self.conn.delete_s(group_dn)
        except ldap.NO_SUCH_OBJECT:
            raise APIException(error_msg='No such group', status_code=EAPIResponseCode.bad_request.value)

    async def create_user(self, username: str, email: str, first_name: str, last_name: str, password: str) -> dict:
        dc = self.dc_template.format(dc1=ConfigSettings.LDAP_DC1, dc2=ConfigSettings.LDAP_DC2)
        user_dn = f'uid={username},ou=users,' + dc
        groups = [i.encode('utf-8') for i in ConfigSettings.LDAP_USER_OBJECT_GROUPS]
        cn = first_name + ' ' + last_name
        entry = {
            'objectClass': groups,
            'cn': cn.encode('utf-8'),
            'givenName': first_name.encode('utf-8'),
            'sn': last_name.encode('utf-8'),
            'homeDirectory': f'/home/{username}'.encode('utf-8'),
            'uidNumber': '0'.encode('utf-8'),
            'gidNumber': '0'.encode('utf-8'),
            'mail': email.encode('utf-8'),
            'userPassword': password.encode('utf-8'),
        }
        ldif = modlist.addModlist(entry)
        try:
            self.conn.add_s(user_dn, ldif)
        except Exception as e:
            _logger.error(f'Error creating user in LDAP: {e}')
        finally:
            self.conn.unbind_s()
        return 'success'
