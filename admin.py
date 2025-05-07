from models import db, UsuarioLogin
from app import app

with app.app_context():
    if UsuarioLogin.query.filter_by(email='admin@admin.com').first():
        print("Administrador já existe.")
    else:
        admin = UsuarioLogin(
            nome='Eduardo Pedrosa Machado',
            email='duka.pedrosa@gmail.com',
            is_admin=True,
            aprovado=True  # já aprovado
        )
        admin.set_senha('@Edu23@Mach84')  # substitua por uma senha segura
        db.session.add(admin)
        db.session.commit()
        print("Administrador criado com sucesso.")
