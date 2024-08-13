# config.py
class Config:
    DEBUG = False
    TESTING = False
    API_URL = 'https://schemes.sg/schemespredict'  # Production API URL

class DevelopmentConfig(Config):
    DEBUG = True
    API_URL = 'http://0.0.0.0:8000/schemespredict'  # Local API URL for development

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
