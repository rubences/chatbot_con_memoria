"""
Pruebas unitarias para el módulo de memoria del chatbot.
Cubren: inicialización del historial, adición de mensajes y truncamiento.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memoria import GestorMemoria


MENSAJE_SISTEMA_PRUEBA = "Eres un asistente de prueba."


class TestInicializacion:
    def test_historial_contiene_mensaje_sistema(self) -> None:
        gestor = GestorMemoria(MENSAJE_SISTEMA_PRUEBA)
        assert gestor.historial[0]["role"] == "system"
        assert gestor.historial[0]["content"] == MENSAJE_SISTEMA_PRUEBA

    def test_historial_inicial_tiene_un_solo_mensaje(self) -> None:
        gestor = GestorMemoria(MENSAJE_SISTEMA_PRUEBA)
        assert gestor.total_mensajes() == 1

    def test_historial_devuelve_copia(self) -> None:
        gestor = GestorMemoria(MENSAJE_SISTEMA_PRUEBA)
        copia = gestor.historial
        copia.append({"role": "user", "content": "hola"})
        # La copia no debe afectar al historial interno
        assert gestor.total_mensajes() == 1


class TestAdicionMensajes:
    def test_agregar_mensaje_usuario(self) -> None:
        gestor = GestorMemoria(MENSAJE_SISTEMA_PRUEBA)
        gestor.agregar_mensaje("user", "Hola")
        assert gestor.total_mensajes() == 2
        assert gestor.historial[-1] == {"role": "user", "content": "Hola"}

    def test_agregar_mensaje_asistente(self) -> None:
        gestor = GestorMemoria(MENSAJE_SISTEMA_PRUEBA)
        gestor.agregar_mensaje("assistant", "¡Hola a ti!")
        assert gestor.historial[-1]["role"] == "assistant"

    def test_orden_de_mensajes_se_preserva(self) -> None:
        gestor = GestorMemoria(MENSAJE_SISTEMA_PRUEBA)
        gestor.agregar_mensaje("user", "Pregunta 1")
        gestor.agregar_mensaje("assistant", "Respuesta 1")
        gestor.agregar_mensaje("user", "Pregunta 2")
        roles = [m["role"] for m in gestor.historial[1:]]
        assert roles == ["user", "assistant", "user"]


class TestTruncamientoMemoria:
    def test_no_supera_el_limite(self) -> None:
        limite = 4
        gestor = GestorMemoria(MENSAJE_SISTEMA_PRUEBA, limite_mensajes=limite)
        for i in range(10):
            gestor.agregar_mensaje("user", f"Mensaje {i}")
        # El mensaje de sistema + máximo `limite` mensajes de conversación
        assert gestor.total_mensajes() == limite + 1

    def test_mensaje_sistema_nunca_se_elimina(self) -> None:
        gestor = GestorMemoria(MENSAJE_SISTEMA_PRUEBA, limite_mensajes=2)
        for i in range(10):
            gestor.agregar_mensaje("user", f"Mensaje {i}")
        assert gestor.historial[0]["role"] == "system"
        assert gestor.historial[0]["content"] == MENSAJE_SISTEMA_PRUEBA

    def test_conserva_mensajes_mas_recientes(self) -> None:
        gestor = GestorMemoria(MENSAJE_SISTEMA_PRUEBA, limite_mensajes=2)
        for i in range(5):
            gestor.agregar_mensaje("user", f"Mensaje {i}")
        contenidos = [m["content"] for m in gestor.historial[1:]]
        assert "Mensaje 3" in contenidos
        assert "Mensaje 4" in contenidos


class TestReinicio:
    def test_reiniciar_borra_conversacion(self) -> None:
        gestor = GestorMemoria(MENSAJE_SISTEMA_PRUEBA)
        gestor.agregar_mensaje("user", "Hola")
        gestor.agregar_mensaje("assistant", "Hola a ti")
        gestor.reiniciar()
        assert gestor.total_mensajes() == 1

    def test_reiniciar_preserva_mensaje_sistema(self) -> None:
        gestor = GestorMemoria(MENSAJE_SISTEMA_PRUEBA)
        gestor.agregar_mensaje("user", "Hola")
        gestor.reiniciar()
        assert gestor.historial[0]["content"] == MENSAJE_SISTEMA_PRUEBA
