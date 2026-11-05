"""Validadores seguros para los editores ficticios del juego."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PatchResult:
    correct: bool
    explanation: str
    missing: tuple[str, ...] = ()


def validate_sql_patch(code: str) -> PatchResult:
    """Comprueba reglas educativas sin ejecutar ni interpretar el código."""
    normalized = " ".join(code.lower().split())
    missing = []
    if "select" not in normalized:
        missing.append("conservar una consulta SELECT")
    if not any(marker in normalized for marker in ("?", ":username", "%s")):
        missing.append("usar un marcador de parámetro")
    if "execute" not in normalized:
        missing.append("enviar la consulta mediante execute")
    if not any(marker in normalized for marker in ("params", "username", "parametro", "parámetro")):
        missing.append("separar los valores en parámetros")
    if "+" in normalized or 'f"' in normalized or "f'" in normalized:
        missing.append("eliminar la concatenación o interpolación")
    if missing:
        return PatchResult(
            False,
            "La consulta aún mezcla código y datos. " + "; ".join(missing) + ".",
            tuple(missing),
        )
    return PatchResult(
        True,
        "Parche correcto: el marcador y los valores se envían separados; "
        "la entrada ficticia del atacante ya no cambia la estructura de la consulta.",
    )


def validate_buffer_patch(code: str) -> PatchResult:
    normalized = " ".join(code.lower().split())
    missing = []
    if "len(" not in normalized and "length" not in normalized:
        missing.append("comprobar la longitud de la entrada")
    if not any(marker in normalized for marker in ("8", "sizeof", "size")):
        missing.append("comparar con el límite de 8 casillas")
    if not any(marker in normalized for marker in ("reject", "rechazar", "return", "error")):
        missing.append("rechazar la entrada que supera el límite")
    if missing:
        return PatchResult(False, "El búfer sigue expuesto. " + "; ".join(missing) + ".", tuple(missing))
    return PatchResult(
        True,
        "Parche correcto: la entrada se valida antes de copiarla y no pisa la dirección de retorno.",
    )


def validate_auth_patch(code: str) -> PatchResult:
    normalized = " ".join(code.lower().split())
    missing = []
    if not any(marker in normalized for marker in ("mfa", "2fa", "doble", "multifactor")):
        missing.append("activar MFA")
    if not any(marker in normalized for marker in ("bloque", "lockout", "intentos", "rate")):
        missing.append("limitar intentos y bloquear temporalmente")
    if not any(marker in normalized for marker in ("hash", "sal", "bcrypt", "argon")):
        missing.append("usar hash con sal")
    if not any(marker in normalized for marker in ("longitud", "length", "password_policy", "contraseña")):
        missing.append("exigir una política de contraseña")
    if missing:
        return PatchResult(
            False,
            "La cuenta aún resiste poco al ataque. " + "; ".join(missing) + ".",
            tuple(missing),
        )
    return PatchResult(
        True,
        "Parche correcto: la política, el bloqueo, MFA y el almacenamiento seguro reducen el riesgo de fuerza bruta.",
    )
