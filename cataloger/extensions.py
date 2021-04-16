# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""

from environs import Env

from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_ldap3_login import LDAP3LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_static_digest import FlaskStaticDigest

from flask_wtf.csrf import CSRFProtect

from cataloger.omero_login import OmeroLoginManager

env = Env()
env.read_env()


bcrypt = Bcrypt()
csrf_protect = CSRFProtect()
login_manager = LoginManager()
ldap_manager = LDAP3LoginManager()
omero_manager = OmeroLoginManager()

if env.str("AUTH_METHOD") == "OMERO":
    auth_manager = omero_manager
elif env.str("AUTH_METHOD") == "LDAP":
    auth_manager = ldap_manager
else:
    auth_manager = None


db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
debug_toolbar = DebugToolbarExtension()

flask_static_digest = FlaskStaticDigest()
