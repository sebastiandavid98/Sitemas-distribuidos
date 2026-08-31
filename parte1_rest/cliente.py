"""
PARTE 1 - CLIENTE REST
======================
Script que realiza peticiones al servidor REST y analiza:
  - Respuestas JSON
  - Overhead (sobrecarga) generado por los headers HTTP en cada petición
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"


# ----------------------------------------------------------------
# Utilidad: mide y muestra el overhead de headers HTTP
# ----------------------------------------------------------------
def analizar_overhead(response: requests.Response, label: str):
    """
    Calcula el tamaño aproximado en bytes de:
      - Headers de la PETICIÓN  (request)
      - Headers de la RESPUESTA (response)
      - Cuerpo de la respuesta (payload)
    """
    # ---- Headers de la petición ----
    req = response.request
    req_headers_raw = "\r\n".join(f"{k}: {v}" for k, v in req.headers.items())
    req_headers_bytes = len(req_headers_raw.encode("utf-8"))

    # ---- Body de la petición ----
    req_body_bytes = len(req.body.encode("utf-8")) if req.body else 0

    # ---- Headers de la respuesta ----
    resp_headers_raw = "\r\n".join(f"{k}: {v}" for k, v in response.headers.items())
    resp_headers_bytes = len(resp_headers_raw.encode("utf-8"))

    # ---- Body de la respuesta ----
    resp_body_bytes = len(response.content)

    total_bytes = req_headers_bytes + req_body_bytes + resp_headers_bytes + resp_body_bytes
    overhead_pct = ((req_headers_bytes + resp_headers_bytes) / total_bytes * 100) if total_bytes else 0

    print(f"\n{'─'*55}")
    print(f"  ANÁLISIS DE OVERHEAD HTTP  →  {label}")
    print(f"{'─'*55}")
    print(f"  [REQUEST]")
    print(f"    Headers  : {req_headers_bytes:>6} bytes")
    print(f"    Body     : {req_body_bytes:>6} bytes")
    print(f"  [RESPONSE]")
    print(f"    Headers  : {resp_headers_bytes:>6} bytes")
    print(f"    Body     : {resp_body_bytes:>6} bytes")
    print(f"  ─────────────────────────────────────")
    print(f"  Total transferido : {total_bytes:>6} bytes")
    print(f"  Overhead headers  : {req_headers_bytes + resp_headers_bytes:>6} bytes  ({overhead_pct:.1f}%)")
    print(f"{'─'*55}")


# ----------------------------------------------------------------
# 1) Listar todos los productos  →  GET /productos
# ----------------------------------------------------------------
def listar_productos():
    print("\n" + "="*55)
    print("  GET /productos  →  Listar catálogo completo")
    print("="*55)

    inicio = time.perf_counter()
    resp = requests.get(f"{BASE_URL}/productos")
    latencia = (time.perf_counter() - inicio) * 1000

    print(f"  Status     : {resp.status_code}")
    print(f"  Latencia   : {latencia:.2f} ms")

    datos = resp.json()
    print(f"  Productos  : {datos['total']}")
    for p in datos["productos"]:
        print(f"    [{p['id']}] {p['nombre']:25s} ${p['precio']:>10,}  stock:{p['stock']}")

    analizar_overhead(resp, "GET /productos")
    return datos["productos"]


# ----------------------------------------------------------------
# 2) Obtener producto por ID  →  GET /productos/<id>
# ----------------------------------------------------------------
def obtener_producto(producto_id: int):
    print("\n" + "="*55)
    print(f"  GET /productos/{producto_id}  →  Producto individual")
    print("="*55)

    inicio = time.perf_counter()
    resp = requests.get(f"{BASE_URL}/productos/{producto_id}")
    latencia = (time.perf_counter() - inicio) * 1000

    print(f"  Status   : {resp.status_code}")
    print(f"  Latencia : {latencia:.2f} ms")

    if resp.status_code == 200:
        p = resp.json()
        print(f"  Nombre   : {p['nombre']}")
        print(f"  Precio   : ${p['precio']:,}")
        print(f"  Stock    : {p['stock']}")
        print(f"  Categoría: {p['categoria']}")
    else:
        print(f"  Error    : {resp.json()['error']}")

    analizar_overhead(resp, f"GET /productos/{producto_id}")


# ----------------------------------------------------------------
# 3) Registrar nuevo producto  →  POST /productos
# ----------------------------------------------------------------
def crear_producto(nombre: str, precio: int, stock: int, categoria: str):
    print("\n" + "="*55)
    print("  POST /productos  →  Registrar nuevo producto")
    print("="*55)

    payload = {
        "nombre":    nombre,
        "precio":    precio,
        "stock":     stock,
        "categoria": categoria,
    }
    print(f"  Payload enviado: {json.dumps(payload, ensure_ascii=False)}")

    inicio = time.perf_counter()
    resp = requests.post(
        f"{BASE_URL}/productos",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    latencia = (time.perf_counter() - inicio) * 1000

    print(f"  Status   : {resp.status_code}")
    print(f"  Latencia : {latencia:.2f} ms")

    datos = resp.json()
    if resp.status_code == 201:
        p = datos["producto"]
        print(f"  ✓ Creado → ID={p['id']}  Nombre={p['nombre']}")
    else:
        print(f"  ✗ Error: {datos}")

    analizar_overhead(resp, "POST /productos")
    return datos


# ----------------------------------------------------------------
# 4) Comparativa overhead: una sola petición vs múltiples
# ----------------------------------------------------------------
def comparativa_overhead_multiple(n: int = 5):
    print("\n" + "="*55)
    print(f"  COMPARATIVA: overhead acumulado en {n} peticiones")
    print("="*55)

    total_header_bytes = 0
    total_body_bytes   = 0

    for i in range(n):
        resp = requests.get(f"{BASE_URL}/productos")
        req = resp.request

        req_headers = len("\r\n".join(f"{k}: {v}" for k, v in req.headers.items()).encode())
        resp_headers = len("\r\n".join(f"{k}: {v}" for k, v in resp.headers.items()).encode())
        body = len(resp.content)

        total_header_bytes += req_headers + resp_headers
        total_body_bytes   += body

    total = total_header_bytes + total_body_bytes
    pct   = (total_header_bytes / total * 100) if total else 0

    print(f"  Peticiones realizadas   : {n}")
    print(f"  Total bytes headers     : {total_header_bytes:>7} bytes")
    print(f"  Total bytes body (datos): {total_body_bytes:>7} bytes")
    print(f"  Total transferido       : {total:>7} bytes")
    print(f"  Overhead headers        : {pct:.1f}%")
    print()
    print("  CONCLUSIÓN:")
    print("  En HTTP/1.1 los headers se repiten ÍNTEGRAMENTE en cada")
    print("  petición (sin compresión por defecto). Con muchas peticiones")
    print("  el overhead puede superar el 50% del tráfico total,")
    print("  especialmente cuando el payload JSON es pequeño.")


# ----------------------------------------------------------------
# Menú principal
# ----------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "█"*55)
    print("  CLIENTE REST  –  Taller Sistemas Distribuidos")
    print("█"*55)

    # Operaciones básicas
    listar_productos()
    obtener_producto(1)
    obtener_producto(99)   # debería dar 404

    # Crear un producto nuevo
    crear_producto(
        nombre    = "Monitor UltraWide 34\"",
        precio    = 1850000,
        stock     = 8,
        categoria = "Electrónica"
    )

    # Verificar que el producto fue agregado
    listar_productos()

    # Análisis de overhead con múltiples peticiones
    comparativa_overhead_multiple(n=5)
