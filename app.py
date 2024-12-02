from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
import json
import pandas as pd
from collections import Counter
from datetime import datetime
from analytics.processing import parse_messages, analyze_chat

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

#
# # Функция парсинга сообщений
# def parse_messages(data):
#     messages = []
#     for msg in data.get('messages', []):
#         if msg['type'] == 'message':
#             if 'text_entities' in msg and isinstance(msg['text_entities'], list):
#                 text = " ".join(
#                     [entity.get('text', '') for entity in msg['text_entities'] if entity.get('type') == 'plain']
#                 )
#             else:
#                 text = msg.get('text', '')
#
#             messages.append({
#                 "id": msg.get("id"),
#                 "date": msg.get("date"),
#                 "from": msg.get("from"),
#                 "from_id": msg.get("from_id"),
#                 "text": text,
#             })
#     return pd.DataFrame(messages)
#
#
# # Анализ чата
# def analyze_chat(file_path, start_date=None, end_date=None):
#     with open(file_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)
#
#     df = parse_messages(data)
#     if df.empty:
#         return {
#             "total_messages": 0,
#             "unique_users": 0,
#             "most_active_user": None,
#             "top_words": []
#         }
#
#     df['date'] = pd.to_datetime(df['date'])
#     if start_date:
#         start_date = pd.to_datetime(start_date)
#         df = df[df['date'] >= start_date]
#     if end_date:
#         end_date = pd.to_datetime(end_date)
#         df = df[df['date'] <= end_date]
#
#     total_messages = len(df)
#     unique_users = df['from'].nunique()
#     most_active_user = df['from'].value_counts().idxmax() if not df.empty else None
#     word_counts = Counter(" ".join(df['text'].dropna()).split())
#     top_words = [{"word": word, "count": count} for word, count in word_counts.most_common(10)]
#
#     return {
#         "total_messages": total_messages,
#         "unique_users": unique_users,
#         "most_active_user": most_active_user,
#         "top_words": top_words
#     }
#

# Эндпоинт для загрузки нескольких файлов
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'files' not in request.files:
            return jsonify({"status": "error", "message": "Файлы не прикреплены"}), 400

        files = request.files.getlist('files')
        uploaded_files = []
        for file in files:
            if file.filename.endswith('.json'):
                data = json.load(file)
                chat_id = data.get("id")
                if not chat_id:
                    return jsonify({"status": "error", "message": "Некорректный JSON: отсутствует поле id"}), 400

                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{chat_id}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                uploaded_files.append(chat_id)

        return jsonify({"status": "success", "uploaded_files": uploaded_files}), 200
    return render_template('upload.html')


# Эндпоинт для получения статистики
@app.route('/stats', methods=['GET'])
def stats():
    chat_id = request.args.get('chat_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{chat_id}.json")

    if not os.path.exists(file_path):
        return f"<h1>Файл с ID {chat_id} не найден.</h1>", 404

    stats = analyze_chat(file_path, start_date=start_date, end_date=end_date)
    return render_template('stats.html', stats=stats)


# Эндпоинт для поиска сообщений
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        chat_id = request.form.get('chat_id')
        keyword = request.form.get('keyword', '').lower()
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{chat_id}.json")

        if not os.path.exists(file_path):
            return f"<h1>Файл с ID {chat_id} не найден.</h1>", 404

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        df = parse_messages(data)
        df['text'] = df['text'].str.lower()

        results = df[df['text'].str.contains(keyword, na=False)]
        return render_template('search_results.html', results=results.to_dict(orient='records'))

    return render_template('search.html')


# Эндпоинт для экспорта данных
@app.route('/export', methods=['GET'])
def export():
    chat_id = request.args.get('chat_id')
    file_format = request.args.get('format', 'json').lower()
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{chat_id}.json")

    if not os.path.exists(file_path):
        return f"<h1>Файл с ID {chat_id} не найден.</h1>", 404

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df = parse_messages(data)
    export_path = None
    if file_format == 'csv':
        export_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{chat_id}.csv")
        df.to_csv(export_path, index=False)
    elif file_format == 'json':
        export_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{chat_id}_export.json")
        df.to_json(export_path, orient='records', force_ascii=False)
    else:
        return f"<h1>Неверный формат экспорта.</h1>", 400

    return f"<h1>Данные успешно экспортированы в файл: {export_path}</h1>"


if __name__ == '__main__':
    app.run(debug=True)
