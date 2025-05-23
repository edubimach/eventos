from forms import CadastroForm
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Evento, Usuario, UsuarioLogin
from flask_migrate import Migrate
from datetime import datetime
import random
from sqlalchemy.exc import IntegrityError
from functools import wraps
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meubanco.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'sua-chave-secreta-aqui'

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Loader obrigatório para flask-login
@login_manager.user_loader
def load_user(user_id):
    return UsuarioLogin.query.get(int(user_id))

with app.app_context():
    db.create_all()

def login_obrigatorio(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = UsuarioLogin.query.filter_by(email=email).first()
        if usuario and usuario.verificar_senha(senha):
            if usuario.is_admin or usuario.aprovado:
                session['usuario_id'] = usuario.id
                session['is_admin'] = usuario.is_admin  # <-- CORRIGIDO
                login_user(usuario)  # Flask-Login
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Sua conta ainda não foi aprovada.', 'warning')
        else:
            flash('Login inválido. Verifique seu e-mail e senha.', 'danger')
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    form = CadastroForm()

    if form.validate_on_submit():
        nome = form.nome.data
        email = form.email.data
        senha = form.senha.data

        if UsuarioLogin.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'warning')
            return redirect(url_for('cadastro'))

        novo_usuario = UsuarioLogin(nome=nome, email=email)
        novo_usuario.set_senha(senha)
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Aguarde aprovação.', 'success')
        return redirect(url_for('admin'))

    return render_template('cadastro.html', form=form)


@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    session.pop('is_admin', None)
    logout_user()
    flash('Você saiu da conta com sucesso.', 'info')
    return redirect(url_for('login'))

from flask_login import login_required, current_user
from flask import session, redirect, url_for, flash, render_template
from models import UsuarioLogin  # Supondo que você tenha o modelo de dados correto

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        flash('Você precisa ser um administrador para acessar essa página', 'danger')
        return redirect(url_for('home'))

    # Carregar usuários aprovados e pendentes
    usuarios_pendentes = UsuarioLogin.query.filter_by(aprovado=False).all()
    usuarios_aprovados = UsuarioLogin.query.filter_by(aprovado=True).all()

    return render_template('admin.html',
                           usuarios_pendentes=usuarios_pendentes,
                           usuarios_aprovados=usuarios_aprovados)


@app.route('/aprovar_usuario/<int:usuario_id>', methods=['POST'])
@login_required
def aprovar_usuario(usuario_id):
    if not current_user.is_admin:
        flash('Ação não permitida.', 'danger')
        return redirect(url_for('home'))

    usuario = UsuarioLogin.query.get_or_404(usuario_id)
    usuario.aprovado = True
    db.session.commit()
    flash(f'Usuário {usuario.nome} aprovado com sucesso!', 'success')
    return redirect(url_for('admin'))  # Redireciona para a página de administração



@app.route('/rejeitar_usuario/<int:usuario_id>', methods=['POST'])
@login_required
def rejeitar_usuario(usuario_id):
    if not current_user.is_admin:
        flash('Ação não permitida.', 'danger')
        return redirect(url_for('home'))

    usuario = UsuarioLogin.query.get_or_404(usuario_id)
    db.session.delete(usuario)
    db.session.commit()
    flash(f'Usuário {usuario.nome} rejeitado e removido.', 'danger')
    return redirect(url_for('admin_page'))


@app.route('/home')
@login_obrigatorio
def home():
    eventos = Evento.query.all()
    return render_template('home.html', eventos=eventos)

@app.route('/evento/<int:evento_id>')
@login_obrigatorio
def evento_detalhes(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    return render_template('evento_detalhes.html', evento=evento)

@app.route('/usuarios')
@login_obrigatorio
def lista_usuarios():
    if not session.get('is_admin'):
        flash('Ação não permitida.', 'danger')
        return redirect(url_for('home'))

    usuarios = UsuarioLogin.query.all()
    return render_template('usuarios.html', usuarios=usuarios)


@app.route('/cadastro_evento', methods=['GET', 'POST'])
@login_obrigatorio
def cadastro_evento():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        data_evento = datetime.strptime(request.form['data_evento'], '%Y-%m-%d').date()
        telefone = request.form.get('telefone', None)
        comite = request.form.get('comite')  # <-- captura o comitê

        palestrantes = request.form.get('speakers', '')
        lista_palestrantes = [p.strip() for p in palestrantes.split(',') if p.strip()]

        # Criação do evento com comitê incluído
        novo_evento = Evento(
            nome=nome,
            descricao=descricao,
            data_evento=data_evento,
            telefone=telefone,
            palestrantes=', '.join(lista_palestrantes),
            comite=comite  # <-- salva no banco
        )

        db.session.add(novo_evento)
        db.session.commit()

        flash('Evento cadastrado com sucesso!', 'success')
        return redirect(url_for('home'))

    return render_template('cadastro_evento.html')


@app.route('/cadastro_usuario', methods=['GET', 'POST'])
@login_obrigatorio
def cadastro_usuario():
    eventos = Evento.query.all()  # Para popular o select no HTML

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        evento_id = request.form.get('evento_id')  # Pode ser None

        if Usuario.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado.', 'danger')
            return redirect(url_for('cadastro_usuario'))

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            telefone=telefone,
            evento_id=int(evento_id) if evento_id else None  # Associa o evento, se selecionado
        )

        db.session.add(novo_usuario)
        try:
            db.session.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('usuarios_cadastrados'))  # Certifique-se de que esta rota lista os usuários
        except IntegrityError:
            db.session.rollback()
            flash('Erro ao cadastrar usuário.', 'danger')

    return render_template('cadastro_usuario.html', eventos=eventos)


