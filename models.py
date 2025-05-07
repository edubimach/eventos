from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Usuario(db.Model):
    __tablename__ = 'usuario'  # Define o nome da tabela explicitamente
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    telefone = db.Column(db.String(20), nullable=False)

    # A relação inversa é criada automaticamente com backref em Evento


class Evento(db.Model):
    __tablename__ = 'evento'  # Define o nome da tabela explicitamente
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200))
    data_evento = db.Column(db.Date)  # Considerando que só usa data, não hora
    telefone = db.Column(db.String(20))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

    # Cria a relação com o usuário
    usuario = db.relationship('Usuario', backref='eventos')
