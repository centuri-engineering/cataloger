# -*- coding: utf-8 -*-
"""User forms."""
import logging

from environs import Env
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask import current_app

from flask_ldap3_login.forms import LDAPLoginForm

from cataloger.omero_login import AuthenticationResponseStatus

from .models import User, Group


log = logging.getLogger(__name__)


class LocalLoginForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=25)]
    )
    email = StringField(
        "Email", validators=[DataRequired(), Email(), Length(min=6, max=40)]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=6, max=40)]
    )
    confirm = PasswordField(
        "Verify password",
        [DataRequired(), EqualTo("password", message="Passwords must match")],
    )
    select_group = SelectField("Group")

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.user = None
        self.select_group.choices = [(g.id, g.groupname) for g in Group.query.all()]

    def validate(self):
        """Validate the form."""
        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append("Username already registered")
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append("Email already registered")
            return False
        return True


class OmeroLoginForm(FlaskForm):

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")
    remember_me = BooleanField("Remember Me", default=True)

    def validate(self, *args, **kwargs):
        """Try to connects to the omero database"""
        valid = FlaskForm.validate(self, *args, **kwargs)
        if not valid:
            log.debug(
                "Form validation failed before we had a chance to "
                "check ldap. Reasons: '{0}'".format(self.errors)
            )
            return valid

        omero_manager = current_app.omero_login_manager
        username = self.username.data
        password = self.password.data
        result = omero_manager.authenticate(username, password)
        if result.status == AuthenticationResponseStatus.success:
            self.user = omero_manager._save_user(result.user_info)
            return True
        else:
            self.user = None
            self.username.errors.append("Invalid Username/Password.")
            self.password.errors.append("Invalid Username/Password.")
            return False


class NewGroupForm(FlaskForm):
    """Create a group"""

    groupname = StringField(
        "Group Name", validators=[DataRequired(), Length(min=3, max=25)]
    )

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super().validate()
        if not initial_validation:
            return False
        group = Group.query.filter_by(groupname=self.groupname.data).first()
        if group:
            self.groupname.errors.append("Group name already registered")
            return False
        return True


env = Env()
env.read_env()


if env.str("AUTH_METHOD") == "OMERO":
    RegisterForm = OmeroLoginForm

elif env.str("AUTH_METHOD") == "LDAP":
    RegisterForm = LDAPLoginForm
else:
    RegisterForm = LocalLoginForm
