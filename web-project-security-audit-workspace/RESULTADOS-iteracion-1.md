# Resultados — iteración 1

Comparación: **monolito** (`skill-snapshot/`, versión previa al split) contra
**split** (`references/` por dominio). Mismo modelo, mismos prompts, mismos
fixtures, corridas lanzadas en paralelo.

## Calidad

| Eval | Split | Monolito |
|---|---|---|
| recall-y-precision-proyecto-con-backend | 13/13 | 13/13 |
| contencion-en-proyecto-simple | 6/6 | 5/6 |
| modo-enfocado-dependencias | 5/5 | 5/5 |
| **Total** | **24/24 (100%)** | **23/24 (95,8%)** |

La única diferencia es un ítem de *sospechas a verificar* del monolito sobre
2FA del equipo en un sitio de un solo desarrollador. Es una diferencia de
criterio menor, no un defecto: no debe leerse como que el split sea mejor
auditando. **En calidad, empate.**

Sobre el fixture con respuesta conocida, ambas versiones lograron
**recall 12/12** sobre las vulnerabilidades plantadas y **3/3** señuelos
descartados correctamente.

## Coste

| Eval | Tokens split | Tokens monolito | Δ |
|---|---|---|---|
| proyecto con backend | 106.141 | 111.262 | −4,6% |
| proyecto simple | 76.472 | 80.897 | −5,5% |
| modo enfocado | 97.176 | 108.825 | −10,7% |
| **Media** | **93.263** | **100.328** | **−7,0%** |

| Eval | Bytes de reporte split | Monolito | Δ |
|---|---|---|---|
| proyecto con backend | 84.290 | 118.163 | −28,7% |
| proyecto simple | 29.918 | 45.225 | −33,8% |

## Ruteo (el riesgo que motivó medir)

| Eval | Referencias leídas | Correcto |
|---|---|---|
| proyecto con backend | 5 de 7 (omitió infraestructura e IA) | Sí — sin Docker/K8s ni modelo de IA |
| proyecto simple | 1 de 7 (solo entrada-externa) | Sí — solo hay un formulario |
| modo enfocado | 0 de 7 | Sí — dependencias es bloque transversal de SKILL.md |

El ruteo funcionó en los tres casos, incluido el de no activar ninguno.
Ninguna corrida leyó las 7 referencias "por si acaso" ni omitió una que
aplicara.

## Conclusión

El split **no mejora la calidad de la auditoría** y no era su objetivo.
Lo que compra, medido: ~7% menos tokens, reportes ~30% menos verbosos
sin perder hallazgos, y espacio para profundizar cada dominio sin
cobrárselo a quien audita un proyecto simple. El riesgo que justificaba
medir —que el modelo no abriera el archivo correcto— no se materializó.

## Limitaciones de esta medición

- **n=1 por celda.** Sin repeticiones no hay varianza; diferencias menores
  al ~10% no son distinguibles de ruido.
- **Dos fixtures sintéticos**, escritos por quien diseñó las aserciones.
- **El ground truth resultó incompleto**: ambas corridas encontraron una
  vulnerabilidad no catalogada (clave de firma de sesión trivial en
  `src/server.js:11`) y matizaron la SQLi correctamente como código muerto.
- **Una aserción no es verificable por regex** (detección de inflado sobre
  prosa); quedó en rojo a propósito en vez de ajustar el patrón hasta
  que diera verde.
