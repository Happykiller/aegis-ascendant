#!/usr/bin/env bash
# Audit du rangement documentaire — l'etat est DERIVE du depot, jamais declare.
#
# POURQUOI CET OUTIL EXISTE. Le champ `Statut` des briefs de forge a ete maintenu
# 5 fois sur 37 : le 2026-08-25, 32 briefs livres portaient encore « assigne » ou
# « brouillon ». Un etat tenu a la main rouille toujours. Celui-ci se lit dans le
# depot : un brief est LIVRE s'il a une sortie dans docs/forge/output/ ou une ligne
# dans ASSET_PROVENANCE.csv. Personne n'a rien a tenir a jour.
#
#   ./scripts/audit-docs.sh          rapport seul
#   ./scripts/audit-docs.sh --fix    range : archive les livres, recale les statuts
#   ./scripts/audit-docs.sh --strict rapport, et sort en erreur s'il y a de la derive
set -euo pipefail
cd "$(dirname "$0")/.."
MODE="${1:-}"
python3 - "$MODE" <<'PYEOF'
import csv, io, os, re, sys, glob, subprocess
mode = sys.argv[1] if len(sys.argv) > 1 else ""
fix = mode == "--fix"
strict = mode == "--strict"

BRIEFS, OUT = "docs/forge/briefs", "docs/forge/output"
PLANS, PROV = "docs/plans", "assets/licenses/ASSET_PROVENANCE.csv"
prov = io.open(PROV, encoding="utf-8").read() if os.path.exists(PROV) else ""
outs = " ".join(os.listdir(OUT)).lower() if os.path.isdir(OUT) else ""
drift = 0

def move(src, dst_dir):
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, os.path.basename(src))
    subprocess.run(["git", "mv", src, dst], check=False, capture_output=True)
    relink(src, dst)

def relink(src, dst):
    """Recale les liens relatifs d'un document qui vient de changer de dossier.

    ⚠️ RANGER CASSAIT CE QU'IL RANGEAIT. Un brief archive descend d'un cran, donc chacun de ses
    `../` pointe un cran trop haut. Mesure du 2026-08-29, avant correctif : **6 liens relatifs
    morts sur 6** dans 52 briefs archives — autrement dit, tout lien relatif ayant traverse
    l'archivage etait mort, depuis le premier jour. Le defaut ne se voyait pas parce qu'un brief
    archive ne se relit presque jamais... jusqu'au jour ou on cherche precisement le plan qui
    l'a motive.

    On re-resout chaque cible depuis l'ancien dossier, puis on la re-exprime depuis le nouveau.
    Les liens qui pointaient deja dans le vide sont laisses tels quels : les reparer serait
    deviner, et ce script ne devine pas.
    """
    if not os.path.exists(dst):
        return
    old_dir, new_dir = os.path.dirname(src), os.path.dirname(dst)
    txt = io.open(dst, encoding="utf-8").read()

    def fix(match):
        target = match.group(1)
        if "://" in target or target.startswith(("/", "#")):
            return match.group(0)
        absolute = os.path.normpath(os.path.join(old_dir, target))
        if not os.path.exists(absolute):
            return match.group(0)
        return "](%s)" % os.path.relpath(absolute, new_dir)

    fixed = re.sub(r"\]\(([^)]+)\)", fix, txt)
    if fixed != txt:
        io.open(dst, "w", encoding="utf-8").write(fixed)

# --- BRIEFS : livre = une sortie OU une ligne de provenance ----------------
stale, open_ = [], []
for path in sorted(glob.glob(os.path.join(BRIEFS, "*.md"))):
    name = os.path.basename(path)
    tag = re.search(r"BRIEF-\d{4}", name)
    if not tag:
        continue
    tag = tag.group(0)
    txt = io.open(path, encoding="utf-8").read()
    m = re.search(r"\*\*Statut\*\* *: *([^\n]+)", txt)
    declared = m.group(1).strip() if m else "(aucun)"
    # ⚠️ LE GRAS N'EST PAS UN STATUT. Un statut ecrit « **livré** (2026-08-28) — … »
    # ne commençait par aucun des mots testes plus bas : il repassait pour OUVERT, et
    # l'audit annoncait « 0 livres » un jour ou deux briefs venaient de l'etre
    # (2026-08-28). On compare donc sur une forme normalisee, sans les asterisques.
    probe = declared.lstrip("*_ ").lower()
    # ⚠️ DERIVE **OU** DECLARE-FINI. Le signal derive sert a rattraper ce que personne
    # n'a pense a marquer ; il ne doit JAMAIS annuler une declaration positive. Sans
    # cette disjonction, BRIEF-0037 et 0038 — declares « integre », mais dont les
    # livrables ne portent pas le numero du brief — repassaient pour ouverts.
    delivered = (tag.lower() in outs or tag in prov
                 or probe.startswith(("livr", "intégr", "integr")))
    if delivered:
        stale.append((tag, name, declared, path))
    elif not probe.startswith(("caduc", "abandon")):
        open_.append((tag, declared))

print("BRIEFS — %d livres, %d encore ouverts" % (len(stale), len(open_)))
menteurs = [s for s in stale if not s[2].lstrip("*_ ").lower().startswith(("livr", "intégr", "integr"))]
if menteurs:
    drift += len(menteurs)
    print("  %d livres dont le statut declare ment :" % len(menteurs))
    for tag, name, declared, path in menteurs[:6]:
        print("     %s  declare « %s »" % (tag, declared))
    if len(menteurs) > 6:
        print("     ... et %d autres" % (len(menteurs) - 6))
for tag, declared in open_:
    print("  ouvert : %s (« %s »)" % (tag, declared))

if fix and stale:
    for tag, name, declared, path in stale:
        txt = io.open(path, encoding="utf-8").read()
        txt = re.sub(r"(\*\*Statut\*\* *: *)[^\n]+", r"\1livré", txt, count=1)
        io.open(path, "w", encoding="utf-8").write(txt)
        move(path, os.path.join(BRIEFS, "archive"))
    print("  -> %d briefs recales et archives dans %s/archive/" % (len(stale), BRIEFS))

# --- PLANS : un plan supersede ou termine n'a rien a faire parmi les vivants
for path in sorted(glob.glob(os.path.join(PLANS, "*.md"))):
    txt = io.open(path, encoding="utf-8").read(4000)
    m = re.search(r"^etat *: *([^\n]+)|\| *\*\*État\*\* *\| *([^|\n]+)", txt, re.M)
    etat = (m.group(1) or m.group(2) or "").strip() if m else "(aucun)"
    closed = re.match(r"(?i)(supersede|superséd|termin|clos|fini)", etat)
    print("PLAN %-42s %s" % (os.path.basename(path), etat[:58]))
    if closed:
        drift += 1
        if fix:
            move(path, os.path.join(PLANS, "archive"))
            print("     -> archive")

# --- DOCUMENTS DE PILOTAGE DORMANTS ---------------------------------------
for path in sorted(glob.glob("docs/*.md")):
    days = subprocess.run(["git", "log", "-1", "--format=%cr", "--", path],
                          capture_output=True, text=True).stdout.strip()
    print("DOC  %-42s dernier commit %s" % (os.path.basename(path), days or "?"))

print()
print("derive : %d element(s) a ranger%s" % (drift, "" if drift else " — rien a faire"))
if strict and drift:
    sys.exit(1)
PYEOF
