# Dynamic GraphQL Interface for SQLAlchemy with Polymorphic Models

This example is meant to show how a dynamic interface may be generating from
polymorphic database models. This example uses SQLAlchemy for ORM and Graphene
for a API facade.

The purpose of this method is to reduce the development overhead for new models
or changes to existing models by relying on the default kinds of contraints
offered by GraphQL and Graphene.

## Example

This will produce a full interface for every model defined. The example uses
a single ORM class, `UserModel` with 2 derived classes.

### Models

```python
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
```

### Query

```graphql
query {
  AnyUsers {
    ... on IUser {
      name
      role
    }
    ... on IAdmin {
      adminSecret
    }
    ... on ISuperAdmin {
      superSecret
    }
  }
}
```

### Result

```yaml
data:
  AnyUsers:
  - name: b
    role: user
  - name: c
    role: user
  - adminSecret: 9a2145461348
    name: a
    role: admin
  - adminSecret: 9a2145461348
    name: d
    role: superadmin
    superSecret: d2377afec750

```

## Setup

### Python Example

```bash
python3.7 -m venv .poly
. .poly/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
```

### Apollo Server

```
npm install
node server.js
```
