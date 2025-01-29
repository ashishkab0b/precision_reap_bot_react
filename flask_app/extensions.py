# flask_app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy.orm import Query
from flask_mail import Mail
from flask_login import LoginManager


class SoftDeleteQuery(Query):
    """
    A custom query class that automatically excludes rows
    where deleted_at is not null, unless explicitly stated.

    To include soft-deleted rows, use the with_deleted() method.
    MyModel.query.with_deleted().all()
    """
    _with_deleted = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def with_deleted(self):
        """
        Chainable method that disables the soft-delete filter,
        returning all records (including soft-deleted).
        """
        self._with_deleted = True
        return self

    def _apply_deleted_criteria(self):
        """
        Add filters to exclude rows whose deleted_at is not null
        for all mapped classes that have deleted_at.
        """
        for entity in self._mapper_entities:
            model = entity.mapper.class_
            # Only apply filter if the model actually has 'deleted_at'
            if hasattr(model, 'deleted_at'):
                self = self.filter(model.deleted_at.is_(None))
        return self

    def __iter__(self):
        """
        Overridden to apply the soft-delete filter right before iteration.
        """
        if not self._with_deleted:
            self = self._apply_deleted_criteria()
        return super().__iter__()

# Create the global Flask extensions
db = SQLAlchemy(query_class=SoftDeleteQuery)
migrate = Migrate()
cors = CORS()
mail = Mail()
login_manager = LoginManager()

def init_extensions(app):

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    # login_manager.login_view = 'auth.login'
    login_manager.login_view = None
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": [
                "https://js.stripe.com", 
                "https://m.stripe.network",
                "http://reappraise.it",
                "https://reappraise.it", 
                "http://localhost:3000", 
                "http://localhost:4173", 
                "http://localhost:5173", 
                "https://www.google.com",  # For Google reCAPTCHA
                "https://www.gstatic.com"  # For reCAPTCHA assets
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Authorization", "Content-Type", "X-CSRFToken"],
            "supports_credentials": True,  
        }
    }) 
    
    from db.models import User, Conversation, Message, Support, Donation
    
    
