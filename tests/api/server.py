"""
Flask API minimal para pruebas de integracion - DownLoader Pro v2.1.0
ISO/IEC 29119 - Test Plan, seccion 4.2

Endpoints implementados:
  POST   /api/downloads          - Crear descarga
  GET    /api/downloads          - Listar descargas
  GET    /api/downloads/<id>     - Detalle de descarga
  POST   /api/downloads/<id>/pause   - Pausar descarga
  POST   /api/downloads/<id>/resume  - Reanudar descarga
  DELETE /api/downloads/<id>     - Eliminar descarga
  GET    /api/stats              - Estadisticas
  POST   /api/validate           - Validar URL
"""

import os
import sys
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS

# Agregar el directorio raiz al path para importar src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.database import Database
from src.utils.validators import is_valid_url

app = Flask(__name__)
CORS(app)

# Base de datos temporal para las pruebas
_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_file.close()
db = Database(db_path=_db_file.name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _not_found(download_id):
    return jsonify({"success": False, "error": f"Descarga {download_id} no encontrada"}), 404


def _ok(data=None, message=None, **kwargs):
    payload = {"success": True}
    if data is not None:
        payload["data"] = data
    if message:
        payload["message"] = message
    payload.update(kwargs)
    return jsonify(payload), 200


def _created(data):
    return jsonify({"success": True, "data": data}), 201


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/downloads", methods=["POST"])
def create_download():
    body = request.get_json(silent=True) or {}
    url = body.get("url", "")
    destination = body.get("destination", "/tmp")
    filename = body.get("filename", "pending")

    if not url:
        return jsonify({"success": False, "error": "URL requerida"}), 400

    if not is_valid_url(url):
        return jsonify({"success": False, "error": "URL invalida"}), 422

    download_id = db.create_download(url=url, filename=filename, destination=destination)
    record = db.get_download(download_id)
    return _created({"id": download_id, "download": record})


@app.route("/api/downloads", methods=["GET"])
def list_downloads():
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    status = request.args.get("status", None)

    all_records = db.get_all_downloads(status=status) if status else db.get_all_downloads()

    start = (page - 1) * limit
    paginated = all_records[start: start + limit]

    return _ok(
        data=paginated,
        total=len(all_records),
        page=page,
        limit=limit,
    )


@app.route("/api/downloads/<int:download_id>", methods=["GET"])
def get_download(download_id):
    record = db.get_download(download_id)
    if not record:
        return _not_found(download_id)
    return _ok(data=record)


@app.route("/api/downloads/<int:download_id>/pause", methods=["POST"])
def pause_download(download_id):
    record = db.get_download(download_id)
    if not record:
        return _not_found(download_id)

    db.update_download(download_id, status="PAUSED")
    updated = db.get_download(download_id)
    return _ok(data=updated, message="Descarga pausada")


@app.route("/api/downloads/<int:download_id>/resume", methods=["POST"])
def resume_download(download_id):
    record = db.get_download(download_id)
    if not record:
        return _not_found(download_id)

    db.update_download(download_id, status="DOWNLOADING")
    updated = db.get_download(download_id)
    return _ok(data=updated, message="Descarga reanudada")


@app.route("/api/downloads/<int:download_id>", methods=["DELETE"])
def delete_download(download_id):
    record = db.get_download(download_id)
    if not record:
        return _not_found(download_id)

    db.delete_download(download_id)
    return _ok(message=f"Descarga {download_id} eliminada")


@app.route("/api/stats", methods=["GET"])
def get_stats():
    stats = db.get_statistics()
    return _ok(data=stats)


@app.route("/api/validate", methods=["POST"])
def validate_url():
    body = request.get_json(silent=True) or {}
    url = body.get("url", "")
    valid = is_valid_url(url)
    return _ok(data={"url": url, "valid": valid})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
