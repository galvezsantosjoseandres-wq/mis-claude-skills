# Catálogo de skills de seguridad estudiadas

Este directorio **no contiene skills instaladas**. Es un registro de skills de
terceros que se revisaron para extraer conocimiento.

## Por qué catálogo y no instalación

Varias skills de seguridad instaladas a la vez compiten por el disparo: todas
tienen descripciones agresivas que casan con "revisa la seguridad de esto", el
modelo elige una de forma no determinista, y el mismo prompt produce auditorías
distintas según cuál se activó.

Peor: cuando dos se contradicen, el criterio aplicado depende de cuál disparó.
No es hipotético — ver la contradicción documentada abajo sobre credenciales en
archivos de prueba.

La arquitectura elegida es una sola skill orquestadora
(`web-project-security-audit`) que absorbe conocimiento ajeno como archivos de
`references/` y `scripts/`, sin heredar reglas que la contradigan.

Skills genuinamente distintas sí conviven bien (auditoría ≠ respuesta a
incidentes ≠ modelado de amenazas ≠ revisión de diff): no colisionan porque las
palabras de intención son distintas. Lo que no puede haber son dos que hagan lo
mismo.

---

## cyber-neo

- **Origen:** https://github.com/Hainrixz/cyber-neo
- **Licencia:** MIT · Copyright (c) 2026 Cyber Neo Contributors
- **Revisado:** 2026-09-13 (commit `dcac0a8`, último commit upstream 2026-07-17)
- **Qué es:** plugin de Claude Code, una skill, 10.310 líneas. Reconocimiento de
  stack → 5 subagentes en paralelo (SCA, SAST, secretos, config/infra, cadena de
  suministro y CI/CD) → reporte. 14 referencias, 2 scripts en Python.
- **Estado:** **NO instalado.** Conocimiento extraído.

### Auditoría de seguridad

Lo limpio, verificado ejecutando y leyendo el código:

| Chequeo | Resultado |
|---|---|
| Egreso de red en los scripts | Ninguno |
| `subprocess` | Un solo uso: `git diff --cached --name-only` |
| Dependencias externas | Cero, solo stdlib |
| Escrituras | Solo `~/Desktop/`, nunca en el proyecto auditado |
| Diseño | *IRON LAW: READ-ONLY*, repetida en cada subagente |

No hay malware ni comportamiento encubierto.

**Hallazgo 1 — Fuga de secretos en claro. Alta.**
`SKILL.md:331` promete *"NEVER include actual secret values in your report.
Redact them."* El script no redacta: la variable se llama `redacted` pero solo
trunca a 200 caracteres (`scripts/scan_secrets.py:350-352`). Verificado
ejecutándolo contra un fixture: devolvió `sk_live_9f3a1c7d24b84e0fa6c5` completo
en el campo `evidence`. El secreto viaja al contexto del subagente, al reporte
fusionado, y acaba en un archivo de texto plano en el Desktop del auditor.

**Hallazgo 2 — `Bash(python3 *)` pre-aprobado. Media.**
El frontmatter pre-autoriza `python3` con cualquier argumento, lo que equivale a
ejecución arbitraria de código sin confirmación. Combinado con que la skill lee
archivos de proyectos no confiables y los inyecta en prompts de subagentes, y con
que **no hay ninguna advertencia sobre tratar el contenido del proyecto auditado
como dato no confiable** (verificado: cero menciones de prompt injection fuera de
definiciones de CWE), queda una superficie de inyección abierta. Riesgo teórico,
no una puerta trasera: requiere auditar un repositorio hostil.

**Hallazgo 3 — el escáner de secretos es ciego a `.github/`, `.circleci/`, `.aws/` y
`.ssh/`. Alta, y solo se detectó al portarlo.**
`scripts/scan_secrets.py:438` descarta del recorrido **todo directorio que empieza
por punto**, no solo los de `SKIP_DIRS`. Efecto: el escáner nunca entra a
`.github/workflows/`, que es justo donde viven los secretos de CI — la categoría que
la propia skill dice cubrir. Peor: los directorios podados no se cuentan en
`files_skipped`, así que el JSON de salida reporta cobertura total (`files_skipped: 0`)
siendo falsa. Verificado con una prueba controlada: la misma cadena de prueba
(`AKIA...`) se detectaba en un directorio normal y desaparecía en uno con punto.
No lo detecté leyendo el código — lo encontró un subagente al validar la versión
portada contra un fixture con workflows, y se confirmó de forma independiente antes
de aceptarlo. Corregido en nuestra copia (`escanear_secretos.py`); no reportado
upstream todavía.

**Si alguien quisiera usarla tal cual**, el mínimo sería: quitar `Bash(python3 *)`
del frontmatter, arreglar la redacción, arreglar la ceguera a dot-dirs, y mover el
destino del reporte fuera del Desktop.

### Contradicción con nuestra skill

Su tabla "RED FLAGS" dice:

> *"Esto probablemente es solo un archivo de test" → Los archivos de test con
> secretos reales sí se commitean. Repórtalo.*

Nuestra skill dice que una credencial ficticia en una suite de pruebas no es una
fuga de producción. Las evals verificaron ese criterio como correcto.

Detalle revelador: **su propio script no obedece a su SKILL.md** — degrada los
hallazgos en archivos de test a severidad `low` en vez de reportarlos como fuga.
El código es más sensato que la instrucción.

### Qué se extrajo

| Elemento | Destino | Estado |
|---|---|---|
| Corpus de 56 patrones de credenciales | `scripts/escanear_secretos.py` | Portado con redacción real, clasificación por contexto y el bug de dot-dirs corregido |
| Cobertura de CI/CD | `references/cicd-security.md` | Reescrito, no copiado; validado contra fixture con 7 vulnerabilidades plantadas |
| Chequeo de lockfiles | — | Descartado: ya cubierto por el bloque de dependencias |

### Validación de lo portado

`references/cicd-security.md` y `scripts/escanear_secretos.py` se probaron contra un
fixture nuevo (`pipeline`, 7 vulnerabilidades de CI/CD plantadas + un workflow correcto
como señuelo) antes de darlos por buenos, no solo se escribieron y commitearon. El
subagente de validación encontró el Hallazgo 3 de arriba y tres huecos de contenido
en la referencia (ejecución vía `npm install`/`postinstall`, explotabilidad real de
`github.head_ref`, ausencia de controles de protección del disparador como
`environment` con revisores o CODEOWNERS sobre `.github/`) — los tres se cerraron
antes del commit final.

### Qué se descartó deliberadamente

- **El *risk score*** `min(100, críticas×25 + altas×10 + medias×3 + bajas×1)`:
  parece cuantitativo, no está calibrado contra nada.
- **La rúbrica de severidad por clase de vulnerabilidad** ("SQL injection = High"):
  es el colapso de un solo eje que nuestra skill corrigió a impacto ×
  explotabilidad. Nuestras evals mostraron el valor de la diferencia: ambas
  corridas bajaron tres "críticas" de npm a Media porque el paquete afectado
  nunca se importa.
- **El reporte a `~/Desktop/`**: específico de macOS y fuera del proyecto. Nuestro
  `security-audit/` en el repo es lo que habilita los modos Rápido y Diff.
- **Los 5 subagentes en paralelo**: cambio arquitectónico grande, y costaría la
  contención en proyectos simples que nuestras evals miden como buena.
- **La fila RED FLAGS sobre archivos de test**: contradice nuestro triaje.
