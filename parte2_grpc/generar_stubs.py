"""
PARTE 2 - GENERADOR DE STUBS
==============================
Este script compila el archivo inventario.proto y genera
automáticamente los stubs Python necesarios para usar gRPC:
  - inventario_pb2.py       (clases de mensajes Protobuf)
  - inventario_pb2_grpc.py  (clases del stub cliente/servidor)

Ejecutar UNA SOLA VEZ antes de correr servidor_grpc.py y cliente_grpc.py
"""

import subprocess
import sys
import os

def generar_stubs():
    print("=" * 55)
    print("  Generando stubs gRPC desde inventario.proto")
    print("=" * 55)

    # Directorio donde está este script (y el .proto)
    directorio = os.path.dirname(os.path.abspath(__file__))
    proto_file = os.path.join(directorio, "inventario.proto")

    if not os.path.exists(proto_file):
        print(f"  ✗ No se encontró: {proto_file}")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"-I{directorio}",
        f"--python_out={directorio}",
        f"--grpc_python_out={directorio}",
        proto_file
    ]

    print(f"  Ejecutando: {' '.join(cmd)}\n")

    resultado = subprocess.run(cmd, capture_output=True, text=True)

    if resultado.returncode == 0:
        print("  ✓ Stubs generados exitosamente:")
        print("    - inventario_pb2.py")
        print("    - inventario_pb2_grpc.py")
        print("\n  Ahora puedes ejecutar:")
        print("    python servidor_grpc.py   (en una terminal)")
        print("    python cliente_grpc.py    (en otra terminal)")
    else:
        print(f"  ✗ Error al compilar el .proto:")
        print(resultado.stderr)
        print("\n  Asegúrate de tener instalado: pip install grpcio-tools")
        sys.exit(1)


if __name__ == "__main__":
    generar_stubs()
