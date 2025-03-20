from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
import os
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from wtforms import StringField, TextAreaField, IntegerField, SubmitField, PasswordField, SelectField,FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from datetime import datetime
from sqlalchemy.orm import joinedload
from flask import send_from_directory, current_app
import re
from flask import abort
app = Flask(__name__)

def replace_youtube_links(text):
    youtube_regex = r"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+))"
    return re.sub(youtube_regex, r'<iframe width="560" height="310" src="https://www.youtube.com/embed/\2" frameborder="0" allowfullscreen></iframe>', text)

app.jinja_env.filters['replace_youtube_links'] = replace_youtube_links

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'mysql://sql7768667:jcZ7X5WcwU@sql7.freesqldatabase.com:3306/sql7768667')


app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt'}

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    boards = db.relationship('Board', backref='owner', lazy=True)

board_users = db.Table('board_users',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('board_id', db.Integer, db.ForeignKey('boards.id'), primary_key=True)
)

class Board(db.Model):
    __tablename__ = 'boards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lists = db.relationship('List', backref='board', lazy=True)
    users = db.relationship('User', secondary=board_users, backref=db.backref('shared_boards', lazy='dynamic'))

class List(db.Model):
    __tablename__ = 'lists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'), nullable=False)
    position = db.Column(db.Integer, default=0)
    cards = db.relationship('Card', backref='list', lazy=True)


class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    list_id = db.Column(db.Integer, db.ForeignKey('lists.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    position = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id', ondelete="CASCADE"), nullable=False)
    attachment = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref='comments')
    card = db.relationship('Card', backref=db.backref('comments', cascade="all, delete", passive_deletes=True))


class ChecklistItem(db.Model):
    __tablename__ = 'checklist_items'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), nullable=False)

    card = db.relationship('Card', backref=db.backref('checklist_items', lazy=True))

class ChecklistItemForm(FlaskForm):
    text = StringField('Название пункта', validators=[DataRequired()])
    submit = SubmitField('Добавить пункт')

class CommentForm(FlaskForm):
    content = TextAreaField('Комментарий', validators=[DataRequired()])
    file = FileField('Прикрепить файл')
    submit = SubmitField('Добавить комментарий')

    def save_attachment(self, file):
        if file:

            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return filename
        return None
class ListForm(FlaskForm):
    name = StringField('Название списка', validators=[DataRequired()])
    position = IntegerField('Позиция', default=0, validators=[NumberRange(min=0, max=100)])
    submit = SubmitField('Добавить список')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class BoardForm(FlaskForm):
    name = StringField('Название доски', validators=[DataRequired()])
    submit = SubmitField('Создать доску')

class RegisterForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(), Length(min=3, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтверждение пароля', validators=[
        DataRequired(),
        EqualTo('password', message='Пароли должны совпадать!')
    ])
    submit = SubmitField('Зарегистрироваться')

class CardForm(FlaskForm):
    title = StringField('Заголовок карточки', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    due_date = StringField('Дата выполнения (гггг-мм-дд)', validators=[DataRequired()])
    position = IntegerField('Позиция', default=0, validators=[NumberRange(min=0, max=100)])
    list_id = SelectField('Выберите список', coerce=int)
    submit = SubmitField('Добавить карточку')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if not user:
            user = User(email=form.email.data, password=generate_password_hash('testpassword'))
            db.session.add(user)
            db.session.commit()

        login_user(user)
        flash('Вы успешно вошли!', 'success')
        return redirect(url_for('index'))

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Пользователь с таким email уже существует.', 'error')
            return render_template('register.html', form=form)

        hashed_password = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed_password)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Вы успешно зарегистрированы!', 'success')
            login_user(user)
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при регистрации. Попробуйте снова.', 'error')
            print("Error:", e)

    return render_template('register.html', form=form)



@app.route('/')
@login_required
def index():
    boards = Board.query.filter((Board.user_id == current_user.id) | (Board.users.any(id=current_user.id))).all()
    return render_template('index.html', boards=boards)



@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли!', 'success')
    return redirect(url_for('index'))


@app.route('/board/<int:board_id>')
@login_required
def board(board_id):
    board = Board.query.get(board_id)
    if not board:
        abort(404)

    if current_user.id != board.user_id and current_user not in board.users:
        abort(403)

    lists = List.query.filter_by(board_id=board.id).all()
    cards = Card.query.filter(Card.list_id.in_([lst.id for lst in lists])).all()

    return render_template('board.html', board=board, lists=lists, cards=cards)


@app.route('/create_board', methods=['GET', 'POST'])
@login_required
def create_board():
    form = BoardForm()

    if form.validate_on_submit():
        board = Board(name=form.name.data, user_id=current_user.id)
        db.session.add(board)
        db.session.commit()
        flash('Доска успешно создана!', 'success')
        return redirect(url_for('index'))

    return render_template('create_board.html', form=form)

@app.route('/create_list/<int:board_id>', methods=['GET', 'POST'])
def create_list(board_id):
    board = Board.query.get_or_404(board_id)
    form = ListForm()

    if form.validate_on_submit():
        new_list = List(
            name=form.name.data,
            position=form.position.data,
            board_id=board.id
        )
        db.session.add(new_list)
        db.session.commit()
        flash('Список успешно добавлен!', 'success')
        return redirect(url_for('board', board_id=board.id))

    return render_template('create_list.html', form=form, board=board)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    uploads_path = os.path.join(app.config['UPLOAD_FOLDER'])
    return send_from_directory(uploads_path, filename)

