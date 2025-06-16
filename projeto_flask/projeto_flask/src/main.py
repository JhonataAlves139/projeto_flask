from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Chave secreta para sessões e mensagens flash

# Configuração da conexão com o banco de dados
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='projeto',
        password='12345',
        db='usuarios_db',
        cursorclass=pymysql.cursors.DictCursor
    )

# Rota para a página inicial (login)
@app.route('/')
def home():
    # Se o usuário já estiver logado, redireciona para a home
    if 'loggedin' in session and session['loggedin']:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Rota para a página home (dashboard)
@app.route('/dashboard')
def dashboard():
    # Verifica se o usuário está logado
    if 'loggedin' not in session or not session['loggedin']:
        flash('Por favor, faça login para acessar esta página!', 'error')
        return redirect(url_for('home'))
    
    # Buscar os itens cadastrados pelo usuário
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM itens WHERE username = %s", (session['username'],))
            itens = cursor.fetchall()
    except Exception as e:
        flash(f'Erro ao buscar itens: {str(e)}', 'error')
        itens = []
    finally:
        conn.close()
    
    return render_template('home.html', username=session['username'], itens=itens)

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['login']
        password = request.form['senha']
        session['login'] = username
        
        # Validar se os campos foram preenchidos
        if not username or not password:
            flash('Por favor, preencha todos os campos!', 'error')
            return redirect(url_for('home'))
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Buscar o usuário no banco de dados
                cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
                user = cursor.fetchone()
                
                # Verificar se o usuário existe e a senha está correta
                if user and check_password_hash(user['password'], password):
                    # Criar sessão para o usuário
                    session['loggedin'] = True
                    session['id'] = user['id']
                    session['username'] = user['username']
                    
                    # Redirecionar para a página home
                    return redirect(url_for('dashboard'))
                else:
                    flash('Nome de usuário ou senha incorretos!', 'error')
                    return redirect(url_for('home'))
        except Exception as e:
            flash(f'Erro ao fazer login: {str(e)}', 'error')
            return redirect(url_for('home'))
        finally:
            conn.close()

@app.route('/logout')
def logout():
    # Remover dados da sessão
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    
    # Redirecionar para a página de login
    return redirect(url_for('home'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    # Verifica se o usuário está logado
    if 'loggedin' not in session or not session['loggedin']:
        flash('Por favor, faça login para acessar esta página!', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form['name']
        marca = request.form['marca']
        lote = request.form['lote']
        date = request.form['date']
        quantidade = request.form['quantidade']
        username = session['username']

        if not all([name, marca, lote, date, quantidade]):
            flash('Por favor, preencha todos os campos!', 'error')
            return redirect(url_for('cadastro'))
    
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO itens (name, marca, lote, date, quantidade, username) VALUES (%s, %s, %s, %s, %s, %s)",
                    (name, marca, lote, date, quantidade, username)
                )
                conn.commit()
                flash('Produto cadastrado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Erro ao cadastrar o produto: {str(e)}', 'error')
            return redirect(url_for('cadastro'))
        finally:
            conn.close()
    
    return render_template('cadastro.html', username=session['username'])

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if 'loggedin' not in session or not session['loggedin']:
        flash('Por favor, faça login para acessar esta página!', 'error')
        return redirect(url_for('home'))

    conn = get_db_connection()
    item = None
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM itens WHERE id = %s AND username = %s", (item_id, session['username']))
            item = cursor.fetchone()

        if not item:
            flash('Produto não encontrado ou você não tem permissão para editá-lo.', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            name = request.form['name']
            marca = request.form['marca']
            lote = request.form['lote']
            date = request.form['date']
            quantidade = request.form['quantidade']

            if not all([name, marca, lote, date, quantidade]):
                flash('Por favor, preencha todos os campos!', 'error')
                return redirect(url_for('edit_item', item_id=item_id))

            cursor.execute(
                "UPDATE itens SET name = %s, marca = %s, lote = %s, date = %s, quantidade = %s WHERE id = %s AND username = %s",
                (name, marca, lote, date, quantidade, item_id, session['username'])
            )
            conn.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Erro ao editar o produto: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()

    return render_template('edit_cadastro.html', item=item, username=session['username'])

@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    if 'loggedin' not in session or not session['loggedin']:
        flash('Por favor, faça login para acessar esta página!', 'error')
        return redirect(url_for('home'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Verifica se o item pertence ao usuário logado antes de deletar
            cursor.execute("DELETE FROM itens WHERE id = %s AND username = %s", (item_id, session['username']))
            conn.commit()
            if cursor.rowcount == 0:
                flash('Produto não encontrado ou você não tem permissão para deletá-lo.', 'error')
            else:
                flash('Produto deletado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao deletar o produto: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    return render_template('registro.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # Validar se os campos foram preenchidos
        if not all([username, password, email]):
            flash('Por favor, preencha todos os campos!', 'error')
            return redirect(url_for('registro'))
        
        # Hash da senha para armazenamento seguro
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Verificar se o usuário já existe
                cursor.execute("SELECT * FROM usuarios WHERE username = %s OR email = %s", (username, email))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    flash('Nome de usuário ou email já cadastrado!', 'error')
                    return redirect(url_for('registro'))
                
                # Inserir novo usuário
                cursor.execute(
                    "INSERT INTO usuarios (username, password, email) VALUES (%s, %s, %s)",
                    (username, hashed_password, email)
                )
                conn.commit()
                flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
                return redirect(url_for('home'))
        except Exception as e:
            flash(f'Erro ao cadastrar: {str(e)}', 'error')
            return redirect(url_for('registro'))
        finally:
            conn.close()

def init_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Criar tabela de usuários se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Criar tabela de itens se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS itens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    marca VARCHAR(50) NOT NULL,
                    lote VARCHAR(50) NOT NULL,
                    date DATE NOT NULL,
                    quantidade INT NOT NULL,
                    username VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("✅ Tabelas 'usuarios' e 'itens' verificadas/criadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar o banco de dados: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    # Inicializar o banco de dados antes de iniciar o aplicativo
    init_db()
    app.run(debug=True, host='0.0.0.0')
