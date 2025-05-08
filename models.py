from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class UsuarioLogin(db.Model, UserMixin):
    __tablename__ = 'usuario_login'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    senha_hash = db.Column(db.String(128), nullable=False)
    aprovado = db.Column(db.Boolean, default=False)  # Para usuários que precisam de aprovação
    is_admin = db.Column(db.Boolean, default=False)  # Marca o usuário como administrador

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<usuarioLogin {self.nome}, {self.email}>"

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    telefone = db.Column(db.String(20), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'), nullable=True)
    evento = db.relationship('Evento', backref='usuarios', foreign_keys=[evento_id])

class Evento(db.Model):
    __tablename__ = 'evento'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200))
    data_evento = db.Column(db.Date)
    telefone = db.Column(db.String(20))
