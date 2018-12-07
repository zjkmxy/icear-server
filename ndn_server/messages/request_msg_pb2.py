# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ndn_server/messages/request-msg.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='ndn_server/messages/request-msg.proto',
  package='ndn_message',
  syntax='proto2',
  serialized_options=None,
  serialized_pb=_b('\n%ndn_server/messages/request-msg.proto\x12\x0bndn_message\"\x19\n\x04Name\x12\x11\n\tcomponent\x18\x08 \x03(\x0c\"-\n\x0bOpComponent\x12\x0e\n\x05model\x18\xc8\x01 \x02(\x0c\x12\x0e\n\x05\x66lags\x18\xc9\x01 \x01(\r\";\n\nOperations\x12-\n\ncomponents\x18\xcb\x01 \x03(\x0b\x32\x18.ndn_message.OpComponent\"\xfa\x01\n\x17SegmentParameterMessage\x12Q\n\x11segment_parameter\x18\xd2\x01 \x02(\x0b\x32\x35.ndn_message.SegmentParameterMessage.SegmentParameter\x1a\x8b\x01\n\x10SegmentParameter\x12\x1f\n\x04name\x18\x07 \x02(\x0b\x32\x11.ndn_message.Name\x12\x14\n\x0bstart_frame\x18\xdc\x01 \x02(\r\x12\x12\n\tend_frame\x18\xdd\x01 \x02(\r\x12,\n\noperations\x18\xde\x01 \x02(\x0b\x32\x17.ndn_message.Operations\"\x9f\x01\n\x15ServerResponseMessage\x12K\n\x0fserver_response\x18\xd3\x01 \x02(\x0b\x32\x31.ndn_message.ServerResponseMessage.ServerResponse\x1a\x39\n\x0eServerResponse\x12\x11\n\x08ret_code\x18\xe6\x01 \x02(\r\x12\x14\n\x0bretry_after\x18\xe7\x01 \x01(\r')
)




_NAME = _descriptor.Descriptor(
  name='Name',
  full_name='ndn_message.Name',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='component', full_name='ndn_message.Name.component', index=0,
      number=8, type=12, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=54,
  serialized_end=79,
)


_OPCOMPONENT = _descriptor.Descriptor(
  name='OpComponent',
  full_name='ndn_message.OpComponent',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='model', full_name='ndn_message.OpComponent.model', index=0,
      number=200, type=12, cpp_type=9, label=2,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='flags', full_name='ndn_message.OpComponent.flags', index=1,
      number=201, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=81,
  serialized_end=126,
)


_OPERATIONS = _descriptor.Descriptor(
  name='Operations',
  full_name='ndn_message.Operations',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='components', full_name='ndn_message.Operations.components', index=0,
      number=203, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=128,
  serialized_end=187,
)


_SEGMENTPARAMETERMESSAGE_SEGMENTPARAMETER = _descriptor.Descriptor(
  name='SegmentParameter',
  full_name='ndn_message.SegmentParameterMessage.SegmentParameter',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='ndn_message.SegmentParameterMessage.SegmentParameter.name', index=0,
      number=7, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='start_frame', full_name='ndn_message.SegmentParameterMessage.SegmentParameter.start_frame', index=1,
      number=220, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='end_frame', full_name='ndn_message.SegmentParameterMessage.SegmentParameter.end_frame', index=2,
      number=221, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='operations', full_name='ndn_message.SegmentParameterMessage.SegmentParameter.operations', index=3,
      number=222, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=301,
  serialized_end=440,
)

_SEGMENTPARAMETERMESSAGE = _descriptor.Descriptor(
  name='SegmentParameterMessage',
  full_name='ndn_message.SegmentParameterMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='segment_parameter', full_name='ndn_message.SegmentParameterMessage.segment_parameter', index=0,
      number=210, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_SEGMENTPARAMETERMESSAGE_SEGMENTPARAMETER, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=190,
  serialized_end=440,
)


_SERVERRESPONSEMESSAGE_SERVERRESPONSE = _descriptor.Descriptor(
  name='ServerResponse',
  full_name='ndn_message.ServerResponseMessage.ServerResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='ret_code', full_name='ndn_message.ServerResponseMessage.ServerResponse.ret_code', index=0,
      number=230, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='retry_after', full_name='ndn_message.ServerResponseMessage.ServerResponse.retry_after', index=1,
      number=231, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=545,
  serialized_end=602,
)

_SERVERRESPONSEMESSAGE = _descriptor.Descriptor(
  name='ServerResponseMessage',
  full_name='ndn_message.ServerResponseMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='server_response', full_name='ndn_message.ServerResponseMessage.server_response', index=0,
      number=211, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_SERVERRESPONSEMESSAGE_SERVERRESPONSE, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=443,
  serialized_end=602,
)

