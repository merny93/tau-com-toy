# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: combined.proto
# Protobuf Python Version: 5.28.3
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    28,
    3,
    '',
    'combined.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import state_pb2 as state__pb2
import action_pb2 as action__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0e\x63ombined.proto\x12\x08\x63ombined\x1a\x0bstate.proto\x1a\x0c\x61\x63tion.proto\"e\n\x0f\x43ombinedMessage\x12\x1d\n\x05state\x18\x01 \x01(\x0b\x32\x0c.state.StateH\x00\x12\'\n\x06\x61\x63tion\x18\x02 \x01(\x0b\x32\x15.action.ExampleActionH\x00\x42\n\n\x08\x63ombinedb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'combined_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_COMBINEDMESSAGE']._serialized_start=55
  _globals['_COMBINEDMESSAGE']._serialized_end=156
# @@protoc_insertion_point(module_scope)