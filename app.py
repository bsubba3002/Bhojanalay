from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            materials TEXT,
            image TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dish_id INTEGER,
            quantity INTEGER,
            customer_name TEXT,
            customer_phone TEXT,
            FOREIGN KEY(dish_id) REFERENCES dishes(id)
        )
    ''')

    # Default admin
    cursor.execute('SELECT * FROM admin WHERE username=?', ('admin',))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO admin (username, password) VALUES (?, ?)', ('admin', 'admin123'))

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    conn = sqlite3.connect('database.db')
    dishes = conn.execute("SELECT * FROM dishes").fetchall()
    conn.close()
    return render_template('menu.html', dishes=dishes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        admin = conn.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        if admin:
            session['admin'] = True
            return redirect('/admin')
        else:
            return "Invalid login"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    dishes = conn.execute("SELECT * FROM dishes").fetchall()
    orders = conn.execute("""
        SELECT orders.id, dishes.name, orders.quantity, customer_name, customer_phone
        FROM orders JOIN dishes ON orders.dish_id = dishes.id
    """).fetchall()
    conn.close()
    return render_template('admin_dashboard.html', dishes=dishes, orders=orders)

@app.route('/add_dish', methods=['GET', 'POST'])
def add_dish():
    if not session.get('admin'):
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['name']
        desc = request.form['description']
        price = request.form['price']
        materials = request.form['materials']
        image = request.files['image']
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = sqlite3.connect('database.db')
        conn.execute("INSERT INTO dishes (name, description, price, materials, image) VALUES (?, ?, ?, ?, ?)",
                     (name, desc, price, materials, filename))
        conn.commit()
        conn.close()
        return redirect('/admin')
    return render_template('add_dish.html')

@app.route('/update_dish/<int:dish_id>', methods=['GET', 'POST'])
def update_dish(dish_id):
    if not session.get('admin'):
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    dish = conn.execute("SELECT * FROM dishes WHERE id=?", (dish_id,)).fetchone()
    conn.close()

    if request.method == 'POST':
        name = request.form['name']
        desc = request.form['description']
        price = request.form['price']
        materials = request.form['materials']
        image = request.files['image']
        filename = dish[5]
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = sqlite3.connect('database.db')
        conn.execute("UPDATE dishes SET name=?, description=?, price=?, materials=?, image=? WHERE id=?",
                     (name, desc, price, materials, filename, dish_id))
        conn.commit()
        conn.close()
        return redirect('/admin')
    return render_template('update_dish.html', dish=dish)

@app.route('/delete_dish/<int:dish_id>')
def delete_dish(dish_id):
    if not session.get('admin'):
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    conn.execute("DELETE FROM dishes WHERE id=?", (dish_id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        dish_id = request.form['dish_id']
        quantity = request.form['quantity']
        name = request.form['customer_name']
        phone = request.form['customer_phone']
        conn = sqlite3.connect('database.db')
        conn.execute("INSERT INTO orders (dish_id, quantity, customer_name, customer_phone) VALUES (?, ?, ?, ?)",
                     (dish_id, quantity, name, phone))
        conn.commit()
        conn.close()
        return "Order Placed Successfully!"
    conn = sqlite3.connect('database.db')
    dishes = conn.execute("SELECT * FROM dishes").fetchall()
    conn.close()
    return render_template('cart.html', dishes=dishes)

@app.route('/delete_order/<int:order_id>')
def delete_order(order_id):
    if not session.get('admin'):
        return redirect('/login')
    conn = sqlite3.connect('database.db')
    conn.execute("DELETE FROM orders WHERE id=?", (order_id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

if __name__ == '__main__':
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')
    app.run(debug=True)
