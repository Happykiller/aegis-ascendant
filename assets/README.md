# assets/ — la carte

Une seule question range chaque fichier : **est-ce que ça finit dans le jeu ?**

| Dossier | Réponse | Le moteur le charge ? |
|---|---|---|
| **`imported/`** | oui, **directement** | **oui** — c'est le runtime |
| **`fonts/`** | oui, directement | oui |
| **`source/`** | oui, **en passant par un outil** | non (`.gdignore`) |
| **`reference/`** | **non** — ça sert à regarder et à décider | non (`.gdignore`) |
| `licenses/` | — | non (`.gdignore`) |

## Les trois règles qui découlent de la carte

1. **`imported/` ne contient que ce qui est chargé.** Un fichier que plus aucune scène ni aucun
   script ne référence n'y a pas sa place : Godot le réimporte à chaque démarrage et il se fait
   passer pour du runtime. Vérification :

   ```bash
   for f in $(find assets/imported -type f ! -name "*.import" ! -name "*.uid"); do
     grep -rqlF "res://$f" --include="*.tscn" --include="*.gd" --include="*.tres" . \
       || echo "ORPHELIN $f"
   done
   ```

2. **`source/` ne contient que ce qui fabrique.** Chaque fichier y répond à « quel outil le lit, et
   quel fichier de `imported/` en sort ? ». La table complète — y compris ce qui **dort** — est dans
   [`source/README.md`](source/README.md).

3. **`reference/` ne fabrique rien.** Aucun outil n'y lit, aucun script n'y écrit. On y regarde.
   La séparation `concepts/` (nos planches, originales) contre `inspiration/` (planches tierces,
   sensibles côté IP) est développée dans [`reference/README.md`](reference/README.md) — elle a des
   conséquences juridiques, pas seulement de rangement (ADR-0005, ADR-0009).

## Provenance

Tout fichier présent ici a sa ligne dans `licenses/ASSET_PROVENANCE.csv` (spec §24.7). Le CSV et le
disque doivent concorder dans les deux sens — un chemin du CSV qui ne pointe sur rien est un bug :

```bash
python3 - <<'PY'
import csv, io, os
rows = list(csv.reader(io.open("assets/licenses/ASSET_PROVENANCE.csv", encoding="utf-8")))
i = rows[0].index("file_path")
for r in rows[1:]:
    if not os.path.exists(r[i]): print("INTROUVABLE", r[i])
PY
```

Les binaires (`*.png`, `*.wav`, `*.ogg`, `*.glb`, `*.blend`) passent par **Git LFS** (spec §24.8).
