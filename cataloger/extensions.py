# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_ldap3_login import LDAP3LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_static_digest import FlaskStaticDigest

from flask_wtf.csrf import CSRFProtect

bcrypt = Bcrypt()
csrf_protect = CSRFProtect()
login_manager = LoginManager()
ldap_manager = LDAP3LoginManager()
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
debug_toolbar = DebugToolbarExtension()


class CataFlaskStaticDigest(FlaskStaticDigest):
    def static_url_for(self, endpoint, *args, **kwargs):
        endpoint = "cataloger/" + endpoint
        return super().static_url_for(endpoint, *args, **kwargs)


# flask_static_digest = CataFlaskStaticDigest()
flask_static_digest = FlaskStaticDigest()
