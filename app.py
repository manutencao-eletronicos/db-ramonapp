from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime


DATABASE = "phone-maintenance.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                telefone TEXT,
                cpf TEXT,
                cep TEXT,
                endereco TEXT,
                numero TEXT,
                bairro TEXT,
                cidade TEXT,
                uf TEXT
              )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS registros (
                numero INTEGER PRIMARY KEY
              )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS orcamentos (
                numero_registro INTEGER PRIMARY KEY,
                nome_cliente TEXT,
                telefone TEXT,
                cpf TEXT,
                cep TEXT,
                endereco TEXT,
                numero TEXT,
                bairro TEXT,
                cidade TEXT,
                uf TEXT,
                descricao TEXT,
                forma_pagamento TEXT,
                valor REAL
              )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS caixa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_comprovante TEXT UNIQUE,
                data TEXT NOT NULL,
                valor REAL NOT NULL,
                descricao TEXT
            )"""
        )
        db.execute(
            """
        CREATE TABLE IF NOT EXISTS faturamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lucros REAL,
            despesas REAL,
            total REAL,
            data TEXT DEFAULT CURRENT_TIMESTAMP
        )
         """
        )
        # Inserir o número inicial de registro (999999) se a tabela estiver vazia
        if db.execute("SELECT COUNT(*) FROM registros").fetchone()[0] == 0:
            db.execute("INSERT INTO registros (numero) VALUES (999999)")

        db.commit()


def create_app():
    app = Flask(__name__)
    CORS(app)
    init_db()

    @app.route("/cadastro_cliente", methods=["POST"])
    def cadastro_cliente():
        data = request.get_json()
        nome = data.get("nome").strip().upper()
        novo_cliente = {
            "nome": nome,
            "telefone": data.get("telefone"),
            "cpf": data.get("cpf"),
            "cep": data.get("cep"),
            "endereco": data.get("endereco"),
            "numero": data.get("numero"),
            "bairro": data.get("bairro"),
            "cidade": data.get("cidade"),
            "uf": data.get("uf"),
        }

        with get_db() as db:
            db.execute(
                """
                INSERT INTO clientes (nome, telefone, cpf, cep, endereco, numero, bairro, cidade, uf)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    novo_cliente["nome"],
                    novo_cliente["telefone"],
                    novo_cliente["cpf"],
                    novo_cliente["cep"],
                    novo_cliente["endereco"],
                    novo_cliente["numero"],
                    novo_cliente["bairro"],
                    novo_cliente["cidade"],
                    novo_cliente["uf"],
                ),
            )
            db.commit()

        return jsonify({"message": "Cliente cadastrado com sucesso!"}), 201

    @app.route("/cadastro_clientes-all", methods=["GET"])
    def get_all_clientes():
        with get_db() as db:
            clientes = db.execute("SELECT * FROM clientes").fetchall()

        clientes_data = [
            {
                "nome": cliente["nome"],
                "telefone": cliente["telefone"],
                "cpf": cliente["cpf"],
                "cep": cliente["cep"],
                "endereco": cliente["endereco"],
                "numero": cliente["numero"],
                "bairro": cliente["bairro"],
                "cidade": cliente["cidade"],
                "uf": cliente["uf"],
            }
            for cliente in clientes
        ]

        return jsonify(clientes_data), 200

    @app.route("/cadastro_cliente/<string:nome>", methods=["GET"])
    def get_cliente(nome):
        nome = nome.strip().upper()
        with get_db() as db:
            cliente = db.execute(
                """
                SELECT * FROM clientes
                WHERE TRIM(REPLACE(nome, ' ', '')) = TRIM(REPLACE(?, ' ', ''))
                """,
                (nome,),
            ).fetchone()

            if cliente:
                cliente_data = {
                    "nome": cliente["nome"],
                    "telefone": cliente["telefone"],
                    "cpf": cliente["cpf"],
                    "cep": cliente["cep"],
                    "endereco": cliente["endereco"],
                    "numero": cliente["numero"],
                    "bairro": cliente["bairro"],
                    "cidade": cliente["cidade"],
                    "uf": cliente["uf"],
                }
                return jsonify(cliente_data), 200
            else:
                return jsonify({"message": "Cliente não encontrado!"}), 404

    @app.route("/cadastro_cliente/<string:nome>", methods=["DELETE"])
    def delete_cliente(nome):
        nome = nome.strip().upper()
        with get_db() as db:
            cliente = db.execute(
                """
                SELECT * FROM clientes
                WHERE TRIM(REPLACE(nome, ' ', '')) = TRIM(REPLACE(?, ' ', ''))
                """,
                (nome,),
            ).fetchone()

            if cliente:
                db.execute(
                    """
                    DELETE FROM clientes
                    WHERE TRIM(REPLACE(nome, ' ', '')) = TRIM(REPLACE(?, ' ', ''))
                    """,
                    (nome,),
                )
                db.commit()
                return jsonify({"message": "Cliente deletado com sucesso!"}), 200
            else:
                return jsonify({"message": "Cliente não encontrado!"}), 404

    @app.route("/obter_numero_registro", methods=["GET"])
    def obter_numero_registro():
        with get_db() as db:
            numero = db.execute(
                "SELECT numero FROM registros ORDER BY numero DESC LIMIT 1"
            ).fetchone()
            novo_numero = numero["numero"] - 1

            try:
                db.execute("INSERT INTO registros (numero) VALUES (?)", (novo_numero,))
                db.commit()
            except sqlite3.IntegrityError:
                while True:
                    novo_numero -= 1
                    try:
                        db.execute(
                            "INSERT INTO registros (numero) VALUES (?)", (novo_numero,)
                        )
                        db.commit()
                        break
                    except sqlite3.IntegrityError:
                        continue

            return jsonify({"numero": novo_numero}), 200

    @app.route("/orcamento", methods=["POST", "GET"])
    def orcamento():
        if request.method == "POST":
            data = request.get_json()

            # Processar os dados recebidos
            numero_registro = data.get("comprovanteOrcamento")
            nome_cliente = data.get("clienteOrcamento").strip().upper()
            telefone = data.get("telefone")
            cpf = data.get("cpf")
            cep = data.get("cep")
            endereco = data.get("endereco")
            numero = data.get("numero")
            bairro = data.get("bairro")
            cidade = data.get("cidade")
            uf = data.get("uf")
            descricao = data.get("descricaoOrcamento")
            forma_pagamento = data.get("formaDepagementoOrcamento")
            valor = data.get("valorOrcamento")

            with get_db() as db:
                cursor = db.cursor()
                cursor.execute(
                    """
                INSERT INTO orcamentos (numero_registro, nome_cliente, telefone, cpf, cep, endereco, numero, bairro, cidade, uf, descricao, forma_pagamento, valor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        numero_registro,
                        nome_cliente,
                        telefone,
                        cpf,
                        cep,
                        endereco,
                        numero,
                        bairro,
                        cidade,
                        uf,
                        descricao,
                        forma_pagamento,
                        valor,
                    ),
                )
                db.commit()

                # Adiciona o orçamento à tabela de caixa
                cursor.execute(
                    """
                INSERT INTO caixa (numero_comprovante, valor, data)
                VALUES (?, ?, datetime('now'))
                """,
                    (numero_registro, valor),
                )
                db.commit()

            return (
                jsonify({"message": "Orçamento salvo e caixa atualizado com sucesso!"}),
                201,
            )

        elif request.method == "GET":
            with get_db() as db:
                orcamentos = db.execute("SELECT * FROM orcamentos").fetchall()

            orcamentos_data = [
                {
                    "numero_registro": orcamento["numero_registro"],
                    "nome_cliente": orcamento["nome_cliente"],
                    "telefone": orcamento["telefone"],
                    "cpf": orcamento["cpf"],
                    "cep": orcamento["cep"],
                    "endereco": orcamento["endereco"],
                    "numero": orcamento["numero"],
                    "bairro": orcamento["bairro"],
                    "cidade": orcamento["cidade"],
                    "uf": orcamento["uf"],
                    "descricao": orcamento["descricao"],
                    "forma_pagamento": orcamento["forma_pagamento"],
                    "valor": orcamento["valor"],
                }
                for orcamento in orcamentos
            ]

            return jsonify(orcamentos_data), 200

    @app.route("/orcamento/<int:numero_registro>", methods=["GET"])
    def get_orcamento(numero_registro):
        with get_db() as db:
            db.row_factory = sqlite3.Row  # Configure para retornar como dicionário
            cursor = db.cursor()
            orcamento = cursor.execute(
                """
            SELECT * FROM orcamentos WHERE numero_registro = ?
            """,
                (numero_registro,),
            ).fetchone()

            if orcamento:
                orcamento_data = {
                    "numero_registro": orcamento["numero_registro"],
                    "nome_cliente": orcamento["nome_cliente"],
                    "telefone": orcamento["telefone"],
                    "cpf": orcamento["cpf"],
                    "cep": orcamento["cep"],
                    "endereco": orcamento["endereco"],
                    "numero": orcamento["numero"],
                    "bairro": orcamento["bairro"],
                    "cidade": orcamento["cidade"],
                    "uf": orcamento["uf"],
                    "descricao": orcamento["descricao"],
                    "forma_pagamento": orcamento["forma_pagamento"],
                    "valor": orcamento["valor"],
                }
                return jsonify(orcamento_data), 200
            else:
                return jsonify({"message": "Orçamento não encontrado!"}), 404

    @app.route("/caixa", methods=["POST", "PUT", "DELETE", "GET"])
    def caixa():
        if request.method in ["POST", "PUT"] and not request.is_json:
            return (
                jsonify(
                    {
                        "error": "Unsupported Media Type: Content-Type must be application/json"
                    }
                ),
                415,
            )

        with get_db() as db:
            if request.method == "POST":
                data = request.get_json()
                numero_comprovante = data.get("numero_comprovante")
                valor = data.get("valor")

                db.execute(
                    """
                    INSERT INTO caixa (numero_comprovante, valor, data)
                    VALUES (?, ?, datetime('now'))
                    """,
                    (numero_comprovante, valor),
                )
                db.commit()
                return jsonify({"message": "Caixa atualizado com sucesso!"}), 201

            elif request.method == "PUT":
                data = request.get_json()
                numero_comprovante = data.get("numero_comprovante")
                valor = data.get("valor")

                db.execute(
                    """
                    UPDATE caixa
                    SET valor = ?
                    WHERE numero_comprovante = ?
                    """,
                    (valor, numero_comprovante),
                )
                db.commit()
                return jsonify({"message": "Caixa atualizado com sucesso!"}), 200

            elif request.method == "DELETE":
                data = request.get_json()
                numero_comprovante = data.get("numero_comprovante")

                db.execute(
                    "DELETE FROM caixa WHERE numero_comprovante = ?",
                    (numero_comprovante,),
                )
                db.commit()
                return (
                    jsonify({"message": "Registro de caixa deletado com sucesso!"}),
                    200,
                )

            elif request.method == "GET":
                registros_caixa = db.execute("SELECT * FROM caixa").fetchall()
                caixa_data = [
                    {
                        "numero_comprovante": registro["numero_comprovante"],
                        "valor": registro["valor"],
                        "data": registro["data"],
                    }
                    for registro in registros_caixa
                ]
                return jsonify(caixa_data), 200

    @app.route("/faturamento", methods=["POST"])
    def registrar_faturamento():
        try:
            data = request.get_json()
            lucros = data.get("lucros", 0)
            despesas = data.get("despesas", 0)
            total = data.get("total", lucros - despesas)
            data_registro = data.get("data", datetime.now().strftime("%Y-%m-%d"))

            with get_db() as db:
                # Verifica se já existe um registro para a data especificada
                registro_existente = db.execute(
                    "SELECT * FROM faturamento WHERE data = ?", (data_registro,)
                ).fetchone()

                if registro_existente:
                    # Se existir, atualiza o registro existente
                    db.execute(
                        """
                        UPDATE faturamento 
                        SET lucros = ?, despesas = ?, total = ? 
                        WHERE data = ?
                        """,
                        (lucros, despesas, total, data_registro),
                    )
                else:
                    # Se não existir, insere um novo registro
                    db.execute(
                        """
                        INSERT INTO faturamento (lucros, despesas, total, data)
                        VALUES (?, ?, ?, ?)
                        """,
                        (lucros, despesas, total, data_registro),
                    )

                db.commit()

            return (
                jsonify(
                    {
                        "message": "Faturamento registrado com sucesso!",
                        "lucros": lucros,
                        "despesas": despesas,
                        "total": total,
                        "data": data_registro,
                    }
                ),
                201,
            )

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/faturamento", methods=["GET"])
    def consultar_faturamento():
        data_param = request.args.get("data")

        if not data_param:
            return jsonify({"error": "Data não fornecida"}), 400

        with get_db() as db:
            rows = db.execute(
                "SELECT * FROM faturamento WHERE data = ?", (data_param,)
            ).fetchall()

        faturamento_data = [
            {
                "id": row["id"],
                "lucros": row["lucros"],
                "despesas": row["despesas"],
                "total": row["total"],
                "data": row["data"],
            }
            for row in rows
        ]

        return jsonify(faturamento_data), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
