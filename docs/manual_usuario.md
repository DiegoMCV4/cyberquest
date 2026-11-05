# Manual de instalación y ejecución

## Requisitos

- Docker Desktop con Compose.
- Navegador actualizado.
- PowerShell (Windows) o una terminal compatible.

## Instalación

```powershell
Copy-Item .env.example .env
# Edita .env y cambia las contraseñas y JWT_SECRET
docker compose up --build
```

Abre `http://localhost:8080`. Comprueba el servicio en
`http://localhost:8080/health`. Para detenerlo:

```powershell
docker compose down
```

La documentación de desarrollo de la API está en
`http://localhost:8080/api/docs`.

## Cómo jugar

1. Regístrate e inicia sesión.
2. Lee el aviso ético y completa el tutorial.
3. Realiza el pre-test, repara los tres módulos y lee cada explicación.
4. Usa Escape Room para BD/código y Detective para ingeniería social.
5. Si pierdes las vidas, elige **Reintentar nivel**; el progreso no se borra.
6. Completa el post-test y revisa las estadísticas finales.

El directorio `lab/` es un laboratorio opcional, local y aislado para la
demostración técnica. No lo expongas a Internet ni lo uses contra sistemas
sin autorización.

