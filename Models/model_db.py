"""Compatibility shim for the database service layer.

Database logic now lives in Controller.database_service to keep Models focused on ORM.
"""
from Controller.database_service import Database

__all__ = ["Database"]
