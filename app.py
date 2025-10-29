import pymysql
import hashlib
from os import getenv
from datetime import datetime
from waitress import serve
from flask import Flask, request, render_template, render_template_string, session, redirect, url_for, jsonify
from functools import wraps

app = Flask(__name__)
app.secret_key = "super_secret_key_change_in_production_12345"

def get_db_connection():
    """Cria conexão com o banco de dados"""
    return pymysql.connect(
        host=getenv("MYSQL_HOST"),
        user=getenv("MYSQL_USER"),
        password=getenv("MYSQL_PASSWORD"),
        database=getenv("MYSQL_DATABASE"),
        autocommit=False  # Importante para transações
    )

def login_required(f):
    """Decorador para rotas que requerem autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET"])
def index():
    """Página inicial redireciona para login"""
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Página de login"""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        
        if username and password:
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                password_hash = hashlib.sha224(password.encode("utf-8")).hexdigest()
                query = "SELECT username, balance FROM users WHERE username = %s AND password = %s"
                cursor.execute(query, (username, password_hash))
                user = cursor.fetchone()
                
                if user:
                    session['username'] = user[0]
                    session['balance'] = float(user[1])
                    conn.commit()
                    return redirect(url_for('home'))
                else:
                    return render_template("login.html", error="Invalid username or password")
            except Exception as e:
                conn.rollback()
                return render_template("login.html", error="Database error")
            finally:
                conn.close()
    
    return render_template("login.html")

@app.route("/logout", methods=["GET"])
def logout():
    """Logout do usuário"""
    session.clear()
    return redirect(url_for('login'))

@app.route("/home", methods=["GET"])
@login_required
def home():
    """Página inicial após login"""
    username = session.get('username')
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username = %s", (username,))
        balance = cursor.fetchone()[0]
        session['balance'] = float(balance)
        
        # Verificar se pode acessar premium content (flag aparece aqui)
        cursor.execute("SELECT COUNT(*) FROM orders WHERE username = %s AND item_id = (SELECT id FROM items WHERE name = 'Premium Access' LIMIT 1)", (username,))
        has_premium = cursor.fetchone()[0] > 0
        flag = getenv("USER_FLAG") if has_premium else None
        
        return render_template("home.html", 
                             username=username, 
                             balance=balance,
                             flag=flag,
                             has_premium=has_premium)
    except Exception as e:
        return render_template("error.html", error=str(e))
    finally:
        conn.close()

@app.route("/shop", methods=["GET", "POST"])
@login_required
def shop():
    """Loja para comprar itens"""
    username = session.get('username')
    
    if request.method == "POST":
        item_id = request.form.get("item_id")
        quantity = int(request.form.get("quantity", 1))
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Buscar item
            cursor.execute("SELECT id, name, price FROM items WHERE id = %s", (item_id,))
            item = cursor.fetchone()
            
            if not item:
                return redirect(url_for('shop'))
            
            item_name, item_price = item[1], float(item[2])
            total_cost = item_price * quantity
            
            # Verificar saldo
            cursor.execute("SELECT balance FROM users WHERE username = %s", (username,))
            balance = float(cursor.fetchone()[0])
            
            if balance < total_cost:
                return render_template("shop.html", 
                                     username=username,
                                     balance=balance,
                                     items=get_items(),
                                     error="Insufficient balance")
            
            # Atualizar saldo e criar pedido
            new_balance = balance - total_cost
            cursor.execute("UPDATE users SET balance = %s WHERE username = %s", 
                          (new_balance, username))
            
            cursor.execute("""
                INSERT INTO orders (username, item_id, quantity, total_price, refunded, created_at)
                VALUES (%s, %s, %s, %s, 0, NOW())
            """, (username, item_id, quantity, total_cost))
            
            order_id = cursor.lastrowid
            conn.commit()
            
            session['balance'] = new_balance
            return render_template("shop.html",
                                 username=username,
                                 balance=new_balance,
                                 items=get_items(),
                                 success=f"Purchase successful! Order ID: {order_id}")
        except Exception as e:
            conn.rollback()
            return render_template("shop.html",
                                 username=username,
                                 balance=session.get('balance', 0),
                                 items=get_items(),
                                 error=f"Error: {str(e)}")
        finally:
            conn.close()
    
    # GET request
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username = %s", (username,))
        balance = float(cursor.fetchone()[0])
        session['balance'] = balance
        return render_template("shop.html",
                             username=username,
                             balance=balance,
                             items=get_items())
    except Exception as e:
        return render_template("error.html", error=str(e))
    finally:
        conn.close()

