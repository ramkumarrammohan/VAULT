"""
Database instance and initialization
This module provides the SQLAlchemy database instance
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
