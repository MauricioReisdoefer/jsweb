# jsweb/database.py

from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.inspection import inspect
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

Base = declarative_base()
SessionLocal = None
_engine = None


def init_db(database_url, echo=False):
    global SessionLocal, _engine
    _engine = create_engine(database_url, echo=echo)
    SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    Base.metadata.bind = _engine


def get_engine():
    if _engine is None:
        raise RuntimeError("Database engine is not initialized. Call init_db() first.")
    return _engine


def get_session():
    if SessionLocal is None:
        raise RuntimeError("Database session is not initialized. Call init_db() first.")
    return SessionLocal()


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


def _handle_db_error(db_session, e):
    """Rolls back the session and raises a custom DatabaseError."""
    db_session.rollback()
    if isinstance(e, IntegrityError):
        simple_message = str(e.orig)
        raise DatabaseError(f"Constraint failed: {simple_message}") from e
    else:
        raise DatabaseError(f"Database operation failed: {e}") from e


class ModelBase(Base):
    __abstract__ = True

    # ✅ FIX: Removed the @property decorator. It's now a standard class method.
    @classmethod
    def query(cls):
        """Returns a new, chainable Query object for this model class."""
        return get_session().query(cls)

    def save(self):
        """Saves the object, handling potential errors and transaction rollback."""
        db = get_session()
        try:
            db.add(self)
            db.commit()
        except SQLAlchemyError as e:
            _handle_db_error(db, e)
        finally:
            db.close()

    def delete(self):
        """Deletes the object, handling potential errors and transaction rollback."""
        db = get_session()
        try:
            db.delete(self)
            db.commit()
        except SQLAlchemyError as e:
            _handle_db_error(db, e)
        finally:
            db.close()

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    # ✅ REFACTORED: All helper methods now correctly call `cls.query()`
    @classmethod
    def all(cls):
        """Retrieves all objects of this model."""
        db = get_session()
        try:
            return cls.query().all()
        except SQLAlchemyError as e:
            _handle_db_error(db, e)
        finally:
            db.close()

    @classmethod
    def get(cls, id):
        """Retrieves a single object by its primary key."""
        db = get_session()
        try:
            return cls.query().get(id)
        except SQLAlchemyError as e:
            _handle_db_error(db, e)
        finally:
            db.close()

    @classmethod
    def filter(cls, **kwargs):
        """Filters objects by exact keyword arguments."""
        db = get_session()
        try:
            return cls.query().filter_by(**kwargs).all()
        except SQLAlchemyError as e:
            _handle_db_error(db, e)
        finally:
            db.close()

    @classmethod
    def first(cls, **kwargs):
        """Finds the first object matching the exact keyword arguments."""
        db = get_session()
        try:
            return cls.query().filter_by(**kwargs).first()
        except SQLAlchemyError as e:
            _handle_db_error(db, e)
        finally:
            db.close()


__all__ = [
    "init_db", "get_engine", "get_session", "SessionLocal", "ModelBase", "Base",
    "DatabaseError",
    "Integer", "String", "Float", "Boolean", "DateTime", "Text",
    "Column", "ForeignKey", "relationship"
]