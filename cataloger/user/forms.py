# -*- coding: utf-8 -*-
"""User forms."""
import logging

from environs import Env
from flask_wtf import FlaskForm
from wtforms import (
    PasswordField,
    StringField,
    SubmitField,
    BooleanField,
    SelectField,
    Label,
)
from wtforms.validators import DataRequired, EqualTo, Length
from flask import current_app

from flask_login import current_user
from flask_ldap3_login.forms import LDAPLoginForm

from cataloger.omero_login import AuthenticationResponseStatus

from .models import User, Group


log = logging.getLogger(__name__)


class LocalRegisterForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=25)]
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
        super().__init__(*args, **kwargs)
        self.user = None
        self.select_group.choices = [(g.id, g.groupname) for g in Group.query.all()]

    def validate(self):
        """Validate the form."""
        initial_validation = super().validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append("Username already registered")
            return False
        self.user = User.create(
            username=self.username.data,
            active=True,
            group_id=self.select_group.data,
        )
        self.user.set_password(self.password.data)
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
                "check omero. Reasons: '{0}'".format(self.errors)
            )
            return valid

        omero_manager = current_app.omero_login_manager
        username = self.username.data
        password = self.password.data
        result = omero_manager.authenticate(username, password)
        if result.status == AuthenticationResponseStatus.success:
            self.user = omero_manager._save_user(result.user_info)
            log.info("Registered user {%s} from omero ", username)
            return True
        else:
            self.user = None
            self.username.errors.append("Invalid Username/Password.")
            self.password.errors.append("Invalid Username/Password.")
            return False


class EditUserForm(LocalRegisterForm):

    old_password = PasswordField("Old password", validators=[DataRequired()])
    firstname = StringField("First name", validators=[DataRequired()])
    lastname = StringField("Last name", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.password.label.text = "New password"
        self.confirm.label.text = "Confirm new password"
        self.user = None

    def validate(self, *args, **kwargs):

        if not FlaskForm.validate(self, *args, **kwargs):
            return False
        if self.user.password and not self.user.check_password(self.old_password.data):
            self.old_password.errors.append("Invalid old password")
            return False
        return True


class CreateUserForm(LocalRegisterForm):

    firstname = StringField("First name", validators=[DataRequired()])
    lastname = StringField("Last name", validators=[DataRequired()])
    is_admin = BooleanField("admin privileges")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self, *args, **kwargs):

        if not super().validate(*args, **kwargs):
            return False
        self.user.update(
            first_name=self.firstname.data,
            last_name=self.firstname.data,
            is_admin=self.is_admin.data,
        )
        return True


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
    RegisterForm = LocalRegisterForm
