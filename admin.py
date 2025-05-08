from app import app
from models import db, UsuarioLogin

# Substitua pelo e-mail do usuário que deseja promover
EMAIL_USUARIO = 'duka.pedrosa@gmail.com'  # <<== coloque aqui seu e-mail

with app.app_context():
    usuario = UsuarioLogin.query.filter_by(email=EMAIL_USUARIO).first()

    if usuario:
        usuario.is_admin = True
        usuario.aprovado = True  # garantir que esteja aprovado também
        db.session.commit()
        print(f"Usuário {usuario.nome} foi promovido a administrador com sucesso!")
    else:
        print("Usuário não encontrado.")
