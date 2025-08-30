from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # hashed password

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, raw_password):
        """Hash and set the password"""
        self.password = generate_password_hash(raw_password, method='sha256')

    def check_password(self, raw_password):
        """Check password against hash"""
        return check_password_hash(self.password, raw_password)

    def to_dict(self, include_email=True):
        """Return user data as dictionary"""
        data = {
            'id': self.id,
            'username': self.username
        }
        if include_email:
            data['email'] = self.email
        return data
