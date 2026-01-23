from app.extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "description": self.description
        }