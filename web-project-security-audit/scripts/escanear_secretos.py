#!/usr/bin/env python3
"""
escanear_secretos.py — detección de credenciales sin dependencias externas.

Existe para cerrar un hueco concreto de la skill: recomendamos `gitleaks`,
prohibimos instalarlo con `curl | bash`, y el fallback era un `grep` manual
que la propia skill califica de "peor que no haberlo hecho". Esto es el
fallback decente: solo stdlib, sin red, sin instalar nada.

PROCEDENCIA
Adaptado de `scan_secrets.py` del proyecto cyber-neo
(https://github.com/Hainrixz/cyber-neo), licencia MIT,
Copyright (c) 2026 Cyber Neo Contributors. El corpus de 56 patrones de
credenciales viene de ahí y es la parte de más valor del original.

CAMBIOS RESPECTO AL ORIGINAL (ambos son correcciones de seguridad):

1. REDACCIÓN REAL. El original nombra `redacted` a una variable que solo
   trunca a 200 caracteres: el secreto sale completo en el campo `evidence`,
   contradiciendo su propio SKILL.md ("NEVER include actual secret values").
   Verificado ejecutándolo: devolvía `sk_live_9f3a1c7d24b84e0fa6c5` en claro.
   Aquí el valor se enmascara antes de salir — se conserva solo el prefijo
   necesario para identificar al proveedor y localizar la línea.

2. CLASIFICACIÓN POR CONTEXTO en vez de solo rebaja de severidad. El original
   baja la severidad en archivos de prueba pero los mezcla con los hallazgos
   de producción. La skill distingue código de primera parte, de pruebas y
   vendorizado, y aplica rigor distinto a cada uno: el campo `contexto` deja
   esa decisión explícita en lugar de enterrarla en la severidad.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────

MAX_FILE_SIZE_KB = 500
MAX_LINE_LENGTH = 2000

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
    ".next", ".nuxt", "vendor", "target", "Pods", ".gradle",
    "coverage", ".nyc_output", ".cache", "bower_components",
    # Dot-dirs ruidosos anadidos al portar: antes quedaban cubiertos por un
    # descarte generico de todo lo que empieza por punto, que causaba el bug
    # descrito abajo.
    ".idea", ".vscode", ".svn", ".hg", ".terraform", ".serverless",
    ".pnpm-store", ".yarn", ".turbo", ".parcel-cache",
}

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp3", ".mp4", ".avi", ".mov", ".webm",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".pyc", ".pyo", ".class", ".o", ".so", ".dylib", ".dll",
    ".exe", ".bin", ".dat", ".db", ".sqlite", ".sqlite3",
    ".lock",  # Lock files have long hashes that trigger false positives
    ".map",
}

SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Pipfile.lock", "poetry.lock", "Cargo.lock", "Gemfile.lock",
    "go.sum", "composer.lock",
}

# ─── Secret Patterns ────────────────────────────────────────────────────────
# Each pattern: (name, regex, severity, description)

PATTERNS = [
    # AWS
    ("AWS Access Key ID", r"AKIA[0-9A-Z]{16}", "critical",
     "AWS access key ID — provides direct access to AWS services"),
    ("AWS Secret Access Key", r"(?i)aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{40}['\"]?", "critical",
     "AWS secret access key"),
    ("AWS MWS Key", r"amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "critical",
     "Amazon MWS auth token"),

    # GCP
    ("GCP API Key", r"AIza[0-9A-Za-z_-]{35}", "high",
     "Google Cloud API key"),
    ("GCP Service Account", r'"type"\s*:\s*"service_account"', "critical",
     "GCP service account JSON key file"),

    # Azure
    ("Azure Connection String", r"(?i)DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]{88}", "critical",
     "Azure Storage connection string"),

    # GitHub
    ("GitHub PAT (classic)", r"ghp_[A-Za-z0-9_]{36}", "critical",
     "GitHub personal access token"),
    ("GitHub OAuth", r"gho_[A-Za-z0-9_]{36}", "critical",
     "GitHub OAuth access token"),
    ("GitHub App Token", r"ghu_[A-Za-z0-9_]{36}", "high",
     "GitHub user-to-server token"),
    ("GitHub App Install Token", r"ghs_[A-Za-z0-9_]{36}", "high",
     "GitHub server-to-server token"),
    ("GitHub Refresh Token", r"ghr_[A-Za-z0-9_]{36}", "critical",
     "GitHub refresh token"),
    ("GitHub Fine-Grained PAT", r"github_pat_[A-Za-z0-9_]{22,255}", "critical",
     "GitHub fine-grained personal access token"),

    # GitLab
    ("GitLab PAT", r"glpat-[A-Za-z0-9_-]{20}", "critical",
     "GitLab personal access token"),

    # Slack
    ("Slack Bot Token", r"xoxb-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24}", "critical",
     "Slack bot token"),
    ("Slack User Token", r"xoxp-[0-9]{10,13}-[0-9]{10,13}-[0-9]{10,13}-[a-f0-9]{32}", "critical",
     "Slack user token"),
    ("Slack Webhook", r"https://hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[A-Za-z0-9]{24}", "high",
     "Slack incoming webhook URL"),

    # Stripe
    ("Stripe Live Secret Key", r"sk_live_[0-9a-zA-Z]{24,}", "critical",
     "Stripe live secret key — can charge real money"),
    ("Stripe Live Publishable Key", r"pk_live_[0-9a-zA-Z]{24,}", "medium",
     "Stripe live publishable key (limited risk but should not be in source)"),
    ("Stripe Restricted Key", r"rk_live_[0-9a-zA-Z]{24,}", "critical",
     "Stripe restricted API key"),

    # Twilio
    ("Twilio API Key", r"SK[0-9a-fA-F]{32}", "high",
     "Twilio API key"),

    # SendGrid
    ("SendGrid API Key", r"SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}", "critical",
     "SendGrid API key"),

    # Mailgun
    ("Mailgun API Key", r"key-[0-9a-zA-Z]{32}", "high",
     "Mailgun API key"),

    # Firebase
    ("Firebase Config", r"(?i)firebase[A-Za-z]*\s*[=:]\s*['\"][A-Za-z0-9_-]+['\"]", "medium",
     "Firebase configuration value"),

    # Database Connection Strings
    ("PostgreSQL Connection", r"postgres(?:ql)?://[^\s'\"]+:[^\s'\"]+@[^\s'\"]+", "critical",
     "PostgreSQL connection string with credentials"),
    ("MySQL Connection", r"mysql://[^\s'\"]+:[^\s'\"]+@[^\s'\"]+", "critical",
     "MySQL connection string with credentials"),
    ("MongoDB Connection", r"mongodb(?:\+srv)?://[^\s'\"]+:[^\s'\"]+@[^\s'\"]+", "critical",
     "MongoDB connection string with credentials"),
    ("Redis Connection", r"redis://[^\s'\"]*:[^\s'\"]+@[^\s'\"]+", "high",
     "Redis connection string with credentials"),

    # Private Keys
    ("RSA Private Key", r"-----BEGIN RSA PRIVATE KEY-----", "critical",
     "RSA private key"),
    ("EC Private Key", r"-----BEGIN EC PRIVATE KEY-----", "critical",
     "EC private key"),
    ("DSA Private Key", r"-----BEGIN DSA PRIVATE KEY-----", "critical",
     "DSA private key"),
    ("PGP Private Key", r"-----BEGIN PGP PRIVATE KEY BLOCK-----", "critical",
     "PGP private key block"),
    ("Generic Private Key", r"-----BEGIN PRIVATE KEY-----", "critical",
     "Generic private key (PKCS#8)"),
    ("OpenSSH Private Key", r"-----BEGIN OPENSSH PRIVATE KEY-----", "critical",
     "OpenSSH private key"),

    # JWT
    ("JWT Token", r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "high",
     "JSON Web Token (may contain sensitive claims)"),

    # npm
    ("npm Token", r"(?i)npm_[A-Za-z0-9]{36}", "critical",
     "npm access token"),
    ("npm Auth Token", r"//registry\.npmjs\.org/:_authToken=[^\s]+", "critical",
     "npm registry auth token in .npmrc"),

    # PyPI
    ("PyPI Token", r"pypi-[A-Za-z0-9_-]{50,}", "critical",
     "PyPI API token"),

    # Telegram
    ("Telegram Bot Token", r"[0-9]{8,10}:[A-Za-z0-9_-]{35}", "high",
     "Telegram bot API token"),

    # Discord
    ("Discord Bot Token", r"(?i)(?:discord|bot).*?['\"][A-Za-z0-9_-]{24}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27}['\"]", "high",
     "Discord bot token"),
    ("Discord Webhook", r"https://discord(?:app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+", "high",
     "Discord webhook URL"),

    # Heroku
    ("Heroku API Key", r"(?i)heroku.*?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "high",
     "Heroku API key"),

    # Shopify
    ("Shopify Token", r"shpat_[a-fA-F0-9]{32}", "critical",
     "Shopify admin API token"),
    ("Shopify Shared Secret", r"shpss_[a-fA-F0-9]{32}", "critical",
     "Shopify shared secret"),

    # Datadog
    ("Datadog API Key", r"(?i)dd(?:og)?_?api_?key\s*[=:]\s*['\"]?[a-f0-9]{32}['\"]?", "high",
     "Datadog API key"),

    # OpenAI
    ("OpenAI API Key", r"sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}", "critical",
     "OpenAI API key"),
    ("OpenAI Project Key", r"sk-proj-[A-Za-z0-9_-]{40,}", "critical",
     "OpenAI project API key"),

    # Anthropic
    ("Anthropic API Key", r"sk-ant-[A-Za-z0-9_-]{40,}", "critical",
     "Anthropic API key"),

    # Generic Patterns
    ("Hardcoded Password", r"(?i)(?:password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{8,}['\"]", "high",
     "Hardcoded password in source code"),
    ("Hardcoded Secret", r"(?i)(?:secret|secret_key)\s*[=:]\s*['\"][^'\"]{8,}['\"]", "high",
     "Hardcoded secret in source code"),
    ("Hardcoded API Key", r"(?i)(?:api_key|apikey|api-key)\s*[=:]\s*['\"][^'\"]{8,}['\"]", "high",
     "Hardcoded API key in source code"),
    ("Hardcoded Token", r"(?i)(?:access_token|auth_token|bearer)\s*[=:]\s*['\"][^'\"]{8,}['\"]", "high",
     "Hardcoded token in source code"),
    ("Authorization Header", r"(?i)authorization['\"]?\s*[=:]\s*['\"]?Bearer\s+[A-Za-z0-9_.-]{20,}", "high",
     "Hardcoded Authorization Bearer token"),
    ("Basic Auth Header", r"(?i)authorization['\"]?\s*[=:]\s*['\"]?Basic\s+[A-Za-z0-9+/=]{20,}", "high",
     "Hardcoded Basic auth credentials"),

    # .env file patterns (unquoted values)
    ("Env Password", r"(?i)^(?:DB_PASSWORD|DATABASE_PASSWORD|MYSQL_PASSWORD|POSTGRES_PASSWORD|REDIS_PASSWORD|PASSWORD)\s*=\s*\S{6,}", "high",
     "Password in environment variable file"),
    ("Env Secret Key", r"(?i)^(?:SECRET_KEY|JWT_SECRET|SESSION_SECRET|ENCRYPTION_KEY|APP_SECRET|AUTH_SECRET)\s*=\s*\S{6,}", "high",
     "Secret key in environment variable file"),
    ("Env API Key", r"(?i)^(?:API_KEY|APIKEY|API_SECRET|APP_KEY|PRIVATE_KEY)\s*=\s*\S{6,}", "high",
     "API key in environment variable file"),
]

# Patterns that indicate a file is a test/example/doc (lower severity)
TEST_INDICATORS = {
    "test", "tests", "spec", "specs", "mock", "mocks",
    "fake", "fakes", "fixture", "fixtures", "example", "examples",
    "sample", "samples", "demo", "demos", "dummy", "stub", "stubs", "seed",
}

# ─── Allowlist patterns (common false positives) ────────────────────────────

ALLOWLIST_REGEXES = [
    # Placeholder values like "your_api_key", "test-secret", "dummy_token"
    re.compile(r"['\"](?:your|example|fake|dummy|placeholder|xxx|TODO)[_-]", re.IGNORECASE),
    re.compile(r"sk_test_"),   # Stripe test keys are safe
    re.compile(r"pk_test_"),   # Stripe test publishable keys are safe
    # Password fields with common placeholder values (exact match, not prefix)
    re.compile(r"(?i)password\s*[=:]\s*['\"](?:password|changeme|secret|admin|test|example)['\"]"),
]

ALLOWLIST_WORDS = [
    "placeholder", "your_", "your-", "xxx", "todo",
    "changeme", "test_key", "replace_me", "insert_", "<your", "${", "{{",
]

# Regex pattern to detect placeholder-style values (not real secrets)
PLACEHOLDER_RE = re.compile(
    r"(?:example|fake|dummy|sample)[-_](?:key|secret|token|password|api)",
    re.IGNORECASE
)


def is_allowlisted(line: str, matched_text: str = "") -> bool:
    """Check if a match is a false positive.

    Args:
        line: The full line of code
        matched_text: The specific text that matched the secret pattern
    """
    lower = line.lower()

    # Check general allowlist words against the full line
    if any(w in lower for w in ALLOWLIST_WORDS):
        return True

    # Check regex allowlist patterns (sk_test_, pk_test_, etc.)
    if any(rx.search(line) for rx in ALLOWLIST_REGEXES):
        return True

    # Check for placeholder-style values like "example_secret_key" or "fake-api-key"
    # but NOT hostnames like "example.com" in connection strings
    if PLACEHOLDER_RE.search(line):
        return True

    return False


def is_test_file(filepath: str, target_root: str = "") -> bool:
    """Check if the file is a test/example/fixture file.

    Uses the path relative to target_root to avoid false positives
    from parent directory names (e.g., /home/user/beta-test-app/).
    """
    # Use relative path if target_root is provided
    check_path = filepath
    if target_root:
        try:
            check_path = os.path.relpath(filepath, target_root)
        except ValueError:
            pass  # Different drive on Windows, use full path

    parts = check_path.lower().replace("\\", "/").split("/")
    for part in parts:
        segments = re.split(r"[-_./]", part)
        for segment in segments:
            if segment in TEST_INDICATORS:
                return True
    return False


def should_skip_file(filepath: Path) -> bool:
    """Determine if a file should be skipped."""
    name = filepath.name
    suffix = filepath.suffix.lower()

    if name in SKIP_FILES:
        return True
    if suffix in SKIP_EXTENSIONS:
        return True
    if name.endswith(".min.js") or name.endswith(".min.css"):
        return True

    # Check directory components
    parts = set(filepath.parts)
    if parts & SKIP_DIRS:
        return True

    # Skip large files
    try:
        if filepath.stat().st_size > MAX_FILE_SIZE_KB * 1024:
            return True
    except OSError:
        return True

    return False


VENDOR_INDICATORS = {
    "node_modules", "vendor", "vendored", "third_party", "thirdparty",
    "bower_components", "site-packages", "dist", "build", ".venv", "venv",
}


def clasificar_contexto(filepath: str, target_root: str = "") -> str:
    """primera-parte | test | vendorizado.

    La skill aplica rigor distinto a cada uno: en codigo vendorizado la
    correccion pasa por actualizar la dependencia, no por editar el archivo,
    y una credencial ficticia en una suite de pruebas no es una fuga."""
    partes = {p.lower() for p in Path(filepath).parts}
    if partes & VENDOR_INDICATORS:
        return "vendorizado"
    if is_test_file(filepath, target_root):
        return "test"
    return "primera-parte"


def redactar(linea: str, coincidencia: str) -> str:
    """Enmascara el secreto conservando lo justo para identificarlo.

    Devolver el valor completo convierte al escaner en el vector: el secreto
    viaja al contexto del modelo, al reporte y al archivo en disco.

    Lo que SI se conserva, a proposito: el nombre de la variable y el prefijo
    del proveedor (`sk_live_`, `AKIA`, `ghp_`, `glpat-`). Sin eso el hallazgo
    dice "hay una credencial aqui" pero no cual, y el usuario no sabe que ir a
    rotar — que es la unica accion que importa cuando un secreto se filtro.
    """
    def enmascarar(valor: str) -> str:
        visible = valor[:8] if len(valor) > 16 else valor[:4] if len(valor) > 10 else ""
        return f"{visible}{'*' * 6}[REDACTADO:{len(valor)} chars]"

    salida = linea.strip()
    # Preferencia: redactar solo el literal entrecomillado dentro de la
    # coincidencia, para no borrar el nombre de la variable ni el operador.
    literales = re.findall(r"['\"]([^'\"\s]{6,})['\"]", coincidencia)
    if not literales:
        literales = re.findall(r"['\"]([^'\"\s]{6,})['\"]", salida)
    if literales:
        for valor in sorted(set(literales), key=len, reverse=True):
            salida = salida.replace(valor, enmascarar(valor))
    else:
        crudo = coincidencia.strip().strip("'\"")
        salida = salida.replace(coincidencia.strip(), enmascarar(crudo))

    return salida[:200] + ("..." if len(salida) > 200 else "")


def scan_file(filepath: Path, compiled_patterns: list, target_root: str = "") -> list:
    """Scan a single file for secrets."""
    findings = []

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                # Skip very long lines (likely minified/binary)
                if len(line) > MAX_LINE_LENGTH:
                    continue

                for name, pattern, severity, description in compiled_patterns:
                    match = pattern.search(line)
                    if match:
                        # Skip allowlisted patterns
                        if is_allowlisted(line, match.group(0)):
                            continue

                        # La severidad se rebaja solo fuera del codigo de
                        # primera parte; el campo `contexto` dice por que, para
                        # que el reporte pueda aplicar la regla de triaje de la
                        # skill en vez de heredar una severidad ya masajeada.
                        actual_severity = severity
                        if clasificar_contexto(str(filepath), target_root) != "primera-parte":
                            actual_severity = {"critical": "medium", "high": "low"}.get(severity, severity)

                        findings.append({
                            "type": name,
                            "severity": actual_severity,
                            "contexto": clasificar_contexto(str(filepath), target_root),
                            "file": str(filepath),
                            "line": line_num,
                            "description": description,
                            "evidence": redactar(line, match.group(0)),
                            "redactado": True,
                        })
                        break  # One finding per line to avoid duplicates

    except (OSError, UnicodeDecodeError):
        pass

    return findings


def check_gitignore(target_dir: Path) -> list:
    """Check if sensitive files are properly gitignored."""
    findings = []
    gitignore_path = target_dir / ".gitignore"

    sensitive_patterns = [".env", ".env.local", ".env.production",
                          "*.pem", "*.key", "*.p12", "*.pfx",
                          "credentials.json", "service-account.json"]

    if not gitignore_path.exists():
        findings.append({
            "type": "Missing .gitignore",
            # `info`, no `medium`: no hay evidencia de que se haya filtrado
            # nada. Presentarlo como hallazgo de severidad media infla el
            # reporte, que es justo lo que la Fase A prohibe.
            "severity": "info",
            "contexto": "higiene",
            "file": str(target_dir / ".gitignore"),
            "line": 0,
            "description": "No .gitignore file found — sensitive files may be committed",
            "evidence": "Missing .gitignore",
        })
        return findings

    try:
        gitignore_content = gitignore_path.read_text(encoding="utf-8")
        for pattern in sensitive_patterns:
            # Check for .env files existing but not gitignored
            if pattern == ".env":
                env_files = list(target_dir.glob(".env*"))
                env_files = [f for f in env_files if f.name != ".env.example"
                             and f.name != ".env.sample" and f.name != ".env.template"]
                if env_files and ".env" not in gitignore_content:
                    findings.append({
                        "type": ".env not gitignored",
                        "severity": "high",
                        "contexto": "higiene",
                        "file": str(gitignore_path),
                        "line": 0,
                        "description": f".env files exist ({', '.join(f.name for f in env_files)}) but .env is not in .gitignore",
                        "evidence": "Missing .env in .gitignore",
                    })
    except OSError:
        pass

    return findings


def get_staged_files() -> list:
    """Get list of staged files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return [f for f in result.stdout.strip().split("\n") if f]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def scan_directory(target_dir: Path) -> list:
    """Escanea un arbol de directorios en busca de credenciales.

    `dirs_saltados` existe para que la metadata no afirme cobertura total
    cuando se podaron arboles enteros: un reporte que no dice que NO miro se
    lee como si lo hubiera mirado todo.
    """
    dirs_saltados: list = []
    compiled = [(name, re.compile(pattern), severity, desc)
                for name, pattern, severity, desc in PATTERNS]

    findings = []
    file_count = 0
    skipped_count = 0

    for root, dirs, files in os.walk(target_dir):
        # Skip hidden and known dirs
        # NO descartar todo lo que empieza por punto. El original lo hacia, y
        # eso dejaba `.github/`, `.circleci/`, `.gitlab/`, `.aws/` y `.ssh/`
        # completamente fuera del escaneo — justo donde viven los secretos de
        # CI y las credenciales de despliegue. Verificado: la misma cadena
        # AKIA... se detectaba en `plain/x.yml` y se perdia en
        # `.github/workflows/x.yml`, con la metadata reportando cobertura
        # total. SKIP_DIRS ya enumera los dot-dirs que si conviene saltarse.
        omitidos = [d for d in dirs if d in SKIP_DIRS]
        dirs_saltados.extend(omitidos)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            filepath = Path(root) / filename

            if should_skip_file(filepath):
                skipped_count += 1
                continue

            file_count += 1
            findings.extend(scan_file(filepath, compiled, str(target_dir)))

    # Also check .gitignore coverage
    findings.extend(check_gitignore(target_dir))

    return findings, file_count, skipped_count, sorted(set(dirs_saltados))


