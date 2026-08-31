"""
PARTE 2 - CLIENTE gRPC
=======================
Invoca los métodos remotos del servicio Inventario y realiza
un análisis comparativo entre gRPC y REST en cuanto a:
  - Tamaño del payload (binario vs JSON)
  - Latencia de llamada
  - Ventajas arquitectónicas
"""

import grpc
import time
import json
import sys

import inventario_pb2
import inventario_pb2_grpc


GRPC_HOST = "localhost:50051"


# ---------------------------------------------------------------
# Utilidad: serializa un mensaje Protobuf y mide su tamaño
# ---------------------------------------------------------------
def tamaño_binario(msg) -> int:
    """Retorna el tamaño en bytes de un mensaje Protocol Buffers serializado."""
    return len(msg.SerializeToString())


def tamaño_json(obj: dict) -> int:
    """Retorna el tamaño en bytes de un dict serializado como JSON."""
    return len(json.dumps(obj, ensure_ascii=False).encode("utf-8"))


def separador(titulo: str = ""):
    linea = "=" * 60
    if titulo:
        print(f"\n{linea}")
        print(f"  {titulo}")
        print(linea)
    else:
        print(linea)


# ---------------------------------------------------------------
# 1) ObtenerProducto  →  Unary RPC
# ---------------------------------------------------------------
def obtener_producto(stub, producto_id: int):
    separador(f"ObtenerProducto  (id={producto_id})")

    inicio = time.perf_counter()
    try:
        resp = stub.ObtenerProducto(inventario_pb2.SolicitudProducto(id=producto_id))
        latencia = (time.perf_counter() - inicio) * 1000

        print(f"  ID       : {resp.id}")
        print(f"  Nombre   : {resp.nombre}")
        print(f"  Precio   : ${resp.precio:,.0f}")
        print(f"  Stock    : {resp.stock}")
        print(f"  Categoría: {resp.categoria}")
        print(f"  Latencia : {latencia:.2f} ms")

        # Comparativa de tamaño de payload
        bytes_proto = tamaño_binario(resp)
        json_equiv  = {"id": resp.id, "nombre": resp.nombre,
                       "precio": resp.precio, "stock": resp.stock,
                       "categoria": resp.categoria}
        bytes_json  = tamaño_json(json_equiv)

        print(f"\n  --- Comparativa de serialización ---")
        print(f"  Payload Protobuf : {bytes_proto:>4} bytes")
        print(f"  Payload JSON     : {bytes_json:>4} bytes")
        ahorro = (1 - bytes_proto / bytes_json) * 100
        print(f"  Ahorro gRPC      : {ahorro:.1f}% menos datos")

    except grpc.RpcError as e:
        latencia = (time.perf_counter() - inicio) * 1000
        print(f"  ✗ Error gRPC [{e.code()}]: {e.details()}")
        print(f"  Latencia: {latencia:.2f} ms")


# ---------------------------------------------------------------
# 2) ListarProductos  →  Unary RPC
# ---------------------------------------------------------------
def listar_productos(stub):
    separador("ListarProductos  (catálogo completo)")

    inicio = time.perf_counter()
    resp = stub.ListarProductos(inventario_pb2.SolicitudVacia())
    latencia = (time.perf_counter() - inicio) * 1000

    print(f"  Total    : {resp.total} productos")
    print(f"  Latencia : {latencia:.2f} ms")
    print()
    for p in resp.productos:
        print(f"    [{p.id}] {p.nombre:25s}  ${p.precio:>10,.0f}  stock:{p.stock}")

    # Comparativa de tamaño del catálogo completo
    bytes_proto = tamaño_binario(resp)
    json_lista  = [{"id": p.id, "nombre": p.nombre, "precio": p.precio,
                    "stock": p.stock, "categoria": p.categoria}
                   for p in resp.productos]
    json_obj    = {"total": resp.total, "productos": json_lista}
    bytes_json  = tamaño_json(json_obj)

    print(f"\n  --- Comparativa de serialización (catálogo) ---")
    print(f"  Payload Protobuf : {bytes_proto:>5} bytes")
    print(f"  Payload JSON     : {bytes_json:>5} bytes")
    ahorro = (1 - bytes_proto / bytes_json) * 100
    print(f"  Ahorro gRPC      : {ahorro:.1f}% menos datos")


# ---------------------------------------------------------------
# 3) CrearProducto  →  Unary RPC
# ---------------------------------------------------------------
def crear_producto(stub, nombre, precio, stock, categoria):
    separador("CrearProducto  (nuevo producto)")

    solicitud = inventario_pb2.NuevoProducto(
        nombre=nombre, precio=precio, stock=stock, categoria=categoria
    )
    print(f"  Enviando → nombre='{nombre}'  precio={precio}  stock={stock}")

    # Tamaño de la solicitud serializada
    bytes_req_proto = tamaño_binario(solicitud)
    bytes_req_json  = tamaño_json({"nombre": nombre, "precio": precio,
                                   "stock": stock, "categoria": categoria})

    inicio = time.perf_counter()
    resp   = stub.CrearProducto(solicitud)
    latencia = (time.perf_counter() - inicio) * 1000

    print(f"  Éxito    : {resp.exito}")
    print(f"  Mensaje  : {resp.mensaje}")
    print(f"  Latencia : {latencia:.2f} ms")
    if resp.exito:
        p = resp.producto
        print(f"  Producto → ID={p.id}  Nombre={p.nombre}")

    print(f"\n  --- Comparativa solicitud ---")
    print(f"  Request Protobuf : {bytes_req_proto:>4} bytes")
    print(f"  Request JSON     : {bytes_req_json:>4} bytes")


