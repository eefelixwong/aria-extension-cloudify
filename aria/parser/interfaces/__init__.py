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

from .operation_merger import (
    NodeTypeNodeTypeOperationMerger,
    RelationshipTypeRelationshipInstanceOperationMerger,
    RelationshipTypeRelationshipTypeOperationMerger,
    NodeTemplateNodeTypeOperationMerger)
from .interfaces_merger import InterfacesMerger


INTERFACES = 'interfaces'
SOURCE_INTERFACES = 'source_interfaces'
TARGET_INTERFACES = 'target_interfaces'


def merge_node_type_interfaces(
        overriding_interfaces,
        overridden_interfaces):
    return InterfacesMerger(
        overriding_interfaces=overriding_interfaces,
        overridden_interfaces=overridden_interfaces,
        operation_merger=NodeTypeNodeTypeOperationMerger
    ).merge()


def merge_node_type_and_node_template_interfaces(  # pylint: disable=invalid-name
        node_type_interfaces,
        node_template_interfaces):
    return InterfacesMerger(
        overriding_interfaces=node_template_interfaces,
        overridden_interfaces=node_type_interfaces,
        operation_merger=NodeTemplateNodeTypeOperationMerger
    ).merge()


def merge_relationship_type_interfaces(  # pylint: disable=invalid-name
        overriding_interfaces,
        overridden_interfaces):
    return InterfacesMerger(
        overriding_interfaces=overriding_interfaces,
        overridden_interfaces=overridden_interfaces,
        operation_merger=RelationshipTypeRelationshipTypeOperationMerger
    ).merge()


def merge_relationship_type_and_instance_interfaces(  # pylint: disable=invalid-name
        relationship_type_interfaces,
        relationship_instance_interfaces):
    return InterfacesMerger(
        overriding_interfaces=relationship_instance_interfaces,
        overridden_interfaces=relationship_type_interfaces,
        operation_merger=RelationshipTypeRelationshipInstanceOperationMerger
    ).merge()
