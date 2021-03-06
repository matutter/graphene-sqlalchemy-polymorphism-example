def update_schema(path, schema):
  s = str(schema)
  with open(path, 'r') as fd:
    if len(fd.read()) == len(s):
      return
  print(f'Writing scheama to {path}')
  with open(path, 'w') as fd:
    fd.write(s)

def dump_yaml(d:dict):
  from graphql.execution.base import ExecutionResult
  from ruamel.yaml import YAML, Representer
  from collections import OrderedDict
  from ruamel.yaml import RoundTripRepresenter as RTR, RoundTripDumper as RTD
  import ruamel.yaml as yaml
  import sys

  if isinstance(d, ExecutionResult):
    d = d.to_dict()


  yaml.add_representer(OrderedDict, RTR.represent_dict, Dumper=RTD)
  yaml.dump(d, sys.stdout, Dumper=RTD)

def get_class_map(classes):
  from collections import OrderedDict
  class_map = OrderedDict()
  classes = list(classes)
  while classes:
    cls = classes.pop(0)
    subclasses = class_map[cls] = list()
    _get_class_map(cls, subclasses, classes)
  return class_map

def _get_class_map(cls, subclasses, allclasses):
  for sub in cls.__subclasses__():
    subclasses.append(sub)
    allclasses.append(sub)
    _get_class_map(sub, subclasses, allclasses)

def make_graphene_interface(cls):
  from graphene.types.utils import yank_fields_from_attrs
  from graphene import Field, Interface
  from graphene_sqlalchemy.types import construct_fields, get_global_registry
  from graphene_sqlalchemy.fields import default_connection_field_factory
  from graphene_sqlalchemy import SQLAlchemyObjectType

  name       = cls.__name__.replace('Model', '')

  SqlType  = type(name, (SQLAlchemyObjectType,), {
    'Meta': type('Meta',(), {
        'model': cls
      , 'interfaces': tuple()
    })})

  fields = yank_fields_from_attrs(
            construct_fields(
                obj_type=SqlType,
                model=cls,
                registry=get_global_registry(),
                only_fields=[],
                exclude_fields=[],
                connection_field_factory=default_connection_field_factory,
            ),
            _as=Field,
            sort=False,
        )

  return type(f'I{name}', (Interface, ), fields)
