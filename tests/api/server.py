"""
Servidor Flask de pruebas para DownLoader Pro.
Expone la lógica del core via API REST y sirve interfaz web para pruebas UI.
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from flask import Flask, request, jsonify
from flask_cors import CORS
from src.core.database import Database
from src.core.config import load_config
from src.utils.validators import is_valid_url

app = Flask(__name__)
CORS(app)

_test_db_dir = tempfile.mkdtemp()
_test_db = Database(db_path=os.path.join(_test_db_dir, 'test.db'))

HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>DownLoader Pro - Test UI</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; margin: 0; padding: 20px; }
        h1 { color: #e94560; }
        h2 { color: #a0c4ff; font-size: 1.1rem; }
        section { background: #16213e; border-radius: 8px; padding: 16px; margin: 12px 0; }
        input { background: #0f3460; border: 1px solid #e94560; color: #fff; padding: 8px 12px; border-radius: 4px; width: 60%; font-size: 1rem; }
        button { background: #e94560; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 1rem; margin-left: 8px; }
        #validation-result { margin-top: 10px; font-weight: bold; min-height: 20px; }
        .valid { color: #4caf50; }
        .invalid { color: #e94560; }
        #stats-content, #downloads-content { color: #ccc; margin-top: 6px; }
    </style>
</head>
<body>
    <h1 id="app-title">DownLoader Pro</h1>
    <p id="app-subtitle">Sistema de gestion de descargas</p>

    <section id="url-form">
        <h2>Validar URL</h2>
        <input id="url-input" type="text" placeholder="Ingresa una URL para validar...">
        <button id="validate-btn" onclick="validateUrl()">Validar URL</button>
        <div id="validation-result"></div>
    </section>

    <section id="stats">
        <h2>Estadisticas</h2>
        <div id="stats-content">Cargando...</div>
    </section>

    <section id="downloads-list">
        <h2>Descargas Recientes</h2>
        <div id="downloads-content">Cargando...</div>
    </section>

    <script>
        async function validateUrl() {
            var url = document.getElementById('url-input').value;
            try {
                var res = await fetch('/api/validate-url', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: url})
                });
                var data = await res.json();
                var el = document.getElementById('validation-result');
                if (data.valid) {
                    el.textContent = 'URL valida \u2713';
                    el.className = 'valid';
                } else {
                    el.textContent = 'URL invalida \u2717';
                    el.className = 'invalid';
                }
            } catch(e) {
                document.getElementById('validation-result').textContent = 'Error de conexion';
            }
        }

        async function loadStats() {
            try {
                var res = await fetch('/api/stats');
                var data = await res.json();
                document.getElementById('stats-content').textContent =
                    'Total: ' + data.total + ' | Completadas: ' + data.completed + ' | Fallidas: ' + data.failed;
            } catch(e) {
                document.getElementById('stats-content').textContent = 'Error cargando estadisticas';
            }
        }

        async function loadDownloads() {
            try {
                var res = await fetch('/api/downloads');
                var data = await res.json();
                var el = document.getElementById('downloads-content');
                if (data.downloads.length === 0) {
                    el.textContent = 'Sin descargas registradas';
                } else {
                    el.textContent = data.downloads.length + ' descarga(s) encontrada(s)';
                }
            } catch(e) {
                document.getElementById('downloads-content').textContent = 'Error cargando descargas';
            }
        }

        window.onload = function() {
            loadStats();
            loadDownloads();
        };
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return HTML_PAGE


@app.route('/api/stats')
def stats():
    return jsonify(_test_db.get_statistics())


@app.route('/api/downloads')
def downloads():
    return jsonify({'downloads': _test_db.get_all_downloads()})


@app.route('/api/validate-url', methods=['POST'])
def validate_url():
    data = request.get_json(silent=True) or {}
    url = data.get('url', '')
    valid = is_valid_url(url)
    return jsonify({'valid': valid, 'url': url})


@app.route('/api/config')
def config():
    cfg = load_config()
    safe_keys = ['default_threads', 'chunk_size', 'max_retries', 'timeout',
                 'max_speed_kbps', 'notifications', 'scheduler_enabled']
    return jsonify({k: cfg[k] for k in safe_keys if k in cfg})


if __name__ == '__main__':
    port = int(os.environ.get('API_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
