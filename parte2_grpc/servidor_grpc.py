"""
PARTE 2 - SERVIDOR gRPC
========================
Implementa el servicio 'Inventario' definido en inventario.proto.
Transporta los datos usando Protocol Buffers (binario) sobre HTTP/2.

Métodos implementados:
  - ObtenerProducto     (Unary RPC)
  - ListarProductos     (Unary RPC)
  - CrearProducto       (Unary RPC)
  - TransmitirCatalogo  (Server-Side Streaming RPC)

Para generar los stubs a partir del .proto ejecutar:
  python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. inventario.proto
"""

import grpc
import time
import logging
from concurrent import futures

# Stubs generados por protoc
import inventario_pb2
import inventario_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GRPC-SERVER] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Base de datos en memoria
# ---------------------------------------------------------------
_productos = [
    inventario_pb2.Producto(id=1, nombre="Laptop Pro 15",      precio=2500000, stock=10, categoria="Electrónica"),
    inventario_pb2.Producto(id=2, nombre="Mouse Inalámbrico",  precio=85000,   stock=50, categoria="Periféricos"),
    inventario_pb2.Producto(id=3, nombre="Teclado Mecánico",   precio=320000,  stock=25, categoria="Periféricos"),
]
_next_id = 4


# ---------------------------------------------------------------
# Implementación del Servicer (lógica de negocio)
# ---------------------------------------------------------------
class InventarioServicer(inventario_pb2_grpc.InventarioServicer):

    # ----------------------------------------------------------
    # ObtenerProducto  →  Unary RPC
    # ----------------------------------------------------------
    def ObtenerProducto(self, request, context):
        log.info(f"ObtenerProducto  id={request.id}")

        producto = next((p for p in _productos if p.id == request.id), None)

        if producto is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Producto con id={request.id} no encontrado")
            return inventario_pb2.Producto()

        log.info(f"  → Retornando: {producto.nombre}")
        return producto

    # ----------------------------------------------------------
    # ListarProductos  →  Unary RPC
    # ----------------------------------------------------------
    def ListarProductos(self, request, context):
        log.info("ListarProductos  (catálogo completo)")

        catalogo = inventario_pb2.CatalogoProductos(
            total=len(_productos),
            productos=_productos
        )
        log.info(f"  → {catalogo.total} productos enviados")
        return catalogo

    # ----------------------------------------------------------
    # CrearProducto  →  Unary RPC
    # ----------------------------------------------------------
    def CrearProducto(self, request, context):
        global _next_id, _productos
        log.info(f"CrearProducto  nombre='{request.nombre}'  precio={request.precio}")

        # Validaciones básicas
        if not request.nombre.strip():
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("El campo 'nombre' es obligatorio")
            return inventario_pb2.Confirmacion(exito=False, mensaje="Nombre vacío")

        if request.precio <= 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("El precio debe ser mayor a 0")
            return inventario_pb2.Confirmacion(exito=False, mensaje="Precio inválido")

        nuevo = inventario_pb2.Producto(
            id        = _next_id,
            nombre    = request.nombre,
            precio    = request.precio,
            stock     = request.stock,
            categoria = request.categoria,
        )
        _productos.append(nuevo)
        _next_id += 1

        log.info(f"  → Producto creado con id={nuevo.id}")
        return inventario_pb2.Confirmacion(
            exito    = True,
            mensaje  = f"Producto '{nuevo.nombre}' registrado con id={nuevo.id}",
            producto = nuevo
        )

    # ----------------------------------------------------------
    # TransmitirCatalogo  →  Server-Side Streaming RPC
    # Envía cada producto como un mensaje independiente
    # ----------------------------------------------------------
    def TransmitirCatalogo(self, request, context):
        log.info("TransmitirCatalogo  (streaming iniciado)")
        for producto in _productos:
            log.info(f"  → Streaming: {producto.nombre}")
            time.sleep(0.1)   # simula procesamiento
            yield producto
        log.info("TransmitirCatalogo  (streaming finalizado)")


# ---------------------------------------------------------------
# Arranque del servidor
# ---------------------------------------------------------------
def iniciar_servidor(puerto: int = 50051):
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.max_send_message_length",    10 * 1024 * 1024),
            ("grpc.max_receive_message_length", 10 * 1024 * 1024),
        ]
    )

    inventario_pb2_grpc.add_InventarioServicer_to_server(
        InventarioServicer(), server
    )

    server.add_insecure_port(f"[::]:{puerto}")
    server.start()

    log.info(f"Servidor gRPC escuchando en puerto {puerto} (HTTP/2 + Protocol Buffers)")
    log.info("Métodos disponibles:")
    log.info("  ObtenerProducto     (Unary)")
    log.info("  ListarProductos     (Unary)")
    log.info("  CrearProducto       (Unary)")
    log.info("  TransmitirCatalogo  (Server Streaming)")
    log.info("Ctrl+C para detener el servidor")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        log.info("Deteniendo servidor gRPC...")
        server.stop(grace=5)
        log.info("Servidor detenido.")


if __name__ == "__main__":
    iniciar_servidor()
