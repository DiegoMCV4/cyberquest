import random

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Assessment, Attempt, DetectiveState, Evidence, EscapeRoomState, GameProgress, PlayerProfile, Question, TowerDefenseState, User
from ..schemas import AnswerIn, AnswerOut, AssessmentAnswerIn, AssessmentStartIn, BossStatus, DefeatIn, DetectiveAnswerIn, EscapeAnswerIn, EscapeHintIn, FinalAnswerIn, MentorHintIn, QuestionCreate, QuestionOut, SettingsIn, TowerAnswerIn, Zone
from ..security import get_current_user

router = APIRouter(prefix="/game", tags=["game"])

DISTRICTS = {
    "redes": {
        "name": "Ciudad de Redes",
        "boss": "Interceptor MITM",
        "attack": "Man-in-the-Middle",
        "description": "Un atacante intercepta el tráfico entre los dispositivos de la ciudad.",
        "reward_xp": 75,
    },
    "vulnerabilidades": {
        "name": "Fortaleza de Seguridad",
        "boss": "Phisher Supremo",
        "attack": "Phishing",
        "description": "El impostor intenta robar credenciales con mensajes engañosos.",
        "reward_xp": 85,
    },
    "bd": {
        "name": "Cueva de Bases de Datos",
        "boss": "Inyector SQL",
        "attack": "SQL Injection",
        "description": "Una consulta manipulada amenaza con alterar los datos de la ciudad.",
        "reward_xp": 95,
    },
    "programacion": {
        "name": "Bosque de Programación",
        "boss": "Señor DDoS",
        "attack": "DDoS",
        "description": "Una avalancha de solicitudes intenta derribar el servidor central.",
        "reward_xp": 100,
    },
}

TOWER_WAVES = [
    {"attack": "SYN flood", "damage": 18, "tip": "El firewall filtra conexiones sospechosas."},
    {"attack": "Escaneo de puertos", "damage": 16, "tip": "Una ACL limita quién puede acceder."},
    {"attack": "Sniffing", "damage": 22, "tip": "El cifrado protege los datos en tránsito."},
    {"attack": "Intrusión desconocida", "damage": 25, "tip": "Un IDS detecta patrones anómalos."},
    {"attack": "Ataque coordinado", "damage": 30, "tip": "Combina varias capas de defensa."},
]

DEFENSES = {
    "firewall": {"name": "Firewall", "description": "Filtra tráfico según reglas.", "best_against": "SYN flood"},
    "acl": {"name": "ACL", "description": "Controla quién puede acceder.", "best_against": "Escaneo de puertos"},
    "ids": {"name": "IDS", "description": "Detecta actividad anómala.", "best_against": "Intrusión desconocida"},
    "cifrado": {"name": "Cifrado", "description": "Protege la confidencialidad.", "best_against": "Sniffing"},
}

ESCAPE_ROOMS = {
    "bd": {
        "name": "Cámara de Bases de Datos",
        "intro": "Recupera el registro de ciudadanos sin permitir una inyección SQL.",
        "reward": 120,
        "challenges": [
            {"id": "bd-select", "title": "Consulta segura", "prompt": "¿Qué consulta recupera usuarios activos sin concatenar datos?", "code": "SELECT * FROM usuarios WHERE estado = ?", "options": ["Usar parámetros preparados", "Concatenar el filtro recibido", "Ejecutar como root", "Desactivar el firewall"], "answer": 0, "explanation": "Los parámetros separan la consulta de los datos y reducen SQL Injection.", "hint": "Busca la opción que separa código y datos."},
            {"id": "bd-normalize", "title": "Tabla ordenada", "prompt": "¿Qué práctica evita repetir datos de un cliente en cada pedido?", "code": "pedidos(cliente_nombre, cliente_email, producto)", "options": ["Normalizar y separar entidades", "Duplicar todas las columnas", "Eliminar las claves", "Guardar todo como texto"], "answer": 0, "explanation": "La normalización reduce redundancia y anomalías de actualización.", "hint": "Separa clientes y pedidos usando claves."},
            {"id": "bd-roles", "title": "Permisos mínimos", "prompt": "¿Qué permiso debe tener la cuenta de la aplicación?", "code": "app_db -> usuarios", "options": ["Solo SELECT/INSERT necesarios", "ALL PRIVILEGES", "DROP DATABASE", "Acceso de root"], "answer": 0, "explanation": "El mínimo privilegio limita el impacto si la cuenta es comprometida.", "hint": "La aplicación no necesita ser administradora."},
            {"id": "bd-backup", "title": "Salida de emergencia", "prompt": "¿Cuál es la mejor defensa contra pérdida de datos por ransomware?", "code": "backup_diario", "options": ["Copias probadas y fuera de línea", "Una sola copia en el mismo servidor", "Desactivar registros", "Compartir la contraseña"], "answer": 0, "explanation": "Las copias aisladas y verificadas permiten recuperar la información.", "hint": "Una copia conectada también puede ser cifrada."},
        ],
    },
    "programacion": {
        "name": "Laboratorio de Código",
        "intro": "Corrige el código vulnerable antes de que el sistema quede expuesto.",
        "reward": 130,
        "challenges": [
            {"id": "code-xss", "title": "Salida segura", "prompt": "¿Qué línea evita XSS al mostrar el nombre?", "code": "1. element.innerHTML = nombre\\n2. element.textContent = nombre\\n3. eval(nombre)", "options": ["Línea 1", "Línea 2", "Línea 3", "Todas"], "answer": 1, "explanation": "textContent trata el valor como texto; innerHTML puede interpretar etiquetas.", "hint": "No insertes datos del usuario como HTML."},
            {"id": "code-password", "title": "Contraseña protegida", "prompt": "¿Cómo se debe guardar una contraseña?", "code": "guardar(usuario.password)", "options": ["Texto plano", "Hash lento con sal", "Base64", "Cifrado reversible con clave fija"], "answer": 1, "explanation": "Un hash con sal evita guardar la contraseña original.", "hint": "La opción correcta no debe poder revertirse."},
            {"id": "code-validate", "title": "Entrada confiable", "prompt": "¿Qué debe hacerse antes de usar datos de un formulario?", "code": "email = request.form['email']", "options": ["Validar formato y longitud", "Confiar en el navegador", "Ejecutar el valor", "Eliminar los logs"], "answer": 0, "explanation": "La validación del servidor no puede depender solo del cliente.", "hint": "El servidor debe revisar siempre la entrada."},
            {"id": "code-review", "title": "Despliegue seguro", "prompt": "Ordena mentalmente el flujo más seguro antes de publicar.", "code": "cambio -> producción", "options": ["Revisar, probar, escanear y desplegar", "Desplegar y revisar después", "Ignorar errores", "Copiar secretos al código"], "answer": 0, "explanation": "La revisión y las pruebas detectan fallas antes de producción.", "hint": "La seguridad ocurre antes del despliegue."},
        ],
    },
}

