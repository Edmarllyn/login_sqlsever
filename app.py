from flask import Flask, render_template, request, redirect, url_for, session
import pyodbc
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey123'

# Conexão com SQL Server (autenticação do Windows)
conn_str = (
    "Driver={SQL Server};"
    "Server=EDY\\MSSQLSERVER2;"
    "Database=Sistemas;"
    "Trusted_Connection=yes;"
)

def get_db_connection():
    return pyodbc.connect(conn_str)


def get_db_connection():
    return pyodbc.connect(conn_str)

# ---------------------------------------------
# LOGIN
# ---------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT senha FROM usuarios WHERE usuario = ?", usuario)
        row = cursor.fetchone()
        conn.close()
        if row:
            senha_salva = row[0]
            if (senha_salva.startswith('pbkdf2:sha') and check_password_hash(senha_salva, senha)) or senha_salva == senha:
                session['usuario'] = usuario
                return redirect(url_for('menu'))
        return render_template('login.html', mensagem='Usuário ou senha inválidos.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/menu')
def menu():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('menu.html')

# ---------------------------------------------
# CLIENTE
# ---------------------------------------------
@app.route('/cliente', methods=['GET', 'POST'])
def cliente():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    mensagem = ''
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        cpf_cnpj = request.form['cpf_cnpj']
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        endereco = request.form.get('endereco')  # campo endereço adicionado

        try:
            cursor.execute("""
                INSERT INTO cliente (nome, cpf_cnpj, email, telefone, endereco)
                VALUES (?, ?, ?, ?, ?)
            """, nome, cpf_cnpj, email, telefone, endereco)
            conn.commit()
            mensagem = 'Cliente cadastrado com sucesso!'
        except Exception as e:
            mensagem = f'Erro: {e}'

    cursor.execute("SELECT clienteid, nome, cpf_cnpj, email, telefone, endereco FROM cliente ORDER BY clienteid DESC")
    clientes = cursor.fetchall()
    conn.close()
    return render_template('cliente.html', clientes=clientes, mensagem=mensagem)

# ---------------------------------------------
# FORNECEDOR
# ---------------------------------------------
@app.route('/fornecedor', methods=['GET', 'POST'])
def fornecedor():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    mensagem = ''
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        cnpj = request.form['cnpj']
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        endereco = request.form.get('endereco')  # campo endereço adicionado

        try:
            cursor.execute("""
                INSERT INTO fornecedor (nome, cnpj, email, telefone, endereco)
                VALUES (?, ?, ?, ?, ?)
            """, nome, cnpj, email, telefone, endereco)
            conn.commit()
            mensagem = 'Fornecedor cadastrado com sucesso!'
        except Exception as e:
            mensagem = f'Erro: {e}'

    cursor.execute("SELECT fornecedorid, nome, cnpj, email, telefone, endereco FROM fornecedor ORDER BY fornecedorid DESC")
    fornecedores = cursor.fetchall()
    conn.close()
    return render_template('fornecedor.html', fornecedores=fornecedores, mensagem=mensagem)

# ---------------------------------------------
# CATEGORIA
# ---------------------------------------------
@app.route('/categoria', methods=['GET', 'POST'])
def categoria():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    mensagem = ''
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        try:
            cursor.execute("INSERT INTO categoria (nome) VALUES (?)", nome)
            conn.commit()
            mensagem = 'Categoria cadastrada com sucesso!'
        except Exception as e:
            mensagem = f'Erro: {e}'

    cursor.execute("SELECT categoriaid, nome FROM categoria ORDER BY categoriaid DESC")
    categorias = cursor.fetchall()
    conn.close()
    return render_template('categoria.html', categorias=categorias, mensagem=mensagem)

# ---------------------------------------------
# PRODUTO
# ---------------------------------------------
@app.route('/produto', methods=['GET', 'POST'])
def produto():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    mensagem = ''
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT categoriaid, nome FROM categoria")
    categorias = cursor.fetchall()

    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao')
        precovenda = request.form['precovenda']
        precocompra = request.form['precocompra']
        estoque = request.form['estoque']
        categoriaid = request.form['categoriaid']

        try:
            cursor.execute("""
                INSERT INTO produto (nome, descricao, precovenda, precocompra, estoque, categoriaid)
                VALUES (?, ?, ?, ?, ?, ?)
            """, nome, descricao, precovenda, precocompra, estoque, categoriaid)
            conn.commit()
            mensagem = 'Produto cadastrado com sucesso!'
        except Exception as e:
            mensagem = f'Erro: {e}'

    conn.close()
    return render_template('produto.html', categorias=categorias, mensagem=mensagem)

