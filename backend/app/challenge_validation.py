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
    if "+" in normalized or "f\"" in normalized or "f'" in normalized:
        missing.append("eliminar la concatenación o interpolación")

    if missing:
        return PatchResult(
            correct=False,
            explanation="La consulta aún mezcla código y datos. " + "; ".join(missing) + ".",
            missing=tuple(missing),
        )
    return PatchResult(
        correct=True,
        explanation="Parche correcto: el marcador y los valores se envían separados; "
        "la entrada ficticia del atacante ya no cambia la estructura de la consulta.",
    )
