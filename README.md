# Taller — Sistemas Distribuidos
## Protocolos: REST · gRPC · WebSockets

---

## Estructura del proyecto

```
taller-distribuidos/
├── requirements.txt            ← dependencias Python
│
├── parte1_rest/
│   ├── servidor.py             ← Servidor HTTP/1.1 con Flask
│   └── cliente.py              ← Cliente REST + análisis overhead
│
├── parte2_grpc/
│   ├── inventario.proto        ← Contrato del servicio (Protocol Buffers)
│   ├── generar_stubs.py        ← Compila el .proto y genera los stubs
│   ├── servidor_grpc.py        ← Servidor gRPC (HTTP/2 + Protobuf)
│   └── cliente_grpc.py         ← Cliente gRPC + análisis comparativo
│
└── README.md
```

---

## Requisitos

- Python 3.9 o superior
- pip

---

## Instalación

```bash
# 1. Crear entorno virtual (recomendado)
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt
```

---

## Parte 1 — REST (HTTP/1.1)

### Iniciar el servidor

```bash
cd parte1_rest
python servidor.py
```

El servidor queda escuchando en `http://localhost:5000`.

### Ejecutar el cliente

Abrir **otra terminal** (con el entorno virtual activo):

```bash
cd parte1_rest
python cliente.py
```

### Endpoints disponibles

| Método | URL                    | Descripción                    |
|--------|------------------------|-------------------------------|
| GET    | /productos             | Lista el catálogo completo     |
| GET    | /productos/`<id>`      | Obtiene un producto por ID     |
| POST   | /productos             | Registra un nuevo producto     |

### Ejemplo con curl

```bash
# Listar todos los productos
curl http://localhost:5000/productos

# Obtener producto con id=1
curl http://localhost:5000/productos/1

# Crear un producto nuevo
curl -X POST http://localhost:5000/productos \
     -H "Content-Type: application/json" \
     -d '{"nombre":"Audífonos BT","precio":250000,"stock":30,"categoria":"Audio"}'
```

### Análisis de overhead HTTP

El cliente mide en cada petición:
- Bytes de los headers del **request**
- Bytes de los headers del **response**
- Bytes del body (payload útil)
- Porcentaje de overhead respecto al total transferido

**Resultado típico observado:**

```
  [REQUEST]
    Headers  :   350 bytes
    Body     :     0 bytes
  [RESPONSE]
    Headers  :   215 bytes
    Body     :   180 bytes
  Total transferido :   745 bytes
  Overhead headers  :   565 bytes  (75.8%)
```

> En HTTP/1.1 los headers se envían **sin comprimir** en cada petición,
> representando entre el 40 % y el 80 % del tráfico total cuando
> el payload JSON es pequeño.

---

## Parte 2 — gRPC (HTTP/2 + Protocol Buffers)

### Paso 1: compilar el archivo .proto

```bash
cd parte2_grpc
python generar_stubs.py
```

Esto genera en la misma carpeta:
- `inventario_pb2.py`       — clases de mensajes
- `inventario_pb2_grpc.py`  — stub cliente y servicer

### Paso 2: iniciar el servidor gRPC

```bash
python servidor_grpc.py
```

El servidor escucha en el puerto **50051** usando HTTP/2.

### Paso 3: ejecutar el cliente gRPC

Abrir **otra terminal**:

```bash
python cliente_grpc.py
```

### Métodos RPC implementados

| Método              | Tipo RPC               | Descripción                         |
|---------------------|------------------------|-------------------------------------|
| ObtenerProducto     | Unary                  | Busca un producto por ID            |
| ListarProductos     | Unary                  | Devuelve el catálogo completo       |
| CrearProducto       | Unary                  | Registra un nuevo producto          |
| TransmitirCatalogo  | Server-Side Streaming  | Envía productos de uno en uno       |

---

## Análisis Comparativo: gRPC vs REST

| Característica          | REST (HTTP/1.1)                 | gRPC (HTTP/2)                  |
|-------------------------|---------------------------------|--------------------------------|
| Serialización           | JSON (texto legible)            | Protocol Buffers (binario)     |
| Tamaño de payload       | Mayor (~3–5× más grande)        | Menor (datos compactos)        |
| Compresión de headers   | No (se repiten completos)       | HPACK (compresión HTTP/2)      |
| Multiplexación          | No (1 req por conexión)         | Sí (múltiples streams / TCP)   |
| Contrato de API         | Informal / OpenAPI opcional     | Obligatorio (.proto)           |
| Streaming               | Limitado (SSE, polling)         | Bidireccional nativo           |
| Generación de código    | Manual o con Swagger            | Automática desde .proto        |
| Soporte en navegadores  | Nativo                          | Requiere gRPC-Web proxy        |
| Mejor para              | APIs públicas, frontends        | Microservicios internos        |

### ¿Por qué gRPC es mejor en microservicios con alto tráfico?

1. **Eficiencia de datos**: Protocol Buffers produce mensajes hasta 70 % más
   pequeños que JSON equivalente, reduciendo ancho de banda y tiempo de
   procesamiento en cada llamada.

2. **Multiplexación HTTP/2**: múltiples llamadas RPC se transportan sobre una
   sola conexión TCP de forma simultánea, eliminando el problema de
   "head-of-line blocking" de HTTP/1.1 y reduciendo la latencia end-to-end.

3. **Contrato estricto**: el archivo `.proto` obliga a todos los servicios a
   respetar los tipos de datos y la interfaz. El código se genera
   automáticamente, eliminando errores de integración entre equipos.

4. **Streaming nativo**: gRPC soporta cuatro modalidades (Unary, Client
   Streaming, Server Streaming, Bidirectional) sin necesidad de
   soluciones externas como WebSockets o SSE.

**REST sigue siendo preferible** para APIs públicas consumidas desde
navegadores o clientes externos, ya que JSON es universalmente compatible
y no requiere herramientas adicionales.

---

## Diagrama de flujo de cada protocolo

```
REST (HTTP/1.1)
  Cliente ──── TCP Handshake ──────────────────→ Servidor
  Cliente ──── HTTP Request (headers + JSON) ──→ Servidor
  Cliente ←─── HTTP Response (headers + JSON) ── Servidor
  [conexión se cierra o reutiliza con keep-alive]

gRPC (HTTP/2)
  Cliente ──── TCP + TLS Handshake ────────────→ Servidor
  Cliente ──── HTTP/2 SETTINGS frame ──────────→ Servidor
  Cliente ──── HEADERS frame (metadata) ───────→ Servidor
  Cliente ──── DATA frame (Protobuf binario) ──→ Servidor
  Cliente ←─── HEADERS frame (status) ──────── Servidor
  Cliente ←─── DATA frame (Protobuf binario) ── Servidor
  [misma conexión TCP reutilizada para N llamadas]
```

---

## Solución de problemas frecuentes

| Problema                              | Solución                                              |
|---------------------------------------|-------------------------------------------------------|
| `ModuleNotFoundError: flask`          | `pip install -r requirements.txt`                     |
| `ModuleNotFoundError: grpc`           | `pip install grpcio grpcio-tools`                     |
| `No module named inventario_pb2`      | Ejecutar `python generar_stubs.py` primero            |
| `Connection refused` en gRPC          | Asegurarse de que `servidor_grpc.py` está corriendo   |
| Puerto 5000 ocupado                   | Cambiar `port=5000` en `servidor.py`                  |
| Puerto 50051 ocupado                  | Cambiar puerto en `servidor_grpc.py` y `cliente_grpc.py` |
