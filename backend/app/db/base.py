"""Declarative base for all SQLAlchemy models.

Every database model in this project inherits from Base.
SQLAlchemy uses this to track all table definitions and
generate the correct CREATE TABLE statements.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass
