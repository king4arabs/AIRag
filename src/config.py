import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = os.getenv('DEBUG')
    DATABASE_URL = os.getenv('DATABASE_URL')

config = Config()