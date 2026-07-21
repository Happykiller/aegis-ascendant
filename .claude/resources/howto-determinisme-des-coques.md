# Howto — garder les coques 3D déterministes

ADR-0008 exige que deux exécutions d'un script de coque rendent un `.glb` **byte-identique**.
Cet invariant **était faux** entre ADR-0011 et le 2026-07-21, sans que rien ne le signale.

## Le symptôme, et pourquoi il trompe

Deux exécutions de `build_aegis_citadel.py` rendaient des fichiers différents de **6 à 12 octets**
sur 4,5 Mo. Tous dans des accesseurs `TANGENT`, par paires d'octets adjacents — des bits de mantisse.

Trois fausses pistes, toutes plausibles, toutes coûteuses :

| Hypothèse | Pourquoi elle tombe |
|---|---|
| « le script a un aléa non seedé » | en mettant `TANGENT` à zéro, cinq exécutions donnent la même empreinte : le maillage est bit-à-bit stable |
| « les UV dégénérées rendent la tangente indéfinie » | vrai, mais **pas la cause** : le Specter-9 a proportionnellement **plus** d'UV dégénérées (2,97 % contre 0,58 %) et reste stable |
| « c'est pré-existant, ça touche toute la flotte » | le Specter-9 régénéré est **byte-identique** à celui du dépôt. Le défaut n'apparaît qu'au-dessus d'une certaine taille de maillage |

## La cause

**Le calcul des tangentes de Blender (mikktspace) somme en virgule flottante dans un ordre qui
dépend du nombre de workers.** Au-dessus d'un certain nombre de triangles, Blender parallélise, et
l'ordre de réduction change d'une exécution à l'autre. C'est pour ça que le défaut n'apparaît que
sur les grosses coques : le Specter-9 (29 716 tri) reste sous le seuil, la citadelle (62 712) le
franchit.

Les tangentes sont exportées depuis ADR-0011, pour les normal maps. L'invariant a donc cessé d'être
vrai **ce jour-là**, silencieusement — aucun test ne le vérifiait.

## La parade

```bash
./scripts/build-hull.sh aegis_citadel           # régénère (mono-thread, toujours)
./scripts/build-hull.sh --check aegis_citadel   # 2 exécutions + comparaison sha256
./scripts/build-hull.sh --all                   # toute la flotte
```

Le script force `blender45 **-t 1**`. Mesuré : multi-thread → 6-12 octets divergents ;
mono-thread → **0**.

⚠️ **Ne jamais lancer un `build_*.py` à la main sans `-t 1`.** Le `.glb` produit sera valide et
jouable — c'est bien le problème : rien ne le signalera, et le dépôt accumulera des binaires qui
diffèrent sans qu'aucun changement de code le justifie. Sur des fichiers LFS de plusieurs mégaoctets,
c'est du poids pur.

## Ce que ça n'était pas

Le contrat auto-validé de `export_hull()` (bbox, budget, matériaux, points d'attache) **passe** dans
les deux cas. Un contrat vert ne dit rien du déterminisme : il fallait le mesurer à part, d'où
`--check`.