@app.route('/editar_usuario/<int:usuario_id>', methods=['GET', 'POST'])
@login_obrigatorio
def editar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    eventos = Evento.query.all()

    if request.method == 'POST':
        usuario.nome = request.form['nome']
        usuario.email = request.form['email']
        usuario.telefone = request.form['telefone']
        evento_id = request.form.get('evento_id')

        usuario.evento_id = int(evento_id) if evento_id else None

        try:
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('usuarios_cadastrados'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar usuário.', 'danger')

    return render_template('editar_usuario.html', usuario=usuario, eventos=eventos)



@app.route('/excluir_evento/<int:evento_id>', methods=['POST'])
@login_obrigatorio
def excluir_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    db.session.delete(evento)
    db.session.commit()
    flash('Evento excluído com sucesso!', 'success')
    return redirect(url_for('home'))

@app.route('/excluir_usuario/<int:usuario_id>', methods=['POST'])
@login_obrigatorio
def excluir_usuario(usuario_id):
    usuario = UsuarioLogin.query.get_or_404(usuario_id)  # <-- corrigido aqui
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário excluído com sucesso.', 'info')
    return redirect(url_for('lista_usuarios'))

@app.route('/excluir_usuario_aprovado/<int:usuario_id>', methods=['POST'])
@login_required
def excluir_usuario_aprovado(usuario_id):
    if not current_user.is_admin:
        flash('Ação não permitida.', 'danger')
        return redirect(url_for('home'))

    usuario = UsuarioLogin.query.get_or_404(usuario_id)
    db.session.delete(usuario)
    db.session.commit()
    flash(f'Usuário {usuario.nome} excluído com sucesso.', 'info')
    return redirect(url_for('admin'))


@app.route('/sortear/<int:evento_id>', methods=['POST'])
@login_obrigatorio
def sortear_usuario(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    if evento.usuarios:
        flash('Este evento já possui um usuário sorteado.')
        return redirect(url_for('home'))

    usuarios_disponiveis = Usuario.query.filter(Usuario.evento_id == None).all()

    if not usuarios_disponiveis:
        flash('Nenhum usuário disponível para sorteio.')
        return redirect(url_for('home'))

    sorteado = random.choice(usuarios_disponiveis)
    sorteado.evento = evento
    db.session.commit()
    flash(f'Usuário {sorteado.nome} foi sorteado para o evento {evento.nome}!')
    return redirect(url_for('home'))

@app.route('/limpar_sorteio/<int:evento_id>', methods=['POST'])
@login_obrigatorio
def limpar_sorteio(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    for usuario in evento.usuarios:
        usuario.evento_id = None
    db.session.commit()
    flash(f'O sorteio do evento "{evento.nome}" foi limpo com sucesso.', 'info')
    return redirect(url_for('home'))

@app.route('/usuarios_cadastrados')
@login_required
def usuarios_cadastrados():
    if not current_user.is_admin:
        flash('Você precisa ser um administrador para acessar esta página', 'danger')
        return redirect(url_for('home'))

    usuarios = Usuario.query.all()
    return render_template('usuarios_cadastrados.html', usuarios=usuarios)

# ... (importações e configurações anteriores)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_page():
    # Verificar se o usuário está aprovado antes de continuar
    if not current_user.is_admin:
        flash('Você precisa ser um administrador para acessar essa página', 'danger')
        return redirect(url_for('home'))

    if not current_user.aprovado:
        flash('Sua conta ainda não foi aprovada.', 'warning')
        return redirect(url_for('home'))  # Ou outra página apropriada

    usuarios_pendentes = UsuarioLogin.query.filter_by(aprovado=False).all()
    usuarios_aprovados = UsuarioLogin.query.filter_by(aprovado=True).all()
    return render_template('admin.html', usuarios_pendentes=usuarios_pendentes, usuarios_aprovados=usuarios_aprovados)

@app.route('/calendario')
@login_obrigatorio
def calendario():
    eventos = Evento.query.all()
    return render_template('calendario.html', eventos=eventos)




if __name__ == '__main__':
    app.run(debug=True)