DETECTIVE_CASE = {
    "title": "Expediente Gran Brecha",
    "intro": "Analiza los registros, el tráfico y las fuentes públicas para identificar al atacante.",
    "reward": 180,
    "challenges": [
        {
            "id": "log-auth",
            "title": "Registro de autenticación",
            "source": "auth.log",
            "evidence": "Credenciales robadas",
            "snippet": "03:14:22 LOGIN failed user=admin ip=185.44.19.8\\n03:14:25 LOGIN success user=admin ip=185.44.19.8",
            "prompt": "¿Qué indicador es más importante en este registro?",
            "options": ["Éxito desde la misma IP tras muchos fallos", "Un usuario cerró sesión", "El servidor tiene un nombre", "La hora usa formato 24 h"],
            "answer": 0,
            "explanation": "Muchos fallos seguidos de un acceso exitoso desde una IP externa sugieren fuerza bruta o credenciales comprometidas.",
        },
        {
            "id": "log-dns",
            "title": "Consulta DNS sospechosa",
            "source": "dns.log",
            "evidence": "Canal de mando",
            "snippet": "host-07 -> q7x2.malware.invalid\\nhost-07 -> q8x2.malware.invalid\\nhost-07 -> q9x2.malware.invalid",
            "prompt": "¿Qué patrón puede indicar comunicación con un servidor de mando?",
            "options": ["Consultas periódicas a dominios generados", "Una consulta al dominio institucional", "Una respuesta DNS vacía aislada", "El uso de una dirección IPv4"],
            "answer": 0,
            "explanation": "Dominios variables y consultas periódicas son señales frecuentes de comunicación automatizada con infraestructura de ataque.",
        },
        {
            "id": "wireshark",
            "title": "Captura de red",
            "source": "captura-wireshark.pcap",
            "evidence": "Intercepción de tráfico",
            "snippet": "10.0.0.15 -> 10.0.0.1  HTTP POST /login\\nContenido: usuario=ana&password=***",
            "prompt": "¿Qué riesgo revela esta captura?",
            "options": ["Credenciales enviadas sin cifrado HTTPS", "Una contraseña con hash seguro", "Una conexión SSH protegida", "Un paquete ARP normal"],
            "answer": 0,
            "explanation": "HTTP permite observar datos en tránsito; HTTPS cifra la comunicación y reduce el riesgo de interceptación.",
        },
        {
            "id": "osint-domain",
            "title": "OSINT del dominio",
            "source": "registro público",
            "evidence": "Infraestructura vinculada",
            "snippet": "Dominio: soporte-ciudad-segura.example\\nCreado: 2 días antes del ataque\\nRegistrante: protegido",
            "prompt": "¿Qué conclusión es responsable con esta información?",
            "options": ["Es un indicador que requiere correlación, no una prueba única", "El registrante protegido es culpable", "El dominio prueba la identidad del atacante", "Se debe publicar la identidad del registrante"],
            "answer": 0,
            "explanation": "OSINT aporta pistas; deben verificarse con otras evidencias antes de atribuir un ataque.",
        },
        {
            "id": "timeline",
            "title": "Línea de tiempo",
            "source": "correlación de fuentes",
            "evidence": "Patrón coordinado",
            "snippet": "03:14 acceso anómalo · 03:16 DNS sospechoso · 03:19 POST HTTP · 03:25 caída del servicio",
            "prompt": "¿Cuál es la mejor acción investigativa?",
            "options": ["Correlacionar tiempos, IP, cuentas y alertas", "Borrar los registros para proteger la privacidad", "Acusar al primer usuario listado", "Ignorar los eventos anteriores a la caída"],
            "answer": 0,
            "explanation": "La correlación temporal y contextual permite construir una hipótesis verificable sin destruir evidencia.",
        },
    ],
}