def scan_staged() -> list:
    """Scan only git staged files."""
    compiled = [(name, re.compile(pattern), severity, desc)
                for name, pattern, severity, desc in PATTERNS]

    staged_files = get_staged_files()
    findings = []

    for filepath_str in staged_files:
        filepath = Path(filepath_str)
        if filepath.exists() and not should_skip_file(filepath):
            findings.extend(scan_file(filepath, compiled))

    return findings, len(staged_files), 0


def main():
    args = sys.argv[1:]

    if not args:
        print(json.dumps({"error": "Usage: scan_secrets.py <target_dir> | --staged-only"}))
        sys.exit(1)

    output_mode = "json"
    staged_only = False
    target_dir = None

    for arg in args:
        if arg == "--staged-only":
            staged_only = True
        elif arg == "--summary":
            output_mode = "summary"
        elif arg == "--json":
            output_mode = "json"
        else:
            target_dir = arg

    if staged_only:
        findings, file_count, skipped_count = scan_staged()
        if findings:
            # For pre-commit hook: exit 2 to block
            if output_mode == "json":
                print(json.dumps(findings, indent=2))
            else:
                print(f"BLOCKED: Found {len(findings)} potential secret(s) in staged files:")
                for f in findings:
                    print(f"  {f['severity'].upper()}: {f['type']} in {f['file']}:{f['line']}")
            sys.exit(2)
        sys.exit(0)

    if not target_dir:
        print(json.dumps({"error": "No target directory specified"}))
        sys.exit(1)

    target = Path(target_dir).resolve()
    if not target.is_dir():
        print(json.dumps({"error": f"Not a directory: {target}"}))
        sys.exit(1)

    findings, file_count, skipped_count, dirs_saltados = scan_directory(target)

    if output_mode == "summary":
        severity_counts = {}
        for f in findings:
            severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1
        print(f"Scanned {file_count} files ({skipped_count} skipped)")
        print(f"Found {len(findings)} potential secret(s)")
        for sev in ["critical", "high", "medium", "low"]:
            if sev in severity_counts:
                print(f"  {sev.upper()}: {severity_counts[sev]}")
        if findings:
            sys.exit(1)
    else:
        result = {
            "findings": findings,
            "metadata": {
                "files_scanned": file_count,
                "files_skipped": skipped_count,
                "dirs_skipped": dirs_saltados,
                "total_findings": len(findings),
                "cobertura": (
                    "Solo el arbol de trabajo actual. NO cubre el historial de git: "
                    "una clave ya rotada del codigo puede seguir en commits anteriores. "
                    "Para eso hace falta `gitleaks detect --log-opts=\"--all\"`."
                ),
            }
        }
        print(json.dumps(result, indent=2))
        if findings:
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
