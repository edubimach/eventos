from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Evento, Usuario
import random
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meubanco.db'  # Configuração para SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desativa rastreamento de modificações
app.secret_key = '123456'  # Use uma chave mais segura em produção

# Inicializa extensões
db.init_app(app)
migrate = Migrate(app, db)

# Cria as tabelas na primeira execução (apenas para desenvolvimento)
with app.app_context():
    db.create_all()


# Rota para cadastrar um evento
@app.route('/cadastro_evento', methods=['GET', 'POST'])
def cadastro_evento():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        data_evento_str = request.form['data_evento']
        data_evento = datetime.strptime(data_evento_str, '%Y-%m-%d').date()
        telefone = request.form.get('telefone', None)

        novo_evento = Evento(nome=nome, descricao=descricao, data_evento=data_evento, telefone=telefone)
        db.session.add(novo_evento)
        db.session.commit()

        flash('Evento cadastrado com sucesso!', 'success')
        return redirect(url_for('home'))

    return render_template('cadastro_evento.html')


# Rota para cadastrar um usuário
@app.route('/cadastro_usuario', methods=['GET', 'POST'])
def cadastro_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']

        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este e-mail já está cadastrado. Tente outro.', 'danger')
            return redirect(url_for('cadastro_usuario'))

        novo_usuario = Usuario(nome=nome, email=email, telefone=telefone)
        db.session.add(novo_usuario)
        try:
            db.session.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('home'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro ao cadastrar usuário. Tente novamente.', 'danger')

    return render_template('cadastro_usuario.html')


# Rota para listar os eventos
@app.route('/')
def home():
    eventos = Evento.query.all()
    return render_template('home.html', eventos=eventos)


@app.route('/evento/<int:evento_id>')
def evento_detalhes(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    return render_template('evento_detalhes.html', evento=evento)


@app.route('/usuarios')
def lista_usuarios():
    usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)


@app.route('/excluir_evento/<int:evento_id>', methods=['POST'])
def excluir_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    db.session.delete(evento)
    db.session.commit()
    flash('Evento excluído com sucesso!', 'success')
    return redirect(url_for('home'))


@app.route('/sorteio/<int:evento_id>', methods=['POST'])
def sortear_usuario(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    if evento.usuario_id:
        flash('Este evento já possui um usuário sorteado.', 'warning')
    else:
        usuarios = Usuario.query.all()
        if usuarios:
            sorteado = random.choice(usuarios)
            evento.usuario_id = sorteado.id
            db.session.commit()
            flash(f'Usuário {sorteado.nome} foi sorteado para o evento "{evento.nome}".', 'success')
        else:
            flash('Nenhum usuário cadastrado para sortear.', 'danger')

    return redirect(url_for('home'))


@app.route('/limpar_sorteio/<int:evento_id>', methods=['POST'])
def limpar_sorteio(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    evento.usuario_id = None
    db.session.commit()
    flash(f'O sorteio do evento "{evento.nome}" foi limpo com sucesso.', 'info')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
