"""
PARTE 1 - SERVIDOR REST
=======================
Servidor HTTP con Flask que expone:
  GET  /productos        -> retorna el catálogo completo
  POST /productos        -> registra un nuevo producto
  GET  /productos/<id>   -> retorna un producto por ID

Protocolo: HTTP/1.1 + JSON
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# ------------------------------------------------------------
# Base de datos en memoria (simulada)
# ------------------------------------------------------------
productos = [
    {"id": 1, "nombre": "Laptop Pro 15", "precio": 2500000, "stock": 10, "categoria": "Electrónica"},
    {"id": 2, "nombre": "Mouse Inalámbrico",  "precio": 85000,  "stock": 50, "categoria": "Periféricos"},
    {"id": 3, "nombre": "Teclado Mecánico",   "precio": 320000, "stock": 25, "categoria": "Periféricos"},
]
next_id = 4  # contador auto-incremental


# ------------------------------------------------------------
# Middleware: registra cada request en consola (muestra headers)
# ------------------------------------------------------------
@app.before_request
def log_request():
    print("\n" + "=" * 60)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {request.method} {request.path}")
    print("--- HEADERS ---")
    header_bytes = 0
    for k, v in request.headers:
        linea = f"  {k}: {v}"
        print(linea)
        header_bytes += len(k) + len(v) + 4  # ": " + "\r\n"
    print(f"--- Overhead estimado de headers: {header_bytes} bytes ---")


# ------------------------------------------------------------
# GET /productos  ->  listar catálogo
# ------------------------------------------------------------
@app.route("/productos", methods=["GET"])
def listar_productos():
    categoria = request.args.get("categoria")  # filtro opcional por query param

    resultado = productos
    if categoria:
        resultado = [p for p in productos if p["categoria"].lower() == categoria.lower()]

    respuesta = {
        "total": len(resultado),
        "productos": resultado
    }
    return jsonify(respuesta), 200


# ------------------------------------------------------------
# GET /productos/<id>  ->  obtener producto individual
# ------------------------------------------------------------
@app.route("/productos/<int:producto_id>", methods=["GET"])
def obtener_producto(producto_id):
    producto = next((p for p in productos if p["id"] == producto_id), None)
    if producto is None:
        return jsonify({"error": f"Producto con id={producto_id} no encontrado"}), 404
    return jsonify(producto), 200


# ------------------------------------------------------------
# POST /productos  ->  registrar nuevo producto
# ------------------------------------------------------------
@app.route("/productos", methods=["POST"])
def crear_producto():
    global next_id

    datos = request.get_json()
    if not datos:
        return jsonify({"error": "El cuerpo debe ser JSON válido"}), 400

    # Validar campos obligatorios
    campos_requeridos = ["nombre", "precio", "stock", "categoria"]
    faltantes = [c for c in campos_requeridos if c not in datos]
    if faltantes:
        return jsonify({"error": f"Faltan campos obligatorios: {faltantes}"}), 422

    nuevo = {
        "id":        next_id,
        "nombre":    datos["nombre"],
        "precio":    datos["precio"],
        "stock":     datos["stock"],
        "categoria": datos["categoria"],
    }
    productos.append(nuevo)
    next_id += 1

    return jsonify({"mensaje": "Producto creado exitosamente", "producto": nuevo}), 201


# ------------------------------------------------------------
# Punto de entrada
# ------------------------------------------------------------
if __name__ == "__main__":
    print("Servidor REST iniciado en http://localhost:5000")
    print("Endpoints disponibles:")
    print("  GET  http://localhost:5000/productos")
    print("  GET  http://localhost:5000/productos/<id>")
    print("  POST http://localhost:5000/productos")
    app.run(host="0.0.0.0", port=5000, debug=True)
