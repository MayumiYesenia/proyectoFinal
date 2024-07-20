import json
import requests
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

API_CREATE_USER = 'https://4onwavnlwe.execute-api.us-east-1.amazonaws.com/prod/usuario/crear'
API_LOGIN = 'https://4onwavnlwe.execute-api.us-east-1.amazonaws.com/prod/usuario/login'
API_LIST_VIDEOS = 'https://ej56wk4029.execute-api.us-east-1.amazonaws.com/prod/video/listarvideo'
API_ADD_TO_FAVORITES = 'https://ej56wk4029.execute-api.us-east-1.amazonaws.com/prod/video/favorito'

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    correo = data.get('correo')
    password = data.get('password')
    
    if not correo or not password:
        return jsonify(message='Correo y contraseña son necesarios'), 400
    
    try:
        response = requests.post(API_CREATE_USER, json={
            'correo': correo,
            'password': password
        })

        logging.debug(f"API Response: {response.text}")

        if response.status_code == 200:
            response_json = response.json()
            body = response_json.get('body')
            
            if body:
                logging.debug(f"Response Body: {body}")
                try:
                    body_data = json.loads(body)
                    user_id = body_data.get('user_id')
                    
                    if user_id:
                        return jsonify(message='Usuario registrado exitosamente', user_id=user_id), 200
                    else:
                        return jsonify(message='Error en el registro', error='Respuesta sin user_id'), 500
                except json.JSONDecodeError as e:
                    logging.error(f"Error decodificando JSON: {e}")
                    return jsonify(message='Error en el registro', error='Cuerpo de respuesta no es un JSON válido'), 500
            else:
                logging.error("Cuerpo de la respuesta no encontrado")
                return jsonify(message='Error en el registro', error='Respuesta sin cuerpo'), 500
        else:
            return jsonify(message='Error en el registro', error=response.json().get('message')), response.status_code
    
    except requests.exceptions.RequestException as e:
        return jsonify(message='Error en la solicitud', error=str(e)), 500

@app.route('/login', methods=['POST'])
def login_post():
    data = request.json
    correo = data.get('correo')
    password = data.get('password')
    user_id = data.get('user_id')

    if not correo or not password or not user_id:
        return jsonify(message='Correo, contraseña y user_id son necesarios'), 400

    try:
        response = requests.post(API_LOGIN, json={
            'correo': correo,
            'password': password,
            'user_id': user_id
        })

        logging.debug(f"API Response: {response.text}")

        if response.status_code == 200:
            response_json = response.json()
            logging.debug(f"Response JSON: {response_json}")

            token = response_json.get('token')
            if token:
                message = 'Login exitoso. Gracias por volver'
                return jsonify(message=message, token=token), 200
            else:
                return jsonify(message='Error en el login', error='Respuesta incompleta'), 500
        else:
            return jsonify(message='Error en el login', error=response.json().get('message')), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify(message='Error en la solicitud', error=str(e)), 500


@app.route('/videos')
def videos():
    token = request.args.get('token')
    if not token:
        return redirect(url_for('login'))
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    try:
        response = requests.get(API_LIST_VIDEOS, headers=headers)
        if response.status_code == 200:
            videos = response.json().get('response', {}).get('videos', [])
            return render_template('videos.html', videos=videos, token=token)
        else:
            return redirect(url_for('login'))
    except requests.exceptions.RequestException as e:
        return jsonify(message='Error en la solicitud de videos', error=str(e)), 500

@app.route('/video/<string:video_id>')
def video_detail(video_id):
    token = request.args.get('token')
    if not token:
        return redirect(url_for('login'))
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    try:
        response = requests.get(API_LIST_VIDEOS, headers=headers)
        if response.status_code == 200:
            videos = response.json().get('response', {}).get('videos', [])
            video = next((v for v in videos if v['video_id'] == video_id), None)
            if video:
                return render_template('video_detail.html', video=video, token=token)
            else:
                return "Video no encontrado", 404
        else:
            return redirect(url_for('login'))
    except requests.exceptions.RequestException as e:
        return jsonify(message='Error en la solicitud de video', error=str(e)), 500

@app.route('/video/add_to_favorites', methods=['POST'])
def add_to_favorites():
    data = request.json
    user_id = data.get('user_id')
    video_id = data.get('video_id')
    token = data.get('token')

    if not user_id or not video_id:
        return jsonify(message='Se requieren ID de usuario y video'), 400

    if not token:
        return jsonify(message='Token es necesario para agregar a favoritos'), 401

    headers = {'Authorization': f'Bearer {token}'}
    try:
        response = requests.post(API_ADD_TO_FAVORITES, json={'user_id': user_id, 'video_id': video_id}, headers=headers)
        if response.status_code == 200:
            return jsonify(message='Video agregado a favoritos'), 200
        else:
            return jsonify(message='Error al agregar video a favoritos', error=response.json().get('message')), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify(message='Error en la solicitud', error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)
