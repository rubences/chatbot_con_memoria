"""
Herramientas personalizadas de crewAI para el análisis de transcripciones
de llamadas de servicio al cliente.

Cada herramienta implementa la interfaz BaseTool de crewAI y encapsula
una técnica concreta de procesamiento de texto:
  - HerramientaAnalisisSentimiento: clasifica el sentimiento de cada participante.
  - HerramientaExtraccionPalabrasClave: extrae términos y frases relevantes.
"""

from __future__ import annotations

import re
from collections import Counter

from crewai.tools import BaseTool

# ── Léxico de referencia (inglés/español) ────────────────────────────────────
_PALABRAS_NEGATIVAS: frozenset[str] = frozenset(
    {
        # Inglés
        "frustrated", "frustrating", "angry", "awful", "terrible", "horrible",
        "bad", "wrong", "problem", "issue", "upset", "disgusted", "annoyed",
        "unacceptable", "ridiculous", "disappointed", "rude", "disrespectful",
        "unprofessional", "incompetent", "useless", "pathetic", "furious",
        "outraged", "disgusting", "mess", "spilled", "open", "damaged",
        "blaming", "dramatic", "unbelievable", "chill",
        # Español
        "frustrado", "frustrada", "enojado", "enojada", "terrible", "horrible",
        "mal", "malo", "problema", "queja", "alterado", "alterada",
        "inaceptable", "ridículo", "decepcionado", "decepcionada", "grosero",
        "grosera", "irrespetuoso", "irrespetuosa", "incompetente", "inútil",
        "furioso", "furiosa", "indignado", "indignada", "estropeado", "roto",
        "culpa", "dramático", "increíble",
    }
)

_PALABRAS_POSITIVAS: frozenset[str] = frozenset(
    {
        # Inglés
        "good", "great", "excellent", "helpful", "thank", "thanks", "appreciate",
        "wonderful", "happy", "satisfied", "resolved", "fixed", "pleased",
        "outstanding", "perfect", "amazing", "brilliant", "gladly", "welcome",
        # Español
        "bien", "bueno", "buena", "excelente", "útil", "gracias", "agradecer",
        "maravilloso", "maravillosa", "feliz", "satisfecho", "satisfecha",
        "resuelto", "solucionado", "perfecto", "perfecto", "increíble",
        "bienvenido", "encantado", "encantada", "dispuesto",
    }
)

_PALABRAS_VACIAS: frozenset[str] = frozenset(
    {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "it", "this", "that", "i", "you",
        "we", "he", "she", "they", "me", "my", "your", "our", "their", "be",
        "been", "was", "were", "are", "have", "has", "had", "do", "does",
        "did", "will", "would", "could", "should", "may", "might", "can",
        "not", "no", "so", "if", "as", "just", "like", "what", "well",
        "yeah", "okay", "ok", "ugh", "know", "really", "even", "kind",
        "going", "get", "got", "im", "its", "ll", "ve", "re", "dont",
        "isnt", "cant", "wont", "didnt", "wasnt", "gonna", "wanna",
        # Español
        "el", "la", "los", "las", "un", "una", "unos", "unas", "del", "con",
        "por", "para", "que", "qué", "como", "cómo", "cuando", "donde",
        "porque", "pero", "sino", "aunque", "también", "todo", "todos",
        "esta", "este", "esto", "ese", "esa", "eso", "ser", "estar", "tener",
        "hay", "más", "muy", "sí", "no", "si", "ya", "aquí", "allí",
    }
)


def _tokenizar(texto: str) -> list[str]:
    """Extrae tokens alfabéticos de 3 o más caracteres (normalizado a minúsculas)."""
    return re.findall(r"[a-záéíóúñüàèìòùâêîôûäëïöü]{3,}", texto.lower())


