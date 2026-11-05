# Ciudad Red: La Gran Brecha — Fase 5

Videojuego educativo web sobre redes, seguridad, bases de datos y programación.

## Ejecutar con Docker

1. Copia `.env.example` como `.env`.
2. Cambia `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` y `JWT_SECRET`.
3. Ejecuta:

```powershell
docker compose up --build
```

Si ya existía un volumen de MySQL de una versión anterior, el arranque crea
automáticamente las tablas nuevas mediante `Base.metadata.create_all`; conserva
los datos existentes. Para una instalación limpia de demostración:

```powershell
docker compose down -v
docker compose up --build
```

No uses `down -v` en producción: elimina el volumen de datos.

También puedes iniciarlo desde PowerShell con:

```powershell
npm start
```

Este comando solo es un atajo para `docker compose up --build`; no instala
dependencias de Node.js. Para detener los servicios usa `npm run stop`.

Abre el juego en <http://localhost:8080>. La documentación de la API, si se
habilita para desarrollo, está disponible detrás del proxy en
<http://localhost:8080/api/docs>.

La primera ejecución crea las tablas y carga automáticamente **200 preguntas
educativas sin duplicados exactos**, distribuidas en redes, vulnerabilidades,
bases de datos y programación, con tres niveles de dificultad.
El panel `📝` permite realizar un pre-test y un post-test por tema; el resumen
muestra el porcentaje y la mejora entre ambas evaluaciones. Las preguntas falladas se priorizan posteriormente para reforzar el
aprendizaje y el modo adaptativo ajusta la dificultad según el rendimiento
reciente del jugador.

El botón `⚙️` permite guardar volumen, dificultad adaptativa o fija y consultar
logros. Los comodines se gestionan en el perfil persistente del jugador.

La API no se publica directamente en el host: el acceso recomendado es mediante
<http://localhost:8080/api/>; el estado está disponible en
<http://localhost:8080/health>. Para producción se debe colocar TLS delante de
Nginx y cambiar todos los secretos del archivo `.env`.

## Ejecutar el backend sin Docker