@app.route('/create_card/<int:list_id>', methods=['GET', 'POST'])
def create_card(list_id):
    list_ = List.query.get_or_404(list_id)
    form = CardForm()

    form.list_id.choices = [(lst.id, lst.name) for lst in List.query.filter_by(board_id=list_.board_id).all()]

    if form.validate_on_submit():
        selected_list = List.query.get(form.list_id.data)

        due_date = None
        if form.due_date.data:
            due_date = datetime.strptime(form.due_date.data, '%Y-%m-%d')

        new_card = Card(
            title=form.title.data,
            description=form.description.data,
            due_date=due_date,
            list_id=selected_list.id,
            position=form.position.data
        )

        db.session.add(new_card)
        db.session.commit()
        flash('Карточка успешно добавлена!', 'success')
        return redirect(url_for('board', board_id=list_.board_id))

    return render_template('create_card.html', form=form, list=list_)



@app.route('/assign_user/<int:board_id>', methods=['POST'])
@login_required
def assign_user(board_id):
    board = Board.query.get_or_404(board_id)
    email = request.form.get('email')

    if not email:
        flash('Введите email пользователя.', 'danger')
        return redirect(url_for('board', board_id=board.id))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash('Пользователь с таким email не найден.', 'danger')
        return redirect(url_for('board', board_id=board.id))

    if user in board.users:
        flash('Этот пользователь уже добавлен на доску.', 'warning')
        return redirect(url_for('board', board_id=board.id))

    board.users.append(user)
    db.session.commit()

    flash(f'Пользователь {user.email} успешно добавлен на доску!', 'success')
    return redirect(url_for('board', board_id=board.id))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/card/<int:card_id>', methods=['GET', 'POST'])
@login_required
def card(card_id):
    card = Card.query.get_or_404(card_id)
    form = CommentForm()

    comments = Comment.query.filter_by(card_id=card_id).order_by(Comment.created_at.desc()).all()

    if form.validate_on_submit():
        attachment = form.save_attachment(form.file.data)

        new_comment = Comment(
            content=form.content.data,
            card_id=card_id,
            user_id=current_user.id,
            attachment=attachment
        )
        db.session.add(new_comment)
        db.session.commit()

        flash('Комментарий добавлен!', 'success')
        return redirect(url_for('card', card_id=card.id))

    return render_template('card.html', card=card, form=form, comments=comments, replace_youtube_links=replace_youtube_links)


@app.route('/card/complete/<int:card_id>')
def complete_card(card_id):
    card = Card.query.get_or_404(card_id)
    card.completed = True
    db.session.commit()
    flash('Карточка помечена как выполненная!', 'success')
    return redirect(url_for('board', board_id=card.list.board_id))

@app.route('/list/delete/<int:list_id>', methods=['POST'])
@login_required
def delete_list(list_id):
    list_ = List.query.get_or_404(list_id)
    board_id = list_.board_id

    Card.query.filter_by(list_id=list_.id).delete()

    db.session.delete(list_)
    db.session.commit()

    flash('Список удален!', 'success')
    return redirect(url_for('board', board_id=board_id))


@app.route('/card/delete/<int:card_id>', methods=['POST'])
@login_required
def delete_card(card_id):
    card = Card.query.get_or_404(card_id)
    board_id = card.list.board_id

    ChecklistItem.query.filter_by(card_id=card.id).delete()
    Comment.query.filter_by(card_id=card.id).delete()

    db.session.delete(card)
    db.session.commit()

    flash('Карточка и все связанные данные удалены!', 'success')
    return redirect(url_for('board', board_id=board_id))

@app.route('/card/toggle_completed/<int:card_id>', methods=['POST'])
def toggle_card_completed(card_id):
    card = Card.query.get_or_404(card_id)
    card.completed = not card.completed
    db.session.commit()
    flash('Состояние карточки обновлено!', 'success')
    return redirect(url_for('board', board_id=card.list.board_id))

@app.route('/card/<int:card_id>/checklist', methods=['POST'])
@login_required
def add_checklist_item(card_id):
    form = ChecklistItemForm()
    if form.validate_on_submit():
        item = ChecklistItem(text=form.text.data, card_id=card_id)
        db.session.add(item)
        db.session.commit()
        flash('Пункт добавлен в чек-лист!', 'success')
    return redirect(url_for('card', card_id=card_id))


@app.route('/checklist/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_checklist_item(item_id):
    item = ChecklistItem.query.get_or_404(item_id)
    item.completed = not item.completed
    db.session.commit()
    return redirect(url_for('card', card_id=item.card_id))


@app.route('/checklist/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_checklist_item(item_id):
    item = ChecklistItem.query.get_or_404(item_id)
    card_id = item.card_id
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('card', card_id=card_id))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    card_id = comment.card_id
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('card', card_id=card_id))

@app.route('/board/delete/<int:board_id>', methods=['POST'])
@login_required
def delete_board(board_id):
    board = Board.query.get_or_404(board_id)

    if board.user_id != current_user.id:
        flash('Вы не можете удалить эту доску!', 'danger')
        return redirect(url_for('index'))

    for list_ in board.lists:
        Card.query.filter_by(list_id=list_.id).delete()
        db.session.delete(list_)

    db.session.delete(board)
    db.session.commit()

    flash('Доска удалена!', 'success')
    return redirect(url_for('index'))
from flask import request, jsonify

@app.route('/update_card_date', methods=['POST'])
def update_card_date():
    data = request.get_json()
    card_id = data.get('card_id')
    new_date = data.get('new_date')

    card = Card.query.get(card_id)
    if card:
        card.due_date = new_date
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Карточка не найдена'})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