# ---------------------------------------------------------------
# 4) TransmitirCatalogo  →  Server-Side Streaming RPC
# ---------------------------------------------------------------
def transmitir_catalogo(stub):
    separador("TransmitirCatalogo  (Server-Side Streaming)")
    print("  El servidor transmite cada producto como mensaje independiente:\n")

    inicio = time.perf_counter()
    count  = 0
    total_bytes_proto = 0
    total_bytes_json  = 0

    for producto in stub.TransmitirCatalogo(inventario_pb2.SolicitudVacia()):
        count += 1
        total_bytes_proto += tamaño_binario(producto)
        total_bytes_json  += tamaño_json({"id": producto.id, "nombre": producto.nombre,
                                          "precio": producto.precio, "stock": producto.stock,
                                          "categoria": producto.categoria})
        print(f"  ← Recibido stream #{count}: [{producto.id}] {producto.nombre}")

    latencia_total = (time.perf_counter() - inicio) * 1000
    print(f"\n  Total mensajes recibidos : {count}")
    print(f"  Tiempo total streaming   : {latencia_total:.2f} ms")
    print(f"  Bytes Protobuf totales   : {total_bytes_proto}")
    print(f"  Bytes JSON equivalentes  : {total_bytes_json}")


# ---------------------------------------------------------------
# 5) Análisis comparativo gRPC vs REST
# ---------------------------------------------------------------
def analisis_comparativo():
    separador("ANÁLISIS COMPARATIVO: gRPC vs REST")

    tabla = [
        ("Característica",          "REST (HTTP/1.1)",              "gRPC (HTTP/2)"),
        ("─"*24,                    "─"*28,                         "─"*28),
        ("Protocolo transporte",     "HTTP/1.1",                     "HTTP/2"),
        ("Serialización",            "JSON (texto)",                 "Protocol Buffers (binario)"),
        ("Tamaño payload",           "Mayor (~3-5x más grande)",     "Menor (datos compactos)"),
        ("Compresión headers",       "No (se repiten completos)",    "HPACK (compresión HTTP/2)"),
        ("Multiplexación",           "No (1 req/conexión)",          "Sí (múltiples streams)"),
        ("Tipado de datos",          "Dinámico (sin contrato fijo)", "Estricto (definido en .proto)"),
        ("Streaming",                "Limitado (SSE, polling)",      "Bidireccional nativo"),
        ("Generación de código",     "Manual o con OpenAPI",         "Automática desde .proto"),
        ("Legibilidad humana",       "Alta (JSON legible)",          "Baja (binario)"),
        ("Latencia (microservicios)","Mayor (overhead texto+headers)","Menor (~40% más rápido)"),
        ("Soporte navegadores",      "Nativo",                       "Requiere gRPC-Web proxy"),
        ("Casos de uso ideales",     "APIs públicas, CRUD simple",   "Microservicios internos"),
    ]

    for fila in tabla:
        print(f"  {fila[0]:<25} {fila[1]:<30} {fila[2]}")

    print("""
  CONCLUSIÓN:
  ──────────────────────────────────────────────────────────
  gRPC supera a REST en entornos de microservicios con alto
  tráfico por tres razones principales:

  1. EFICIENCIA DE DATOS: Protocol Buffers serializa los datos
     en formato binario compacto. Un mensaje que en JSON ocupa
     150 bytes puede ocupar solo 40 bytes en Protobuf, reduciendo
     el ancho de banda hasta un 70% en escenarios reales.

  2. MULTIPLEXACIÓN HTTP/2: gRPC corre sobre HTTP/2, que permite
     enviar múltiples llamadas RPC simultáneas sobre una sola
     conexión TCP. REST sobre HTTP/1.1 requiere una conexión
     por petición (o keep-alive con pipelining limitado),
     generando mayor latencia y uso de recursos.

  3. CONTRATO ESTRICTO CON .proto: El archivo .proto actúa como
     contrato entre servicios. El código cliente/servidor se
     genera automáticamente, elimina errores de integración y
     facilita el versionado de APIs entre equipos independientes.

  REST sigue siendo superior para APIs públicas consumidas
  por navegadores y clientes externos, gracias a su simplicidad
  y soporte universal.
  ──────────────────────────────────────────────────────────
""")


# ---------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("█" * 60)
    print("  CLIENTE gRPC  –  Taller Sistemas Distribuidos")
    print("█" * 60)
    print(f"  Conectando a {GRPC_HOST} ...\n")

    with grpc.insecure_channel(GRPC_HOST) as canal:
        stub = inventario_pb2_grpc.InventarioStub(canal)

        # Operaciones básicas
        obtener_producto(stub, 1)
        obtener_producto(stub, 2)
        obtener_producto(stub, 99)   # caso NOT_FOUND

        listar_productos(stub)

        crear_producto(
            stub,
            nombre    = "Webcam 4K",
            precio    = 420000,
            stock     = 15,
            categoria = "Periféricos"
        )

        # Verificar que el nuevo producto aparece
        listar_productos(stub)

        # Streaming
        transmitir_catalogo(stub)

        # Análisis comparativo final
        analisis_comparativo()