# ---------------------------------------------
# COMPRA
# ---------------------------------------------
@app.route('/compra', methods=['GET', 'POST'])
def compra():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    mensagem = ''
    sucesso = False
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT fornecedorid, nome FROM fornecedor")
    fornecedores = cursor.fetchall()

    cursor.execute("SELECT produtoid, nome FROM produto")
    produtos = cursor.fetchall()

    if request.method == 'POST':
        fornecedorid = request.form['fornecedorid']
        datacompra = request.form['datacompra']
        produtoid = request.form['produtoid']
        quantidade = int(request.form['quantidade'])
        precounitario = float(request.form['precounitario'])
        valortotal = quantidade * precounitario

        try:
            cursor.execute("""
                INSERT INTO compra (fornecedorid, datacompra, valortotal)
                OUTPUT INSERTED.compraID
                VALUES (?, ?, ?)
            """, fornecedorid, datacompra, valortotal)
            row = cursor.fetchone()
            if row:
                compra_id = row[0]
            else:
                conn.rollback()
                raise Exception("Erro ao obter ID da compra com OUTPUT INSERTED.")

            cursor.execute("""
                INSERT INTO itemcompra (compraID, produtoid, quantidade, precounitario)
                VALUES (?, ?, ?, ?)
            """, compra_id, produtoid, quantidade, precounitario)
            conn.commit()
            mensagem = 'Compra registrada com sucesso!'
            sucesso = True
        except Exception as e:
            mensagem = f'Erro: {e}'

    cursor.execute("""
        SELECT c.compraID, f.nome AS fornecedor, c.datacompra, 
               SUM(ic.quantidade * ic.precounitario) AS valortotal
        FROM compra c
        JOIN fornecedor f ON c.fornecedorid = f.fornecedorid
        JOIN itemcompra ic ON c.compraID = ic.compraID
        GROUP BY c.compraID, f.nome, c.datacompra
        ORDER BY c.compraID DESC
    """)
    compras = cursor.fetchall()

    conn.close()
    return render_template('compra.html', fornecedores=fornecedores, produtos=produtos, compras=compras, mensagem=mensagem, sucesso=sucesso)

# ---------------------------------------------
# VENDA
# ---------------------------------------------
@app.route('/venda', methods=['GET', 'POST'])
def venda():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    mensagem = ''
    sucesso = False
    conn = get_db_connection()
    cursor = conn.cursor()

    # Carregar dados para os dropdowns
    cursor.execute("SELECT clienteid, nome FROM cliente")
    clientes = cursor.fetchall()

    cursor.execute("SELECT produtoid, nome FROM produto")
    produtos = cursor.fetchall()

    if request.method == 'POST':
        clienteid = request.form['clienteid']
        datavenda = request.form['datavenda']
        produtoid = request.form['produtoid']
        quantidade = int(request.form['quantidade'])
        precounitario = float(request.form['precounitario'])
        valortotal = quantidade * precounitario

        try:
            cursor.execute("""
                INSERT INTO venda (clienteid, datavenda, valortotal)
                OUTPUT INSERTED.vendaID
                VALUES (?, ?, ?)
            """, clienteid, datavenda, valortotal)
            row = cursor.fetchone()
            if row:
                venda_id = row[0]
            else:
                conn.rollback()
                raise Exception("Erro ao obter ID da venda com OUTPUT INSERTED.")

            cursor.execute("""
                INSERT INTO itemvenda (vendaID, produtoid, quantidade, precounitario)
                VALUES (?, ?, ?, ?)
            """, venda_id, produtoid, quantidade, precounitario)

            conn.commit()
            mensagem = 'Venda registrada com sucesso!'
            sucesso = True
        except Exception as e:
            mensagem = f'Erro: {e}'

    # Buscar vendas registradas
    cursor.execute("""
        SELECT v.VendaID, c.Nome, v.DataVenda, v.ValorTotal
        FROM Venda v
        JOIN Cliente c ON v.ClienteID = c.ClienteID
        ORDER BY v.VendaID DESC
    """)
    vendas = cursor.fetchall()
    conn.close()

    # Formatar data para exibição
    vendas_formatadas = []
    for venda in vendas:
        vendaid, cliente_nome, datavenda, valortotal = venda
        if isinstance(datavenda, str):
            try:
                datavenda_obj = datetime.strptime(datavenda, '%Y-%m-%d')
            except ValueError:
                datavenda_obj = None
        else:
            datavenda_obj = datavenda

        if datavenda_obj:
            data_formatada = datavenda_obj.strftime('%d/%m/%Y')
        else:
            data_formatada = ''

        vendas_formatadas.append({
            'vendaid': vendaid,
            'cliente_nome': cliente_nome,
            'datavenda': data_formatada,
            'valortotal': valortotal if valortotal is not None else 0.0
        })

    return render_template('venda.html',
                           clientes=clientes,
                           produtos=produtos,
                           vendas=vendas_formatadas,
                           mensagem=mensagem,
                           sucesso=sucesso)



if __name__ == '__main__':
    app.run(debug=True)