_OPERATIONS.fields_by_name['components'].message_type = _OPCOMPONENT
_SEGMENTPARAMETERMESSAGE_SEGMENTPARAMETER.fields_by_name['name'].message_type = _NAME
_SEGMENTPARAMETERMESSAGE_SEGMENTPARAMETER.fields_by_name['operations'].message_type = _OPERATIONS
_SEGMENTPARAMETERMESSAGE_SEGMENTPARAMETER.containing_type = _SEGMENTPARAMETERMESSAGE
_SEGMENTPARAMETERMESSAGE.fields_by_name['segment_parameter'].message_type = _SEGMENTPARAMETERMESSAGE_SEGMENTPARAMETER
_SERVERRESPONSEMESSAGE_SERVERRESPONSE.containing_type = _SERVERRESPONSEMESSAGE
_SERVERRESPONSEMESSAGE.fields_by_name['server_response'].message_type = _SERVERRESPONSEMESSAGE_SERVERRESPONSE
DESCRIPTOR.message_types_by_name['Name'] = _NAME
DESCRIPTOR.message_types_by_name['OpComponent'] = _OPCOMPONENT
DESCRIPTOR.message_types_by_name['Operations'] = _OPERATIONS
DESCRIPTOR.message_types_by_name['SegmentParameterMessage'] = _SEGMENTPARAMETERMESSAGE
DESCRIPTOR.message_types_by_name['ServerResponseMessage'] = _SERVERRESPONSEMESSAGE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Name = _reflection.GeneratedProtocolMessageType('Name', (_message.Message,), dict(
  DESCRIPTOR = _NAME,
  __module__ = 'ndn_server.messages.request_msg_pb2'
  # @@protoc_insertion_point(class_scope:ndn_message.Name)
  ))
_sym_db.RegisterMessage(Name)

OpComponent = _reflection.GeneratedProtocolMessageType('OpComponent', (_message.Message,), dict(
  DESCRIPTOR = _OPCOMPONENT,
  __module__ = 'ndn_server.messages.request_msg_pb2'
  # @@protoc_insertion_point(class_scope:ndn_message.OpComponent)
  ))
_sym_db.RegisterMessage(OpComponent)

Operations = _reflection.GeneratedProtocolMessageType('Operations', (_message.Message,), dict(
  DESCRIPTOR = _OPERATIONS,
  __module__ = 'ndn_server.messages.request_msg_pb2'
  # @@protoc_insertion_point(class_scope:ndn_message.Operations)
  ))
_sym_db.RegisterMessage(Operations)

SegmentParameterMessage = _reflection.GeneratedProtocolMessageType('SegmentParameterMessage', (_message.Message,), dict(

  SegmentParameter = _reflection.GeneratedProtocolMessageType('SegmentParameter', (_message.Message,), dict(
    DESCRIPTOR = _SEGMENTPARAMETERMESSAGE_SEGMENTPARAMETER,
    __module__ = 'ndn_server.messages.request_msg_pb2'
    # @@protoc_insertion_point(class_scope:ndn_message.SegmentParameterMessage.SegmentParameter)
    ))
  ,
  DESCRIPTOR = _SEGMENTPARAMETERMESSAGE,
  __module__ = 'ndn_server.messages.request_msg_pb2'
  # @@protoc_insertion_point(class_scope:ndn_message.SegmentParameterMessage)
  ))
_sym_db.RegisterMessage(SegmentParameterMessage)
_sym_db.RegisterMessage(SegmentParameterMessage.SegmentParameter)

ServerResponseMessage = _reflection.GeneratedProtocolMessageType('ServerResponseMessage', (_message.Message,), dict(

  ServerResponse = _reflection.GeneratedProtocolMessageType('ServerResponse', (_message.Message,), dict(
    DESCRIPTOR = _SERVERRESPONSEMESSAGE_SERVERRESPONSE,
    __module__ = 'ndn_server.messages.request_msg_pb2'
    # @@protoc_insertion_point(class_scope:ndn_message.ServerResponseMessage.ServerResponse)
    ))
  ,
  DESCRIPTOR = _SERVERRESPONSEMESSAGE,
  __module__ = 'ndn_server.messages.request_msg_pb2'
  # @@protoc_insertion_point(class_scope:ndn_message.ServerResponseMessage)
  ))
_sym_db.RegisterMessage(ServerResponseMessage)
_sym_db.RegisterMessage(ServerResponseMessage.ServerResponse)


# @@protoc_insertion_point(module_scope)
