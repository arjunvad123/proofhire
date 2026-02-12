"""
SQLAlchemy base configuration and utilities.
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

# Base class for all database models
Base = declarative_base()


class DBBase(DeclarativeBase):
    """Alternative base using modern SQLAlchemy 2.0 style."""
    pass
