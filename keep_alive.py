from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "🤖 Sistema ESP32 activo y funcionando!"

@app.route('/status')
def status():
    return {
        "status": "running",
        "service": "ESP32 Control Inteligente",
        "version": "1.0"
    }

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()