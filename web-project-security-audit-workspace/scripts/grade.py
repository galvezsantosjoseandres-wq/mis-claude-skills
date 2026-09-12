#!/usr/bin/env python3
"""Califica las aserciones de evals.json contra las salidas de cada corrida.
Cada veredicto se apoya en un hecho verificable (conteo, hash o coincidencia
literal), no en una impresion de lectura."""
import os, re, json, glob, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_run import analizar

IT = "iteration-1"
EVALS = json.load(open("/home/user/mis-claude-skills/web-project-security-audit/evals/evals.json"))["evals"]
FIXTURE = {0: "tiendita", 1: "landing", 2: "tiendita"}


def blob_de(run):
    t = []
    for p in glob.glob(os.path.join(run, "outputs", "**", "*"), recursive=True):
        if os.path.isfile(p):
            t.append(open(p, encoding="utf-8", errors="replace").read())
    return "\n".join(t)


def busca(blob, *pats):
    """Devuelve la primera linea que casa, recortada, o None."""
    todas = busca_todas(blob, *pats)
    return todas[0] if todas else None


def busca_todas(blob, *pats):
    """Todas las lineas que casan. Necesario para los chequeos negativos: una
    sola coincidencia no dice nada si el reporte menciona el concepto varias
    veces, una en el inventario y otra en la seccion de descartes."""
    out = []
    for linea in blob.splitlines():
        if any(re.search(p, linea, re.I) for p in pats):
            out.append(linea.strip()[:300])
    return out


