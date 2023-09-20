# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import LoggerFactory
from fastapi_sqlalchemy import db

from app.config import ConfigSettings
from app.models.api_response import EAPIResponseCode
from app.models.permissions import CasbinRule
from app.models.permissions import PermissionMetadataModel
from app.models.permissions import RoleModel
from app.models.permissions_schema import ListPermissions
from app.models.permissions_schema import RuleModel
from app.resources.error_handler import APIException

_logger = LoggerFactory(
    'api_permissions',
    level_default=ConfigSettings.LOG_LEVEL_DEFAULT,
    level_file=ConfigSettings.LOG_LEVEL_FILE,
    level_stdout=ConfigSettings.LOG_LEVEL_STDOUT,
    level_stderr=ConfigSettings.LOG_LEVEL_STDERR,
).get_logger()


def list_permissions(data: ListPermissions) -> tuple[list[PermissionMetadataModel], int]:
    """List permissions with pagination and sorting."""
    permissions = db.session.query(PermissionMetadataModel)
    count = permissions.count()
    if data.order_type == 'desc':
        sort_param = getattr(PermissionMetadataModel, data.order_by).desc()
    else:
        sort_param = getattr(PermissionMetadataModel, data.order_by).asc()
    permissions = permissions.order_by(sort_param).offset(data.page * data.page_size).limit(data.page_size).all()
    return permissions, count


def get_permission_metadata_by_id(metadata_id: str) -> dict:
    """Get permission metadata by id."""
    try:
        return db.session.query(PermissionMetadataModel).get(metadata_id)
    except Exception as e:
        error_msg = f'Error getting permission metadata rules in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)


def get_roles_by_code(project_code: str) -> list[str]:
    """Get roles by code."""
    try:
        all_roles = (
            db.session.query(CasbinRule).filter_by(v4=project_code).with_entities(CasbinRule.v0).distinct().all()
        )
        all_roles = [i[0] for i in all_roles]
        return all_roles
    except Exception as e:
        error_msg = f'Error getting permission metadata rules in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)


def get_rules_by_role(project_role: str) -> list[CasbinRule]:
    """Get roles by role."""
    try:
        all_roles = db.session.query(CasbinRule).filter_by(v4=project_role).all()
        return all_roles
    except Exception as e:
        error_msg = f'Error getting casbin rules in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)


def get_casbin_rules(resource: str, operation: str, zone: str, project_code: str) -> dict[str, bool]:
    """Get casbin rules."""
    all_roles = get_roles_by_code(project_code)
    rule_model = RuleModel(v1=zone, v2=resource, v3=operation, v4=project_code)
    try:
        rules = db.session.query(CasbinRule).filter_by(**rule_model.dict(exclude_unset=True))
        result = {i: False for i in all_roles if i != 'platform_admin'}
        for rule in rules:
            result[rule.v0] = True
    except Exception as e:
        error_msg = f'Error getting casbin rules in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
    return result


def get_permission_metadata_by_ids_bulk(metadata_ids: list[str]) -> list[dict]:
    """Bulk get permissions metadata by id list."""
    metadata = db.session.query(PermissionMetadataModel).filter(PermissionMetadataModel.id.in_(metadata_ids)).all()
    if not metadata:
        error_msg = f'Permission metadata not found: {metadata_ids}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.not_found.value, error_msg=error_msg)
    return metadata


def create_casbin_rule_bulk(rules: list[dict], project_code: str):
    """Bulk create rules from list of metadata id's and project roles."""
    new_rules = []
    try:
        for project_role, metadata_list in rules.items():
            metadata_obj_list = get_permission_metadata_by_ids_bulk(metadata_list)
            for permission_metadata in metadata_obj_list:
                rule_model = RuleModel(
                    ptype='p',
                    v0=project_role,
                    v1=permission_metadata.zone,
                    v2=permission_metadata.resource,
                    v3=permission_metadata.operation,
                    v4=project_code,
                )
                new_rule = CasbinRule(**rule_model.dict(exclude_unset=True))
                new_rules.append(new_rule)
        db.session.bulk_save_objects(new_rules)
        db.session.commit()
    except APIException as e:
        raise e
    except Exception as e:
        error_msg = f'Error bulk creating rules {rules}: {e}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)


def create_casbin_rule(project_role: str, resource: str, operation: str, zone: str, project_code: str):
    """Create a casbin rule."""
    rule_data = {
        'ptype': 'p',
        'v0': project_role,
        'v1': zone,
        'v2': resource,
        'v3': operation,
        'v4': project_code,
    }
    try:
        duplicate = db.session.query(CasbinRule).filter_by(**rule_data)
    except Exception as e:
        error_msg = f'Error creating rule in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)

    if duplicate.count():
        raise APIException(error_msg='Role already exists', status_code=EAPIResponseCode.conflict.value)

    try:
        new_rule = CasbinRule(**rule_data)
        db.session.add(new_rule)
        db.session.commit()
    except Exception as e:
        error_msg = f'Error creating rule in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)


def delete_casbin_rule(project_role: str, resource: str, operation: str, zone: str, project_code: str):
    """Delete a casbin rule."""
    try:
        rule_model = RuleModel(v0=project_role, v1=zone, v2=resource, v3=operation, v4=project_code)
        db.session.query(CasbinRule).filter_by(**rule_model.dict(exclude_unset=True)).delete()
        db.session.commit()
    except Exception as e:
        error_msg = f'Error deleting rule in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)


def delete_casbin_rules_bulk(rules: list[dict], project_code: str):
    """Bulk delete casbin rules from list of metadata id's and project roles."""
    try:
        for project_role, metadata_list in rules.items():
            metadata_obj_list = get_permission_metadata_by_ids_bulk(metadata_list)
            for permission_metadata in metadata_obj_list:
                rule_model = RuleModel(
                    v0=project_role,
                    v1=permission_metadata.zone,
                    v2=permission_metadata.resource,
                    v3=permission_metadata.operation,
                    v4=project_code,
                )
                rule_model.dict(exclude_unset=True)
                db.session.query(CasbinRule).filter_by(**rule_model.dict(exclude_unset=True)).delete()
        db.session.commit()
    except APIException as e:
        raise e
    except Exception as e:
        error_msg = f'Error bulk creating rules {rules}: {e}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)


def create_role_record(name: str, project_code: str, is_default: bool):
    try:
        role = RoleModel(name=name, project_code=project_code, is_default=is_default)
        db.session.add(role)
        db.session.commit()
    except Exception as e:
        error_msg = f'Error creating role record in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)


def list_roles(project_code: str, order_by: str, order_type: str) -> list[dict]:
    try:
        query = db.session.query(RoleModel).filter_by(project_code=project_code, is_default=False)
        if order_type == 'desc':
            sort_param = getattr(RoleModel, order_by).desc()
        else:
            sort_param = getattr(RoleModel, order_by).asc()
        result = query.order_by(sort_param).all()
        default_query = db.session.query(RoleModel).filter_by(project_code=project_code, is_default=True)
        default_result = default_query.order_by(RoleModel.name).all()
    except Exception as e:
        error_msg = f'Error listing roles in psql: {str(e)}'
        _logger.error(error_msg)
        raise APIException(status_code=EAPIResponseCode.internal_error.value, error_msg=error_msg)
    all_results = [role.to_dict() for role in default_result]
    all_results += [role.to_dict() for role in result]
    return all_results
