import os
import shutil

import schedule
from flask import Flask, redirect, render_template
from flask_login import LoginManager, login_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import PasswordField, BooleanField, SubmitField, EmailField, StringField
from wtforms.validators import DataRequired

import db_session
from static import PATH_TO_SOURCE
# from eq_solve import das_eq
# from text_detecting import show_text_from
from users import User

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
LOGIN = False
user_id = None


def clear_source():
    for filename in os.listdir(PATH_TO_SOURCE):
        file_path = os.path.join(PATH_TO_SOURCE, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


schedule.every().day.at("23:40").do(clear_source)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


class RegisterForm(FlaskForm):
    nickname = StringField('Никнейм', validators=[DataRequired()])
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Пароль заново', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class FuncForm(FlaskForm):
    file = FileField('Изображение', validators=[FileRequired()])
    submit1 = SubmitField('РЕШИТЬ УРАВНЕНИЕ')
    submit2 = SubmitField('НАЙТИ ТЕКСТ')
    submit3 = SubmitField('QR КОД')
    submit = SubmitField('Отправить')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            nickname=form.nickname.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        global LOGIN
        LOGIN = True
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            global LOGIN, user_id
            LOGIN = True
            user_id = user.id
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/functional', methods=['GET', 'POST'])
def functional():
    form = FuncForm()
    res = make_response(render_template('func.html', form=form, name=request.cookies.get('file')))
    # fetching data from db
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    id = str(user.id)
    result = None
    if form.submit3.data == True:
        print('QR')
        # result = dad_qr(file)
    elif form.submit2.data == True:
        print('TEXT')
        # result = show_text_from(file)
    elif form.submit1.data == True:
        print('EQ')
        # result = das_eq(file)
    elif form.submit.data == True:
        f = form.file.data
        res.set_cookie('file', f'''static/img/source/curent_file{id}.png''')
        f.save(os.path.join('static/img/source', f'''curent_file{id}.png'''))
    else:
        result = 'Не удалось получить данные'
    return res


@app.route('/landing')
@app.route('/')
def landing():
    if LOGIN:
        global ima
        ima = None
        return render_template('work_sides.html', title='Начальная страница')
    else:
        return render_template('sides.html', title='Начальная страница')


@app.route('/profile')
def profile():
    global user_id
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    return render_template('profile.html', nickname=user.nickname, email=user.email)


@app.route('/quit')
def quit():
    global LOGIN
    LOGIN = False
    return redirect('/')


@app.route('/func')
def func():
    return render_template('func_false.html', title='Начальная страница')


def main():
    db_session.global_init('db/users.db')
    app.run()


if __name__ == '__main__':
    main()