FINAL_CASE = {
    "name": "La Sombra del Proxy",
    "attack": "Campaña coordinada de intrusión",
    "prompt": "Con las evidencias reunidas, ¿qué conclusión identifica mejor al atacante?",
    "options": [
        "Una persona interna, porque el ataque usó una cuenta válida",
        "La Sombra del Proxy: infraestructura externa que robó credenciales y ocultó su origen",
        "El proveedor de Internet, sin necesidad de más pruebas",
        "Nadie: los registros son siempre falsos",
    ],
    "answer": 1,
    "explanation": "La cuenta válida, el tráfico HTTP, los dominios variables y la infraestructura recién creada describen una campaña externa con credenciales comprometidas y técnicas de ocultamiento.",
    "reward": 300,
}

MENTOR_HINTS = {
    "redes": [
        "Piensa en capas: identifica primero si el problema está en el tráfico, el direccionamiento o el acceso.",
        "Compara el ataque con la propiedad que quieres proteger: disponibilidad, integridad o confidencialidad.",
        "Busca una defensa que limite o inspeccione el tráfico antes de que llegue al servicio.",
    ],
    "seguridad": [
        "No confíes solo en el aspecto de un mensaje: revisa remitente, enlace, urgencia y contexto.",
        "Una buena decisión de seguridad combina prevención, detección y respuesta.",
        "Aplica mínimo privilegio y verifica la identidad por un canal independiente.",
    ],
    "bd": [
        "Separa los datos de las instrucciones y evita que una entrada del usuario cambie la consulta.",
        "Pregúntate si la información está repetida y qué anomalía ocurriría al actualizarla.",
        "La cuenta de la aplicación debe tener únicamente los permisos que necesita para su tarea.",
    ],
    "programacion": [
        "Trata toda entrada externa como no confiable y valida también en el servidor.",
        "Distingue entre texto y código: no ejecutes ni insertes directamente valores proporcionados por usuarios.",
        "Revisa validación, salida codificada, secretos y manejo de errores antes de desplegar.",
    ],
    "detective": [
        "Una pista aislada no prueba una atribución: correlaciona fuente, hora, IP y comportamiento.",
        "En logs, busca secuencias anómalas y cambios de patrón, no solo eventos individuales.",
        "Construye una hipótesis verificable y conserva la evidencia original.",
    ],
    "jefe_final": [
        "Reúne las pistas antes de atribuir responsabilidades; una cuenta válida no demuestra quién inició el ataque.",
        "Relaciona credenciales comprometidas, tráfico sin cifrar, DNS anómalo e infraestructura reciente.",
        "La conclusión más sólida explica todas las evidencias sin afirmar más de lo que permiten probar.",
    ],
}

MENTOR_SOURCES = {
    "redes": {"title": "NIST SP 800-41 Rev. 1", "url": "https://csrc.nist.gov/publications/detail/sp/800-41/rev-1/final"},
    "seguridad": {"title": "OWASP Top 10", "url": "https://owasp.org/www-project-top-ten/"},
    "bd": {"title": "OWASP SQL Injection Prevention", "url": "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"},
    "programacion": {"title": "OWASP Cross Site Scripting Prevention", "url": "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html"},
    "detective": {"title": "NIST SP 800-61 Rev. 2", "url": "https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final"},
    "jefe_final": {"title": "NIST Cybersecurity Framework 2.0", "url": "https://www.nist.gov/cyberframework"},
}


def _get_progress(db: Session, user_id: int) -> GameProgress:
    state = db.scalar(select(GameProgress).where(GameProgress.user_id == user_id))
    if state is None:
        state = GameProgress(user_id=user_id)
        db.add(state)
        db.flush()
    return state


def _get_profile(db: Session, user_id: int) -> PlayerProfile:
    profile = db.scalar(select(PlayerProfile).where(PlayerProfile.user_id == user_id))
    if profile is None:
        profile = PlayerProfile(user_id=user_id, settings={"volume": 70, "difficulty": "adaptativa", "language": "es"})
        db.add(profile)
        db.flush()
    return profile


@router.get("/profile")
def player_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _get_profile(db, user.id)
    return {
        "settings": profile.settings or {},
        "achievements": profile.achievements or [],
        "jokers": profile.jokers or {},
    }


