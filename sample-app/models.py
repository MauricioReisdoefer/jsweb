from sqlalchemy.orm import declarative_base
from jsweb.database import ModelBase, String, Integer, Column
Base = declarative_base()

# Example Model
class User(ModelBase):
    __tablename__ = 'users'  # Explicit table name is good practice
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, nullable=False)

