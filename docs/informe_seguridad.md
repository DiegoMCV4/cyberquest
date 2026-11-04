# Informe de seguridad de CyberQuest

Auditoría interna del propio proyecto (Análisis de Vulnerabilidades). Puntuación **CVSS v3.1** calculada con la fórmula oficial a partir del vector que se muestra; el vector describe el escenario **sin** el control aplicado. Valídalo con la calculadora de FIRST antes de entregar.

## 1. Resumen

| ID | Hallazgo | Vector CVSS v3.1 | Puntaje | Severidad | Estado |
|---|---|---|---|---|---|
| V-01 | Inyección SQL | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` | 9.8 | Crítica | Mitigado |
| V-02 | Fuerza bruta en el login | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N` | 8.2 | Alta | Mitigado (falta MFA) |
| V-03 | Respuestas correctas expuestas al cliente | `AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:L/A:N` | 4.3 | Media | Mitigado |
| V-04 | Robo del token por XSS | `AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N` | 5.4 | Media | Mitigado |
| V-05 | JWT_SECRET por defecto o débil | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N` | 6.5 | Media | Mitigado |
| V-06 | Tráfico sin cifrar (HTTP) | `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:L/A:N` | 6.5 | Media | Pendiente |
| V-07 | Puerto 8000 de la API expuesto directamente | `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L` | 5.3 | Media | Mitigado |
| V-08 | Phaser remoto sin Subresource Integrity | `AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:N` | 6.5 | Media | Mitigado |
| V-09 | Dependencias Python desactualizadas | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N` | 6.5 | Media | Mitigado |

## 2. Detalle y controles

**V-01 – Inyección SQL** (9.8, Crítica). Control: Consultas parametrizadas con SQLAlchemy y validación de esquemas (Pydantic); usuario de BD sin acceso a otras bases. Estado: Mitigado.

**V-02 – Fuerza bruta en el login** (8.2, Alta). Control: Límite de 5 intentos/min por IP, contraseñas con bcrypt, mensaje de error genérico (no revela si el usuario existe). Estado: Mitigado (falta MFA).

**V-03 – Respuestas correctas expuestas al cliente** (4.3, Media). Control: La validación se hace solo en el servidor; el XP se otorga una única vez por pregunta. Estado: Mitigado.

**V-04 – Robo del token por XSS** (5.4, Media). Control: Token solo en memoria (sin localStorage), CSP restrictiva, cabeceras de seguridad y texto insertado con textContent. Estado: Mitigado.

**V-05 – JWT_SECRET por defecto o débil** (6.5, Media). Control: La API se niega a arrancar si el secreto es corto o de ejemplo; se define en .env (fuera de Git). Estado: Mitigado.

**V-06 – Tráfico sin cifrar (HTTP)** (6.5, Media). Control: Pendiente: en producción poner TLS (Caddy/Let's Encrypt o certificado en nginx). Estado: Pendiente.

**V-07 – Puerto 8000 de la API expuesto directamente** (5.3, Media). Control: Se eliminó el mapeo "8000:8000"; la API queda en la red interna y solo Nginx se publica al host. Estado: Mitigado.

**V-08 – Phaser remoto sin Subresource Integrity** (6.5, Media). Control: El script CDN ahora usa un hash SHA-384 con `integrity` y `crossorigin`. Estado: Mitigado.

**V-09 – Dependencias Python desactualizadas** (6.5, Media). Control: Se actualizaron
FastAPI, cryptography y PyJWT a versiones corregidas; `pip-audit -r
backend/requirements.txt` no reporta vulnerabilidades conocidas al momento de la
auditoría. Debe repetirse antes de cada entrega. Estado: Mitigado.

## 3. Pruebas recomendadas (solo contra tu propia instancia local)

- OWASP ZAP (escaneo activo sobre http://localhost:8080)
- Intentar SQLi y XSS manualmente en los campos de login para documentar que son rechazados
- `pip-audit` sobre requirements.txt y `docker scout`/`trivy` sobre las imágenes
- Nmap sobre localhost para confirmar puertos expuestos (8080 y 8000)

## 4. Conclusiones

El diseño aplica defensa en profundidad (validación, hash, límites, CSP, mínimo privilegio). Lo pendiente (TLS y cierre del puerto 8000) corresponde al despliegue en producción.