def get_items():
    """Retorna lista de itens disponíveis"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, description FROM items")
        items = []
        for row in cursor.fetchall():
            items.append({
                'id': row[0],
                'name': row[1],
                'price': float(row[2]),
                'description': row[3]
            })
        return items
    finally:
        conn.close()

@app.route("/orders", methods=["GET"])
@login_required
def orders():
    """Lista pedidos do usuário"""
    username = session.get('username')
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username = %s", (username,))
        balance = float(cursor.fetchone()[0])
        session['balance'] = balance
        
        cursor.execute("""
            SELECT o.id, i.name, o.quantity, o.total_price, o.refunded, o.created_at
            FROM orders o
            JOIN items i ON o.item_id = i.id
            WHERE o.username = %s
            ORDER BY o.created_at DESC
        """, (username,))
        
        orders_list = []
        for row in cursor.fetchall():
            orders_list.append({
                'id': row[0],
                'item_name': row[1],
                'quantity': row[2],
                'total_price': float(row[3]),
                'refunded': bool(row[4]),
                'created_at': row[5]
            })
        
        return render_template("orders.html",
                             username=username,
                             orders=orders_list,
                             balance=balance)
    except Exception as e:
        return render_template("error.html", error=str(e))
    finally:
        conn.close()

@app.route("/history", methods=["GET"])
@login_required
def history():
    """Histórico de transações"""
    username = session.get('username')
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username = %s", (username,))
        balance = float(cursor.fetchone()[0])
        
        # Histórico completo (compras e cancelamentos)
        cursor.execute("""
            SELECT 'purchase' as type, o.created_at as date, i.name, o.total_price as amount
            FROM orders o
            JOIN items i ON o.item_id = i.id
            WHERE o.username = %s
            UNION ALL
            SELECT 'refund' as type, o.created_at as date, i.name, o.total_price as amount
            FROM orders o
            JOIN items i ON o.item_id = i.id
            WHERE o.username = %s AND o.refunded = 1
            ORDER BY date DESC
            LIMIT 50
        """, (username, username))
        
        history_list = []
        for row in cursor.fetchall():
            history_list.append({
                'type': row[0],
                'date': row[1],
                'item': row[2],
                'amount': float(row[3])
            })
        
        return render_template("history.html",
                             username=username,
                             history=history_list,
                             balance=balance)
    except Exception as e:
        return render_template("error.html", error=str(e))
    finally:
        conn.close()

@app.route("/order/cancel", methods=["POST"])
@login_required
def cancel_order():
    """
    VULNERÁVEL A RACE CONDITION!
    
    O problema: A verificação e o update não são atômicos.
    Múltiplas requisições simultâneas podem processar o mesmo reembolso.
    """
    username = session.get('username')
    order_id = request.form.get("order_id")
    
    if not order_id:
        return jsonify({"error": "Order ID required"}), 400
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verificar se o pedido existe e pertence ao usuário
        cursor.execute("""
            SELECT refunded, total_price 
            FROM orders 
            WHERE id = %s AND username = %s
        """, (order_id, username))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Order not found"}), 404
        
        is_refunded, order_amount = result[0], float(result[1])
        
        # VULNERABILIDADE: Não usa transação atômica ou lock
        # Entre a verificação e o update, outra requisição pode passar
        if is_refunded == 1:
            return jsonify({"error": "Order already refunded"}), 400
        
        # Simula um pequeno delay (aumenta chance de race condition)
        time.sleep(0.1)
        
        # VULNERABILIDADE: Atualizar saldo SEM usar transação com lock
        # Múltiplas requisições podem ler o mesmo saldo e não acumular corretamente
        # Para explorar melhor, vamos usar UPDATE direto sem ler antes
        # Isso permite que múltiplas requisições incrementem o saldo
        cursor.execute("""
            UPDATE users 
            SET balance = balance + %s 
            WHERE username = %s
        """, (order_amount, username))
        
        # Ler o novo saldo para retornar
        cursor.execute("SELECT balance FROM users WHERE username = %s", (username,))
        new_balance = float(cursor.fetchone()[0])
        
        # CRÍTICO: Delay ANTES de marcar como refunded
        # Isso permite que outras requisições ainda vejam refunded=0 e processem
        time.sleep(0.15)
        
        # Marcar como reembolsado (mas pode já ter sido marcado por outra thread!)
        # VULNERABILIDADE: Não verifica se já foi marcado antes de atualizar
        cursor.execute("UPDATE orders SET refunded = 1 WHERE id = %s", (order_id,))
        
        conn.commit()
        
        session['balance'] = new_balance
        
        return jsonify({
            "success": True,
            "message": f"Refund processed: ${order_amount:.2f}",
            "new_balance": new_balance
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

def init_database():
    """Inicializa o banco de dados criando tabelas e dados iniciais se não existirem"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Criar tabelas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(50) PRIMARY KEY,
                password VARCHAR(64) NOT NULL,
                balance DECIMAL(10, 2) DEFAULT 100.00
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                description TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                item_id INT NOT NULL,
                quantity INT NOT NULL DEFAULT 1,
                total_price DECIMAL(10, 2) NOT NULL,
                refunded TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username),
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        """)
        
        # Verificar se já tem dados
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            # Inserir usuários
            cursor.execute("""
                INSERT INTO users (username, password, balance) VALUES
                ('user', 'ef6868fe47958067cf0f396891d6f4de11f038e4a93a70557d9f8e20', 100.00),
                ('guest', 'ec7d20355024b9a9c84357a9cfb9b2669ac4c019ad9266851d6ad17b', 100.00)
            """)
            
            # Inserir itens
            cursor.execute("""
                INSERT INTO items (name, price, description) VALUES
                ('Premium Access', 10000.00, 'Unlock exclusive premium features and content'),
                ('Standard Item', 50.00, 'A standard item for your collection'),
                ('Basic Item', 25.00, 'Essential basic item'),
                ('Gaming Mouse', 75.00, 'High precision gaming mouse'),
                ('Wireless Keyboard', 120.00, 'Ergonomic wireless keyboard'),
                ('USB Cable', 15.00, 'High-speed USB-C cable')
            """)
        
        conn.commit()
        conn.close()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    # Inicializar banco de dados
    init_database()
    port = int(getenv("PORT", 80))
    # threads=100 permite processar muitas requisições simultâneas para race condition
    serve(app, host="0.0.0.0", port=port, threads=100)