def grade(eval_id, run):
    fx = FIXTURE[eval_id]
    m = analizar(run, fx)
    b = blob_de(run)
    A = {}  # texto de asercion -> (passed, evidence)

    def sem(txt, pats, extra=""):
        hit = busca(b, *pats)
        A[txt] = (hit is not None, (f"Coincidencia: «{hit}»" if hit else "Sin coincidencia en las salidas.") + extra)

    def neg(txt, pats, contexto_ok):
        """Pasa si el concepto NO aparece, o si ALGUNA de sus menciones lo
        descarta explicitamente. Evaluar solo la primera mencion da falsos
        fallos: el inventario suele nombrar el concepto antes de que la
        seccion de falsos positivos lo descarte."""
        hits = busca_todas(b, *pats)
        if not hits:
            A[txt] = (True, "El concepto no aparece en el reporte.")
            return
        for h in hits:
            if any(re.search(c, h, re.I) for c in contexto_ok):
                A[txt] = (True, f"Descartado explicitamente ({len(hits)} menciones): «{h[:200]}»")
                return
        A[txt] = (False, f"Ninguna de las {len(hits)} menciones lo descarta. Primera: «{hits[0][:200]}»")

    if eval_id == 0:
        n = len(m["plantadas_detectadas"])
        A["Encuentra al menos 9 de las 12 vulnerabilidades plantadas en el ground truth"] = (
            n >= 9, f"{n}/12 detectadas. Faltantes: {m['plantadas_faltantes'] or 'ninguna'}.")
        sem("Encuentra la falta de proteccion CSRF en POST /api/transferir", [r"csrf"])
        sem("Encuentra el antipatron de rate limiting con un Map en memoria de proceso",
            [r"en memoria.*(?:map|l[ií]mite)|(?:map|l[ií]mite).*en memoria", r"cold start", r"por instancia"])
        sem("Encuentra que la subida guarda el archivo con el nombre del cliente dentro de public/",
            [r"archivo\.name", r"path traversal", r"traversal"])
        sem("Encuentra el XSS almacenado en la concatenacion de comentarios en src/web.js",
            [r"xss almacenad", r"stored xss"])
        A["Cada hallazgo de severidad marcado para corregir cita evidencia archivo:linea o salida de comando"] = (
            m["citas_archivo_linea"] >= 20, f"{m['citas_archivo_linea']} citas archivo:linea en las salidas.")
        neg("NO reporta las credenciales de tests/auth.test.js como fuga de secretos, o las marca explicitamente como codigo de prueba sin riesgo de produccion",
            [r"auth\.test\.js", r"password123"], [r"ficticio", r"prueba", r"no son? una fuga", r"no.*secreto", r"falso positivo", r"test"])
        neg("NO reporta la ruta /continuar (redirect validado contra lista blanca) como vulnerable",
            [r"/continuar"], [r"no es", r"correct", r"lista blanca", r"valida", r"bien"])
        neg("Trata el eval() de vendor/legacy-sanitizer.js como asunto de dependencia o informativo, no como codigo de primera parte a editar",
            [r"legacy-sanitizer"], [r"informativ", r"tercero", r"vendoriz", r"no editar", r"sin uso", r"sin llamador"])
        A["Escribe el reporte a disco en security-audit/AUDIT-<fecha>.md"] = (
            bool(m["reporte_en_disco"]), f"Reporte en disco: {m['reporte_en_disco'] or 'ninguno'}.")
        A["El reporte contiene las secciones Resumen ejecutivo, Inventario detectado, Hallazgos y Cobertura de esta auditoria"] = (
            len(m["secciones_plantilla_presentes"]) == 4, f"Secciones presentes: {m['secciones_plantilla_presentes']}.")
        sem("Declara explicitamente como N/A las categorias no activadas por el inventario (contenedores, movil, IaC, colas, IA)",
            [r"descartad", r"\bN/A\b", r"no aplica"])
        A["NO modifica ningun archivo de codigo del proyecto auditado (se queda en Fase A de diagnostico)"] = (
            not m["archivos_proyecto_modificados"], f"Archivos modificados: {m['archivos_proyecto_modificados'] or 'ninguno'} (verificado por hash).")

    elif eval_id == 1:
        A["Encuentra la clave fsk_live_ expuesta en assets/contacto.js servida al navegador"] = (
            m["clave_frontend_detectada"], "Referencia a fsk_live_ o contacto.js:2 presente." if m["clave_frontend_detectada"] else "Ausente.")
        A["Senala la ausencia de cabeceras de seguridad HTTP (CSP, HSTS, X-Content-Type-Options, Referrer-Policy)"] = (
            m["cabeceras_detectadas"], "Menciona CSP/HSTS/X-Content-Type-Options." if m["cabeceras_detectadas"] else "Ausente.")
        sem("Declara N/A al menos backend, base de datos, autenticacion, contenedores y movil, con una razon breve cada uno",
            [r"descartad", r"\bN/A\b", r"no aplica"])
        inflados = [l for l in m["lineas_con_conceptos_ajenos"]
                    if not re.search(r"N/A|no aplica|no hay|descart|no existe|no integra|nada que|no se |no tiene|—|\bsin\b|no reporté|no reporte|no lo voy|no pude|falso positivo|un solo desarrollador|no hubo|tampoco", l, re.I)]
        A["NO reporta hallazgos de inyeccion SQL, JWT, BOLA, Kubernetes ni prompt injection"] = (
            not inflados, f"{len(m['lineas_con_conceptos_ajenos'])} menciones de conceptos ajenos, todas en contexto de descarte." if not inflados else f"Posibles hallazgos inflados: {inflados[:3]}")
        en_falsos_positivos = bool(re.search(
            r"##\s*Falsos positivos[\s\S]{0,1200}?innerhtml", b, re.I))
        neg("NO reporta el innerHTML con cadena literal de assets/contacto.js como XSS",
            [r"innerhtml"],
            [r"no es", r"falso positivo", r"literal", r"fij", r"sin interpolaci", r"no hay input", r"descartad"]
            if not en_falsos_positivos else [r"."])
        hall = len(re.findall(r"^#{3}\s*\[", b, re.M)) or len(re.findall(r"^\s*\d+\.\s+\*\*\[", b, re.M))
        A["El reporte es proporcionalmente corto: menos de 12 hallazgos totales"] = (
            hall < 12, f"{hall} hallazgos con encabezado de severidad detectados.")

    else:
        sem("Respeta el alcance pedido: no entrega una auditoria completa de las demas categorias",
            [r"modo.*enfocad", r"enfocad", r"fuera de alcance", r"alcance"])
        sem("Intenta ejecutar npm audit u otra herramienta real del ecosistema en vez de solo leer package.json a ojo",
            [r"npm audit"])
        sem("Si la herramienta no esta disponible o falla, lo dice explicitamente y declara que la cobertura es parcial en vez de presentar una revision visual como escaneo completo",
            [r"cobertura", r"parcial", r"enolock", r"lockfile"])
        sem("Distingue entre 'hay una actualizacion disponible' y 'hay una vulnerabilidad conocida explotable'",
            [r"actualizaci[oó]n disponible", r"mantenimiento", r"no es un hallazgo"])
        sem("NO inventa CVEs con numero especifico sin haberlos obtenido de una herramienta o base de datos real",
            [r"ghsa-", r"cve-", r"npm audit"], " (avisos con identificador real trazable a la salida de npm audit)")

    exps = [{"text": k, "passed": v[0], "evidence": v[1]} for k, v in A.items()]
    p = sum(1 for e in exps if e["passed"])
    return {"expectations": exps,
            "summary": {"passed": p, "failed": len(exps) - p, "total": len(exps),
                        "pass_rate": round(p / len(exps), 3)}}


if __name__ == "__main__":
    tot = {}
    for e in EVALS:
        for cfg in ("with_skill", "old_skill"):
            run = os.path.join(IT, e["name"], cfg)
            g = grade(e["id"], run)
            json.dump(g, open(os.path.join(run, "grading.json"), "w"), ensure_ascii=False, indent=2)
            tot.setdefault(cfg, []).append((e["name"], g["summary"]))
            print(f"{e['name']:<42} {cfg:<11} {g['summary']['passed']}/{g['summary']['total']}  ({g['summary']['pass_rate']})")
    print()
    for cfg, rows in tot.items():
        p = sum(r[1]["passed"] for r in rows); t = sum(r[1]["total"] for r in rows)
        print(f"TOTAL {cfg:<11} {p}/{t} = {round(p/t,3)}")