@router.put("/profile/settings")
def update_profile_settings(
    data: SettingsIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_profile(db, user.id)
    profile.settings = data.model_dump()
    db.commit()
    return {"settings": profile.settings}


@router.post("/profile/joker/{joker}")
def use_joker(
    joker: str,
    question_id: int | None = Query(None, ge=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if joker not in {"eliminate", "hint"}:
        raise HTTPException(422, "Comodín desconocido")
    profile = _get_profile(db, user.id)
    jokers = dict(profile.jokers or {})
    if int(jokers.get(joker, 0)) <= 0:
        raise HTTPException(409, "No tienes usos disponibles de este comodín")
    jokers[joker] = int(jokers[joker]) - 1
    profile.jokers = jokers
    blocked_indices = []
    if joker == "eliminate" and question_id is not None:
        question = db.get(Question, question_id)
        if question is None:
            raise HTTPException(404, "Pregunta no encontrada")
        wrong = [index for index in range(len(question.options)) if index != question.correct_index]
        blocked_indices = random.sample(wrong, min(2, len(wrong)))
    db.commit()
    return {"joker": joker, "remaining": jokers[joker], "blocked_indices": blocked_indices}


def _award_achievements(profile: PlayerProfile, user: User, db: Session) -> None:
    achievements = set(profile.achievements or [])
    attempts = db.scalar(select(func.count(Attempt.id)).where(Attempt.user_id == user.id)) or 0
    if attempts >= 10:
        achievements.add("primeros_10_retos")
    if user.xp >= 100:
        achievements.add("nivel_2")
    profile.achievements = sorted(achievements)


def _get_tower_state(db: Session, user_id: int) -> TowerDefenseState:
    state = db.scalar(select(TowerDefenseState).where(TowerDefenseState.user_id == user_id))
    if state is None:
        state = TowerDefenseState(user_id=user_id)
        db.add(state)
        db.flush()
    return state


def _get_escape_state(db: Session, user_id: int, room: str) -> EscapeRoomState:
    state = db.scalar(select(EscapeRoomState).where(
        EscapeRoomState.user_id == user_id, EscapeRoomState.room == room
    ))
    if state is None:
        state = EscapeRoomState(user_id=user_id, room=room)
        db.add(state)
        db.flush()
    return state


def _get_detective_state(db: Session, user_id: int) -> DetectiveState:
    state = db.scalar(select(DetectiveState).where(DetectiveState.user_id == user_id))
    if state is None:
        state = DetectiveState(user_id=user_id)
        db.add(state)
        db.flush()
    return state


@router.post("/mentor/hint")
def mentor_hint(data: MentorHintIn, user: User = Depends(get_current_user)):
    """Recuperación local de pistas curadas; nunca devuelve respuestas ni índices."""
    hints = MENTOR_HINTS[data.topic]
    source = MENTOR_SOURCES[data.topic]
    return {
        "mentor": "Maestro IA",
        "topic": data.topic,
        "level": data.level,
        "hint": hints[data.level - 1],
        "source": source,
        "disclaimer": "Pista educativa: analiza el problema y decide por ti mismo.",
    }


def _escape_response(state: EscapeRoomState, room: str) -> dict:
    data = ESCAPE_ROOMS[room]
    solved = set(state.solved or [])
    challenges = [
        {
            "id": item["id"],
            "title": item["title"],
            "prompt": item["prompt"],
            "code": item["code"],
            "options": item["options"],
            "solved": item["id"] in solved,
        }
        for item in data["challenges"]
    ]
    return {
        "room": room,
        "name": data["name"],
        "intro": data["intro"],
        "challenges": challenges,
        "solved": len(solved),
        "total": len(data["challenges"]),
        "hints_used": state.hints_used,
        "score": state.score,
        "completed": state.completed,
    }


@router.get("/escape-room/{room}")
def escape_room_state(room: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if room not in ESCAPE_ROOMS:
        raise HTTPException(404, "Sala no encontrada")
    return _escape_response(_get_escape_state(db, user.id, room), room)


@router.post("/escape-room/{room}/reset")
def escape_room_reset(room: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if room not in ESCAPE_ROOMS:
        raise HTTPException(404, "Sala no encontrada")
    state = _get_escape_state(db, user.id, room)
    state.solved, state.hints_used, state.score, state.completed = [], 0, 0, False
    db.commit()
    return _escape_response(state, room)


@router.post("/escape-room/answer")
def escape_room_answer(
    data: EscapeAnswerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    state = _get_escape_state(db, user.id, data.room)
    challenge = next((item for item in ESCAPE_ROOMS[data.room]["challenges"] if item["id"] == data.challenge_id), None)
    if challenge is None:
        raise HTTPException(404, "Reto no encontrado")
    if challenge["id"] in (state.solved or []):
        raise HTTPException(409, "Este reto ya fue resuelto")
    if data.option_index >= len(challenge["options"]):
        raise HTTPException(422, "Opción inválida")
    correct = data.option_index == challenge["answer"]
    gained = 0
    if correct:
        solved = list(state.solved or [])
        solved.append(challenge["id"])
        state.solved = solved
        gained = 20
        state.score += gained
        if len(solved) == len(ESCAPE_ROOMS[data.room]["challenges"]):
            state.completed = True
            gained += ESCAPE_ROOMS[data.room]["reward"]
            state.score += ESCAPE_ROOMS[data.room]["reward"]
        user.xp += gained
        progress = _get_progress(db, user.id)
        progress.score += gained
        progress.level = user.xp // 100 + 1
    db.commit()
    result = _escape_response(state, data.room)
    result.update({"correct": correct, "correct_index": challenge["answer"], "explanation": challenge["explanation"], "xp_gained": gained, "total_xp": user.xp})
    return result


@router.post("/escape-room/hint")
def escape_room_hint(
    data: EscapeHintIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    state = _get_escape_state(db, user.id, data.room)
    challenge = next((item for item in ESCAPE_ROOMS[data.room]["challenges"] if item["id"] == data.challenge_id), None)
    if challenge is None:
        raise HTTPException(404, "Reto no encontrado")
    if challenge["id"] in (state.solved or []):
        raise HTTPException(409, "Este reto ya fue resuelto")
    state.hints_used += 1
    state.score = max(0, state.score - 5)
    db.commit()
    return {"hint": challenge["hint"], "score": state.score, "hints_used": state.hints_used}


def _detective_response(state: DetectiveState) -> dict:
    solved = set(state.solved or [])
    return {
        "title": DETECTIVE_CASE["title"],
        "intro": DETECTIVE_CASE["intro"],
        "challenges": [
            {
                "id": item["id"],
                "title": item["title"],
                "source": item["source"],
                "snippet": item["snippet"],
                "prompt": item["prompt"],
                "options": item["options"],
                "solved": item["id"] in solved,
                "evidence": item["evidence"] if item["id"] in solved else None,
            }
            for item in DETECTIVE_CASE["challenges"]
        ],
        "solved": len(solved),
        "total": len(DETECTIVE_CASE["challenges"]),
        "score": state.score,
        "completed": state.completed,
    }


@router.get("/detective/state")
def detective_state(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _detective_response(_get_detective_state(db, user.id))


@router.post("/detective/reset")
def detective_reset(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = _get_detective_state(db, user.id)
    state.solved, state.score, state.completed = [], 0, False
    for evidence in db.scalars(select(Evidence).where(Evidence.user_id == user.id)).all():
        db.delete(evidence)
    db.commit()
    return _detective_response(state)


@router.post("/detective/answer")
def detective_answer(
    data: DetectiveAnswerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    state = _get_detective_state(db, user.id)
    challenge = next((item for item in DETECTIVE_CASE["challenges"] if item["id"] == data.challenge_id), None)
    if challenge is None:
        raise HTTPException(404, "Pista no encontrada")
    if challenge["id"] in (state.solved or []):
        raise HTTPException(409, "Esta pista ya fue analizada")
    if data.option_index >= len(challenge["options"]):
        raise HTTPException(422, "Opción inválida")
    correct = data.option_index == challenge["answer"]
    gained = 0
    if correct:
        solved = list(state.solved or [])
        solved.append(challenge["id"])
        state.solved = solved
        gained = 25
        state.score += gained
        db.add(Evidence(user_id=user.id, name=challenge["evidence"], description=challenge["explanation"]))
        if len(solved) == len(DETECTIVE_CASE["challenges"]):
            state.completed = True
            gained += DETECTIVE_CASE["reward"]
            state.score += DETECTIVE_CASE["reward"]
        user.xp += gained
        progress = _get_progress(db, user.id)
        progress.score += gained
        progress.level = user.xp // 100 + 1
    db.commit()
    result = _detective_response(state)
    result.update({
        "correct": correct,
        "correct_index": challenge["answer"],
        "explanation": challenge["explanation"],
        "xp_gained": gained,
        "total_xp": user.xp,
    })
    return result


@router.get("/detective/evidence")
def detective_evidence(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Evidence).where(Evidence.user_id == user.id).order_by(Evidence.id)).all()
    return [{"id": row.id, "name": row.name, "description": row.description} for row in rows]


@router.get("/final-boss/state")
def final_boss_state(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    progress = _get_progress(db, user.id)
    detective = _get_detective_state(db, user.id)
    unlocked = len(progress.bosses or []) == len(DISTRICTS) and detective.completed
    return {
        "name": FINAL_CASE["name"],
        "attack": FINAL_CASE["attack"],
        "prompt": FINAL_CASE["prompt"],
        "options": FINAL_CASE["options"] if unlocked and not progress.final_defeated else [],
        "unlocked": unlocked,
        "defeated": bool(progress.final_defeated),
        "evidence_count": len(db.scalars(select(Evidence).where(Evidence.user_id == user.id)).all()),
        "required_evidence": len(DETECTIVE_CASE["challenges"]),
    }


@router.post("/final-boss/answer")
def final_boss_answer(
    data: FinalAnswerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    progress = _get_progress(db, user.id)
    detective = _get_detective_state(db, user.id)
    if len(progress.bosses or []) != len(DISTRICTS) or not detective.completed:
        raise HTTPException(409, "Derrota a los cuatro jefes y reúne toda la evidencia primero")
    if progress.final_defeated:
        raise HTTPException(409, "El jefe final ya fue derrotado")
    if data.option_index >= len(FINAL_CASE["options"]):
        raise HTTPException(422, "Opción inválida")
    correct = data.option_index == FINAL_CASE["answer"]
    gained = FINAL_CASE["reward"] if correct else 0
    if correct:
        progress.final_defeated = True
        user.xp += gained
        progress.score += gained
        progress.level = user.xp // 100 + 1
    db.commit()
    return {
        "correct": correct,
        "correct_index": FINAL_CASE["answer"],
        "explanation": FINAL_CASE["explanation"],
        "xp_gained": gained,
        "total_xp": user.xp,
        "defeated": progress.final_defeated,
    }


def _tower_response(state: TowerDefenseState) -> dict:
    wave_index = min(state.wave, len(TOWER_WAVES) - 1)
    return {
        "server_hp": state.server_hp,
        "max_server_hp": 100,
        "wave": state.wave,
        "total_waves": len(TOWER_WAVES),
        "score": state.score,
        "defenses": state.defenses or {},
        "active": state.active,
        "completed": state.completed,
        "current_attack": TOWER_WAVES[wave_index]["attack"] if state.active and state.wave < len(TOWER_WAVES) else None,
        "current_tip": TOWER_WAVES[wave_index]["tip"] if state.active and state.wave < len(TOWER_WAVES) else None,
        "defense_catalog": DEFENSES,
    }


@router.get("/tower-defense/state")
def tower_state(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _tower_response(_get_tower_state(db, user.id))


@router.post("/tower-defense/start")
def tower_start(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = _get_tower_state(db, user.id)
    if state.active:
        return _tower_response(state)
    state.server_hp = 100
    state.wave = 0
    state.score = 0
    state.defenses = {}
    state.active = True
    state.completed = False
    db.commit()
    return _tower_response(state)


@router.post("/tower-defense/answer")
def tower_answer(
    data: TowerAnswerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    state = _get_tower_state(db, user.id)
    if not state.active or state.completed:
        raise HTTPException(409, "No hay una partida Tower Defense activa")
    if state.wave >= len(TOWER_WAVES):
        raise HTTPException(409, "La partida ya terminó")
    question = db.get(Question, data.question_id)
    if question is None or question.zone != "redes":
        raise HTTPException(404, "La pregunta no pertenece al distrito Redes")
    correct = data.option_index == question.correct_index
    wave = TOWER_WAVES[state.wave]
    defense = DEFENSES[data.defense]
    damage = 0
    gained = 0
    if correct:
        gained = 10 * question.difficulty
        if defense["best_against"] != wave["attack"]:
            damage = max(4, wave["damage"] // 3)
        defenses = dict(state.defenses or {})
        defenses[data.defense] = int(defenses.get(data.defense, 0)) + 1
        state.defenses = defenses
        state.score += 25 + gained
        user.xp += gained
    else:
        damage = wave["damage"]
    state.server_hp = max(0, state.server_hp - damage)
    state.wave += 1
    if state.wave >= len(TOWER_WAVES) or state.server_hp <= 0:
        state.active = False
        state.completed = state.server_hp > 0
        if state.completed:
            reward = 150
            user.xp += reward
            state.score += reward
        else:
            reward = 0
    else:
        reward = 0
    progress = _get_progress(db, user.id)
    progress.score += gained + reward
    progress.level = (user.xp // 100) + 1
    db.add(Attempt(user_id=user.id, question_id=question.id, correct=correct))
    db.commit()
    result = _tower_response(state)
    result.update({
        "correct": correct,
        "correct_index": question.correct_index,
        "explanation": question.explanation,
        "damage": damage,
        "xp_gained": gained + reward,
        "total_xp": user.xp,
        "defense": defense["name"],
        "defense_tip": defense["description"],
    })
    return result


@router.get("/districts", response_model=list[BossStatus])
def districts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = db.scalar(select(GameProgress).where(GameProgress.user_id == user.id))
    defeated = state.defeated if state else {}
    bosses = state.bosses if state else []
    return [
        BossStatus(
            zone=zone,
            name=data["boss"],
            attack=data["attack"],
            description=data["description"],
            defeated_enemies=int(defeated.get(zone, 0)),
            enemies_required=4,
            boss_defeated=zone in bosses,
            reward_xp=data["reward_xp"],
        )
        for zone, data in DISTRICTS.items()
    ]


@router.get("/questions", response_model=list[QuestionOut])
def get_questions(
    zone: Zone,
    difficulty: int | None = Query(None, ge=1, le=3),
    min_difficulty: int | None = Query(None, ge=1, le=3),
    count: int = Query(1, ge=1, le=10),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Nunca se envía correct_index al cliente: la validación es solo del servidor
    stmt = select(Question).where(Question.zone == zone)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    # Prioriza falladas y luego preguntas nuevas para reforzar el aprendizaje.
    done = select(Attempt.question_id).where(Attempt.user_id == user.id, Attempt.correct.is_(True))
    failed = select(Attempt.question_id).where(Attempt.user_id == user.id, Attempt.correct.is_(False))
    profile = _get_profile(db, user.id)
    preferred = (profile.settings or {}).get("difficulty", "adaptativa")
    if min_difficulty:
        stmt = stmt.where(Question.difficulty >= min_difficulty)
    elif difficulty is None and preferred == "adaptativa":
        recent = db.scalars(
            select(Attempt).join(Question, Attempt.question_id == Question.id)
            .where(Attempt.user_id == user.id, Question.zone == zone)
            .order_by(Attempt.id.desc())
            .limit(10)
        ).all()
        if len(recent) >= 3:
            accuracy = sum(attempt.correct for attempt in recent) / len(recent)
            target = 3 if accuracy >= 0.8 else 1 if accuracy <= 0.4 else 2
            stmt = stmt.where(Question.difficulty == target)
    elif preferred in {"facil", "normal", "dificil"}:
        target = {"facil": 1, "normal": 2, "dificil": 3}[preferred]
        stmt = stmt.where(Question.difficulty == target)
    random_order = func.rand() if db.bind.dialect.name == "mysql" else func.random()
    return db.scalars(stmt.order_by(Question.id.in_(failed).desc(), Question.id.in_(done), random_order).limit(count)).all()


@router.post("/assessment/start")
def assessment_start(
    data: AssessmentStartIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.kind == "post":
        progress = _get_progress(db, user.id)
        if len(progress.bosses or []) < 3:
            raise HTTPException(409, "Completa al menos tres niveles antes del post-test")
    existing = db.scalar(select(Assessment).where(
        Assessment.user_id == user.id,
        Assessment.kind == data.kind,
        Assessment.topic == data.topic,
    ))
    if existing:
        question_ids = existing.question_ids or []
        if existing.completed:
            existing.answers = {}
            existing.completed = False
            existing.score = 0
    else:
        questions = db.scalars(
            select(Question)
            .where(Question.zone == data.topic)
            .order_by(Question.difficulty, Question.id)
            .limit(10)
        ).all()
        if len(questions) < 5:
            raise HTTPException(409, "No hay suficientes preguntas para esta evaluación")
        question_ids = [question.id for question in questions]
        existing = Assessment(
            user_id=user.id,
            kind=data.kind,
            topic=data.topic,
            question_ids=question_ids,
            answers={},
            completed=False,
            score=0,
        )
        db.add(existing)
        db.flush()
    questions = db.scalars(select(Question).where(Question.id.in_(question_ids))).all()
    by_id = {question.id: question for question in questions}
    return {
        "kind": data.kind,
        "topic": data.topic,
        "completed": existing.completed,
        "score": existing.score,
        "answers": existing.answers or {},
        "total": len(question_ids),
        "questions": [QuestionOut.model_validate(by_id[question_id]).model_dump() for question_id in question_ids],
    }


@router.post("/assessment/answer")
def assessment_answer(
    data: AssessmentAnswerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessment = db.scalar(select(Assessment).where(
        Assessment.user_id == user.id,
        Assessment.kind == data.kind,
        Assessment.topic == data.topic,
        Assessment.completed.is_(False),
    ))
    if assessment is None or data.question_id not in (assessment.question_ids or []):
        raise HTTPException(404, "Evaluación activa no encontrada")
    answers = dict(assessment.answers or {})
    key = str(data.question_id)
    if key in answers:
        raise HTTPException(409, "Esta pregunta ya fue respondida")
    question = db.get(Question, data.question_id)
    if question is None or data.option_index >= len(question.options):
        raise HTTPException(422, "Opción inválida")
    correct = data.option_index == question.correct_index
    answers[key] = {"correct": correct, "option_index": data.option_index}
    assessment.answers = answers
    if correct:
        assessment.score += 1
    if len(answers) == len(assessment.question_ids or []):
        assessment.completed = True
    db.commit()
    return {
        "correct": correct,
        "explanation": question.explanation,
        "answered": len(answers),
        "total": len(assessment.question_ids or []),
        "completed": assessment.completed,
        "score": assessment.score,
    }


@router.get("/assessment/summary")
def assessment_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Assessment).where(
        Assessment.user_id == user.id,
        Assessment.completed.is_(True),
    ).order_by(Assessment.topic, Assessment.kind)).all()
    result = {}
    for row in rows:
        result.setdefault(row.topic, {})[row.kind] = {
            "score": row.score,
            "total": len(row.question_ids or []),
            "percent": round(row.score / len(row.question_ids) * 100) if row.question_ids else 0,
        }
    return result


@router.get("/final-stats")
def final_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    attempts = db.scalars(select(Attempt).where(Attempt.user_id == user.id)).all()
    by_topic = {}
    for attempt in attempts:
        question = db.get(Question, attempt.question_id)
        if question is None:
            continue
        stats = by_topic.setdefault(question.zone, {"correct": 0, "total": 0})
        stats["total"] += 1
        stats["correct"] += int(attempt.correct)
    for stats in by_topic.values():
        stats["percent"] = round(stats["correct"] / stats["total"] * 100) if stats["total"] else 0
    progress = _get_progress(db, user.id)
    profile = _get_profile(db, user.id)
    return {
        "xp": user.xp,
        "level": user.xp // 100 + 1,
        "score": progress.score,
        "by_topic": by_topic,
        "achievements": profile.achievements or [],
        "jokers": profile.jokers or {},
    }


@router.post("/questions/{question_id}/answer", response_model=AnswerOut)
def answer(
    question_id: int,
    data: AnswerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.get(Question, question_id)
    if not q:
        raise HTTPException(404, "Pregunta no encontrada")
    correct = data.option_index == q.correct_index
    already = db.scalar(
        select(Attempt.id).where(
            Attempt.user_id == user.id, Attempt.question_id == q.id, Attempt.correct.is_(True)
        )
    )
    gained = 10 * q.difficulty if correct and not already else 0  # sin farmear XP
    db.add(Attempt(user_id=user.id, question_id=q.id, correct=correct))
    _award_achievements(_get_profile(db, user.id), user, db)
    user.xp += gained
    state = _get_progress(db, user.id)
    state.score += gained
    state.level = user.xp // 100 + 1
    db.commit()
    return AnswerOut(
        correct=correct,
        correct_index=q.correct_index,
        explanation=q.explanation,
        xp_gained=gained,
        total_xp=user.xp,
    )


@router.get("/progress")
def progress(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Question.zone, func.count(func.distinct(Attempt.question_id)))
        .join(Attempt, Attempt.question_id == Question.id)
        .where(Attempt.user_id == user.id, Attempt.correct.is_(True))
        .group_by(Question.zone)
    ).all()
    state = db.scalar(select(GameProgress).where(GameProgress.user_id == user.id))
    defeated = state.defeated if state else {}
    bosses = state.bosses if state else []
    return {
        "xp": user.xp,
        "level": state.level if state else user.xp // 100 + 1,
        "lives": state.lives if state else 3,
        "score": state.score if state else user.xp,
        "zones": {z: n for z, n in rows},
        "defeated": defeated,
        "bosses": bosses,
        "final_defeated": bool(state and state.final_defeated),
    }


@router.post("/progress/defeat")
def record_defeat(
    data: DefeatIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    state = _get_progress(db, user.id)

    if data.final:
        raise HTTPException(400, "El jefe final debe resolverse desde el caso final")
    elif data.boss:
        completed_enemies = int((state.defeated or {}).get(data.zone, 0))
        if completed_enemies < 4:
            raise HTTPException(409, "Debes derrotar a los cuatro enemigos del distrito")
        bosses = list(state.bosses or [])
        if data.zone in bosses:
            raise HTTPException(409, "Este jefe ya fue derrotado")
        bosses.append(data.zone)
        state.bosses = bosses
        reward = DISTRICTS[data.zone]["reward_xp"]
        user.xp += reward
        state.score += reward
        state.level = user.xp // 100 + 1
    else:
        defeated = dict(state.defeated or {})
        defeated[data.zone] = min(4, int(defeated.get(data.zone, 0)) + 1)
        state.defeated = defeated
    db.commit()
    return {
        "ok": True,
        "reward_xp": DISTRICTS[data.zone]["reward_xp"] if data.boss and not data.final else 0,
        "total_xp": user.xp,
    }


@router.get("/questions/all", response_model=list[QuestionOut])
def list_questions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "administrador":
        raise HTTPException(403, "Se requiere rol de administrador")
    return db.scalars(select(Question).order_by(Question.id)).all()


@router.post("/questions", response_model=QuestionOut, status_code=201)
def create_question(
    data: QuestionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "administrador":
        raise HTTPException(403, "Se requiere rol de administrador")
    if data.correct_index >= len(data.options):
        raise HTTPException(422, "correct_index debe apuntar a una opción existente")
    question = Question(**data.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.put("/questions/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    data: QuestionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "administrador":
        raise HTTPException(403, "Se requiere rol de administrador")
    if data.correct_index >= len(data.options):
        raise HTTPException(422, "correct_index debe apuntar a una opción existente")
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(404, "Pregunta no encontrada")
    for field, value in data.model_dump().items():
        setattr(question, field, value)
    db.commit()
    db.refresh(question)
    return question


@router.delete("/questions/{question_id}", status_code=204)
def delete_question(
    question_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != "administrador":
        raise HTTPException(403, "Se requiere rol de administrador")
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(404, "Pregunta no encontrada")
    db.delete(question)
    db.commit()


@router.get("/ranking")
def ranking(db: Session = Depends(get_db)):
    top = db.execute(select(User.username, User.xp).order_by(User.xp.desc()).limit(10)).all()
    return [{"username": u, "xp": x} for u, x in top]
