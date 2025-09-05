from flask_login import UserMixin
from database.db import find_user_by_email, find_user_by_id, create_user as db_create_user
# We removed "from app import bcrypt" from here to break the circular import.

class User(UserMixin):
    """
    A user model that integrates with Flask-Login.
    It's a wrapper around the user data stored in MongoDB.
    """
    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password')

    @staticmethod
    def find_by_email(email):
        """Finds a user by email in the database."""
        user_data = find_user_by_email(email)
        if user_data:
            return User(user_data)
        return None

    @staticmethod
    def find_by_id(user_id):
        """Finds a user by their ID in the database."""
        user_data = find_user_by_id(user_id)
        if user_data:
            return User(user_data)
        return None

    @staticmethod
    def create(email, password):
        """Creates a new user and saves them to the database."""
        # FIX: Import bcrypt here, only when it's needed.
        from app import bcrypt 
        
        # Hash the password before storing it for security
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        return db_create_user(email, hashed_password)

