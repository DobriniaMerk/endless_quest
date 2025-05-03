from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from .models import db, User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

langs = ['ru', 'en']

auth_bp = Blueprint('auth', __name__, url_prefix='/')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже существует')
            return redirect(url_for('auth.register'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('paragraph.show', id=0, lang=langs[0]))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('paragraph.show', id=0, lang=langs[0]))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('paragraph.show', id=0, lang=langs[0]))
        flash('Неправильное имя пользователя или пароль')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('auth.login'))
