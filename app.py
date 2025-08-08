from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Change this!

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        try:
            db = get_db()
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                       (username, hashed_password))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            return "Invalid credentials."
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def user_dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    
    user_passes_raw = query_db('SELECT * FROM bus_passes WHERE user_id = ?', [session['user_id']])
    user_passes=[]
    current_date = datetime.date.today()
    for p_raw in user_passes_raw:
        p=dict(p_raw)
        p_end_date = datetime.datetime.strptime(p['end_date'], '%Y-%m-%d').date()
        p['is_active'] = p_end_date >= current_date
        user_passes.append(p)
    
    return render_template('user_dashboard.html', passes=user_passes)

@app.route('/apply', methods=['GET', 'POST'])
def apply_pass():
    if 'user_id' not in session or session['is_admin']:
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        route = request.form['route']
        
        db = get_db()
        db.execute('INSERT INTO bus_passes (user_id, start_date, end_date, route, status) VALUES (?, ?, ?, ?, ?)',
                   (session['user_id'], start_date, end_date, route, 'pending'))
        db.commit()
        return redirect(url_for('user_dashboard'))
        
    return render_template('apply.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    pending_passes = query_db('''
        SELECT bus_passes.*, users.username FROM bus_passes
        JOIN users ON bus_passes.user_id = users.id
        WHERE bus_passes.status = 'pending'
    ''')
    approved_passes = query_db('''
        SELECT bus_passes.*, users.username FROM bus_passes
        JOIN users ON bus_passes.user_id = users.id
        WHERE bus_passes.status = 'approved'
    ''')

    return render_template('admin_dashboard.html', pending_passes=pending_passes, approved_passes=approved_passes)

@app.route('/admin/approve/<int:pass_id>')
def approve_pass(pass_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    db = get_db()
    db.execute('UPDATE bus_passes SET status = ? WHERE id = ?', ('approved', pass_id))
    db.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:pass_id>')
def reject_pass(pass_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    db = get_db()
    db.execute('UPDATE bus_passes SET status = ? WHERE id = ?', ('rejected', pass_id))
    db.commit()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)