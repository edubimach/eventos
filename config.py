import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///eventos.db'  # Usando SQLite
    SQLALCHEMY_TRACK_MODIFICATIONS = False
