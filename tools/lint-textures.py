#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérifie les demandes de texture contre les six règles de `docs/forge/textures/README.md`.

⚠️ IL EXISTE PARCE QUE LES SIX RÈGLES N'ÉTAIENT VÉRIFIÉES PAR RIEN. Le contrat écrit
« un fichier qui viole l'une d'elles ne part pas au générateur », mais aucun outil ne
disait laquelle — et chacune de ces règles a une histoire, c'est-à-dire une itération
perdue : dix blocs de prompt repris pour un 2048, une normale violette aux gradients
faux, un damier peint dans une image opaque, un seamless qui n'en était pas un, une
couleur de tir volée à un projectile, une échelle inventée qui cadrait la densité sur
du vide.

    python3 tools/lint-textures.py

Sortie : une ligne par violation, code de retour 1 s'il y en a. Aucune dépendance.
"""

from __future__ import annotations

import glob
import json
import sys

RESOLUTIONS = {"1024x1024", "1536x1024", "1024x1536"}

#: Règle 5 — réservés au tir allié et au tir ennemi. Un décor qui les emploie vole leur
#: lisibilité aux projectiles. Comparés en minuscules, sans le croisillon : les demandes
#: les écrivent tantôt « cyan #3FD9E8 », tantôt « #3fd9e8 ».
RESERVEES = ("3fd9e8", "ff5a3d")

#: L'ouverture obligatoire d'un prompt. Relevé le 2026-08-26 : les images revenaient AVEC un
#: fond dès que le sujet n'occupait pas tout le cadre, parce que la consigne était enterrée à la
#: fin, dans « Éviter absolument ». Un générateur pondère ce qu'il lit en premier.
OUVERTURE_FOND = "\u26a0\ufe0f FOND"

#: Les blocs que le schéma impose, dans l'ordre du contrat.
BLOCS = (
    "texture_type", "purpose", "technical", "world_scale", "composition",
    "visual", "data_semantics", "lighting", "constraints", "integration_notes",
)


def verifier(chemin: str, doc: dict) -> list[str]:
    """Les manquements d'une demande, en clair."""
    fautes: list[str] = []

    def faute(regle: str, texte: str) -> None:
        fautes.append("%s : %s" % (regle, texte))

    for bloc in BLOCS:
        if bloc not in doc:
            faute("schéma", "bloc `%s` absent" % bloc)
    tech = doc.get("technical", {})
    visual = doc.get("visual", {})
    echelle = doc.get("world_scale", {})

    # --- Règle 1 — jamais 2048 -------------------------------------------
    res = tech.get("resolution")
    if res not in RESOLUTIONS:
        faute("règle 1", "resolution `%s` hors des trois formats natifs %s — un 2048 revient "
              "agrandi, avec du détail inventé par l'interpolation"
              % (res, sorted(RESOLUTIONS)))

    # --- Règle 2 — une hauteur, jamais une normale -----------------------
    usage = str(tech.get("output_usage", ""))
    if usage == "source_for_normal":
        if tech.get("color_mode") != "grayscale":
            faute("règle 2", "`source_for_normal` demande une hauteur en NIVEAUX DE GRIS "
                  "(color_mode = `%s`)" % tech.get("color_mode"))
        sem = doc.get("data_semantics", {})
        if not sem.get("enabled"):
            faute("règle 2", "`source_for_normal` sans `data_semantics.enabled` : rien ne dit "
                  "ce que le gris signifie, et clair/saillant n'est pas une convention "
                  "universelle")
    if "normal" in usage and usage != "source_for_normal":
        faute("règle 2", "`output_usage: %s` — on ne demande JAMAIS une carte de normale : "
              "on reçoit une image violette qui y ressemble, aux gradients faux, et le relief "
              "s'éclaire à l'envers" % usage)

    # --- Règle 3 — pas de fond transparent -------------------------------
    if tech.get("transparent_background"):
        faute("règle 3", "`transparent_background: true` est interdit — on reçoit un damier "
              "PEINT dans une image RGB opaque. Employer pure_black/pure_white puis "
              "tools/bg-key-alpha.py")

    # --- Règle 4 — un seamless se mesure ---------------------------------
    if tech.get("tileable"):
        exigences = doc.get("constraints", {}).get("seamless_requirements", [])
        if not exigences:
            faute("règle 4", "`tileable: true` sans `seamless_requirements` — un seamless "
                  "demandé n'est pas un seamless obtenu")
        elif not any("check-tiling" in str(e) for e in exigences):
            faute("règle 4", "aucune exigence ne cite `--check-tiling` : la couture serait "
                  "jugée à l'œil, où elle est invisible en preview et évidente en jeu")

    # --- Règle 5 — les deux couleurs de tir sont toujours interdites -----
    interdits = " ".join(
        str(x) for x in visual.get("color_palette", {}).get("forbidden", [])
    ).lower().replace("#", "")
    for teinte in RESERVEES:
        if teinte not in interdits:
            faute("règle 5", "#%s absent de `color_palette.forbidden` — cette teinte est "
                  "réservée à un tir, et un décor qui l'emploie lui vole sa lisibilité"
                  % teinte.upper())

    # --- Règle 6 — une échelle réelle ou déclarée ------------------------
    confiance = echelle.get("confidence")
    if confiance not in ("measured", "decided"):
        faute("règle 6", "`world_scale.confidence` vaut `%s` — attendu `measured` ou "
              "`decided`. Une échelle plausible cadre la densité de détail sur du vide"
              % confiance)
    if not str(echelle.get("rationale", "")).strip():
        faute("règle 6", "`world_scale.rationale` est vide : une échelle sans justification "
              "n'est ni mesurée ni décidée, elle est supposée")
    for cle in ("texture_width_m", "texture_height_m"):
        valeur = echelle.get(cle)
        if not isinstance(valeur, (int, float)) or valeur <= 0:
            faute("règle 6", "`world_scale.%s` doit être un nombre > 0 (lu : %r)"
                  % (cle, valeur))

    # --- Le fond se demande EN PREMIER -----------------------------------
    # ⚠️ Pas une des six, mais la même leçon payée : les images revenaient AVEC un fond
    # dès que le sujet n'occupait pas tout le cadre, parce que la consigne était enterrée
    # à la fin du prompt. Un générateur pondère ce qu'il lit en premier.
    # ⚠️ ET LA FORME EST TESTÉE, PAS LE MOT. Une première version cherchait « fond » dans les
    # deux cents premiers caractères : elle validait « le fond des cratères » et déclarait
    # conforme un prompt qui n'a jamais porté la consigne. Un contrôle qui se laisse tromper
    # par un homonyme est pire que pas de contrôle — il donne la conformité pour acquise.
    prompt = str(doc.get("x_prompt_fr", {}).get("text", ""))
    if prompt and not prompt.lstrip().startswith(OUVERTURE_FOND):
        faute("consigne de fond", "le prompt ne s'OUVRE pas par « %s » — un générateur pondère "
              "ce qu'il lit en premier, et la consigne enterrée plus bas n'est pas suivie"
              % OUVERTURE_FOND)

    return fautes


def main() -> int:
    fichiers = sorted(glob.glob("docs/forge/textures/TEX-*.json"))
    if not fichiers:
        print("[textures] aucune demande trouvée — lancer depuis la racine du dépôt")
        return 1
    total = 0
    for chemin in fichiers:
        try:
            doc = json.load(open(chemin, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as erreur:
            print("[textures] %s : illisible — %s" % (chemin, erreur))
            total += 1
            continue
        for f in verifier(chemin, doc):
            print("[textures] %s\n            %s" % (chemin, f))
            total += 1
    if total:
        print("[textures] %d manquement(s) — voir docs/forge/textures/README.md" % total)
        return 1
    print("[textures] %d demande(s), six règles OK" % len(fichiers))
    return 0


if __name__ == "__main__":
    sys.exit(main())