Requiere Python 3.12 y un servidor MySQL disponible.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL="mysql+pymysql://cyberquest:clave@localhost:3306/cyberquest"
$env:JWT_SECRET="un-secreto-local-de-al-menos-32-caracteres"
uvicorn app.main:app --reload
```

## Controles

- Moverse: WASD, flechas o clic.
- Acercarse a un módulo para iniciar su reto.
- Cada respuesta muestra una explicación educativa.
- Una respuesta correcta daña al enemigo; una incorrecta consume una vida.
- El primer inicio muestra un tutorial jugable de movimiento y combate.
- El botón `📝` abre pre-test y post-test por tema.

## Rúbrica UNACH: niveles y mecánicas

Alex es el programador protagonista que parchea tres módulos de Ciudad Red.
Los retos son ficticios, seguros y no deben ejecutarse contra sistemas reales:

1. **Cámara de Bases de Datos:** el jugador corrige una consulta insegura
   seleccionando parámetros en el Escape Room. La mecánica representa
   parametrización y separación entre código y datos.
2. **Laboratorio de Código:** el jugador elige validación de longitud,
   escape de salida y almacenamiento seguro de credenciales. La mecánica es
   revisión de código, no una pregunta decorativa.
3. **Expediente de Ingeniería Social:** el jugador analiza mensajes, DNS y
   registros ficticios y reúne evidencias. La mecánica es clasificar señales y
   justificar una decisión.

Las preguntas del mapa funcionan como refuerzo entre retos. El post-test se
habilita en el servidor después de completar al menos tres jefes/módulos.
El selector evita preguntas ya vistas por el jugador hasta agotar las
disponibles del tema y dificultad; después reutiliza primero las que falló.
Al perder todas las vidas se muestra una pantalla educativa de derrota con
opción de reintentar sin borrar el progreso guardado.

Todo el contenido es educativo y autorizado. El laboratorio vulnerable de
`lab/` es opcional, local y aislado; no forma parte del flujo obligatorio del
juego.

## Editor ficticio del Nivel 1

En **Escape Room → Cámara de Bases de Datos → Abrir editor SQL**, el jugador
reescribe una consulta ficticia para corregir la inyección SQL. El validador
acepta únicamente reglas educativas: marcador de parámetro, valores separados
y llamada simulada a `execute`; rechaza concatenación e interpolación. El texto
no se ejecuta como Python ni como SQL y el avance se guarda mediante la API.
El modo de opciones original permanece disponible como alternativa.

Capturas nuevas para el documento y la presentación:

1. Editor mostrando la consulta insegura y la entrada ficticia del atacante.
2. Editor con un parche incompleto y el mensaje que indica qué falta.
3. Editor con el parche aceptado, XP y módulo SQL reparado.
4. Escape Room mostrando el progreso persistente del reto `bd-select`.

## Fase 2: distritos y jefes

Cada distrito contiene cuatro enemigos. Al derrotarlos aparece su jefe:

- Redes: **Interceptor MITM** — Man-in-the-Middle.
- Seguridad: **Phisher Supremo** — Phishing.
- Bases de Datos: **Inyector SQL** — SQL Injection.
- Programación: **Señor DDoS** — DDoS.

El servidor valida que los cuatro enemigos del distrito hayan sido derrotados
antes de aceptar la victoria del jefe. Cada jefe entrega una recompensa de XP
persistente y solo puede derrotarse una vez.

## Fase 3: Tower Defense

El botón `🛡️ Redes` abre la defensa del servidor central. Hay cinco oleadas:
SYN flood, escaneo de puertos, sniffing, intrusión desconocida y ataque
coordinado. Cada respuesta consume una pregunta de Redes. Si aciertas,
despliegas una defensa; si fallas, el servidor recibe daño. Las defensas son
Firewall, ACL, IDS y Cifrado. La defensa adecuada reduce el daño y completar
las cinco oleadas entrega una recompensa de 150 XP.

## Fase 4: Escape Room

El botón `🚪 Escape Room` abre dos salas: Bases de Datos y Programación. Cada
sala contiene cuatro retos prácticos con consultas SQL, normalización, roles,
XSS, contraseñas y validación de entradas. Una respuesta correcta otorga XP;
las pistas cuestan 5 puntos y completar una sala entrega una recompensa
adicional. El progreso se guarda por jugador y las respuestas se validan en el
backend.

## Fase 5: modo detective y caso final

El botón `🕵️ Detective` abre el expediente de la Gran Brecha. El jugador
analiza registros de autenticación y DNS, una captura tipo Wireshark, datos
OSINT y una línea de tiempo. Cada análisis correcto crea una evidencia
persistentemente asociada al jugador y entrega XP.

Después de reunir las cinco evidencias y derrotar a los cuatro jefes de
distrito se desbloquea el caso final. La conclusión se valida en el servidor
y entrega 300 XP. El endpoint de derrota directa no puede marcar el final sin
resolver la investigación.

## Fase 6: pulido y experiencia final

La interfaz incluye una tabla de puntajes conectada a `/game/ranking`, acceso
directo al caso final, microanimaciones de combate, efectos de cámara y una
preferencia persistente para activar o silenciar el audio. El botón `🤖
Mentor` ofrece pistas progresivas mediante `/game/mentor/hint`; funciona sin
servicios externos, no revela índices correctos y deja la arquitectura lista
para sustituir el motor local por un proveedor de IA en el futuro.

## API principal

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /game/questions?zone=redes&count=1`
- `POST /game/questions/{id}/answer`
- `GET /game/progress`
- `GET /game/districts`
- `GET /game/escape-room/{room}`
- `POST /game/escape-room/{room}/reset`
- `POST /game/escape-room/answer`
- `POST /game/escape-room/hint`
- `GET /game/detective/state`
- `POST /game/detective/answer`
- `POST /game/detective/reset`
- `GET /game/detective/evidence`
- `GET /game/final-boss/state`
- `POST /game/final-boss/answer`
- `POST /game/mentor/hint`
- `GET /game/ranking`
- Administración protegida: `GET/POST/DELETE /game/questions`

El motor nunca envía la respuesta correcta al cliente al solicitar preguntas.
Las respuestas se comprueban en el servidor con consultas parametrizadas.
