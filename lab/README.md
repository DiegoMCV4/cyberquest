# Laboratorio aislado de vulnerabilidades

Este laboratorio es deliberadamente vulnerable y solo debe ejecutarse en local.
No se incluye en el `docker-compose.yml` principal del juego.

```powershell
cd lab
docker compose up --build
```

## Reto SQL Injection

Instancia vulnerable:

```powershell
curl "http://127.0.0.1:8090/search?username='%20OR%20'1'='1"
```

Instancia corregida:

```powershell
curl "http://127.0.0.1:8091/search?username=' %20OR%20'1'='1"
```

La instancia corregida usa consultas parametrizadas. Documenta el resultado,
el impacto y el vector CVSS en el informe sin conectarla a datos reales.
