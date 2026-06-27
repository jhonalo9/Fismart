from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models.usuario import Usuario
from database.db import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(email=email, activo=True).first()
        
        if usuario and usuario.verify_password(password):
            login_user(usuario, remember=True)
            flash('¡Bienvenido!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Email o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html', user=current_user)

# API Endpoints
@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    usuario = Usuario.query.filter_by(email=email, activo=True).first()
    
    if usuario and usuario.verify_password(password):
        login_user(usuario, remember=True)
        return jsonify({
            'success': True,
            'user': usuario.to_dict(),
            'message': 'Login exitoso'
        })
    
    return jsonify({
        'success': False,
        'message': 'Credenciales inválidas'
    }), 401

@auth_bp.route('/api/me', methods=['GET'])
@login_required
def api_me():
    return jsonify(current_user.to_dict())