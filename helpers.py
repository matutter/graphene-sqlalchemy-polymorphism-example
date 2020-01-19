def update_schema(path, schema):
  s = str(schema)
  with open(path, 'r') as fd:
    if fd.read() == s:
      return
  with open(path, 'w') as fd:
    fd.write(s)

def dump_yaml(d:dict):
  from graphql.execution.base import ExecutionResult
  from ruamel.yaml import YAML, Representer
  from collections import OrderedDict
  import ruamel.yaml as _YAML
  import sys

  if isinstance(d, ExecutionResult):
    d = d.to_dict()

  yaml=YAML(typ='safe', pure=True)
  yaml.indent(sequence=2, offset=0)
  yaml.default_flow_style = False
  yaml.representer.add_representer(OrderedDict, Representer.represent_dict)
  yaml.dump(d, sys.stdout)

def get_class_map(classes):
  class_map = dict()
  classes = list(classes)
  while classes:
    cls = classes.pop()
    subclasses = class_map[cls] = list()
    _get_class_map(cls, subclasses, classes)
  return class_map

def _get_class_map(cls, subclasses, allclasses):
  for sub in cls.__subclasses__():
    subclasses.append(sub)
    allclasses.append(sub)
    _get_class_map(sub, subclasses, allclasses)
