# config.py
class Config:
    DEBUG = False
    TESTING = False
    API_URL = 'https://schemes.sg/schemespredict'  # Production API URL

class DevelopmentConfig(Config):
    DEBUG = True
    API_URL = '/schemespredict'  # Local API URL for development

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
