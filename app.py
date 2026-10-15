from flask import *
from werkzeug.security import *
from psutil import *
import sqlite3

app = Flask(__name__)
app.secret_key = '123'

def conectar():
    conn = sqlite3.connect('smartmonitor.db')
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def criar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS setores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT
    );

    CREATE TABLE IF NOT EXISTS computadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        identificador TEXT NOT NULL UNIQUE,
        id_setor INTEGER NOT NULL,
        FOREIGN KEY (id_setor) REFERENCES setores(id)
    );

    CREATE TABLE IF NOT EXISTS monitoramentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_computador INTEGER NOT NULL,
        cpu REAL NOT NULL,
        ram REAL NOT NULL,
        disco REAL NOT NULL,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_computador) REFERENCES computadores(id)
    );
    ''')

    conn.commit()
    conn.close()


@app.route('/')
def index():
    if 'usuario' not in session:
        return redirect('/login')

    cpu = cpu_percent(interval=1)
    ram = virtual_memory().percent
    disco = disk_usage('C:\\').percent

    return render_template(
        'index.html',
        cpu=cpu,
        ram=ram,
        disco=disco
    )


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = generate_password_hash(request.form['senha'])

        conn = conectar()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)',
                (nome, email, senha)
            )

            conn.commit()
            conn.close()

            return redirect('/login')

        except:
            conn.close()
            return 'Email já cadastrado'

    return render_template('cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM usuarios WHERE email = ?',
            (email,)
        )

        usuario = cursor.fetchone()
        conn.close()

        if usuario and check_password_hash(usuario[3], senha):
            session['usuario'] = usuario[1]
            return redirect('/')

        return 'Email ou senha incorretos'

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/setores', methods=['GET', 'POST'])
def setores():
    if 'usuario' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']

        cursor.execute(
            'INSERT INTO setores (nome, descricao) VALUES (?, ?)',
            (nome, descricao)
        )

        conn.commit()

    cursor.execute('SELECT * FROM setores')
    setores = cursor.fetchall()

    conn.close()

    return render_template(
        'setores.html',
        setores=setores
    )


@app.route('/deletar_setor/<int:id>')
def deletar_setor(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        'DELETE FROM setores WHERE id = ?',
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/setores')


@app.route('/computadores', methods=['GET', 'POST'])
def computadores():
    if 'usuario' not in session:
        return redirect('/login')

    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        identificador = request.form['identificador']
        id_setor = request.form['id_setor']

        cursor.execute(
            'INSERT INTO computadores (nome, identificador, id_setor) VALUES (?, ?, ?)',
            (nome, identificador, id_setor)
        )

        conn.commit()

    cursor.execute('''
        SELECT computadores.id, computadores.nome,
        computadores.identificador, setores.nome
        FROM computadores
        JOIN setores
        ON computadores.id_setor = setores.id
    ''')

    computadores = cursor.fetchall()

    cursor.execute('SELECT * FROM setores')
    setores = cursor.fetchall()

    conn.close()

    return render_template(
        'computadores.html',
        computadores=computadores,
        setores=setores
    )


@app.route('/deletar_computador/<int:id>')
def deletar_computador(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        'DELETE FROM computadores WHERE id = ?',
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/computadores')


if __name__ == '__main__':
    criar_banco()
    app.run(debug=True)