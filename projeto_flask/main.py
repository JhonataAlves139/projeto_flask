from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import pymysql
import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import calendar

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

app = Flask(__name__)
app.secret_key = os.urandom(24)  

# Configuração da conexão com o banco de dados
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='neoestoque',
        password='112233',
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
    
    search_query = request.args.get('search_query')
    
    # Buscar os itens cadastrados pelo usuário
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if search_query:
                # Adicionar filtro de pesquisa
                cursor.execute("SELECT * FROM itens WHERE username = %s AND (name LIKE %s OR marca LIKE %s OR lote LIKE %s)", 
                               (session["username"], f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
            else:
                cursor.execute("SELECT * FROM itens WHERE username = %s", (session["username"],))
            itens = cursor.fetchall()
    except Exception as e:
        flash(f'Erro ao buscar itens: {str(e)}', 'error')
        itens = []
    finally:
        conn.close()
    
    return render_template('home.html', username=session['username'], itens=itens, search_query=search_query)

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
    return redirect(url_for('home'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'loggedin' not in session or not session['loggedin']:
        flash('Por favor, faça login para acessar esta página!', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form['name']
        marca = request.form['marca']
        lote = request.form['lote']
        date_str = request.form['date']
        quantidade = request.form['quantidade']
        username = session['username']

        if not all([name, marca, lote, date_str, quantidade]):
            flash('Por favor, preencha todos os campos!', 'error')
            return redirect(url_for('cadastro'))
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            date = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            flash('Formato de data inválido! Use dd/mm/aaaa', 'error')
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
    
    with get_db_connection() as conn:
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
                date_str = request.form['date']
                quantidade = request.form['quantidade']

                if not all([name, marca, lote, date_str, quantidade]):
                    flash('Por favor, preencha todos os campos!', 'error')
                    return redirect(url_for('edit_item', item_id=item_id))

                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                    date = date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    flash('Formato de data inválido! Use dd/mm/aaaa', 'error')
                    return redirect(url_for('edit_item', item_id=item_id))

                with conn.cursor() as cursor:
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
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimentacoes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT NOT NULL,
                    tipo ENUM('venda', 'entrada') NOT NULL,
                    quantidade INT NOT NULL,
                    data_movimentacao DATE NOT NULL,
                    username VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES itens(id) ON DELETE CASCADE
                )
            """)

            
            conn.commit()
            print("✅ Tabelas 'usuarios' e 'itens' verificadas/criadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar o banco de dados: {e}")
    finally:
        conn.close()
@app.route('/api/dados-graficos')
def api_dados_graficos_json():
    if 'loggedin' not in session or not session['loggedin']:
        return jsonify({'error': 'Não autorizado'}), 401

    filtro = request.args.get('filtro', 'mes')
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if filtro == 'dia':
                    cursor.execute("""
                        SELECT DATE(data_movimentacao) as data, SUM(quantidade) as total
                        FROM movimentacoes 
                        WHERE username = %s AND tipo = 'venda' 
                        AND data_movimentacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                        GROUP BY DATE(data_movimentacao)
                        ORDER BY data
                    """, (session['username'],))
                elif filtro == 'mes':
                    cursor.execute("""
                        SELECT YEAR(data_movimentacao) as ano, MONTH(data_movimentacao) as mes, SUM(quantidade) as total
                        FROM movimentacoes 
                        WHERE username = %s AND tipo = 'venda' 
                        AND data_movimentacao >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                        GROUP BY YEAR(data_movimentacao), MONTH(data_movimentacao)
                        ORDER BY ano, mes
                    """, (session['username'],))
                else:
                    cursor.execute("""
                        SELECT YEAR(data_movimentacao) as ano, SUM(quantidade) as total
                        FROM movimentacoes 
                        WHERE username = %s AND tipo = 'venda' 
                        AND data_movimentacao >= DATE_SUB(NOW(), INTERVAL 5 YEAR)
                        GROUP BY YEAR(data_movimentacao)
                        ORDER BY ano
                    """, (session['username'],))
                    
                dados = cursor.fetchall()
                
        labels = []
        valores = []
        
        for row in dados:
            if filtro == 'dia':
                labels.append(row['data'].strftime('%d/%m'))
            elif filtro == 'mes':
                labels.append(f"{calendar.month_name[row['mes']][:3]}/{row['ano']}")
            else:
                labels.append(str(row['ano']))
            valores.append(row['total'])

        return jsonify({
            'labels': labels,
            'valores': valores
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/registrar-venda', methods=['POST'])
def registrar_venda():
    if 'loggedin' not in session or not session['loggedin']:
        return jsonify({'error': 'Não autorizado'}), 401

    try:
        produto_id = request.form.get('produto_id')
        quantidade = int(request.form.get('quantidade'))
        data_venda = request.form.get('data_venda')

        if not all([produto_id, quantidade, data_venda]):
            return jsonify({'error': 'Todos os campos são obrigatórios'}), 400

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Verificar se o produto existe e tem estoque suficiente
                cursor.execute("SELECT quantidade FROM itens WHERE id = %s AND username = %s", (produto_id, session['username']))
                produto = cursor.fetchone()

                if not produto:
                    return jsonify({'error': 'Produto não encontrado'}), 404

                if produto['quantidade'] < quantidade:
                    return jsonify({'error': 'Estoque insuficiente'}), 400

                # Registrar a movimentação
                cursor.execute("""
                    INSERT INTO movimentacoes (item_id, tipo, quantidade, data_movimentacao, username)
                    VALUES (%s, 'venda', %s, %s, %s)
                """, (produto_id, quantidade, data_venda, session['username']))

                # Atualizar o estoque
                cursor.execute("""
                    UPDATE itens SET quantidade = quantidade - %s WHERE id = %s AND username = %s
                """, (quantidade, produto_id, session['username']))

                conn.commit()

        return jsonify({'success': True, 'message': 'Venda registrada com sucesso!'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/graficos')
def api_dados_graficos():
    if 'loggedin' not in session or not session['loggedin']:
        flash('Por favor, faça login para acessar esta página!', 'error')
        return redirect(url_for('home'))

    filtro = request.args.get('filtro', 'mes')
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            if filtro == 'dia':
                cursor.execute("""
                    SELECT DATE(data_movimentacao) as data, SUM(quantidade) as total
                    FROM movimentacoes 
                    WHERE username = %s AND tipo = 'venda' 
                    AND data_movimentacao >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                    GROUP BY DATE(data_movimentacao)
                    ORDER BY data
                """, (session['username'],))
            elif filtro == 'mes':
                cursor.execute("""
                    SELECT YEAR(data_movimentacao) as ano, MONTH(data_movimentacao) as mes, SUM(quantidade) as total
                    FROM movimentacoes 
                    WHERE username = %s AND tipo = 'venda' 
                    AND data_movimentacao >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                    GROUP BY YEAR(data_movimentacao), MONTH(data_movimentacao)
                    ORDER BY ano, mes
                """, (session['username'],))
            else:
                cursor.execute("""
                    SELECT YEAR(data_movimentacao) as ano, SUM(quantidade) as total
                    FROM movimentacoes 
                    WHERE username = %s AND tipo = 'venda' 
                    AND data_movimentacao >= DATE_SUB(NOW(), INTERVAL 5 YEAR)
                    GROUP BY YEAR(data_movimentacao)
                    ORDER BY ano
                """, (session['username'],))
                
            dados = cursor.fetchall()

    # Processar dados para exibir no HTML
    labels = []
    valores = []
    produtos = []

    for row in dados:
        if filtro == 'dia':
            labels.append(row['data'].strftime('%d/%m'))
        elif filtro == 'mes':
            labels.append(f"{calendar.month_name[row['mes']][:3]}/{row['ano']}")
        else:
            labels.append(str(row['ano']))
        valores.append(row['total'])

    return render_template('graficos.html', username=session['username'], labels=labels, valores=valores, produtos=produtos, filtro=filtro)

@app.route("/vendas")
def vendas():
    if "loggedin" not in session or not session["loggedin"]:
        flash("Por favor, faça login para acessar esta página!", "error")
        return redirect(url_for("home"))

    data_filtro = request.args.get("data_filtro")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT i.name, i.marca, i.lote, m.quantidade, m.data_movimentacao
                    FROM movimentacoes m
                    JOIN itens i ON m.item_id = i.id
                    WHERE m.username = %s AND m.tipo = 'venda'
                """
                params = [session["username"]]

                if data_filtro:
                    query += " AND DATE(m.data_movimentacao) = %s"
                    params.append(data_filtro)

                query += " ORDER BY m.data_movimentacao DESC"

                cursor.execute(query, tuple(params))
                vendas_list = cursor.fetchall()

        return render_template("vendas.html", username=session["username"], vendas=vendas_list, data_filtro=data_filtro)

    except Exception as e:
        flash(f"Erro ao buscar vendas: {str(e)}", "error")
        return redirect(url_for("home"))

@app.route('/api/produtos')
def api_produtos():
    if 'loggedin' not in session or not session['loggedin']:
        return jsonify({'error': 'Não autorizado'}), 401

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, marca, lote, quantidade 
                    FROM itens 
                    WHERE username = %s AND quantidade > 0
                    ORDER BY name
                """, (session['username'],))
                produtos = cursor.fetchall()

        # Converter para lista de dicionários
        produtos_list = []
        for produto in produtos:
            produtos_list.append({
                'id': produto['id'],
                'name': produto['name'],
                'marca': produto['marca'],
                'lote': produto['lote'],
                'quantidade': produto['quantidade']
            })

        return jsonify(produtos_list)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)

