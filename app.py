from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Evento, Usuario
import random
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)

# Definir uma chave secreta para proteger as sessões
app.secret_key = '123456'  # Substitua por uma chave realmente segura


# Rota para cadastrar um evento
@app.route('/cadastro_evento', methods=['GET', 'POST'])
def cadastro_evento():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        data_evento_str = request.form['data_evento']

        # Converte o valor de data_evento de string para datetime (somente a data)
        data_evento = datetime.strptime(data_evento_str, '%Y-%m-%d').date()  # Converte para 'date'

        # Se telefone não foi preenchido, definimos como None
        telefone = request.form.get('telefone', None)

        # Criar o evento e salvar no banco de dados
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
        telefone = request.form['telefone']  # Novo campo

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
    evento = Evento.query.get_or_404(evento_id)  # Obtém o evento com o ID especificado
    return render_template('evento_detalhes.html', evento=evento)


@app.route('/usuarios')
def lista_usuarios():
    # Busca todos os usuários no banco de dados
    usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)


# Rota para excluir um evento
@app.route('/excluir_evento/<int:evento_id>', methods=['POST'])
def excluir_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)  # Procura o evento pelo ID
    db.session.delete(evento)  # Exclui o evento
    db.session.commit()  # Commit para salvar a alteração no banco de dados
    flash('Evento excluído com sucesso!', 'success')
    return redirect(url_for('home'))  # Redireciona para a página inicial


@app.route('/sorteio/<int:evento_id>', methods=['POST'])
def sortear_usuario(evento_id):
    evento = Evento.query.get_or_404(evento_id)

    # Verifique se o evento já possui um usuário sorteado
    if evento.usuario_id:  # Agora estamos verificando o campo usuario_id
        flash('Este evento já possui um usuário sorteado.', 'warning')
    else:
        usuarios = Usuario.query.all()
        if usuarios:
            sorteado = random.choice(usuarios)
            evento.usuario_id = sorteado.id  # Atribuindo o ID do usuário sorteado
            db.session.commit()
            flash(f'Usuário {sorteado.nome} foi sorteado para o evento "{evento.nome}".', 'success')
        else:
            flash('Nenhum usuário cadastrado para sortear.', 'danger')

    return redirect(url_for('home'))


@app.route('/limpar_sorteio/<int:evento_id>', methods=['POST'])
def limpar_sorteio(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    evento.usuario_id = None  # Limpa o usuário sorteado
    db.session.commit()
    flash(f'O sorteio do evento "{evento.nome}" foi limpo com sucesso.', 'info')
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria todas as tabelas com base nos modelos
    app.run(debug=True)
