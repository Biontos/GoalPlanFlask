import pytest
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user
from werkzeug.security import generate_password_hash
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecretkey'
db = SQLAlchemy(app)
login_manager = LoginManager(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100), nullable=False)

@app.route('/create_board', methods=['POST'])
def create_board():
    board_name = request.form['name']
    return jsonify(message="Доска успешно создана!")

@app.route('/create_card/<int:list_id>', methods=['POST'])
def create_card(list_id):
    title = request.form['title']
    return jsonify(message="Карточка успешно добавлена!")

@app.route('/card/complete/<int:card_id>', methods=['POST'])
def complete_card(card_id):
    return jsonify(message="Карточка помечена как выполненная!")

@app.route('/card/delete/<int:card_id>', methods=['POST'])
def delete_card(card_id):
    return jsonify(message="Карточка удалена!")

@pytest.fixture(scope='module')
def new_user():
    user = User(name='Test User', email='testuser@example.com', password='testpassword')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    with app.app_context():
        db.create_all()
    yield client
    with app.app_context():
        db.session.remove()
        db.drop_all()

def test_create_board(client):
    response = client.post('/create_board', data={'name': 'Test Board'})
    assert response.status_code == 200
    response_data = json.loads(response.get_data(as_text=True))
    assert response_data['message'] == 'Доска успешно создана!'

def test_create_card(client):
    client.post('/create_board', data={'name': 'Test Board'})
    response = client.post('/create_card/1', data={
        'title': 'Test Card',
        'description': 'Test Card Description',
        'due_date': '2024-12-01',
        'position': 1,
        'list_id': 1
    })
    assert response.status_code == 200
    response_data = json.loads(response.get_data(as_text=True))
    assert response_data['message'] == 'Карточка успешно добавлена!'

def test_complete_card(client):
    client.post('/create_board', data={'name': 'Test Board'})
    client.post('/create_card/1', data={
        'title': 'Test Card',
        'description': 'Test Card Description',
        'due_date': '2024-12-01',
        'position': 1,
        'list_id': 1
    })
    response = client.post('/card/complete/1')
    assert response.status_code == 200
    response_data = json.loads(response.get_data(as_text=True))
    assert response_data['message'] == 'Карточка помечена как выполненная!'

def test_delete_card(client):
    client.post('/create_board', data={'name': 'Test Board'})
    client.post('/create_card/1', data={
        'title': 'Test Card',
        'description': 'Test Card Description',
        'due_date': '2024-12-01',
        'position': 1,
        'list_id': 1
    })
    response = client.post('/card/delete/1')
    assert response.status_code == 200
    response_data = json.loads(response.get_data(as_text=True))
    assert response_data['message'] == 'Карточка удалена!'
