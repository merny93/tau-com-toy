# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: state.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from validate import validate_pb2 as validate_dot_validate__pb2
from meta import meta_pb2 as meta_dot_meta__pb2
import substate_pb2 as substate__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0bstate.proto\x12\x05state\x1a\x17validate/validate.proto\x1a\x0fmeta/meta.proto\x1a\x0esubstate.proto\"g\n\x05State\x12&\n\x08internal\x18\x01 \x01(\x0b\x32\x14.state.StateInternal\x12 \n\x06\x66ridge\x18\x02 \x01(\x0b\x32\x10.substate.Fridge\x12\x14\n\x0cglobal_param\x18\x03 \x01(\r\"d\n\rStateInternal\x12\"\n\x06param1\x18\x01 \x01(\rB\x12\xfa\x42\x04*\x02\x18\n\xe2\xa1\'\x07\n\x05hello:/\xe2\xa1\'+\n\rStateInternal\x12\x1aThis is the internal state')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'state_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _STATEINTERNAL.fields_by_name['param1']._options = None
  _STATEINTERNAL.fields_by_name['param1']._serialized_options = b'\372B\004*\002\030\n\342\241\'\007\n\005hello'
  _STATEINTERNAL._options = None
  _STATEINTERNAL._serialized_options = b'\342\241\'+\n\rStateInternal\022\032This is the internal state'
  _STATE._serialized_start=80
  _STATE._serialized_end=183
  _STATEINTERNAL._serialized_start=185
  _STATEINTERNAL._serialized_end=285
# @@protoc_insertion_point(module_scope)
