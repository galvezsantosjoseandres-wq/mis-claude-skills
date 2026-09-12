#!/usr/bin/env python3
"""Chequeos mecanicos de una corrida. Produce hechos objetivos que el
calificador semantico usa como base (y que se pueden citar sin opinion)."""
import sys, os, re, json, hashlib, glob

FIXTURES = "/home/user/mis-claude-skills/web-project-security-audit-workspace/fixtures"

# (id, patrones; basta que uno haga match) — deteccion por concepto, no por redaccion
PLANTADAS = [
    ("sqli",                [r"inyecci[oó]n\s+sql", r"sql\s+injection", r"db\.js:1[0-9]", r"SELECT \* FROM usuarios"]),
    ("hash-debil",          [r"sha-?1", r"hash(?:eo|ing)?\s+d[eé]bil", r"bcrypt|scrypt|argon2"]),
    ("cookie-flags",        [r"httponly", r"samesite"]),
    ("csrf",                [r"\bcsrf\b", r"cross-site request forgery"]),
    ("bola",                [r"\bbola\b", r"\bidor\b", r"pertenenc", r"factura/:id", r"autorizaci[oó]n a nivel de objeto"]),
    ("xss-almacenado",      [r"xss\s+almacenad", r"stored\s+xss", r"web\.js:2[5-9]|web\.js:3[0-2]"]),
    ("xss-dom",             [r"innerhtml", r"xss.*dom|dom.*xss"]),
    ("secreto-repo",        [r"sk_live", r"api\.js:[1-9]\b", r"clave.*hardcode|hardcode.*clave|credencial.*c[oó]digo"]),
    ("upload",              [r"archivo\.name", r"path\s+traversal", r"traversal", r"nombre\s+(?:de\s+)?archivo\s+del\s+cliente"]),
    ("open-redirect",       [r"open\s+redirect", r"redirecci[oó]n\s+abierta", r"req\.query\.next", r"redirecci[oó]n\s+no\s+validada"]),
    ("rate-limit-memoria",  [r"en\s+memoria", r"cold\s+start", r"por\s+instancia", r"\bMap\b.*(?:l[ií]mite|rate)|(?:l[ií]mite|rate).*\bMap\b"]),
    ("bopla",               [r"\bbopla\b", r"exposici[oó]n\s+excesiva", r"devuelve.*hash", r"objeto\s+usuario\s+completo", r"/perfil"]),
]

SENUELOS = [
    ("decoy-test",     [r"auth\.test\.js", r"password123", r"test_token"]),
    ("decoy-vendor",   [r"legacy-sanitizer", r"vendor/"]),
    ("decoy-redirect", [r"/continuar", r"DESTINOS_PERMITIDOS"]),
]

SECCIONES = ["resumen ejecutivo", "inventario", "hallazgos", "cobertura"]

# Senales de inflado para el fixture simple: conceptos que NO existen en un
# sitio estatico. Aparecer como descarte N/A es correcto; aparecer como
# hallazgo es inflado. Por eso se devuelve la linea completa, para juzgarlo.
INFLADO = [r"inyecci[oó]n\s+sql", r"\bjwt\b", r"\bbola\b", r"kubernetes",
           r"prompt\s+injection", r"\bcsrf\b", r"contenedor", r"\b2fa\b"]


def leer_outputs(run):
    textos = {}
    for p in glob.glob(os.path.join(run, "outputs", "**", "*"), recursive=True):
        if os.path.isfile(p):
            try:
                textos[p] = open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                pass
    # tambien el reporte dentro del proyecto, si lo escribio ahi
    for p in glob.glob(os.path.join(run, "*", "security-audit", "*.md")):
        textos.setdefault(p, open(p, encoding="utf-8", errors="replace").read())
    return textos


def integridad_fuente(run, fixture):
    """Devuelve la lista de archivos del proyecto modificados respecto al fixture original."""
    orig = os.path.join(FIXTURES, fixture)
    copia = os.path.join(run, fixture)
    cambiados = []
    for raiz, _, archivos in os.walk(orig):
        for a in archivos:
            po = os.path.join(raiz, a)
            rel = os.path.relpath(po, orig)
            pc = os.path.join(copia, rel)
            if not os.path.exists(pc):
                cambiados.append(rel + " (borrado)")
                continue
            ho = hashlib.sha256(open(po, "rb").read()).hexdigest()
            hc = hashlib.sha256(open(pc, "rb").read()).hexdigest()
            if ho != hc:
                cambiados.append(rel)
    return cambiados


def contexto_inflado(blob):
    """Para el fixture simple: cada linea que menciona un concepto ajeno a un
    sitio estatico, para que el calificador decida si es descarte o inflado."""
    salida = []
    for linea in blob.splitlines():
        l = linea.strip()
        if not l:
            continue
        for pat in INFLADO:
            if re.search(pat, l, re.I):
                salida.append(l[:220])
                break
    return salida[:40]


def analizar(run, fixture):
    textos = leer_outputs(run)
    blob = "\n".join(textos.values())
    low = blob.lower()

    if fixture == "landing":
        citas_l = re.findall(r"[\w./-]+\.(?:js|json|html|css|md):\d+", blob)
        return {
            "run": run,
            "fixture": fixture,
            "archivos_salida": sorted(os.path.relpath(p, run) for p in textos),
            "bytes_salida": len(blob),
            "clave_frontend_detectada": bool(re.search(r"fsk_live|contacto\.js:2", blob, re.I)),
            "cabeceras_detectadas": bool(re.search(r"\bcsp\b|content-security-policy|hsts|x-content-type-options", low)),
            "lineas_con_conceptos_ajenos": contexto_inflado(blob),
            "citas_archivo_linea": len(citas_l),
            "reporte_en_disco": [os.path.relpath(p, run) for p in sorted(glob.glob(os.path.join(run, "*", "security-audit", "*.md")))],
            "secciones_plantilla_presentes": [s for s in SECCIONES if s in low],
            "archivos_proyecto_modificados": integridad_fuente(run, fixture),
        }

    encontradas = []
    for vid, pats in PLANTADAS:
        if any(re.search(p, low, re.I) for p in pats):
            encontradas.append(vid)

    senuelos_mencionados = []
    for sid, pats in SENUELOS:
        if any(re.search(p, low, re.I) for p in pats):
            senuelos_mencionados.append(sid)

    citas = re.findall(r"[\w./-]+\.(?:js|json|html|css|md):\d+", blob)
    reporte_en_disco = sorted(glob.glob(os.path.join(run, "*", "security-audit", "*.md")))
    secciones = [s for s in SECCIONES if s in low]

    return {
        "run": run,
        "archivos_salida": sorted(os.path.relpath(p, run) for p in textos),
        "bytes_salida": len(blob),
        "plantadas_detectadas": encontradas,
        "plantadas_faltantes": [v for v, _ in PLANTADAS if v not in encontradas],
        "recall": round(len(encontradas) / len(PLANTADAS), 3),
        "senuelos_mencionados": senuelos_mencionados,
        "citas_archivo_linea": len(citas),
        "citas_unicas": sorted(set(citas))[:25],
        "reporte_en_disco": [os.path.relpath(p, run) for p in reporte_en_disco],
        "secciones_plantilla_presentes": secciones,
        "archivos_proyecto_modificados": integridad_fuente(run, fixture),
    }


if __name__ == "__main__":
    print(json.dumps(analizar(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=2))
