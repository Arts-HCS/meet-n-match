from flask import Flask, request, redirect, url_for, render_template, jsonify, session
import json
import os
import uuid
import hashlib
import random

# Generar una clave secreta aleatoria y convertirla a una cadena
def generate_secret_key():
    return os.urandom(24)  # Genera 24 bytes de datos aleatorios

app = Flask(__name__)
app.secret_key = generate_secret_key()  # Asigna la clave secreta generada

# Archivos de datos
groups_file = 'groups.json'
interests_file = 'interests.json'
users_file = 'users.json'

# Cargar los grupos existentes
if not os.path.exists(groups_file):
    with open(groups_file, 'w') as f:
        json.dump([], f)

# Cargar los intereses existentes
if not os.path.exists(interests_file):
    with open(interests_file, 'w') as f:
        json.dump(["#futbol", "#musica", "#arte", "#karate", "#voleibol", "#ciencia", "#programacion"], f)

# Cargar los usuarios existentes
if not os.path.exists(users_file):
    with open(users_file, 'w') as f:
        json.dump([], f)

# Funciones para manejar archivos
def load_groups():
    with open(groups_file, 'r') as f:
        return json.load(f)

def save_groups(groups):
    with open(groups_file, 'w') as f:
        json.dump(groups, f, indent=4)

def load_interests():
    with open(interests_file, 'r') as f:
        return json.load(f)

def save_interests(interests):
    with open(interests_file, 'w') as f:
        json.dump(interests, f, indent=4)

def load_users():
    with open(users_file, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=4)

def generate_unique_code():
    return str(uuid.uuid4())

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Rutas y lógica de la aplicación
@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')
#-------------------------------------------
@app.route('/new_page')
def new_page_view():  # Renombrado para evitar conflicto
    return render_template('new_page.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/business')
def business():
    return render_template('business.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')



@app.route('/save_registration', methods=['POST'])
def save_registration():
    users = load_users()
    email = request.form['email']
    password = hash_password(request.form['password'])
    
    user = next((user for user in users if user['email'] == email), None)
    
    if user and user['password'] == password:
        session['user'] = email
        return redirect(url_for('new_page'))
    
    if user:
        return redirect(url_for('register'))  
    
    new_user = {
        'name': request.form['name'],
        'dob': request.form['dob'],
        'gender': request.form['gender'],
        'email': email,
        'password': password
    }
    users.append(new_user)
    save_users(users)
    session['user'] = email
    return redirect(url_for('select_interest'))

@app.route('/save_login', methods=['POST'])
def save_login():
    email = request.form['email']
    password = hash_password(request.form['password'])
    
    users = load_users()
    user = next((u for u in users if u['email'] == email and u['password'] == password), None)
    
    if user:
        session['user'] = email
        return redirect(url_for('new_page'))
    
    return "Credenciales incorrectas", 401

@app.route('/select_interest')
def select_interest():
    interests = load_interests()
    return render_template('select_interest.html', interests=interests)

@app.route('/save_interest', methods=['POST'])
def save_interest():
    user_email = session.get('user')
    if not user_email:
        return redirect(url_for('register'))

    user_data = load_users()
    user = next((u for u in user_data if u['email'] == user_email), None)

    if user:
        user['interest'] = request.form['interest']
        user['location'] = request.form['location'] 
        save_users(user_data)

    return redirect(url_for('groups'))

@app.route('/groups')
def groups():
    user_email = session.get('user')
    if not user_email:
        return redirect(url_for('register'))
    
    groups = load_groups()
    user_data = load_users()
    user = next((u for u in user_data if u['email'] == user_email), None)
    interest = user.get('interest', '').lower() if user else ''
    filtered_groups = [group for group in groups if group['tag'].lower() == interest]
    return render_template('groups.html', groups=filtered_groups)

@app.route('/search_interest', methods=['POST'])
def search_interest():
    interest = request.form.get('interest', '').lower()
    groups = load_groups()
    filtered_groups = [group for group in groups if group['tag'].lower() == interest]
    
    if filtered_groups:
        return render_template('groups.html', groups=filtered_groups)
    else:
        return render_template('groups.html', no_results=True)

@app.route('/new_page')
def new_page():
    if 'user' not in session:
        return redirect(url_for('register'))
    return render_template('new_page.html')

@app.route('/create_group')
def create_group():
    user_email = session.get('user')
    if not user_email:
        return redirect(url_for('register'))
    
    user_data = load_users()
    user = next((u for u in user_data if u['email'] == user_email), None)
    interest = user.get('interest', '') if user else ''
    interests = ['correr', 'leer', 'fútbol', 'karaoke']  # Ejemplo de intereses predefinidos
    return render_template('create_group.html', interest=interest, interests=interests)

@app.route('/save_group', methods=['POST'])
def save_group():
    group_interest = request.form['tags'].strip().lower()
    # Cargar los intereses actuales
    interests = load_interests()
    
    # Agregar el nuevo interés si no está presente
    if group_interest not in interests:
        interests.append(group_interest)
        save_interests(interests)
    
    # Crear el nuevo grupo
    group = {
        'name': request.form['group_name'],
        'participants': int(request.form['max_participants']),
        'age_range': f"{request.form['min_age']}-{request.form['max_age']}",
        'gender': request.form['gender'],
        'tags': request.form['tags'],
        'location': request.form['location'],  # Guardar la ubicación ingresada por el usuario
        'business': False,  # Puedes ajustar este campo según sea necesario
        'tag': request.form['tags'],  # Utiliza el tag ingresado por el usuario
        'code': generate_unique_code()  # Genera un código único para el grupo
    }
    
    # Guardar el nuevo grupo
    groups = load_groups()
    groups.append(group)
    save_groups(groups)
    
    return redirect(url_for('groups'))


@app.route('/can_access_chat', methods=['POST'])
def can_access_chat():
    user_email = session.get('user')
    group_code = request.form['group_code']

    if not user_email:
        return jsonify({'access': False})

    users = load_users()
    user = next((u for u in users if u['email'] == user_email), None)
    
    if user and user.get('group_code') == group_code:
        return jsonify({'access': True})
    return jsonify({'access': False})

@app.route('/get_recommended_groups')
def get_recommended_groups():
    # Aquí puedes obtener datos del usuario, como género, edad mínima, etc.
    # Para este ejemplo, tomaremos un conjunto de grupos aleatorios.

    groups = load_groups()
    recommended_groups = random.sample(groups, min(8, len(groups)))
    
    return jsonify({'groups': recommended_groups})



if __name__ == '__main__':
    # Agregar grupos de ejemplo
    if not load_groups():
        example_groups = [
            {"name": "Lemon Juice", "participants": 8, "age_range": "14-16", "gender": "Mixto", "location": "Berkeley, CA", "business": True, "tag": "#musica", "code": generate_unique_code()},
            {"name": "Tech Innovators", "participants": 10, "age_range": "20-30", "gender": "Masculino", "location": "San Francisco, CA", "business": False, "tag": "#programacion", "code": generate_unique_code()},
            {"name": "Art Lovers", "participants": 15, "age_range": "25-35", "gender": "Femenino", "location": "Los Angeles, CA", "business": False, "tag": "#arte", "code": generate_unique_code()}
        ]
        save_groups(example_groups)
    app.run(debug=True)
