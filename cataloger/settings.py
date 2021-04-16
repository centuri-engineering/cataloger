# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set
environment variables.
"""
from environs import Env

env = Env()
env.read_env()

ENV = env.str("FLASK_ENV", default="production")
DEBUG = ENV == "development"
SQLALCHEMY_DATABASE_URI = env.str("DATABASE_URL")
SECRET_KEY = env.str("SECRET_KEY")
SEND_FILE_MAX_AGE_DEFAULT = env.int("SEND_FILE_MAX_AGE_DEFAULT")
BCRYPT_LOG_ROUNDS = env.int("BCRYPT_LOG_ROUNDS", default=13)
DEBUG_TB_ENABLED = DEBUG
DEBUG_TB_INTERCEPT_REDIRECTS = False
CACHE_TYPE = "simple"  # Can be "memcached", "redis", etc.
SQLALCHEMY_TRACK_MODIFICATIONS = False
APPLICATION_ROOT = "/"
SCRIPT_NAME = "/"

AUTH_METHOD = env.str("AUTH_METHOD")  # can be 'LDAP', 'OMERO'


LDAP_PORT = env.int("LDAP_PORT", 369)
LDAP_HOST = env.str("LDAP_HOST", "localhost")
LDAP_READONLY = env.bool("LDAP_READONLY", True)
LDAP_BASE_DN = env.str("LDAP_BASE_DN", "")

LDAP_BIND_USER_DN = env.str("LDAP_BIND_USER_DN")
LDAP_BIND_USER_PASSWORD = env.str("LDAP_BIND_USER_PASSWORD")
LDAP_BIND_DIRECT_CREDENTIALS = env.bool("LDAP_BIND_DIRECT_CREDENTIALS")
LDAP_ALWAYS_SEARCH_BIND = env.bool("LDAP_ALWAYS_SEARCH_BIND")

LDAP_USER_LOGIN_ATTR = env.str("LDAP_USER_LOGIN_ATTR", "uid")
LDAP_USER_RDN_ATTR = env.str("LDAP_USER_RDN_ATTR", "uid")
LDAP_USER_DN = env.str("LDAP_USER_DN")
LDAP_USER_SEARCH_SCOPE = env.str("LDAP_USER_SEARCH_SCOPE", "LEVEL")

LDAP_SEARCH_FOR_GROUPS = env.bool("LDAP_SEARCH_FOR_GROUPS", False)


OMERO_HOST = env.str("OMERO_HOST", "localhost")
OMERO_PORT = env.int("OMERO_PORT", 4064)
