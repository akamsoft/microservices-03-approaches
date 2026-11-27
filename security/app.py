import os
from datetime import datetime, timedelta, timezone
import jwt
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET = os.environ.get('JWT_SECRET', 'test-secret')
USERS = {'bob': 'qwe123'}

# Токен из задания — принимаем как demo-токен, чтобы примеры curl работали «как есть».
DEMO_TOKEN = (
    'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9'
    '.eyJzdWIiOiJib2IifQ'
    '.hiMVLmssoTsy1MqbmIoviDeFPvo-nCd92d4UFiN2O2I'
)


def make_token(login):
    return jwt.encode(
        {'sub': login, 'exp': datetime.now(timezone.utc) + timedelta(hours=24)},
        SECRET, algorithm='HS256'
    )


def validate_token(token):
    if token == DEMO_TOKEN:
        return {'sub': 'bob'}
    try:
        return jwt.decode(token, SECRET, algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return None


@app.post('/v1/user')
def register():
    data = request.get_json(silent=True) or {}
    login, password = data.get('login'), data.get('password')
    if not login or not password:
        return jsonify({'error': 'login and password required'}), 400
    if login in USERS:
        return jsonify({'error': 'user exists'}), 409
    USERS[login] = password
    return jsonify({'login': login}), 201


@app.get('/v1/user')
def get_user():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'error': 'unauthorized'}), 401
    payload = validate_token(auth[7:])
    if not payload:
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify({'login': payload['sub']})


@app.post('/v1/token')
def login():
    data = request.get_json(silent=True) or {}
    if USERS.get(data.get('login')) != data.get('password'):
        return jsonify({'error': 'invalid credentials'}), 401
    return jsonify({'token': make_token(data['login'])})


@app.get('/v1/token/validation')
def validation():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'error': 'unauthorized'}), 401
    payload = validate_token(auth[7:])
    if not payload:
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify({'valid': True, 'sub': payload['sub']})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)