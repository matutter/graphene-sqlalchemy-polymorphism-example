
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Boolean, String, String, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker
from secrets import token_hex
from json import dumps
from collections import defaultdict

from helpers import *

engine = create_engine('sqlite:///:memory:', echo=False)
session = sessionmaker(bind=engine)()
Base = declarative_base()

class UserModel(Base):
  __tablename__ = 'user'
  _id     = Column(Integer, primary_key=True)
  role    = Column(String, nullable=False)
  name    = Column(String)
  enabled = Column(Boolean)

  __mapper_args__ = {
    'polymorphic_identity': 'user',
    'polymorphic_on': 'role'
  }

  def __repr__(self):
    return f'{self.role.capitalize()}({self.name}, enabled={self.enabled})'

class AdminModel(UserModel):
  __tablename__   = 'admin'
  __mapper_args__ = { 'polymorphic_identity': 'admin' }
  _id = Column(Integer, ForeignKey('user._id'), primary_key=True)
  admin_secret = Column(String(30), default=token_hex(6))

class SuperAdminModel(AdminModel):
  __tablename__   = 'superadmin'
  __mapper_args__ = { 'polymorphic_identity': 'superadmin' }
  _id = Column(Integer, ForeignKey('admin._id'), primary_key=True)
  super_secret = Column(String(30), default=token_hex(6))

Base.metadata.create_all(engine)
session.add(AdminModel(name='a', role='admin', enabled=False))
session.add(UserModel(name='b', role='user', enabled=False))
session.add(UserModel(name='c', role='user', enabled=True))
session.add(SuperAdminModel(name='d', role='superadmin', enabled=False))
session.commit()

# A query on User will update the Admin as well.
enabled = ['a', 'd']
session.query(UserModel).update({UserModel.enabled:UserModel.name.in_(enabled)}, synchronize_session=False)
if 0:
  for user in session.query(UserModel):
    print(f'{user}')

def make_resolve_func(cls):
  """
  Generate some dummy queries.
  """
  from graphene.types.union import UnionOptions

  if isinstance(cls._meta, UnionOptions):
    # Resolve a Union
    def resolve_func(self, info):
      result = []
      for typ in cls._meta.types:
        m = typ._meta.model
        query = session.query(m).\
          filter(m.role == m.__mapper_args__['polymorphic_identity'])
        result.extend(query.all())
      return result
  else:
    # Resolve a normal node/relay
    def resolve_func(self, info):
      query = cls.get_query(info)
      return query.all()
  return resolve_func

def make_resolve_type_func(type_map):
  def resolve_type(instance, info):
      return type_map.get(type(instance))
  return resolve_type

def make_schema():
  # Here we dynamically generate an interface similar to this example
  # https://github.com/graphql-python/graphene-sqlalchemy/blob/master/docs/examples.rst

  import graphene
  from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
  from graphene.relay import Connection, Node

  # A map of all classes to list of sub-classes
  class_map = get_class_map(Base.__subclasses__())
  # Map of models to SQLAlchemyObjectType
  sql_map = dict()
  # Map of all things available on query, generates Schema
  queries = dict()

  for cls, subs in class_map.items():
    # Name for the Type of X
    name       = cls.__name__.replace('Model', '')
    # Name for the Type of X and and relationship to Y
    conn_name  = f'{name}Connection'
    # Name for a query of multiple X
    query_name = f'{name.lower()}s'

    SqlType  = type(name, (SQLAlchemyObjectType,), {
      'Meta': type('Meta',(), {
          'model': cls
        , 'interfaces': (Node,)
      })})
    SqlTypeConnection = type(conn_name, (Connection,), {
      'Meta': type('Meta',(), {'node': SqlType})})

    sql_map[cls] = SqlType
    queries[f'relay_{query_name}'] = SQLAlchemyConnectionField(SqlTypeConnection)
    queries[query_name] = graphene.List(SqlType)
    queries[f'resolve_{query_name}'] = make_resolve_func(SqlType)
    print(f'{name} => {query_name} => {cls.__name__}')

  for cls, subs in class_map.items():
    if not subs: continue
    name       = cls.__name__.replace('Model', '')

    sql_types = [sql_map[cls]] + [sql_map[s] for s in subs]

    # Name for the Type of X and that which is derived from X
    poly_name  = f'Any{name}s'
    # Name for the query of multiple X and that which is derived from X
    poly_query_name  = f'resolve_{poly_name}'

    SqlUnionType = type(poly_name, (graphene.Union, ), {
      'Meta': type('Meta',(), {'types': tuple(sql_types)})
      , 'resolve_type': make_resolve_type_func(sql_map)
      })

    queries[poly_name] = graphene.List(SqlUnionType)
    queries[poly_query_name] = make_resolve_func(SqlUnionType)
    print(f'{poly_name} => {poly_query_name} => {",".join([c.__name__ for c in subs])}')

  # Always present
  queries['node'] = Node.Field()

  # Create actual query class
  Query = type('Query', (graphene.ObjectType, ), queries)
  schema = graphene.Schema(query=Query)
  return schema

schema = make_schema()
update_schema('schema.gql', schema)

query = '''
query {
  users {
    name,
    role,
    enabled
  }
}
'''
result = schema.execute(query, context_value={'session': session})
if 0: dump_yaml(result)

query = '''
query {
  relayUsers {
    edges {
      node {
        name,
        role,
        enabled
      }
    }
  }
}
'''
result = schema.execute(query, context_value={'session': session})
if 0: dump_yaml(result)

query = '''
query {
  AnyUsers {
    ... on User {
      name
      role
    }
    ... on Admin {
      name
      adminSecret
    }
    ... on SuperAdmin {
      name
      adminSecret
      superSecret
    }
  }
}
'''
result = schema.execute(query, context_value={'session': session})
dump_yaml(result)

