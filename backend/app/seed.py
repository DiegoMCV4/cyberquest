import random
import zlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Question

# (zona, dificultad, pregunta, opciones, índice_correcto, explicación)
QUESTIONS = [
    ("redes", 1, "¿Qué capa del modelo OSI se encarga del enrutamiento mediante direcciones IP?",
     ["Enlace de datos", "Red", "Transporte", "Sesión"], 1,
     "La capa 3 (Red) usa direcciones IP y routers para enrutar paquetes."),
    ("redes", 1, "¿Qué puerto usa HTTPS por defecto?",
     ["80", "443", "22", "21"], 1, "HTTPS usa el puerto 443; HTTP usa el 80."),
    ("redes", 2, "¿Qué ataque intercepta la comunicación entre dos partes sin que lo noten?",
     ["Denegación de servicio", "Phishing", "Man-in-the-Middle", "Ransomware"], 2,
     "En un MITM el atacante se coloca en medio y puede leer o alterar el tráfico."),
    ("redes", 1, "¿Qué protocolo traduce nombres de dominio a direcciones IP?",
     ["DHCP", "DNS", "ARP", "FTP"], 1, "DNS resuelve nombres como google.com a su IP."),
    ("vulnerabilidades", 1, "¿Para qué sirve el estándar CVSS?",
     ["Cifrar datos", "Puntuar la severidad de vulnerabilidades", "Escanear puertos", "Hacer respaldos"], 1,
     "CVSS asigna una puntuación de 0 a 10 según la gravedad de una vulnerabilidad."),
    ("vulnerabilidades", 2, "En CVSS v3, ¿qué rango corresponde a severidad Crítica?",
     ["0.1 – 3.9", "4.0 – 6.9", "7.0 – 8.9", "9.0 – 10.0"], 3,
     "Crítica es 9.0–10.0; Alta 7.0–8.9; Media 4.0–6.9; Baja 0.1–3.9."),
    ("vulnerabilidades", 1, "¿Qué ataque usa correos falsos para robar credenciales?",
     ["Phishing", "Sniffing", "Fuerza bruta", "Spoofing de MAC"], 0,
     "El phishing suplanta a una entidad legítima para engañar a la víctima."),
    ("bd", 1, "¿Cuál es la mejor defensa contra SQL Injection?",
     ["Concatenar el texto del usuario", "Consultas parametrizadas", "Desactivar respaldos", "Usar la cuenta root"], 1,
     "Las consultas parametrizadas separan el código SQL de los datos del usuario."),
    ("bd", 1, "¿Qué sentencia SQL se usa para consultar datos?",
     ["INSERT", "SELECT", "DROP", "ALTER"], 1, "SELECT recupera filas de una o más tablas."),
    ("programacion", 2, "¿Qué es un ataque XSS?",
     ["Inyectar scripts en páginas que verán otros usuarios", "Saturar un servidor con tráfico",
      "Adivinar contraseñas", "Robar el disco duro"], 0,
     "En Cross-Site Scripting se inyecta JavaScript malicioso que se ejecuta en el navegador de otros."),
    ("programacion", 2, "¿Por qué se guardan contraseñas con hash (bcrypt) y no en texto plano?",
     ["Ocupan menos espacio", "Si se filtra la BD no quedan expuestas directamente",
      "Son más rápidas de comparar", "Lo exige HTTP"], 1,
     "Un hash con sal es unidireccional y lento de atacar, así que una filtración es menos grave."),
]


def _shuffled(text, opts, idx):
    """Mezcla determinista: las respuestas correctas quedan repartidas entre A-D."""
    order = list(range(len(opts)))
    random.Random(zlib.crc32(text.encode())).shuffle(order)
    return [opts[i] for i in order], order.index(idx)


def seed_questions(db: Session) -> None:
    """Crea o actualiza las preguntas (sincroniza por texto)."""
    from .questions_extra import EXTRA, EXPANDED
    rows = {q.text: q for q in db.scalars(select(Question))}
    for zone, diff, text, opts, idx, expl in QUESTIONS + EXTRA + EXPANDED:
        o, i = _shuffled(text, opts, idx)
        q = rows.get(text)
        if q is None:
            db.add(Question(
                zone=zone, topic=zone, difficulty=diff,
                question_type="opcion_multiple", text=text, options=o,
                correct_index=i, explanation=expl
            ))
        else:
            q.zone, q.topic, q.difficulty = zone, zone, diff
            q.question_type, q.options, q.correct_index, q.explanation = (
                "opcion_multiple", o, i, expl
            )
    db.commit()
