# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, request
import time
import threading

app = Flask(__name__)

#Настройки по умолчанию (в минутах)
settings = {
    'pomodoro_minutes': 25,
    'short_break_minutes': 5,
    'long_break_minutes': 15
}

#Состояние таймера
timer_state = {
    'time_left': settings['pomodoro_minutes'] * 60,
    'is_running': False,
    'mode': 'pomodoro',
    'pomodoro_count': 0
}

def get_time_for_mode(mode):
    """Возвращает время в секундах для указанного режима с учётом настроек"""
    if mode == 'pomodoro':
        return settings['pomodoro_minutes'] * 60
    elif mode == 'short_break':
        return settings['short_break_minutes'] * 60
    elif mode == 'long_break':
        return settings['long_break_minutes'] * 60
    return 25 * 60

def format_time(seconds):
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

def run_timer():
    while timer_state['is_running'] and timer_state['time_left'] > 0:
        time.sleep(1)
        if timer_state['is_running']:
            timer_state['time_left'] -= 1

    if timer_state['time_left'] == 0 and timer_state['is_running'] is not False:
        timer_state['is_running'] = False

        if timer_state['mode'] == 'pomodoro':
            timer_state['pomodoro_count'] += 1
            if timer_state['pomodoro_count'] % 4 == 0:
                timer_state['mode'] = 'long_break'
                timer_state['time_left'] = get_time_for_mode('long_break')
            else:
                timer_state['mode'] = 'short_break'
                timer_state['time_left'] = get_time_for_mode('short_break')
        else:
            timer_state['mode'] = 'pomodoro'
            timer_state['time_left'] = get_time_for_mode('pomodoro')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_time')
def get_time():
    return jsonify({
        'time': format_time(timer_state['time_left']),
        'is_running': timer_state['is_running'],
        'mode': timer_state['mode']
    })

@app.route('/get_pomodoro_count')
def get_pomodoro_count():
    return jsonify({'count': timer_state['pomodoro_count']})

@app.route('/start')
def start_timer():
    if not timer_state['is_running']:
        timer_state['is_running'] = True
        thread = threading.Thread(target=run_timer)
        thread.daemon = True
        thread.start()
    return jsonify({'status': 'started'})

@app.route('/pause')
def pause_timer():
    timer_state['is_running'] = False
    return jsonify({'status': 'paused'})

@app.route('/reset')
def reset_timer():
    timer_state['is_running'] = False
    timer_state['mode'] = 'pomodoro'
    timer_state['time_left'] = get_time_for_mode('pomodoro')
    timer_state['pomodoro_count'] = 0
    return jsonify({'status': 'reset'})

@app.route('/set_mode/<mode>')
def set_mode(mode):
    if mode in ['pomodoro', 'short_break', 'long_break']:
        timer_state['is_running'] = False
        timer_state['mode'] = mode
        timer_state['time_left'] = get_time_for_mode(mode)
        return jsonify({'status': 'mode_changed', 'mode': mode})
    return jsonify({'status': 'error', 'message': 'Invalid mode'}), 400

#получить текущие настройки
@app.route('/get_settings')
def get_settings():
    return jsonify({
        'pomodoro_minutes': settings['pomodoro_minutes'],
        'short_break_minutes': settings['short_break_minutes'],
        'long_break_minutes': settings['long_break_minutes']
    })

#сохранить настройки
@app.route('/set_settings', methods=['POST'])
def set_settings():
    global settings
    data = request.get_json()
    settings['pomodoro_minutes'] = max(1, min(99, data.get('pomodoro_minutes', 25)))
    settings['short_break_minutes'] = max(1, min(30, data.get('short_break_minutes', 5)))
    settings['long_break_minutes'] = max(1, min(45, data.get('long_break_minutes', 15)))
    return jsonify({'status': 'ok'})

#сбросить текущий режим с учётом новых настроек (после сохранения)
@app.route('/reset_to_current_mode')
def reset_to_current_mode():
    timer_state['time_left'] = get_time_for_mode(timer_state['mode'])
    timer_state['is_running'] = False
    return jsonify({'status': 'reset_to_mode'})

if __name__ == '__main__':
    app.run(debug=True)