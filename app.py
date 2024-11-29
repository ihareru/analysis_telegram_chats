from flask import Flask, request, jsonify, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

app = Flask(__name__)


UPLOAD_FOLDER = 'uploaded_chats'
ALLOWED_EXTENSIONS = {'json'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


logging.basicConfig(level=logging.INFO)


os.makedirs(UPLOAD_FOLDER, exist_ok=True)



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'Поле файла отсутствует'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Файл не был выбран'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)


        file.save(filepath)
        logging.info(f'Файл {filename} успешно загружен.')



        return jsonify({'status': 'success', 'filename': filename}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Недопустимый формат файла'}), 400



@app.route('/export', methods=['GET'])
def export_analysis():
    chat_id = request.args.get('chat_id')
    format = request.args.get('format', default='csv')


    file_path = os.path.join(UPLOAD_FOLDER, f"{chat_id}.json")

    if not os.path.isfile(file_path):
        return jsonify({'status': 'error', 'message': 'Файл не существует'}), 404


    try:

        df = pd.read_json(file_path)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Некорректный формат файла'}), 400


    if df.empty:
        return jsonify({'status': 'error', 'message': 'Нет данных для экспорта'}), 400


    output_file = os.path.join(UPLOAD_FOLDER, f"{chat_id}_analytics.csv")
    df.to_csv(output_file, index=False)


    return send_file(output_file, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
