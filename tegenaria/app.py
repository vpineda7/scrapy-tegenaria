# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
from flask import Flask, render_template
from flask_admin import Admin
from flask_admin.base import AdminIndexView
from flask_admin.contrib.sqla import ModelView

from tegenaria.extensions import db, debug_toolbar, migrate
from tegenaria.models import Apartment, Opinion, Pin
from tegenaria.settings import ProdConfig
from tegenaria.views import ApartmentModelView, PinModelView


def create_app(config_object=ProdConfig):
    """An application factory, as explained here.

    http://flask.pocoo.org/docs/patterns/appfactories/

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)
    register_extensions(app)
    register_admin(app)
    register_errorhandlers(app)
    return app


def register_extensions(app):
    """Register app extensions."""
    db.init_app(app)
    debug_toolbar.init_app(app)
    migrate.init_app(app, db)


def register_admin(app):
    """Register Flask Admin.

    This extension doesn't behave like the others; that's why we had to initialise it here, not outside.
    See https://github.com/flask-admin/flask-admin/issues/910
    """
    admin = Admin(name='Tegenaria', template_mode='bootstrap3', index_view=AdminIndexView(url='/'))
    admin.init_app(app)
    admin.add_view(ApartmentModelView(Apartment, db.session))
    admin.add_view(ModelView(Opinion, db.session))
    admin.add_view(PinModelView(Pin, db.session))
    return None


def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """If a HTTPException, pull the `code` attribute; default to 500."""
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None