def _detectar_participante(linea: str) -> str | None:
    """
    Clasifica una línea de cabecera de participante.

    Devuelve 'agente' si el hablante se identifica con una empresa (paréntesis),
    'cliente' para el resto, o None si no es cabecera.
    """
    linea = linea.strip()
    if not linea.endswith(":") or len(linea) > 80:
        return None
    nombre = linea[:-1].lower()
    if "(" in nombre and ")" in nombre:
        return "agente"
    return "cliente"


# ── Herramientas ─────────────────────────────────────────────────────────────

class HerramientaAnalisisSentimiento(BaseTool):
    """Analiza el sentimiento de cada participante en la transcripción."""

    name: str = "Herramienta de Análisis de Sentimientos"
    description: str = (
        "Determina el sentimiento neto del cliente y del agente a lo largo de la "
        "transcripción de la llamada. Proporciona el texto completo de la transcripción "
        "como entrada. Devuelve la clasificación de sentimiento y los conteos de indicadores "
        "positivos y negativos para cada participante."
    )

    def _run(self, transcripcion: str) -> str:  # type: ignore[override]
        conteo: dict[str, Counter[str]] = {
            "cliente": Counter(),
            "agente": Counter(),
        }
        participante_actual: str | None = None

        for linea in transcripcion.splitlines():
            resultado = _detectar_participante(linea)
            if resultado is not None:
                participante_actual = resultado
                continue

            if participante_actual is None:
                continue

            tokens = set(_tokenizar(linea))
            conteo[participante_actual]["negativo"] += len(tokens & _PALABRAS_NEGATIVAS)
            conteo[participante_actual]["positivo"] += len(tokens & _PALABRAS_POSITIVAS)

        def _clasificar(contador: Counter[str]) -> str:
            neg = contador.get("negativo", 0)
            pos = contador.get("positivo", 0)
            if neg == 0 and pos == 0:
                return "Neutral"
            ratio = neg / max(pos, 1)
            if ratio >= 3:
                return "Muy Negativo"
            if ratio >= 1.5:
                return "Negativo"
            if pos > neg:
                return "Positivo"
            return "Neutral"

        lineas_resultado = []
        for rol, nombre_legible in (("cliente", "Cliente"), ("agente", "Agente")):
            c = conteo[rol]
            clasificacion = _clasificar(c)
            lineas_resultado.append(
                f"Sentimiento del {nombre_legible}: {clasificacion} "
                f"(indicadores positivos: {c['positivo']}, negativos: {c['negativo']})"
            )

        return "\n".join(lineas_resultado)


class HerramientaExtraccionPalabrasClave(BaseTool):
    """Extrae palabras y frases clave de la transcripción."""

    name: str = "Herramienta de Extracción de Palabras Clave"
    description: str = (
        "Identifica los términos más relevantes y frases recurrentes en la transcripción. "
        "Proporciona el texto completo de la transcripción como entrada. "
        "Devuelve una lista de palabras clave y frases clave ordenadas por frecuencia."
    )

    def _run(self, transcripcion: str) -> str:  # type: ignore[override]
        tokens = _tokenizar(transcripcion)
        frecuencia = Counter(t for t in tokens if t not in _PALABRAS_VACIAS)
        palabras_clave = [palabra for palabra, _ in frecuencia.most_common(15)]

        # Bigramas significativos (aparecen al menos 2 veces)
        texto_normalizado = re.sub(r"[^a-záéíóúñüàèìòùâêîôûäëïöü\s]", " ", transcripcion.lower())
        bigramas = re.findall(
            r"\b([a-záéíóúñüàèìòùâêîôûäëïöü]{3,}\s[a-záéíóúñüàèìòùâêîôûäëïöü]{3,})\b",
            texto_normalizado,
        )
        freq_bigramas = Counter(
            bg for bg in bigramas
            if not all(p in _PALABRAS_VACIAS for p in bg.split())
        )
        frases_clave = [frase for frase, cnt in freq_bigramas.most_common(8) if cnt >= 2]

        resultado = f"Palabras clave principales: {', '.join(palabras_clave)}"
        if frases_clave:
            resultado += f"\nFrases recurrentes: {', '.join(frases_clave)}"
        return resultado
