# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ...exceptions import (
    DSLParsingLogicException,
    ERROR_UNKNOWN_TYPE,
    ERROR_INVALID_TYPE_NAME,
)
from ... import constants, utils
from .. import Value, Requirement, sibling_predicate
from .version import ToscaDefinitionsVersion
from .types import Type, Types, DataTypeDerivedFrom, derived_from_predicate
from . import PRIMITIVE_TYPES, Element, Dict, DictElement, Leaf


class SchemaPropertyDescription(Element):
    schema = Leaf(obj_type=str)


class SchemaPropertyType(Element):
    schema = Leaf(obj_type=str)
    # requires will be modified later.
    requires = {}
    provides = ['component_types']

    def validate(self, data_type, **kwargs):
        if all([self.initial_value,
                self.initial_value not in constants.USER_PRIMITIVE_TYPES,
                not data_type]):
            raise DSLParsingLogicException(
                ERROR_UNKNOWN_TYPE,
                "Illegal type name '{0}'".format(self.initial_value))

    def calculate_provided(self, component_types, **_):
        return {'component_types': component_types}


class SchemaPropertyDefault(Element):
    schema = Leaf(obj_type=PRIMITIVE_TYPES)
    requires = {
        SchemaPropertyType: [Requirement(
            'component_types', required=False, predicate=sibling_predicate)],
    }

    def parse(self, component_types, **_):
        type_name = self.sibling(SchemaPropertyType).value
        initial_value = self.initial_value
        if initial_value is None:
            if all([type_name is not None,
                    type_name not in constants.USER_PRIMITIVE_TYPES]):
                initial_value = {}
            else:
                return None
        component_types = component_types or {}
        prop_name = self.ancestor(SchemaProperty).name
        undefined_property_error = (
            'Undefined property {1} in default value of type {0}')
        current_type = self.ancestor(Schema).parent().name
        return utils.parse_value(
            value=initial_value,
            type_name=type_name,
            data_types=component_types,
            undefined_error_message=undefined_property_error,
            missing_error_message='illegal state',
            node_name=current_type,
            path=[prop_name],
            raise_on_missing_property=False)


class SchemaPropertyRequired(Element):
    schema = Leaf(obj_type=bool)
    requires = {
        ToscaDefinitionsVersion: ['version'],
        'inputs': ['validate_version'],
    }


class SchemaProperty(Element):
    schema = {
        'required': SchemaPropertyRequired,
        'default': SchemaPropertyDefault,
        'description': SchemaPropertyDescription,
        'type': SchemaPropertyType,
    }

    def parse(self):
        result = dict(
            (child.name, child.value)
            for child in self.children() if child.defined)
        if isinstance(self.parent(), SchemaWithInitialDefault):
            initial_default = self.child(SchemaPropertyDefault).initial_value
            result['initial_default'] = initial_default
        return result


class Schema(DictElement):
    schema = Dict(obj_type=SchemaProperty)


class SchemaWithInitialDefault(Schema):
    pass


class DataTypeDescription(Element):
    schema = Leaf(obj_type=str)


class DataTypeVersion(Element):
    schema = Leaf(obj_type=str)


class DataType(Type):
    schema = {
        'properties': SchemaWithInitialDefault,
        'description': DataTypeDescription,
        'derived_from': DataTypeDerivedFrom,
        'version': DataTypeVersion,
    }
    requires = {
        'self': [
            Requirement(
                'component_types',
                multiple_results=True,
                required=False,
                predicate=lambda source, target:
                target.name in source.direct_component_types),
            Value(
                'super_type',
                predicate=derived_from_predicate,
                required=False),
        ]
    }
    provides = ['component_types']

    def __init__(self, *args, **kwargs):
        super(DataType, self).__init__(*args, **kwargs)
        self._direct_component_types = None
        self.component_types = {}

    def validate(self, **kwargs):
        if self.name in constants.USER_PRIMITIVE_TYPES:
            raise DSLParsingLogicException(
                ERROR_INVALID_TYPE_NAME,
                "Can't redefine primitive type {0}".format(self.name))

    def parse(self, super_type, component_types, **_):
        merged_component_types = {}
        for component in component_types:
            merged_component_types.update(component)
        self.component_types.update(merged_component_types)
        result = self.build_dict_result()
        if constants.PROPERTIES not in result:
            result[constants.PROPERTIES] = {}
        if super_type:
            result[constants.PROPERTIES] = utils.merge_schemas(
                overridden_schema=super_type.get('properties', {}),
                overriding_schema=result.get('properties', {}),
                data_types=merged_component_types)
        self.fix_properties(result)
        self.component_types[self.name] = result
        return result

    def calculate_provided(self, **_):
        return {'component_types': self.component_types}

    @property
    def direct_component_types(self):
        if self._direct_component_types is None:
            direct_component_types = set()
            parent_type = self.initial_value.get(constants.DERIVED_FROM)
            if parent_type:
                direct_component_types.add(parent_type)
            for desc in self.descendants(SchemaPropertyType):
                direct_component_types.add(desc.initial_value)
            self._direct_component_types = direct_component_types
        return self._direct_component_types


class DataTypes(Types):
    schema = Dict(obj_type=DataType)
    requires = {
        ToscaDefinitionsVersion: ['version'],
        'inputs': ['validate_version'],
    }


# source: element describing data_type name
# target: data_type
def _has_type(source, target):
    return source.initial_value == target.name


SchemaPropertyType.requires[DataType] = [
    Value('data_type', predicate=_has_type, required=False),
    Requirement('component_types', predicate=_has_type, required=False),
]
