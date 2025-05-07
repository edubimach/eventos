from flask_login import UserMixin

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(100))
    aprovado = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
