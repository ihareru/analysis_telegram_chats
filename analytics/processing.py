from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
import json
import pandas as pd
from collections import Counter
from datetime import datetime



# Функция парсинга сообщений
def parse_messages(data):
    messages = []
    for msg in data.get('messages', []):
        if msg['type'] == 'message':
            if 'text_entities' in msg and isinstance(msg['text_entities'], list):
                text = " ".join(
                    [entity.get('text', '').lower() for entity in msg['text_entities'] if entity.get('type') == 'plain']
                )
            else:
                text = msg.get('text', '')

            messages.append({
                "id": msg.get("id"),
                "date": msg.get("date"),
                "from": msg.get("from"),
                "from_id": msg.get("from_id"),
                "text": text,
            })
    return pd.DataFrame(messages)


# Анализ чата
def analyze_chat(file_path, start_date=None, end_date=None):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df = parse_messages(data)
    if df.empty:
        return {
            "total_messages": 0,
            "unique_users": 0,
            "most_active_user": None,
            "top_words": []
        }

    df['date'] = pd.to_datetime(df['date'])
    if start_date:
        start_date = pd.to_datetime(start_date)
        df = df[df['date'] >= start_date]
    if end_date:
        end_date = pd.to_datetime(end_date)
        df = df[df['date'] <= end_date]


    total_messages = len(df)
    unique_users = df['from'].nunique()
    most_active_user = df['from'].value_counts().idxmax() if not df.empty else None
    word_counts_tmp = Counter(" ".join(df['text'].dropna()).split())
    word_counts = {}
    for key, value in word_counts_tmp.items():
        if len(key) > 3:
            word_counts[key] = value


    top_words = [{"word": word, "count": count} for word, count in Counter(word_counts).most_common(10)]

    return {
        "total_messages": total_messages,
        "unique_users": unique_users,
        "most_active_user": most_active_user,
        "top_words": top_words
    }
