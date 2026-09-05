"""build_pale_leviathan.py — coque 3D du Pale Leviathan, boss final (BRIEF-0040).

    ./scripts/build-hull.sh pale_leviathan        # JAMAIS un `blender-aegis` nu : -t 1

Produit `assets/imported/models/bosses/pale_leviathan.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (tout alea passe par `random.Random(seed)`, jamais par le
module `random` global) et s'auto-valide : `ak.export_hull()` relit le `.glb`
produit et echoue bruyamment si la bounding box, le budget de triangles, les
materiaux, le centrage du pivot ou les points d'attache sortent du contrat.

Reference de design : les trois planches annotees
`assets/reference/concepts/pale_leviathan_parts_sheet.png` (4 vues cotees +
eclate nomme — la reference principale), `..._core_states_sheet.png` (noyau
ferme / vortex / puits a anneaux) et `..._phases_sheet.png` (les 4 etats de
destruction). Deux erreurs de legende connues des planches ne sont PAS
recopiees : le 3e segment d'epine y est note « SPIKE MID » alors que le contrat
dit `Tip`, et les quatre vues sont cotees « 14,0 m » alors que la vue de face
montre les 11 m de largeur.

Repere d'auteur (ADR-0008) : face menacante -Y, dessus +Z, **babord +X**
(cf. l'en-tete d'aegis_kit : le signe de X est contre-intuitif).


CE QUE BRIEF-0040 CHANGE — trois verrous leves d'un coup
========================================================
1. **Rien n'etait animable.** La version precedente livrait des objets separes
   (`Core`, `Shell_Crescent`, `Spike_01..04`) mais **aucun appel a
   `ak.moving_part()`** : chaque piece avait son origine au centre du modele,
   donc tournait autour du boss et non autour de sa charniere. Tout ce qui bouge
   passe desormais par `ak.moving_part()`, qui pose l'origine SUR le pivot et
   accepte un `parent` (chaines articulees). 29 pieces mobiles, 3 niveaux de
   chaine.
2. **Rien n'etait texturable.** Aucun script de boss n'appelait
   `ak.box_project_uv()` : sans UV ni tangentes, le jeu de textures deja livre
   (`assets/source/textures/leviathan/`) n'avait nulle part ou se poser. Chaque
   maillage est desormais deplie a `TEXELS_PER_METER`, dans le meme geste.
3. **Les dimensions** passent a 11,0 x 14,0 m, hauteur <= 3,20 m, budget
   40 000 triangles (ADR-0018).


CE QUE BRIEF-0041 CHANGE — la forme et le budget de MATIERE
===========================================================
BRIEF-0040 a livre une coque animable, texturable et a sa taille. Elle ne
ressemblait pas a ses planches, et deux mesures le disaient : `AA_Emissive_Engine`
portait **28,7 %** des sommets, `AA_Hull` **11,0 %** contre **32,5 %** a
`AA_Greeble`. Un emissif ne recoit pas la lumiere : a ce dosage il noie le
modele et fait lire l'ensemble en rose pale delave, exactement le defaut
qu'ADR-0013 releve pour le noyau de la citadelle.

**Doctrine de materiaux** (elle vaut contrat : chaque face de ce script doit
pouvoir se justifier par une de ces cinq lignes) :

    AA_Hull      anthracite #24252B — LE BLINDAGE. Nappes de pont, flancs
                 d'ecaille, corps des dards. C'est la matiere DOMINANTE.
    AA_Trim      ivoire froid #DDDCD2 — les ecailles claires, celles qui
                 accrochent la lumiere et donnent le « Pale » du nom.
    AA_Panel     violet sombre #452663 — les segments organiques : croute du
                 noyau, paroi du puits, dessous de jupe.
    AA_Greeble   #141419 — les INTERSTICES seulement : dessous de tuile,
                 culots, joints. Jamais une grande surface vue de dessus.
    AA_Emissive  magenta #D93D9C — des VEINES, pas une livree. Le budget est
                 un plafond dur, et la quasi-totalite en revient au noyau.

Quatre corrections de forme, lues panneau par panneau sur
`pale_leviathan_parts_sheet.png` et `..._core_states_sheet.png` :

1. **Le noyau est une SPHERE** (panneau CLOSED CORE), plus une rosette plate.
   Il est desormais bati sur une icosphere — dont les facettes irregulieres
   donnent le reseau de craquelures de la planche, la ou un tour (lathe) a
   grille regulier produisait, vu de dessus, un spirographe concentrique. Il
   est **remonte et grossi** jusqu'a devenir le point le plus haut de la coque
   (z = +1,56 contre +1,37 aux plaques) : c'est ce debord, et lui seul, qui
   fait lire une boule sous une camera qui regarde de dessus.
2. **Le croissant se lit incomplet AU REPOS.** Ce n'etait pas le cas : les
   230 deg de matiere du croissant etaient visuellement refermes par un
   `Shell_Ring` complet a 360 deg. L'anneau porteur est donc lui aussi devenu
   un arc, plus large de 14 deg que le croissant de chaque cote — les deux
   ouvertures se superposent et **une seule encoche** traverse toute la
   coquille.
3. **Les dards s'allongent** : corde de 2,7 a 5,8 m (contre 4,4 m au plus long),
   rayon de base ramene de 0,42 a 0,32 m, effilement porte a 1,45. Ils sont
   plus longs, plus fins, plus segmentes, et **inegaux** — `Spike_01` fait plus
   du double de `Spike_04`.
4. **L'asymetrie est portee par la coque, pas par les zones de touche.** Le
   croissant s'epaissit progressivement d'un bout a l'autre (facteur 1,22 -> 0,80
   sur sa corde), son ouverture est franchement decentree (secteur avant-tribord),
   et les quatre epines n'ont ni la meme longueur ni le meme espacement. Les
   quatre `Plate_0X` restent en revanche de meme taille et de meme portee : le
   joueur les abat dans n'importe quel ordre, elles doivent rester
   interchangeables.

⚠️ Ce que la reforme NE touche pas, et ne doit jamais toucher : le contrat de
noms, les 29 `moving_part` et leurs pivots, `box_project_uv(0.18)`,
`_triangulate_ngons()`, le harnais de degagement bloquant, le determinisme.


CE QUE BRIEF-0083 CHANGE — la gueule cesse de « changer » et s'OUVRE
====================================================================
Playtest du 2026-08-25 : « on n'a pas la sensation que le noyau s'ouvre et
qu'on rentre dedans, plus qu'il change ». Le diagnostic etait exact : rien ne
s'ouvrait. `Shell_Ring` se translatait et grossissait de 18 %, et la seule
piece qui portait un mecanisme de gueule — `Maw_Lip` — n'etait **referencee
nulle part dans le code du combat**. Elle est remplacee par un IRIS DE SIX
VOLETS `Shutter_01..06`, a recul puis coulissement (voir la section suivante).

Quatre chiffres tiennent la piece, et tous sont des maximums qu'une voisine
autorise, pas des reglages :

  * **recul 1 500 mm** — au-dela de 1 290 les noeuds gravitiques sortent enfin
    de la piste de `Shell_Ring` ; en deca, ils la traversent ;
  * **glissement 600 mm**, et seulement APRES le recul : la coquille bouche
    tout ce qui depasse r = 2,18 sur toute la hauteur du volet ;
  * **passage libre 4,378 m** ouvert contre 3,207 fermes — seuil 4,200, soit
    2,4 largeurs de Specter-9 (**1,752 m** en espace MONDE ; le 1,29 m qui a
    circule est une agregation en espace local, sans les transformations de
    noeuds, alors que les ailes sont portees par des noeuds transformes) ;
    ⚠️ ce chiffre est celui de l'IRIS. Le trou que le joueur VOIT est borne par
    la coque a **3,499 m** (denture fixe de la levre du puits), par le noyau
    tant qu'il n'est pas escamote, et par les `Ring_01..05` — trois pieces hors
    du perimetre de ce brief, toutes mesurees au compte-rendu ;
  * **+2 366 triangles** pour six volets, `Maw_Lip` deduite (plafond : 2 500).

⚠️ Ce que ce brief NE change pas, et qui doit le rester : 26 des 30 maillages
du depot sortent BIT A BIT identiques ; seuls `Node_01..03` bougent (de 5 cm,
et la mesure qui l'exige est au commentaire de `NODE_R`).


LE PLAN VIENT DE LA MECANIQUE, PAS SEULEMENT DE LA PLANCHE
==========================================================
La camera de jeu regarde le plan **de dessus** (20 deg d'ecart a la verticale).
Ce que le joueur voit d'un boss de 14 m, c'est sa face +Z d'auteur. Toute la
lecture du combat est donc posee dans ce plan :

  * le **puits** (`Ring_01..05`, `Heart`) descend en -Z d'auteur, et la gueule
    s'ouvre vers le HAUT, face a la camera : la phase 4 se joue dans l'axe de
    vue, le joueur plonge litteralement dans l'ecran ;
  * la coquille (`Shell_Ring`) orbite autour de l'axe **vertical** du noyau, si
    bien que les quatre plaques defilent lateralement face au joueur — la
    fenetre de tir de la phase 1 est une geometrie, pas un minuteur ;
  * la coque est **plate** (3,0 m d'epaisseur pour 14 m de long) : tout ce qui
    compte est visible d'en haut, rien n'est cache sous le ventre.

Consequences directes sur les debattements, et ce sont elles qui ont fixe les
chiffres — pas l'oeil :

  * `Shutter_01..06` **recule puis coulisse** — deux TRANSLATIONS, jamais une
    rotation (BRIEF-0083). Le recul se fait en -Z d'auteur, c'est-a-dire -Y en
    jeu : les volets s'enfoncent LOIN de la camera, dans l'epaisseur du pont, ce
    qui interdit toute lecture « petale qui se souleve » — le geste du Choir
    Harvester, dont il faut se distinguer au premier coup d'oeil. Le
    coulissement est radial sortant, dans le plan de la levre ;
  * `Plate_0X` se **souleve vers l'exterieur** (charniere tangentielle sur son
    bord interne). Elle ne peut pas tomber vers le bas : sous elle il y a la
    coquille, puis le pont. Le geste lit comme une ecaille qu'on arrache, ce que
    montre le panneau CORE EXPOSED ;
  * les quatre epines sont montees sur des **mats dorsaux** qui les tiennent
    au-dessus du pont (z >= 0,90) : leur pointage de +/-40 deg balaie l'aplomb
    des lobes avant et arriere, et une epine posee a fleur de coque s'y serait
    enterree des le premier degre.

Chaque debattement est REMESURE a chaque build sur le maillage livre
(`_clearance_table()`, plus bas). La lecon la plus chere du projet est qu'un
contrat de bounding box valide une pose fixe et ne voit RIEN d'un defaut
d'animation (le Specter-9 a coute quatre briefs sur ce seul point).


CONTRAT DE NOMS (le code du combat sera ecrit contre lui)
=========================================================
    Body                                   maillage porteur, statique
    Shell_Ring -> Shell_Crescent -> Plate_01..04     orbite / bascule / chute
    Core -> Shutter_01..06                           recul + coulissement (iris)
    Shutter_01/02/03 -> Node_01/02/03                repli (un noeud par volet)
    Core -> Ring_01..05                              tunnel, vitesses distinctes
    Core -> Heart                                    statique, mais noeud a part
    Spike_0X -> Spike_0X_Mid -> Spike_0X_Tip         epaule / coude / pointe

⚠️ BRIEF-0083 : `Maw_Lip` a disparu du contrat — six `Shutter_NN` la remplacent,
et `Node_01..03` changent de parent (le volet qui les porte, plus la levre). Le
reste du contrat est INTACT, nom pour nom et parent pour parent : c'est la seule
chose qui casserait le combat entier sans qu'aucun test ne le voie.

⚠️ `Heart` est declare « statique » au contrat, et il l'est : rien ne l'anime.
Il passe pourtant par `ak.moving_part()`, seule primitive du kit qui sache
poser un `parent`. C'est deliberé, et c'est la meme decision que pour le `Core`
du Choir Harvester.

⚠️ **Piege d'integration a connaitre** : `Shutter_01..06`, `Ring_01..05` et
`Heart` sont enfants de `Core`. Cacher le noeud `Core` (`visible = false`)
cacherait donc TOUT l'iris et tout le puits avec lui. Pour escamoter le noyau
pendant la plongee, agir sur son **maillage** (materiau, echelle) et non sur la
visibilite du noeud — `leviathan_combat.gd` met deja `Core` a l'echelle.

⚠️ **Ce que le code doit ecrire pour animer l'iris** (rien d'autre) :

    var dir := Vector3(shutter.position.x, 0.0, shutter.position.z).normalized()
    shutter.position = rest + Vector3(0, -sink, 0) + dir * slide

`sink` va de 0 a IRIS_SINK, PUIS `slide` de 0 a IRIS_SLIDE — dans cet ordre, et
sans recouvrement : mener les deux de front rend une diagonale, donc un
ecartement immediat vu de dessus, donc la lecture « petale » qu'on refuse. La
direction se lit dans la POSITION du noeud parce que le pivot est pose sur la
bissectrice du volet ; elle est la meme dans le repere du fichier et dans celui
du jeu (`FACING_PLAYER` est une rotation de 180 deg autour de Y).
"""

from __future__ import annotations

import math
import os
import random
import sys

import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402  (doit suivre l'ajout au sys.path)

# ==========================================================================
# Contrat (ADR-0008, dimensions amendees par ADR-0018)
# ==========================================================================

CONTRACT = ak.HullContract(
    name="Pale Leviathan",
    width_x=11.00,      # Godot X — portee par les pointes de Spike_01 et _03
    length_z=14.00,     # Godot Z — portee a elle seule par `Body` (bec et dard)
    max_height_y=3.20,  # Godot Y — plafond de lisibilite en vue de dessus
    tri_budget=40_000,  # ADR-0018 ; plafond ADR-0011 de la classe boss : 90 000
    required_materials=ak.MATERIAL_ORDER,  # les 7 : la planche les utilise tous
    required_attach_points=(
        "Core_Center",
        "Maw_Center",
        "Tunnel_End",
        "Muzzle_C",
        "Muzzle_L",
        "Muzzle_R",
        "Muzzle_Plate_01",
        "Muzzle_Plate_02",
        "Muzzle_Plate_03",
        "Muzzle_Plate_04",
        "Muzzle_Spike_01",
        "Muzzle_Spike_02",
        "Muzzle_Spike_03",
        "Muzzle_Spike_04",
    ),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/bosses/pale_leviathan.glb")

#: Graine maitresse. Toute la variation (ecailles, craquelures, greebles) en
#: derive. Rejouer le script est byte-identique.
SEED = 481516

#: Densite du depliage UV : 0,18 tuile/m, soit **une tuile pour 5,5 m**. Sur une
#: coque de 14 m, les ecailles de `leviathan_scales_height` (periode mesuree
#: 0,99 m) lisent a ~1,1 m — l'echelle des planches. Reperes du projet : la
#: citadelle est a 0,12 (une tuile pour 8,33 m), le Specter-9 a 4,0 (25 cm).
TEXELS_PER_METER = 0.18

HALF_L = CONTRACT.length_z / 2.0   # 7,00 — bec en -Y, dard en +Y
HALF_W = CONTRACT.width_x / 2.0    # 5,50 — pointes d'epines

# ==========================================================================
# Le corps — un disque blinde plat, perce d'un puits central
# ==========================================================================

N_SEG = 40   # segments angulaires du disque (multiple de 4 et de 8)

#: Contour de la coque, en coordonnees polaires : (azimut deg, rayon m).
#: L'azimut part de +X (babord) et tourne vers +Y (arriere) ; -Y (l'avant, la
#: face menacante) est donc a 270 deg. Le bec et le dard portent a eux seuls les
#: 14 m de long ; les flancs restent nettement en deca des 11 m de large, que
#: les epines vont chercher. Le contour est volontairement DISSYMETRIQUE :
#: l'epaule babord est pleine vers l'arriere, l'epaule tribord vers l'avant.
#: ⚠️ Le dard est FOURCHU, et les deux pointes tombent sur des azimuts
#: ECHANTILLONNES (81 et 99 deg, multiples des 9 deg du pas angulaire) : c'est
#: la seule facon d'atteindre exactement les 7,00 m de demi-longueur. Une pointe
#: posee entre deux echantillons est rabotee par la discretisation, la longueur
#: tombe a 13,7 m — dans la tolerance — mais le centre derive de 15 cm, sept
#: fois la tolerance de pivot. La premiere version, dard en pointe unique,
#: lisait comme une soucoupe ; la fourche rend la lecture « creature ».
BODY_R: list[tuple[float, float]] = [
    (0.0, 4.78), (25.0, 4.92), (50.0, 5.45), (66.0, 6.30), (72.0, 6.75),
    (81.0, HALF_L / math.sin(math.radians(81.0))), (87.0, 6.55),
    (93.0, 6.30), (99.0, HALF_L / math.sin(math.radians(99.0))),
    (108.0, 6.05), (130.0, 5.05), (155.0, 4.72), (180.0, 4.68), (205.0, 4.90),
    (230.0, 5.40), (255.0, 6.40), (270.0, HALF_L), (285.0, 6.45), (310.0, 5.20),
    (335.0, 4.70), (360.0, 4.78),
]

#: Stations radiales ABSOLUES du pont central (le disque blinde) : levre du
#: puits, gorge de la coquille, contre-levre exterieure. Elles sont absolues et
#: non fractionnaires parce que la coquille orbite dessus : la piste doit etre
#: un solide de revolution, sinon l'orbite raboterait la coque une fois sur deux.
#: ⚠️ `DISC_R[0]` EST la levre du puits : c'est la meme boucle que `SHAFT[0]`
#: (`build_body` reutilise `top_rings[0]` comme premiere station du puits). Les
#: deux valeurs bougent ensemble ou le puits se decolle du pont.
DISC_R = (1.90, 2.02, 2.40, 2.84, 3.18, 3.50, 3.86, 4.14)
DISC_TOP = (0.60, 0.22, 0.18, 0.18, 0.20, 0.36, 0.60, 0.54)
DISC_BOT = (-0.92, -1.02, -1.08, -1.10, -1.08, -1.04, -0.96, -0.90)

#: ⚠️ INVARIANT DE PISTE — (rayon min, rayon max, plafond impose a la COQUE).
#: La coquille orbite au-dessus du disque : tout ce que la coque pose sous elle
#: doit rester sous ce plafond. Un pont d'arme, un mat ou un greeble qui deborde
#: se fait raboter une fois sur deux, et la bounding box au repos n'en dit rien.
#: La premiere version de ce script a perdu la mesure exactement la : ponts
#: d'armes de proue a r = 3,5 (500 triangles en interpenetration avec l'anneau)
#: et mats d'epine a demi-largeur constante (dans les plaques).
SHELL_TRACK = ((2.10, 3.06, 0.24), (3.06, 3.76, 0.88))

#: Jupe exterieure : trois stations en FRACTION de la corde restante
#: (`.claude/resources/pratique-detail-en-fraction-de-corde.md`). Le jour ou le
#: contour bouge, la jupe suit au lieu de flotter.
SKIRT_F = (0.34, 0.68, 1.00)
SKIRT_POW = 1.15          # galbe de la jupe (1 = conique, >1 = creuse)
RIM_HALF = 0.045          # demi-epaisseur de la tranche : jamais un fil de rasoir

#: Paroi INTERIEURE du puits : (z, rayon). Elle part de la levre et descend au
#: coeur. C'est elle qui borne les anneaux — leur rayon en est DERIVE.
#: ⚠️ Le puits est legerement EN TONNEAU (il s'evase de 1,90 a 1,98 sous la
#: levre avant de se resserrer) : le noyau de BRIEF-0041 est une sphere de
#: 1,56 m de rayon posee a z = +0,40, et sa calotte basse descend a z = -0,60.
#: Sans cet evasement, `Ring_01` — dont le rayon derive de cette table — passait
#: 6 cm DANS le noyau. La coupe n'est visible de nulle part ; la collision, si.
SHAFT: tuple[tuple[float, float], ...] = (
    (0.60, 1.90), (0.26, 1.96), (-0.10, 1.98), (-0.44, 1.78),
    (-0.76, 1.50), (-1.04, 1.16), (-1.26, 0.78), (-1.44, 0.32),
)
SHAFT_MATS = ("AA_Panel", "AA_Panel", "AA_Hull", "AA_Panel",
              "AA_Hull", "AA_Panel", "AA_Panel")

#: Ventre : peau exterieure du puits, de la premiere station basse au culot.
BELLY: tuple[tuple[float, float], ...] = (
    (-0.92, 1.90), (-1.14, 1.68), (-1.32, 1.20), (-1.46, 0.70), (-1.54, 0.34),
)

# ==========================================================================
# Le noyau — la cible, et le pivot de tout le puits
# ==========================================================================

#
# ⚠️ BRIEF-0041 : c'est une SPHERE, et elle DEBORDE. Trois chiffres la tiennent,
# et aucun n'est cosmetique :
#   * `CORE_RZ / CORE_RXY = 0,74` (contre 0,45) — au-dessous, la piece lit comme
#     une lentille, pas comme une boule ;
#   * `CORE_Z + CORE_RZ = +1,56` fait du noyau **le point le plus haut de toute
#     la coque** (les plaques culminent a +1,37, la levre a +1,20). Sous une
#     camera qui regarde de dessus, c'est le seul indice de rondeur disponible :
#     une sphere et un disque se projettent tous deux en cercle, seule
#     l'occultation de ce qui l'entoure trahit le volume ;
#   * `CORE_Z - CORE_RZ = -0,76` : la calotte basse plonge dans le puits, dont
#     la table `SHAFT` a ete evasee pour la laisser passer sans toucher
#     `Ring_01`. Descendre le centre re-enterrerait la boule.
CORE_RXY = 1.56           # rayon equatorial
CORE_RZ = 1.16            # demi-hauteur — 0,74 x l'equateur, une boule
CORE_Z = 0.40             # centre du noyau = pivot de `Core`

#: ⚠️ ICOSPHERE, pas un tour (lathe). Un tour a grille reguliere (32 x 15) donnait
#: vu de dessus — l'angle de la camera — un spirographe de cercles concentriques :
#: c'est ce qui faisait lire une rosette plate au lieu d'une boule. Les facettes
#: d'une icosphere n'ont ni rangee ni meridien, et leur reseau de joints EST le
#: « CRACK VEINS » de la planche. Subdivision 3 = 320 facettes, soit ~0,09 m2
#: chacune sur une boule de 3,1 m : l'echelle de plaque du panneau CLOSED CORE.
CORE_SUBDIV = 3           # 320 facettes (Blender : 1 -> 20, 2 -> 80, 3 -> 320)
CORE_CRUST_P = 0.62       # part des facettes soulevees (joint emissif autour)
CORE_FLAT_P = 0.23        # part posee a plat, sans joint : economie d'emissif
CORE_CRUST_LIFT = 0.034
CORE_CRUST_INSET = 0.032

HEART_Z = -1.24
HEART_R = 0.12

# ==========================================================================
# L'IRIS DE LA GUEULE — six volets coulissants (`Shutter_01..06`, BRIEF-0083)
# ==========================================================================
#
# ⚠️ CE QUI REMPLACE `Maw_Lip`, ET POURQUOI. La levre monobloc (secteur arriere
# de 96 deg, charniere derriere, +90 deg autour de X) ne servait a rien : elle
# n'etait referencee nulle part dans le code du combat, et l'ouverture du noyau
# se jouait entierement sur `Shell_Ring`, qui se TRANSLATE et GROSSIT de 18 %.
# D'ou le verdict de playtest — « on n'a pas la sensation que le noyau s'ouvre,
# plus qu'il change » : rien ne s'ecarte, aucune piece n'a de mecanisme.
#
# La levre devient donc **un iris de six volets**, et le geste est une
# CONTRAINTE DE DISTINCTION, pas une preference : le Choir Harvester s'ouvre
# deja avec des `Petal_01..N` qui **pivotent vers l'exterieur**, comme une
# fleur. Les volets du Leviathan ne pivotent JAMAIS. Ils font l'inverse :
#
#     1. ils RECULENT dans l'epaisseur de la coque   (translation -Z d'auteur,
#        soit -Y en jeu : ils s'enfoncent LOIN de la camera) ;
#     2. puis ils COULISSENT lateralement vers l'exterieur radial, dans le plan
#        de la levre, jusqu'a disparaitre sous le pont.
#
# Deux translations pures, aucune rotation. C'est un diaphragme mecanique, pas
# une corolle. Le code anime ; ce script pose la matiere et les pivots.
#
# ⚠️ POURQUOI SIX SECTEURS DE 60 deg ET NON UN IRIS QUI SE FERME SUR L'AXE.
# Le noyau est une BOULE de 3,12 m de diametre dont le pole (z = +1,56) est le
# point le plus haut de toute la coque — c'est l'acquis de BRIEF-0041, et c'est
# lui qui fixe la hauteur au contrat (3,162 m pour 3,20 autorises). Un volet qui
# se refermerait SUR l'axe passerait donc au-dessus du pole : la coque sortirait
# du contrat de hauteur des le premier centimetre. Les volets se ferment donc
# CONTRE la boule, pas sur l'axe : au repos, boule + collier = un disque plein
# de 4,12 m vu de dessus, et la gueule lit comme scellee. Ce que le joueur voit
# s'ouvrir, c'est le collier qui recule et s'ecarte pendant que le combat
# escamote la boule (cf. le piege d'integration en tete de fichier : agir sur le
# MAILLAGE du noyau, `leviathan_combat.gd` le met deja a l'echelle).
#
# La bande radiale et le profil sont ceux de l'ancienne `Maw_Lip`, AU MILLIMETRE
# (r de 1,66 a 2,06 ; z de 0,84 a 1,19 ; epaisseur 0,14) : la ou la levre etait,
# l'iris est exactement la meme matiere. Il l'etend simplement aux 360 deg.
#
#   * en deca de r = 1,66 le volet entre dans le noyau — et il doit RESTER
#     dehors sur TOUTE sa course d'enfoncement, ou il traverse l'equateur de la
#     boule (rayon 1,56 a z = 0,40). Les 10 cm de jeu sont le vrai plancher ;
#   * au-dela de r = 2,10 il entre dans la piste de `Shell_Ring`.
IRIS_N = 6
#: Azimuts des centres de volet. ⚠️ Le calage n'est pas libre : les bornes
#: tombent a 0/60/.../300 deg pour que les trois noeuds gravitiques (58, 92 et
#: 124 deg) atterrissent sur TROIS volets differents. Cale a 0/60 pres, deux
#: noeuds se retrouvaient sur le meme volet et le troisieme seul.
IRIS_AZ = tuple(30.0 + 60.0 * k for k in range(IRIS_N))
#: Demi-ouverture d'un volet. 30 deg exactement serait jointif au sens propre —
#: donc a marge NULLE, et le harnais de degagement refuserait d'exporter (il
#: exige une marge strictement positive entre deux pieces mobiles). On retire
#: donc un demi-jeu de chaque cote : 8,7 mm au rayon interne, 10,8 au rayon
#: externe. C'est une COUTURE, pas un jour : le chanfrein de 5 mm la creuse
#: exactement comme les joints de tuile du reste de la coque.
IRIS_SEAM = 0.60          # deg de jeu TOTAL entre deux volets voisins
IRIS_HALF = 30.0 - IRIS_SEAM * 0.5
IRIS_SEG = 7              # segments angulaires par volet (budget : 8 coutait 46 tris de trop)
#: (rayon, z du dessus) — **la table de `LIP_PROFILE`, inchangee**.
IRIS_PROFILE: tuple[tuple[float, float], ...] = (
    (2.06, 0.84), (1.98, 1.00), (1.86, 1.12), (1.74, 1.19), (1.66, 1.18),
)
IRIS_T = 0.14             # epaisseur de la nappe (ex-`LIP_T`)

#: ⚠️ PIVOT D'UN VOLET. Une translation est indifferente au point d'origine :
#: ce que le pivot decide ici, ce n'est pas la trajectoire, c'est la DIRECTION
#: que le code va lire. Il est pose sur la BISSECTRICE du volet, sous la nappe,
#: a mi-course de sa glissiere — le patin. Consequence voulue :
#: `normalize(Vector3(pos.x, 0, pos.z))` du noeud rend exactement la direction
#: de coulissement, dans le repere du fichier COMME dans celui du jeu (une
#: rotation de 180 deg autour de Y laisse la bissectrice sur elle-meme). C'est
#: le meme procede que `harvester_combat._bind_iris()` pour l'axe des petales :
#: aucune donnee supplementaire a transporter.
IRIS_PIVOT_R = 1.86
IRIS_PIVOT_Z = 0.98       # dessous de la nappe a r = 1,86 (1,12 - 0,14)

#: ⚠️ COURSE, ET CE QUI LA BORNE. Les deux valeurs ne sont pas choisies « pour
#: que ca bouge bien » : chacune est le maximum qu'une piece voisine autorise.
#:   * l'ENFONCEMENT est borne par `Ring_01`, qui tourne a z = -0,12 entre
#:     r = 1,50 et 1,74 : le bord d'attaque du volet (dessous a z = +1,04)
#:     descend juste au-dessus de lui ;
#:   * le COULISSEMENT est borne par le plafond de piste (`SHELL_TRACK`, 0,24 a
#:     r >= 2,10) puis par le pont lui-meme : a fond de course le volet doit
#:     etre AVALE par l'epaisseur du pont (dessus a 0,18), sans quoi la coquille
#:     le raboterait a chaque tour d'orbite.
#: A fond de course, le volet occupe r 2,26 -> 2,66 et z -0,80 -> -0,31 : il est
#: integralement DANS le volume creux du pont, sans qu'aucune de ses surfaces ne
#: croise une surface de coque (marge mesuree : 253 mm). Il est donc invisible,
#: sans z-fighting, et hors de la piste de la coquille.
IRIS_SINK = 1.50          # m, translation -Z d'auteur (= -Y en jeu)
IRIS_SLIDE = 0.60         # m, translation radiale sortante, dans le plan
#: ⚠️ Part de la course consacree au RECUL. Au-dela, le volet coulisse. Les deux
#: temps ne se recouvrent pas : ce n'est pas un choix de style, c'est une
#: mesure. Le coulissement est IMPOSSIBLE tant que le volet n'est pas descendu
#: sous la coquille — `Shell_Crescent` commence a r = 2,24 entre z = 0,75 et
#: 1,16, `Shell_Ring` a r = 2,18 entre 0,28 et 0,68 : ils bouchent tout ce qui
#: est au-dela de r = 2,18 sur toute la hauteur du volet. Un glissement de
#: 300 mm amorce des le repos entre le volet dans le croissant (marge 0,0 mm,
#: mesuree). Il faut donc RECULER D'ABORD — et la deuxieme raison est plus
#: sournoise : les noeuds gravitiques depassent de 32 cm au-dessus de la nappe,
#: si bien qu'ils sortent de la piste de `Shell_Ring` seulement au-dela de
#: 1,29 m d'enfoncement (marge 20 mm a 1,30 ; 215 mm a 1,50).
IRIS_KNEE = 0.70
#: Enfoncement en deca duquel le volet doit rester ENTIEREMENT hors de la coque
#: (c'est la part VISIBLE et franche de la course : le volet se decolle avant de
#: rentrer dans son logement). Au-dela il traverse la levre du puits — par
#: construction, comme une glissiere reelle. La denture fixe de cette levre
#: (`_build_rim_teeth`, crete a z = 0,65) est ce qui borne ce chiffre : le
#: dessous du volet est a z = 0,845 au droit de la derniere dent. Le harnais
#: bloque sur cette part-la, et publie le contact reel.
IRIS_FREE_SINK = 0.10
#: ⚠️ RAYON MINIMAL DU PASSAGE LIBRE, a l'ouverture maximale. Le seuil est un
#: DIAMETRE de 4,20 m, soit 2,4 largeurs de chasseur. Il valait 3,00 m tant que
#: le Specter-9 etait cru large de 1,29 m — chiffre agrege en espace LOCAL, sans
#: les transformations de noeuds, alors que ses ailes sont portees par des
#: noeuds transformes. La vraie mesure, en espace monde, est **1,752 m** : le
#: seuil de 3,00 ne laissait que 1,71 largeur, l'inverse de l'intention ecrite
#: (« sans que ca ait l'air serre »).
IRIS_BORE_MIN = 2.10

#: Dents du bord d'attaque : elles mordent vers la boule sans jamais la
#: toucher. ⚠️ Leur rayon de pointe est un PLANCHER DUR : le volet s'enfonce de
#: 1,04 m, il croise donc l'equateur du noyau (rayon 1,56 a z = 0,40) en cours
#: de route. Les anciennes griffes de `Maw_Lip` allaient a r = 1,46 — elles
#: auraient traverse la boule des le premier tiers de l'enfoncement.
IRIS_TOOTH_AZ = (-14.0, 0.0, 14.0)   # deg, relatifs au centre du volet
IRIS_TOOTH_R = (1.74, 1.62)          # (base, pointe) en rayon
IRIS_TOOTH_Z = 1.115
#: Patin de glissiere, SOUS la nappe (invisible de dessus au repos, et c'est
#: voulu : rien ne doit depasser du dessus, qui passe sous la piste a fond de
#: course). C'est lui qui touche le premier la levre du puits en s'enfoncant.
#: ⚠️ Il s'arrete a r = 1,98 : au-dela, il descendrait sur la denture fixe de la
#: levre du puits (`_build_rim_teeth`, crete a z = 0,65), qui est la piece la
#: plus proche de l'iris au repos.
IRIS_SHOE_R = (1.74, 1.98)
IRIS_SHOE = (3.6, 0.050)             # (demi-ouverture deg, profondeur sous la nappe)
#: Butee de fin de course, posee sur le dessus a l'extremite BASSE du profil
#: (z = 0,96 au rayon 2,00) : la seule saillie superieure, et la plus basse.
IRIS_STOP_R = 2.00
IRIS_STOP = (0.13, 0.05, 0.045)      # (demi-largeur, demi-longueur, hauteur)

#: Noeuds gravitiques : azimut sur la levre, longueur, inclinaison sortante.
#:
#: ⚠️ BRIEF-0041 — DEUX PLACEMENTS ONT ETE REFUSES PAR LA MESURE avant celui-ci,
#: et les deux echecs disent la meme chose : le debattement impose (-60 deg
#: autour de `rotation.x`, tableau de BRIEF-0040, intouchable) fixe la direction
#: de repli, et c'est elle qui contraint la pose, pas l'inverse.
#:   * plante sur le flanc externe (r = 2,00, z = 0,98) : le noeud remontait en
#:     RASANT l'arche de la levre et la traversait entre 25 et 35 cm du pivot —
#:     hors du rayon d'exclusion de charniere, donc une vraie morsure ;
#:   * penche vers l'interieur (`NODE_TILT = 118 deg`) : au repos tout degageait,
#:     mais le repli le rabattait a l'horizontale en travers de la crete.
#: Le placement retenu est sur le POINT HAUT de l'arche, penche vers l'exterieur :
#: le repli le redresse alors presque a la verticale, au-dessus du vide. La levre
#: ayant remonte contre la boule, la pointe ne sort qu'a r = 2,04 — sous la piste
#: de `Shell_Ring`, qui ne monte de toute facon qu'a z = 0,68.
#:
#: ⚠️ BRIEF-0083 — LEUR PARENT CHANGE, LEUR POSITION NON. `Maw_Lip` ayant
#: disparu, chaque noeud devient l'enfant du VOLET sur lequel il est plante : il
#: recule et coulisse avec lui, ce qu'un noeud reste accroche au noyau n'aurait
#: pas fait (il serait reste suspendu au-dessus du vide une fois l'iris ouvert).
#: Les azimuts 58 / 92 / 124 tombent sur `Shutter_01` (centre 30), `Shutter_02`
#: (90) et `Shutter_03` (150) — un noeud par volet, aucun orphelin. Ni le rayon,
#: ni l'altitude, ni la longueur, ni l'inclinaison ne bougent : au repos les
#: trois noeuds sont exactement la ou ils etaient.
NODE_AZ = (58.0, 92.0, 124.0)
#: ⚠️ BRIEF-0083 — SEULE CORRECTION APPORTEE AU PLACEMENT, ET ELLE EST MESUREE.
#: Le rayon passe de 1,78 a 1,83 et l'altitude de 1,15 a 1,134 (le noeud reste
#: enfonce de 4 mm dans la nappe du volet, comme avant). Motif : le repli de
#: -60 deg couche le noeud vers l'INTERIEUR — direction heritee de la levre a
#: charniere arriere, qui n'existe plus — et le volet l'emmene desormais 1,50 m
#: plus bas, c'est-a-dire au droit de l'EQUATEUR du noyau (rayon 1,555 a
#: l'altitude critique). A 1,78 la marge tombait a 7,0 mm (mesure) contre
#: 97,2 mm au depot. Les 5 cm equilibrent les deux marges qui l'encadrent —
#: le noyau en dedans, la piste de `Shell_Ring` en dehors — sans toucher ni la
#: longueur, ni l'inclinaison, ni le debattement du noeud.
NODE_R = 1.83             # rayon d'implantation, sur la crete du volet
NODE_Z = 1.134
NODE_LEN = (0.42, 0.46, 0.40)
NODE_TILT = 55.0          # deg au-dessus du plan, penche vers l'exterieur
NODE_W = 0.16             # demi-largeur de l'embase

# ==========================================================================
# Le puits — cinq anneaux a ouverture decalee (« OFFSET GATE »)
# ==========================================================================
#
# (z, azimut du milieu de l'ouverture, largeur radiale). Le rayon externe est
# DERIVE de la paroi du puits (`shaft_radius`), jamais pose a la main : le jour
# ou le puits change de galbe, les anneaux le suivent au lieu de le traverser.
# L'ouverture fait RING_GAP deg et se decale d'un anneau au suivant — c'est ce
# que la planche nomme « OFFSET GATE », et c'est la mecanique de la phase 4.
RINGS: tuple[tuple[float, float, float], ...] = (
    (-0.12, 0.0, 0.24),
    (-0.44, 72.0, 0.24),
    (-0.74, 144.0, 0.22),
    (-0.98, 216.0, 0.20),
    (-1.18, 288.0, 0.18),
)
RING_GAP = 70.0           # deg d'ouverture
RING_CLEAR = 0.20         # jeu radial impose entre l'anneau et la paroi
RING_T = 0.11             # epaisseur
RING_SEG = 26             # segments sur les 290 deg de matiere

# ==========================================================================
# La coquille : anneau porteur, croissant, quatre plaques
# ==========================================================================
#
# Trois niveaux, et c'est delibere (BRIEF-0040) : `Shell_Ring` porte l'orbite,
# `Shell_Crescent` la bascule, `Plate_0X` la chute. Un axe, un noeud, un
# ecrivain — empiler deux de ces mouvements sur le meme noeud produirait, le
# jour ou les deux sont actifs, une composition d'Euler que personne ne sait
# relire.

#: Croissant : l'anneau INCOMPLET de la charte (SS2, « anneau incomplet »). Il
#: court de -50 a +155 deg, soit 205 deg de matiere ; les 155 deg manquants
#: ouvrent sur le quadrant AVANT-TRIBORD (milieu de l'ouverture a 232 deg, entre
#: le travers tribord a 180 et l'etrave a 270). C'est le secteur que la camera
#: montre en grand : une ouverture posee a l'arriere ne se serait jamais lue.
CR_PHI_A = -50.0
CR_PHI_B = 155.0
CR_OVERLAP = 1.26

#: ⚠️ BRIEF-0041 — CE QUI FAISAIT ECHOUER L'INCOMPLETUDE. Les 230 deg de matiere
#: de BRIEF-0040 etaient corrects sur le papier et invisibles a l'ecran : le
#: `Shell_Ring` porteur, lui, faisait 360 deg et **refermait optiquement**
#: l'ouverture, un anneau concentrique complet passant juste dessous. L'anneau
#: porteur est donc devenu un ARC, deborde de `SR_MARGIN` degres de chaque cote :
#: les deux ouvertures se superposent, et la coquille n'a plus qu'UNE encoche,
#: traversante, visible au repos en vue de dessus. Une seule regle a retenir : ce
#: qui vit sous le croissant ne doit jamais etre plus ferme que lui.
SR_MARGIN = 14.0

SHELL_PIVOT = (0.0, 0.0, CORE_Z)   # l'axe du noyau, et rien d'autre

#: Anneau porteur : deux rangees de tuiles tangentielles qui se recouvrent.
#: (rayon interne, rayon externe, z interne, z externe, tuiles, dephasage).
#: `tuiles` est desormais compte SUR L'ARC, pas sur 360 deg.
RING_ROWS: tuple[tuple[float, float, float, float, int, float], ...] = (
    (2.20, 2.60, 0.56, 0.62, 13, 0.00),
    (2.54, 2.94, 0.62, 0.52, 11, 0.43),
)
RING_Z_BASE = 0.34        # les tuiles plongent dans la gorge : pas de flottement
RING_OVERLAP = 1.30

#: ⚠️ La charniere est posee derriere les PLAQUES (y = 3,74 au plus loin), pas
#: derriere le croissant seul (y = 3,09) : les plaques sont ses enfants, elles
#: basculent avec lui, et une plaque restee en arriere de l'axe plongeait dans
#: la coque des les premiers degres (mesure : morsure a 56 deg de chute).
CR_PIVOT = (0.0, 3.86, 0.94)
#: (rayon interne, rayon externe, tuiles, elevation, dephasage)
CR_ROWS: tuple[tuple[float, float, int, float, float], ...] = (
    (2.26, 2.66, 18, 0.00, 0.00),
    (2.60, 3.02, 14, 0.05, 0.42),
)
CR_Z_BASE = 0.88
CR_TOP = 1.06
#: ⚠️ ASYMETRIE (brief SS2) : facteur applique a la CORDE RADIALE de la tuile,
#: interpole de `CR_PHI_A` a `CR_PHI_B`. Le croissant est donc franchement plus
#: epais a une extremite qu'a l'autre — 1,16 contre 0,78, soit +49 %. C'est
#: l'asymetrie la plus lisible de la silhouette vue de dessus, et elle ne coute
#: rien au gameplay : elle porte sur la COQUE, pas sur les zones de touche.
CR_SWELL = (1.16, 0.78)

#: Tirage des materiaux de tuile. Anthracite et ivoire a parts egales — c'est le
#: blindage (doctrine : `AA_Hull` domine), pique de violet.
PLATE_MATS = (
    "AA_Hull", "AA_Trim", "AA_Hull", "AA_Trim",
    "AA_Trim", "AA_Hull", "AA_Panel", "AA_Hull",
)

#: Les quatre plaques d'armure : azimut du centre, demi-ouverture angulaire.
#: ⚠️ Elles ont toutes la MEME demi-ouverture et la meme portee radiale, et c'est
#: une contrainte de jeu, pas un oubli d'asymetrie : elles orbitent et le joueur
#: les abat dans n'importe quel ordre. Une plaque plus grande que les autres
#: serait une zone de touche plus facile, donc un ordre impose. L'asymetrie du
#: vaisseau est portee par le croissant et les epines (brief SS2).
#: Leur espacement, lui, est irregulier — et toutes tiennent dans l'arc du
#: croissant, sinon elles pendraient dans le vide une fois celui-ci bascule.
PLATES: tuple[tuple[float, float], ...] = (
    (-28.0, 21.0), (26.0, 21.0), (80.0, 21.0), (134.0, 21.0),
)
PLATE_R = (3.10, 3.74)    # (charniere tangentielle, bord externe)
#: ⚠️ BRIEF-0041 : les plaques ont ete ABAISSEES de 8 cm (crete 1,32 au lieu de
#: 1,40). Ce n'est pas un ajustement esthetique : il faut que le noyau (+1,56)
#: soit le point le plus haut de la coque, sinon la boule reste enfermee dans sa
#: couronne et se relit en disque.
PLATE_Z = (1.10, 1.32, 1.12)   # (charniere, crete, bord externe)
PLATE_T = 0.13
PLATE_SEG = 8

# ==========================================================================
# Les quatre bras-epines
# ==========================================================================
#
# Courbes de Bezier quadratiques (racine, controle, pointe). Aucune paire n'est
# le miroir d'une autre : longueurs, epaisseurs, nombres de vertebres et
# courbures different. Les pointes de `Spike_01` et `Spike_02` portent les bornes
# +X et -X (5,527 et -5,502 au maillage) — l'enveloppe est equilibree, la
# silhouette ne l'est pas. `HALF_W` n'est plus une coordonnee de pointe depuis
# BRIEF-0081 : c'est la demi-largeur du CONTRAT, que le maillage approche par en
# dessous (11,029 m pour 11,00 vise).
#
# ⚠️ BRIEF-0081 — LES QUATRE EPINES VISENT LE JOUEUR. `BossController` applique
# `FACING_PLAYER = Vector3(0, PI, 0)` : l'axe lu ICI (plan XY de Blender) EST
# l'angle vu en jeu, et le joueur est a -90 deg. Les quatre axes
# `racine -> Muzzle_Spike_NN` valent -28,9 / -139,1 / -104,4 / -68,5 deg, tous
# dans [-160 ; -20]. Avant ce brief, `Spike_01` et `Spike_02` pointaient a
# +68,7 et +109,0 : deux membres sur quatre tiraient vers l'arriere.
#
# ⚠️ Ce qui rend l'eventail possible, c'est la RACINE de `Spike_03`, reculee de
# 24,7 deg d'azimut (195,3 -> 220,0 deg, rayon inchange a 4,168 m). BRIEF-0080
# avait mesure l'impasse a racine gelee : `Spike_02` retournee venait se coller
# a `Spike_03` (jour 159 mm, ecart angulaire 5,4 deg — un doublet parallele).
# Le couloir babord rouvert, le jour minimal remonte a 1023 mm et l'eventail
# minimal a 34,7 deg, SANS un millimetre de largeur en plus (11,029 m, soit
# 2,7 mm de MOINS qu'avant). Le mat suit la racine : `_build_masts()` relit
# `root`, il n'y a rien d'autre a deplacer.
#
# ⚠️ Les racines sont a z ~ 1,10 et a r >= 4,15 : c'est un mat dorsal qui les
# tient, au-dessus du pont et EN DEHORS de la piste de la coquille. Sans cette
# double condition, le pointage de +/-40 deg enterrerait l'epine dans les lobes
# avant et arriere des le premier degre, et sa rotule se ferait raboter par une
# plaque a chaque tour d'orbite (les deux ont ete mesures).
#
# ⚠️ Le rayon 4,15 est un PLANCHER CALCULE, pas un souvenir : une plaque orbite
# jusqu'a r = 3,74, et le flanc interne d'une epine est a `r_racine - r0`. Avec
# `r0 = 0,32`, une racine posee a 3,96 (ce que la geometrie permettrait) mettrait
# ce flanc a 3,64 — dans la course des plaques. Le harnais de degagement ne le
# verrait PAS : il mesure l'epine contre la coque, jamais contre la coquille.
#
# BRIEF-0041 — LES DARDS S'ALLONGENT. Le panneau DETACHED SPIKE montre une lame
# presque aussi longue que le corps, effilee sur toute sa course. Trois leviers,
# tous mesures :
#   * la CORDE passe de 4,4 m au plus long a 5,8 m — les racines reculent vers
#     l'axe long, les pointes vont chercher les bornes de la boite ;
#   * le rayon de base tombe de 0,425 a 0,32 m et l'effilement monte de 1,26 a
#     1,45 : une epine deux fois plus fine a mi-course qu'avant ;
#   * les vertebres passent de 5-7 a 7-10, donc des ecailles plus courtes et un
#     dard qui lit segmente meme detache, seul a l'ecran (phase 3).
# L'INEGALITE est voulue et forte : `Spike_01` mesure 5,81 m de corde, `Spike_04`
# 2,68 m — moins de la moitie. Un bras long, un moyen, un court, un mognon : la
# silhouette est desequilibree alors que l'enveloppe reste centree au millimetre
# (contrainte de pivot d'`export_hull`, +/- 2 cm).

SPIKES: tuple[dict, ...] = (
    {   # babord : de loin la plus longue, l'aiguille. Elle porte le +X.
        # Axe -28,9 deg en jeu : elle part vers le flanc puis vient border
        # l'avant. `ctrl.z` a 1,55 est l'ARCHE qui paye la provision de pointage
        # a +/-40 deg — a plat (1,16) le maillon de pointe mord la coque des
        # -40 deg de pointage et le build refuse d'exporter (mesure BRIEF-0081).
        "name": "Spike_01",
        "root": (4.14, -0.52, 1.12),
        "ctrl": (5.85, 0.50, 1.55),
        "tip": (5.35, -6.20, 1.10),
        "r0": 0.320, "sides": 9, "vertebrae": 10, "flat": 0.60, "taper": 1.45,
        "splits": (0.30, 0.62), "port": 0.44,
    },
    {   # tribord : la faux longue, tres cambree. Elle porte le -X.
        # Axe -139,1 deg en jeu : sa racine est la plus arriere des quatre, elle
        # contourne donc le flanc par l'exterieur avant de border l'avant. Meme
        # arche que `Spike_01`, et pour la meme raison.
        "name": "Spike_02",
        "root": (-4.10, 1.05, 1.10),
        "ctrl": (-5.95, 1.10, 1.55),
        "tip": (-5.20, -3.80, 1.10),
        "r0": 0.310, "sides": 9, "vertebrae": 9, "flat": 0.64, "taper": 1.40,
        "splits": (0.32, 0.64), "port": 0.46,
    },
    {   # tribord-avant : la lame droite, la seule dont la RACINE ait bouge.
        # Azimut 220,0 deg (contre 195,3), rayon 4,168 m inchange : elle laisse
        # a `Spike_02` le couloir exterieur babord et prend la voie interieure.
        # Axe -104,4 deg en jeu. Pas d'arche : sa courbe ne revient pas sur la
        # coque au pointage (mesure), son `ctrl.z` reste a 1,14.
        #
        # ⚠️ L'AZIMUT 220 N'EST PAS ARRONDI DEPUIS 215 : entre 205 et 218 deg, le
        # mat de cette epine entre dans le creux de degagement des plaques et le
        # harnais tombe de 71,3 a 39,9 mm (mesure par pas de 5 deg, BRIEF-0081).
        # A 220 il remonte a 65,9 mm, et le jour Spike_02-Spike_03 passe de
        # 1156 a 1488 mm. Deplacer cette racine sans rejouer ces deux mesures,
        # c'est reprendre 30 mm de marge a la coquille sans le savoir.
        "name": "Spike_03",
        "root": (-3.193, -2.679, 1.12),
        "ctrl": (-3.40, -4.90, 1.14),
        "tip": (-5.25, -6.80, 0.98),
        "r0": 0.316, "sides": 9, "vertebrae": 9, "flat": 0.58, "taper": 1.42,
        "splits": (0.31, 0.63), "port": 0.42,
    },
    {   # babord-avant : le mognon, moins de la moitie de `Spike_01`. Seule des
        # quatre a n'avoir jamais bouge : elle visait deja le joueur (-68,5 deg).
        "name": "Spike_04",
        "root": (3.74, -2.60, 1.10),
        "ctrl": (4.46, -3.86, 1.12),
        "tip": (4.30, -5.22, 0.94),
        "r0": 0.300, "sides": 9, "vertebrae": 7, "flat": 0.62, "taper": 1.30,
        "splits": (0.33, 0.66), "port": 0.48,
    },
)

SPIKE_SAMPLES = 3         # stations par vertebre
SPIKE_TIP_R = 0.014
SPIKE_FLARE = 0.22        # relief de vertebre (l'ecaille recouvre la suivante)
SPIKE_GAP = 0.35          # retrait d'un troncon a son articulation, en rayons

# ==========================================================================
# Ponts d'armes fixes de la coque (conserves : le controleur generique les lit
# encore si `external_attacks` retombe a faux)
# ==========================================================================

#: ⚠️ Ils sont poses SUR LE BEC, a r >= 5,1 : c'est l'invariant de piste
#: (`SHELL_TRACK`). La premiere version les avait mis a r = 3,5, ou la coquille
#: passe — et la mesure a trouve 500 triangles en interpenetration.
MUZZLE_C = (0.0, -6.05, 0.40)
MUZZLE_LR = (1.15, -5.55, 0.40)   # (|x|, y, z) — `attach_pair` pose les signes


# ==========================================================================
# Interpolation et geometrie de base
# ==========================================================================


def lerp_table(table, x: float) -> float:
    """Interpolation lineaire d'une table (abscisse, valeur), extremites clampees.

    Lineaire par morceaux, volontairement : une spline arrondirait les cassures
    de plaque qui font justement la silhouette hard-surface.
    """
    if x <= table[0][0]:
        return table[0][1]
    if x >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        x0, v0 = table[i]
        x1, v1 = table[i + 1]
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return v0 + (v1 - v0) * t
    return table[-1][1]


def body_radius(deg: float) -> float:
    """Rayon du contour de coque a l'azimut `deg` (periodique)."""
    return lerp_table(BODY_R, deg % 360.0)


def disc_z(table: tuple, r: float) -> float:
    """z du pont a un rayon ABSOLU, dans la zone du disque (r <= DISC_R[-1])."""
    return lerp_table(list(zip(DISC_R, table)), r)


def skirt_z(f: float, z0: float) -> float:
    """z de la jupe a la fraction `f` de la corde restante, depuis `z0`."""
    sign = 1.0 if z0 > 0.0 else -1.0
    edge = sign * RIM_HALF
    return edge + (z0 - edge) * (1.0 - f) ** SKIRT_POW


def track_ceiling(r: float) -> float:
    """Plafond impose a la coque sous la piste de la coquille (`SHELL_TRACK`)."""
    for r0, r1, z in SHELL_TRACK:
        if r0 <= r <= r1:
            return z
    return 9.0


def shaft_radius(z: float) -> float:
    """Rayon INTERIEUR du puits a l'altitude `z` (table lue de haut en bas)."""
    return lerp_table([(-zz, rr) for zz, rr in reversed(SHAFT)], -z)


def ring_radius(index: int) -> float:
    """Rayon externe d'un anneau, DERIVE de la paroi au plus etroit de sa course.

    L'anneau a une epaisseur : c'est son arete BASSE qui frole la paroi, puisque
    le puits se resserre en descendant. Prendre le rayon a l'altitude du milieu
    aurait donne 5 cm de trop, et la mesure l'a effectivement refuse.
    """
    z = RINGS[index][0]
    return shaft_radius(z - RING_T * 0.5) - RING_CLEAR


def hull_top(r: float, deg: float) -> float:
    """Altitude du pont a (rayon, azimut). Sert a poser tout detail EN FRACTION."""
    if r <= DISC_R[-1]:
        return disc_z(DISC_TOP, r)
    span = max(body_radius(deg) - DISC_R[-1], 1e-3)
    return skirt_z(min((r - DISC_R[-1]) / span, 1.0), DISC_TOP[-1])


def _verts_of(faces: list) -> list:
    verts = {v for f in faces if f is not None and f.is_valid for v in f.verts}
    return list(verts)


def oriented_box(bm, center, size, rot, material: str) -> list:
    """Boite orientee : `ak.add_box` ne sait faire qu'aligne sur les axes."""
    faces = ak.add_box(bm, (0.0, 0.0, 0.0), size, material)
    verts = _verts_of(faces)
    if rot is not None:
        bmesh.ops.rotate(bm, cent=(0.0, 0.0, 0.0), matrix=rot, verts=verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=verts)
    return faces


def _align_y(direction: Vector) -> Matrix:
    """Rotation qui amene l'axe local +Y d'une boite sur `direction`."""
    return Vector((0.0, 1.0, 0.0)).rotation_difference(
        direction.normalized()
    ).to_matrix()


def seg_box(bm, a, b, half_w: float, half_h: float, material: str) -> list:
    """Vertebre : boite tendue du point `a` au point `b`."""
    va, vb = Vector(a), Vector(b)
    delta = vb - va
    length = delta.length
    if length < 1e-6:
        return []
    return oriented_box(
        bm, (va + vb) * 0.5, (2.0 * half_w, length, 2.0 * half_h),
        _align_y(delta), material,
    )


def knuckle(bm, center, radius: float, material: str) -> list:
    """Articulation : icosphere subdivisee une fois (80 faces, angles < 30 deg,
    donc epargnee par le biseau — c'est ce qui la rend abordable).

    Une sphere centree sur un pivot est INVARIANTE par rotation autour de ce
    pivot : c'est elle qui autorise une articulation franche sans que le
    troncon rabote son voisin.
    """
    res = bmesh.ops.create_icosphere(
        bm, subdivisions=1, radius=radius,
        matrix=Matrix.Translation(Vector(center)),
    )
    verts = res["verts"]
    idx = ak.mat_index(material)
    faces = []
    for face in {f for v in verts for f in v.link_faces}:
        if all(v in verts for v in face.verts):
            face.material_index = idx
            faces.append(face)
    return faces


def polar_ring(bm, radius: float, z: float, segments: int, phase: float = 0.0):
    """Boucle horizontale (autour de Z) : la primitive du disque et du puits."""
    return ak.add_ring(
        bm,
        [
            (radius * math.cos(2.0 * math.pi * i / segments + phase),
             radius * math.sin(2.0 * math.pi * i / segments + phase),
             z)
            for i in range(segments)
        ],
    )


def slab(bm, lo, hi, mat_top: str, mat_side: str = "AA_Hull",
         mat_bot: str = "AA_Greeble"):
    """Tuile blindee : deux quads (dessous/dessus) relies par 4 flancs.

    Contrairement a `ak.add_box`, elle n'est pas alignee sur les axes : c'est ce
    qui permet de poser des ecailles sur une surface courbe. Retourne
    `(face du dessus, les 4 flancs)` ; `sides[0]` est le **bord d'attaque**, la
    contremarche qui depasse quand la tuile monte sur sa voisine — c'est elle
    qu'on rend emissive pour obtenir les interstices lumineux de la planche.
    """
    ring_lo = ak.add_ring(bm, lo)
    ring_hi = ak.add_ring(bm, hi)
    sides = ak.bridge_rings(bm, ring_lo, ring_hi, mat_side)
    top = ak.cap_ring(bm, ring_hi, mat_top)
    ak.cap_ring(bm, list(reversed(ring_lo)), mat_bot)
    return top, sides


def tangential_tile(bm, rng, a0: float, a1: float, r_in: float, r_out: float,
                    z_in: float, z_out: float, z_base: float, rise: float):
    """Une ecaille tangentielle : longue le long de l'anneau, courte en radial.

    Des plaques RADIALES pleine largeur donnaient, vues de dessus, une roue a
    rayons — un tournesol, tout sauf une carapace. Des tuiles tangentielles qui
    se recouvrent donnent la lecture « ecailles » des planches.
    """
    lo, hi = [], []
    for a, lift in ((a0, 0.0), (a1, rise)):
        for r, z in ((r_in, z_in), (r_out, z_out)):
            x, y = r * math.cos(a), r * math.sin(a)
            lo.append((x, y, z_base))
            hi.append((x, y, z + lift))
    lo = [lo[0], lo[1], lo[3], lo[2]]
    hi = [hi[0], hi[1], hi[3], hi[2]]
    mat = PLATE_MATS[rng.randrange(len(PLATE_MATS))]
    # Flanc en `AA_Hull` : la contremarche d'une ecaille EST du blindage vu de
    # trois quarts. En `AA_Greeble` (#141419) elle disparaissait dans le noir et
    # la coquille perdait son epaisseur — c'est une des sources du desequilibre
    # mesure par BRIEF-0041 (32,5 % de greeble contre 11 % de coque).
    top, sides = slab(bm, lo, hi, mat, mat_side="AA_Hull")
    # ⚠️ Une contremarche emissive sur DOUZE (0,26 -> 0,08). Le magenta est un
    # reseau de veines, pas une livree : a une sur quatre il constellait toute la
    # coquille et volait la vedette au noyau, qui est LA cible (spec pilier B).
    if rng.random() < 0.03:
        ak.set_material([sides[0]], "AA_Emissive_Engine")
    if top is not None and rng.random() < 0.42:
        ak.inset_panel(bm, [top], "AA_Panel", thickness=0.040, depth=-0.026)


def _bezier(p0, p1, p2, t: float) -> Vector:
    u = 1.0 - t
    return Vector(
        (u * u * p0[k] + 2.0 * u * t * p1[k] + t * t * p2[k] for k in range(3))
    )


def _bezier_tangent(p0, p1, p2, t: float) -> Vector:
    u = 1.0 - t
    return Vector(
        (2.0 * u * (p1[k] - p0[k]) + 2.0 * t * (p2[k] - p1[k]) for k in range(3))
    )


def _frame(tangent: Vector) -> tuple[Vector, Vector]:
    """Repere transverse (droite, haut) d'une section perpendiculaire."""
    t = tangent.normalized()
    right = t.cross(Vector((0.0, 0.0, 1.0)))
    if right.length < 1e-5:
        right = Vector((1.0, 0.0, 0.0))
    right.normalize()
    up = right.cross(t).normalized()
    return right, up


# ==========================================================================
# Corps
# ==========================================================================


def build_body() -> object:
    """Le pont blinde : disque perce, puits, ventre, mats d'epines, ponts d'armes."""
    bm = bmesh.new()
    thetas = [2.0 * math.pi * j / N_SEG for j in range(N_SEG)]
    degs = [360.0 * j / N_SEG for j in range(N_SEG)]

    def station(k: int, deg: float) -> tuple[float, float, float]:
        """(rayon, z dessus, z dessous) de la station `k` a l'azimut `deg`."""
        if k < len(DISC_R):
            return DISC_R[k], DISC_TOP[k], DISC_BOT[k]
        f = SKIRT_F[k - len(DISC_R)]
        span = body_radius(deg) - DISC_R[-1]
        return (DISC_R[-1] + span * f,
                skirt_z(f, DISC_TOP[-1]), skirt_z(f, DISC_BOT[-1]))

    n_st = len(DISC_R) + len(SKIRT_F)
    top_rings, bot_rings = [], []
    for k in range(n_st):
        top_rings.append(ak.add_ring(bm, [
            (station(k, d)[0] * math.cos(t), station(k, d)[0] * math.sin(t),
             station(k, d)[1])
            for t, d in zip(thetas, degs)
        ]))
        bot_rings.append(ak.add_ring(bm, [
            (station(k, d)[0] * math.cos(t), station(k, d)[0] * math.sin(t),
             station(k, d)[2])
            for t, d in zip(thetas, degs)
        ]))

    # --- les deux nappes ---------------------------------------------------
    # ⚠️ BRIEF-0041 : ces deux nappes sont, a elles seules, la plus grande
    # surface de la coque — 5 700 sommets, plus du tiers du `Body`. Les laisser
    # en `AA_Greeble` (#141419, la couleur des CREUX) revenait a peindre en noir
    # de fond ce qui est justement le blindage, et c'est ce qui produisait le
    # rapport inverse de la planche : 11 % de coque pour 32,5 % de machinerie.
    # Elles passent en `AA_Hull` (anthracite #24252B) ; le greeble se retire ou
    # il a un sens — culots, dessous de tuile, joints etroits.
    top_bands = [ak.bridge_rings(bm, top_rings[k], top_rings[k + 1], "AA_Hull")
                 for k in range(n_st - 1)]
    bot_bands = [ak.bridge_rings(bm, bot_rings[k + 1], bot_rings[k], "AA_Hull")
                 for k in range(n_st - 1)]
    ak.bridge_rings(bm, top_rings[-1], bot_rings[-1], "AA_Trim")   # la tranche

    # --- le puits, et le coeur au fond -------------------------------------
    well = [top_rings[0]] + [polar_ring(bm, r, z, N_SEG) for z, r in SHAFT[1:]]
    for i in range(len(well) - 1):
        ak.bridge_rings(bm, well[i + 1], well[i], SHAFT_MATS[i])
    floor = bm.verts.new((0.0, 0.0, SHAFT[-1][0] - 0.04))
    ak.fan_to_point(bm, well[-1], floor, "AA_Panel")

    # --- le ventre ---------------------------------------------------------
    belly = [bot_rings[0]] + [polar_ring(bm, r, z, N_SEG) for z, r in BELLY[1:]]
    for i in range(len(belly) - 1):
        ak.bridge_rings(bm, belly[i], belly[i + 1], "AA_Hull" if i % 2 else "AA_Panel")
    keel = bm.verts.new((0.0, 0.0, BELLY[-1][0] - 0.03))
    ak.fan_to_point(bm, list(reversed(belly[-1])), keel, "AA_Panel")

    # --- plaques de pont : couronne, gorge, jupe ---------------------------
    def pick(bands, ks, cols):
        out = []
        for k in ks:
            for j in cols:
                face = bands[k][j % N_SEG]
                if face is not None and face.is_valid:
                    out.append(face)
        return out

    rng = random.Random(SEED + 11)
    for s in range(8):
        cols = range(5 * s, 5 * s + 4)
        ak.inset_panel(bm, pick(top_bands, (5, 6), cols),
                       "AA_Trim" if s % 3 else "AA_Hull",
                       thickness=0.030, depth=0.016)
    for s in range(10):
        cols = range(4 * s, 4 * s + 3)
        ak.inset_panel(bm, pick(top_bands, (8, 9), cols),
                       "AA_Trim" if s % 2 else "AA_Hull",
                       thickness=0.040, depth=0.014)
    for s in range(5):
        cols = range(8 * s + 1, 8 * s + 6)
        ak.inset_panel(bm, pick(bot_bands, (7, 8), cols), "AA_Panel",
                       thickness=0.045, depth=0.012)
    # marquage vert maladif (usage tres limite, charte SS3), a un seul endroit
    ak.inset_panel(bm, pick(top_bands, (6,), range(22, 24)), "AA_Marking_Red",
                   thickness=0.030, depth=0.008)

    # --- veines magenta dans les interstices de la jupe --------------------
    # ⚠️ BRIEF-0041 : trois veines la ou il y en avait cinq, et deux troncons au
    # lieu de trois. Le cout de ces boites en sommets est enorme au regard de leur
    # surface : une reglette de 2 cm de large arrive a l'export avec une
    # cinquantaine de sommets (facettes dupliquees par le lissage, plus le
    # chanfrein qui HERITE du materiau adjacent, donc de l'emissif). C'est cette
    # arithmetique-la, et pas une grande nappe rose, qui portait a elle seule
    # pres d'un dixieme du budget emissif de la coque.
    for j in (7, 27):
        deg = degs[j]
        a = thetas[j]
        pts = []
        for f in (0.18, 0.62):
            r = DISC_R[-1] + (body_radius(deg) - DISC_R[-1]) * f
            pts.append(Vector((r * math.cos(a), r * math.sin(a),
                               hull_top(r, deg) + 0.012)))
        for i in range(len(pts) - 1):
            seg_box(bm, pts[i], pts[i + 1], 0.017, 0.010, "AA_Emissive_Engine")

    _build_rim_teeth(bm)
    _build_crest(bm)
    _build_scales(bm)
    _build_masts(bm)
    _build_gun_decks(bm)
    _build_membranes(bm)

    ak.greeble_strip(
        bm, (0.55, 4.10, hull_top(4.15, 82.0)), (-0.35, 5.40, hull_top(5.45, 96.0)),
        count=7, seed=SEED + 21, size_range=(0.070, 0.150),
        height_range=(0.040, 0.090),
    )
    ak.greeble_strip(
        bm, (1.30, -4.30, hull_top(4.50, 287.0)), (0.40, -5.60, hull_top(5.62, 274.0)),
        count=6, seed=SEED + 22, size_range=(0.060, 0.130),
        height_range=(0.035, 0.080),
    )
    return ak.new_object("Body", bm)


def _build_rim_teeth(bm) -> None:
    """Denture fixe de la levre du puits (l'ARMOR RING de la planche).

    ⚠️ Elle mord vers l'INTERIEUR et reste sous z = 0,62 : la levre mobile passe
    au-dessus, et le noyau — donc la levre, qui en est l'enfant — tourne. Une
    dent qui depasserait raboterait la levre a chaque tour.

    ⚠️ BRIEF-0041 : elle mord aussi vers la BOULE. Le noyau descend a r = 1,53 a
    l'altitude des dents ; elles s'arretent a 1,82, soit 24 cm de jeu remesures
    a chaque build par la ligne « Core / coque » du harnais.
    """
    rng = random.Random(SEED + 31)
    for i in range(18):
        a = 2.0 * math.pi * (i + 0.5) / 18.0
        d = Vector((math.cos(a), math.sin(a), 0.0))
        base = d * 1.98 + Vector((0.0, 0.0, 0.52))
        tip = d * (1.82 + rng.uniform(-0.04, 0.04)) + Vector((0.0, 0.0, 0.58))
        seg_box(bm, base, tip, 0.105, 0.070, "AA_Trim")
        if i % 9 == 0:
            seg_box(bm, d * 2.02 + Vector((0.0, 0.0, 0.60)),
                    d * 1.90 + Vector((0.0, 0.0, 0.62)),
                    0.026, 0.012, "AA_Emissive_Engine")


def _build_crest(bm) -> None:
    """Bec avant et dard arriere : les deux cretes qui portent les 14 m.

    Elles sont posees EN FRACTION de la corde (`hull_top`) : le jour ou le
    contour bouge, elles suivent au lieu de flotter au-dessus du vide.
    """
    for deg, spread, count, mat in ((270.0, 7.0, 6, "AA_Trim"),
                                    (90.0, 5.5, 5, "AA_Trim")):
        a = math.radians(deg)
        d = Vector((math.cos(a), math.sin(a), 0.0))
        side = Vector((-math.sin(a), math.cos(a), 0.0))
        span = body_radius(deg) - DISC_R[-1]
        for k in range(count):
            f0 = 0.12 + 0.86 * k / count
            f1 = 0.12 + 0.86 * (k + 1.25) / count
            r0 = DISC_R[-1] + span * f0
            r1 = DISC_R[-1] + span * min(f1, 1.0)
            w0 = spread * 0.10 * (1.0 - f0) + 0.10
            w1 = spread * 0.10 * (1.0 - f1) + 0.07
            z0 = hull_top(r0, deg)
            z1 = hull_top(r1, deg)
            lo = [tuple(d * r0 + side * w0 + Vector((0.0, 0.0, z0 - 0.10))),
                  tuple(d * r0 - side * w0 + Vector((0.0, 0.0, z0 - 0.10))),
                  tuple(d * r1 - side * w1 + Vector((0.0, 0.0, z1 - 0.10))),
                  tuple(d * r1 + side * w1 + Vector((0.0, 0.0, z1 - 0.10)))]
            hi = [tuple(d * r0 + side * w0 + Vector((0.0, 0.0, z0 + 0.11))),
                  tuple(d * r0 - side * w0 + Vector((0.0, 0.0, z0 + 0.11))),
                  tuple(d * r1 - side * w1 + Vector((0.0, 0.0, z1 + 0.07))),
                  tuple(d * r1 + side * w1 + Vector((0.0, 0.0, z1 + 0.07)))]
            top, sides = slab(bm, lo, hi, mat, mat_side="AA_Hull")
            if k == 1:   # une seule contremarche lumineuse par crete
                ak.set_material([sides[0]], "AA_Emissive_Engine")


#: Ecaillage de la jupe : (azimut de debut, azimut de fin, nombre d'ecailles).
#: Les quatre secteurs evitent le bec (270 deg) et le dard (90 deg), ou courent
#: les cretes.
SCALE_SECTORS = ((14.0, 76.0, 6), (102.0, 160.0, 6),
                 (192.0, 254.0, 6), (288.0, 348.0, 6))
#: Deux rangees qui se recouvrent, en FRACTION de la corde restante : l'interne
#: mord sur la gorge, l'externe va jusqu'au bord de la tranche.
SCALE_ROWS = ((0.02, 0.30, 0.48), (0.40, 0.36, 0.56))


def _build_scales(bm) -> None:
    """Ecaillage dorsal de la jupe : deux rangees qui se recouvrent.

    Leur largeur derive du contour a leur azimut, jamais d'une coordonnee
    absolue : une ecaille ne peut donc pas se retrouver a flotter a cote de la
    coque quand le contour change.

    ⚠️ BRIEF-0041 — c'est ICI que se joue la lecture « coque blindee » plutot que
    « disque machine ». Les planches montrent de grandes plaques qui se
    recouvrent et DOMINENT la silhouette, la machinerie reduite aux interstices ;
    la version precedente n'en posait qu'une rangee de cinq par secteur, sur le
    tiers interne de la jupe, et laissait les deux tiers externes en nappe nue.
    On passe a **deux rangees de six**, qui couvrent la jupe du bord de la gorge
    a la tranche. Ce n'est pas de la decoration ajoutee : c'est la surface qui
    manquait a `AA_Hull` et `AA_Trim` pour dominer le budget de matiere.
    """
    rng = random.Random(SEED + 41)
    for deg0, deg1, count in SCALE_SECTORS:
        for row, (base_f, min_len, max_len) in enumerate(SCALE_ROWS):
            for k in range(count):
                shift = 0.5 if row else 0.0
                a0 = math.radians(deg0 + (deg1 - deg0) * (k + shift * 0.5) / count)
                a1 = math.radians(
                    deg0 + (deg1 - deg0) * (k + shift * 0.5 + 0.88) / count)
                d0, d1 = math.degrees(a0), math.degrees(a1)
                f0 = base_f + rng.uniform(0.0, 0.08)
                f1 = min(f0 + rng.uniform(min_len, max_len), 0.99)
                span0 = body_radius(d0) - DISC_R[-1]
                span1 = body_radius(d1) - DISC_R[-1]
                r_in = DISC_R[-1] + span0 * f0
                r_out = DISC_R[-1] + span1 * f1
                z_in = hull_top(r_in, d0)
                z_out = hull_top(r_out, d1)
                lo = [(r_in * math.cos(a0), r_in * math.sin(a0), z_in - 0.16),
                      (r_out * math.cos(a0), r_out * math.sin(a0), z_out - 0.16),
                      (r_out * math.cos(a1), r_out * math.sin(a1), z_out - 0.16),
                      (r_in * math.cos(a1), r_in * math.sin(a1), z_in - 0.16)]
                hi = [(r_in * math.cos(a0), r_in * math.sin(a0), z_in + 0.085),
                      (r_out * math.cos(a0), r_out * math.sin(a0), z_out + 0.032),
                      (r_out * math.cos(a1), r_out * math.sin(a1), z_out + 0.032),
                      (r_in * math.cos(a1), r_in * math.sin(a1), z_in + 0.085)]
                mat = PLATE_MATS[rng.randrange(len(PLATE_MATS))]
                top, sides = slab(bm, lo, hi, mat, mat_side="AA_Hull")
                if rng.random() < 0.04:
                    ak.set_material([sides[0]], "AA_Emissive_Engine")
                if top is not None and rng.random() < 0.45:
                    ak.inset_panel(bm, [top], "AA_Panel",
                                   thickness=0.055, depth=-0.022)


def _build_masts(bm) -> None:
    """Mats dorsaux des epines : le socle qui porte la rotule d'epaule.

    ⚠️ Le mat est VERTICAL et son axe passe sous le pivot. Ce n'est pas un choix
    de style : un longeron oblique de meme section deborde vers l'axe et vient
    croiser la piste des plaques (mesure), et sa matiere pres de la rotule se
    fait raboter par l'epine des le premier degre de pointage. Vertical, ce qui
    subsiste pres du pivot est un pion centre sur l'axe de rotation.
    """
    for spec in SPIKES:
        root = Vector(spec["root"])
        deg = math.degrees(math.atan2(root.y, root.x))
        r = math.hypot(root.x, root.y)
        d = Vector((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0.0))
        r_post = r - 0.08
        deck = hull_top(r_post, deg)
        post = d * r_post
        seg_box(bm, tuple(post + Vector((0.0, 0.0, deck - 0.22))),
                tuple(post + Vector((0.0, 0.0, root.z - 0.36))),
                spec["r0"] * 1.05, spec["r0"] * 1.05, "AA_Panel")
        # Le pion final est CENTRE SUR L'AXE DE ROTATION et plus mince que
        # l'epine : il vit a l'interieur d'elle et n'en sort jamais, quel que
        # soit le pointage. C'est le seul moyen de combler le joint sans que le
        # mat se fasse raboter (le corps du mat, lui, s'arrete 36 cm plus bas).
        seg_box(bm, tuple(Vector((root.x, root.y, root.z - 0.32))),
                tuple(Vector((root.x, root.y, root.z))),
                spec["r0"] * 0.34, spec["r0"] * 0.34, "AA_Panel")
        # embase : large, mais ecrasee sous le plafond de piste
        base_z = min(deck + 0.10, track_ceiling(r_post - 0.42) - 0.02)
        oriented_box(bm, tuple(post + Vector((0.0, 0.0, base_z - 0.16))),
                     (0.96, 0.86, 0.32),
                     Matrix.Rotation(math.radians(deg) + math.pi / 2.0, 3, "Z"),
                     "AA_Hull")
        # BRIEF-0041 : ce jonc etait emissif sur les quatre mats. Il devient une
        # nervure de blindage — la lumiere du vaisseau vient du noyau et des
        # jointures d'epine, pas de sa quincaillerie.
        seg_box(bm, tuple(post + d * spec["r0"] * 1.05
                          + Vector((0.0, 0.0, deck - 0.10))),
                tuple(post + d * spec["r0"] * 1.05
                      + Vector((0.0, 0.0, root.z - 0.14))),
                0.034, 0.018, "AA_Trim")
        # nodule vert maladif au pied du mat : le « bourgeon » d'ou sort le bras
        ak.add_box(bm, tuple(post + d * 0.52 + Vector((0.0, 0.0, deck - 0.02))),
                   (0.19, 0.19, 0.13), "AA_Marking_Red")


def _build_gun_decks(bm) -> None:
    """Les trois ponts d'armes fixes de la proue (Muzzle_C / _L / _R).

    Ils sont conserves parce que le controleur generique les lit encore si
    `external_attacks` retombe a faux : sans eux, un boss non arme par son
    module tirerait depuis son centre geometrique.
    """
    # Seule la bouche CENTRALE est allumee : les deux laterales sont vues de
    # profil sous la camera de jeu, leur magenta ne portait rien et coutait le
    # meme prix en sommets que celui du noyau.
    for x, y, z, scale, bore in (
            (0.0, MUZZLE_C[1], MUZZLE_C[2], 1.0, "AA_Emissive_Engine"),
            (MUZZLE_LR[0], MUZZLE_LR[1], MUZZLE_LR[2], 0.82, "AA_Panel"),
            (-MUZZLE_LR[0], MUZZLE_LR[1], MUZZLE_LR[2], 0.82, "AA_Panel")):
        # `add_lathe` autour de Y : la premiere coordonnee du contour EST le y
        # absolu, on l'exprime donc par rapport a la bouche.
        ak.add_lathe(
            bm,
            # BRIEF-0041 : une seule bande emissive au lieu de deux — le fond de
            # bouche. La collerette qui la precede redevient du blindage.
            [(y + 0.86, 0.000, "AA_Hull"),
             (y + 0.74, 0.44 * scale, "AA_Hull"),
             (y + 0.46, 0.46 * scale, "AA_Hull"),
             (y + 0.34, 0.36 * scale, "AA_Trim"),
             (y + 0.14, 0.30 * scale, "AA_Panel"),
             (y + 0.05, 0.22 * scale, "AA_Greeble"),
             (y, 0.000, bore)],
            12, center_x=x, center_z=z, axis="Y",
        )
        ak.add_box(bm, (x, y + 1.05, z - 0.14), (0.94 * scale, 0.80, 0.26),
                   "AA_Hull")


def _build_membranes(bm) -> None:
    """Membranes sombres (AA_Glass) : les « yeux » morts de la proue.

    Trois, de tailles differentes, deliberement non appairees, posees en
    fraction de corde sur la jupe avant.
    """
    for deg, f, hw, hl in ((248.0, 0.42, 0.30, 0.46),
                           (292.0, 0.30, 0.22, 0.34),
                           (306.0, 0.55, 0.16, 0.26)):
        a = math.radians(deg)
        r = DISC_R[-1] + (body_radius(deg) - DISC_R[-1]) * f
        z = hull_top(r, deg)
        ak.add_box(bm, (r * math.cos(a), r * math.sin(a), z + 0.02),
                   (hw * 2.0, hl * 2.0, 0.12), "AA_Glass")


# ==========================================================================
# Noyau, levre, noeuds, anneaux, coeur
# ==========================================================================


def build_core() -> ak.MovingPart:
    """Noyau : la BOULE du panneau CLOSED CORE, croutee et veinee.

    Trois decisions, et chacune corrige un defaut mesure de BRIEF-0040.

    **Icosphere, pas un tour.** Un tour a grille reguliere (32 meridiens x
    15 paralleles) projette, vu de dessus — l'angle exact de la camera de jeu —
    une famille de cercles concentriques. Avec un inset par facette, le noyau
    lisait comme un spirographe : une rosette plate, pas une sphere. Les facettes
    d'une icosphere n'ont ni rangee ni meridien ; leur reseau de joints est
    directement le « CRACK VEINS » de la planche.

    **Trois etats de facette, pas deux.** Avant : soulevee (donc cerclee d'un
    joint emissif) ou nue (donc integralement emissive). Le second etat coutait
    tres cher — 28,7 % de la coque en emissif, le magenta partout et le modele
    noye. Desormais une facette est soulevee (joint lumineux), **posee a plat**
    (croute muette, sans un seul sommet emissif) ou nue (eclat vif, rare). Le
    dosage est le seul reglage du magenta de tout le vaisseau.

    **Elle deborde.** `CORE_Z + CORE_RZ` fait du noyau le point le plus haut de
    la coque. Une sphere et un disque se projettent tous deux en cercle sous une
    camera zenithale : ce qui trahit le volume, c'est que la boule passe DEVANT
    ce qui l'entoure. Enterree dans sa couronne, comme elle l'etait, elle ne
    pouvait pas se lire autrement qu'a plat.

    Le tirage est seede : rejouer donne le meme noyau, craquelure pour craquelure.
    """
    bm = bmesh.new()
    res = bmesh.ops.create_icosphere(
        bm, subdivisions=CORE_SUBDIV, radius=1.0,
        matrix=Matrix.Diagonal(Vector((CORE_RXY, CORE_RXY, CORE_RZ, 1.0))),
    )
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.0, CORE_Z)), verts=res["verts"])
    idx = ak.mat_index("AA_Emissive_Engine")
    faces = [f for f in bm.faces if f.is_valid]
    for face in faces:
        face.material_index = idx

    rng = random.Random(SEED + 101)
    for face in faces:
        draw = rng.random()
        if draw < CORE_CRUST_P:
            # Plaque soulevee. ⚠️ Son pourtour ne reste PAS emissif en entier :
            # une craquelure qui fait le tour de chaque plaque dessine un filet
            # regulier — un grillage, pas un reseau. `inset_panel` rend les faces
            # de bordure ; on n'en garde qu'une ou deux en magenta, tirees au
            # sort. Les veines se rejoignent alors par endroits et s'interrompent
            # ailleurs, exactement comme le panneau CLOSED CORE, et le budget
            # emissif du noyau tombe des deux tiers.
            mat = "AA_Panel" if rng.random() < 0.72 else "AA_Hull"
            walls = ak.inset_panel(bm, [face], mat, thickness=CORE_CRUST_INSET,
                                   depth=CORE_CRUST_LIFT * rng.uniform(0.7, 1.25))
            ak.set_material(walls, mat)
            if walls:
                ak.set_material([rng.choice(walls)], "AA_Emissive_Engine")
        elif draw < CORE_CRUST_P + CORE_FLAT_P:
            # croute muette : posee a plat, aucun joint, aucun sommet emissif
            ak.set_material(
                [face], "AA_Panel" if rng.random() < 0.62 else "AA_Hull")
        # sinon : facette laissee nue — un eclat de magenta a vif
    return ak.moving_part("Core", bm, (0.0, 0.0, CORE_Z))


def build_heart() -> ak.MovingPart:
    """Le coeur, au fond du puits : la derniere cible du jeu.

    Statique au contrat — rien ne l'anime — mais noeud a part et enfant de
    `Core`, comme l'exige le contrat de noms. `ak.moving_part()` est la seule
    primitive du kit qui sache poser un parent.
    """
    bm = bmesh.new()
    knuckle(bm, (0.0, 0.0, HEART_Z), HEART_R, "AA_Emissive_Engine")
    knuckle(bm, (0.0, 0.0, HEART_Z), HEART_R * 1.34, "AA_Glass")
    for i in range(6):
        a = 2.0 * math.pi * i / 6.0
        d = Vector((math.cos(a), math.sin(a), 0.0))
        seg_box(bm, tuple(d * HEART_R * 1.2 + Vector((0.0, 0.0, HEART_Z))),
                tuple(d * (HEART_R * 1.2 + 0.16) + Vector((0.0, 0.0, HEART_Z - 0.06))),
                0.030, 0.024, "AA_Trim")
    return ak.moving_part("Heart", bm, (0.0, 0.0, HEART_Z), parent="Core")


def iris_top(r: float) -> float:
    """z du DESSUS du volet a un rayon absolu.

    ⚠️ `IRIS_PROFILE` est ecrite de l'exterieur vers l'interieur (rayons
    DECROISSANTS), comme l'etait `LIP_PROFILE` : `lerp_table` la lirait a
    l'envers et rendrait la borne au lieu de l'interpolation. On la retourne.
    """
    return lerp_table([(rr, zz) for rr, zz in reversed(IRIS_PROFILE)], r)


def shutter_pivot(index: int) -> Vector:
    """Pivot d'un volet : sur sa bissectrice, sous la nappe, a mi-glissiere.

    C'est le PATIN. Une translation ne depend pas de son origine — ce que ce
    point fixe, c'est la direction que le code lira dans le noeud : pose sur la
    bissectrice, il rend `normalize(Vector3(pos.x, 0, pos.z))` egal a la
    direction de coulissement, dans le repere du fichier comme dans celui du
    jeu (`FACING_PLAYER` est une rotation de 180 deg autour de Y : elle laisse
    une bissectrice sur elle-meme, au signe pres).
    """
    a = math.radians(IRIS_AZ[index])
    return Vector((IRIS_PIVOT_R * math.cos(a), IRIS_PIVOT_R * math.sin(a),
                   IRIS_PIVOT_Z))


def build_shutter(index: int) -> ak.MovingPart:
    """Un volet de l'iris : secteur de 60 deg de l'ancienne levre, motorise.

    La matiere est celle de `Maw_Lip` au millimetre (`IRIS_PROFILE` EST
    `LIP_PROFILE`) : meme bande radiale, meme profil, meme epaisseur, meme
    tranche interne emissive. Ce qui change, c'est qu'il y en a six, qu'ils
    couvrent 360 deg au lieu de 96, et que chacun est une piece a course
    RECTILIGNE — un diaphragme, l'exact oppose des petales du Choir Harvester.

    Trois details portent la lecture « mecanisme » sous une camera a 20 deg de
    la verticale, et aucun n'est gratuit :
      * les six COUTURES radiales, creusees par le chanfrein : elles disent
        d'avance ou la matiere va se separer ;
      * le PATIN sous la nappe : c'est la piece qui touche la levre du puits en
        premier, et la seule qui explique par quoi le volet est tenu ;
      * les DENTS du bord d'attaque, heritees des griffes de la levre mais
        ramenees a r = 1,62 — au-dela, elles traverseraient l'equateur du noyau
        pendant l'enfoncement.
    """
    bm = bmesh.new()
    center = IRIS_AZ[index]
    angles = [math.radians(center - IRIS_HALF + 2.0 * IRIS_HALF * i / IRIS_SEG)
              for i in range(IRIS_SEG + 1)]

    tops, bots = [], []
    for r, z in IRIS_PROFILE:
        tops.append(ak.add_ring(bm, [(r * math.cos(a), r * math.sin(a), z)
                                     for a in angles]))
        bots.append(ak.add_ring(bm, [(r * math.cos(a), r * math.sin(a), z - IRIS_T)
                                     for a in angles]))
    # Dessus : ivoire sur les deux bandes internes (la couronne qu'on voit),
    # anthracite sur les deux externes (le blindage qui plonge sous la piste).
    for i in range(len(IRIS_PROFILE) - 1):
        ak.bridge_rings(bm, tops[i], tops[i + 1],
                        "AA_Hull" if i < 2 else "AA_Trim", closed=False)
        ak.bridge_rings(bm, bots[i + 1], bots[i], "AA_Greeble", closed=False)
    # Tranche externe : le dos du volet.
    ak.bridge_rings(bm, bots[0], tops[0], "AA_Hull", closed=False)
    # ⚠️ Tranche interne : le BORD D'ATTAQUE, et c'est la seule surface emissive
    # de la piece. Au repos les six arcs dessinent un cercle magenta continu
    # autour de la boule ; des que l'iris s'ecarte, il se casse en six morceaux
    # qui s'eloignent. C'est ce signal-la, et pas la course elle-meme, qui dit
    # au joueur que la gueule s'ouvre — la course, vue de dessus, est en grande
    # partie un enfoncement, donc peu lisible dans l'axe de la camera.
    ak.bridge_rings(bm, bots[-1], tops[-1], "AA_Emissive_Engine", closed=False)
    # Flancs du secteur : ce sont eux qu'on decouvre quand l'iris s'ecarte.
    for j, mat in ((0, "AA_Greeble"), (IRIS_SEG, "AA_Greeble")):
        ring = [tops[i][j] for i in range(len(tops))]
        ring += [bots[i][j] for i in reversed(range(len(bots)))]
        ak.cap_ring(bm, ring if j else list(reversed(ring)), mat)

    # --- dents du bord d'attaque -------------------------------------------
    for deg in IRIS_TOOTH_AZ:
        a = math.radians(center + deg)
        d = Vector((math.cos(a), math.sin(a), 0.0))
        seg_box(bm, tuple(d * IRIS_TOOTH_R[0] + Vector((0.0, 0.0, IRIS_TOOTH_Z))),
                tuple(d * IRIS_TOOTH_R[1] + Vector((0.0, 0.0, IRIS_TOOTH_Z - 0.03))),
                0.070, 0.045, "AA_Trim")

    # --- patin de glissiere, SOUS la nappe ----------------------------------
    #
    # ⚠️ Il est bati en RINGS, pas avec `seg_box`. `_align_y()` emploie la
    # rotation la plus courte de +Y vers la direction demandee : sur une pente
    # de 49 deg elle fait BASCULER la section de la boite, et les coins bas
    # descendaient 5 cm plus bas que la ligne demandee — droit sur la denture
    # fixe de la levre du puits (marge tombee a 21,6 mm, mesuree). Un balayage
    # de sections suit le profil exactement, sans surprise d'orientation.
    a = math.radians(center)
    d = Vector((math.cos(a), math.sin(a), 0.0))
    half = math.radians(IRIS_SHOE[0])
    sections = []
    for r, z in IRIS_PROFILE:
        if not (IRIS_SHOE_R[0] - 1e-6 <= r <= IRIS_SHOE_R[1] + 1e-6):
            continue
        top, bot = z - IRIS_T + 0.004, z - IRIS_T - IRIS_SHOE[1]
        al, ar = a - half, a + half
        sections.append(ak.add_ring(bm, [
            (r * math.cos(al), r * math.sin(al), top),
            (r * math.cos(ar), r * math.sin(ar), top),
            (r * math.cos(ar), r * math.sin(ar), bot),
            (r * math.cos(al), r * math.sin(al), bot),
        ]))
    for i in range(len(sections) - 1):
        ak.bridge_rings(bm, sections[i], sections[i + 1], "AA_Greeble")
    ak.cap_ring(bm, list(reversed(sections[0])), "AA_Greeble")
    ak.cap_ring(bm, sections[-1], "AA_Greeble")

    # --- butee de fin de course, sur le dessus ------------------------------
    zs = iris_top(IRIS_STOP_R)
    oriented_box(bm, tuple(d * IRIS_STOP_R + Vector((0.0, 0.0, zs + IRIS_STOP[2] * 0.4))),
                 (IRIS_STOP[0] * 2.0, IRIS_STOP[1] * 2.0, IRIS_STOP[2]),
                 _align_y(d), "AA_Panel")

    return ak.moving_part(f"Shutter_{index + 1:02d}", bm,
                          tuple(shutter_pivot(index)), parent="Core")


def shutter_of_node(index: int) -> str:
    """Le volet qui porte le noeud `index` — decide par l'azimut, pas a la main."""
    az = NODE_AZ[index] % 360.0
    for k, center in enumerate(IRIS_AZ):
        if abs(((az - center + 180.0) % 360.0) - 180.0) <= 30.0:
            return f"Shutter_{k + 1:02d}"
    raise ak.ContractError(f"noeud a {az} deg : aucun volet ne le porte")


def node_base(index: int) -> Vector:
    a = math.radians(NODE_AZ[index])
    return Vector((NODE_R * math.cos(a), NODE_R * math.sin(a), NODE_Z))


def build_node(index: int) -> ak.MovingPart:
    """Un noeud gravitique : fer de lance sur embase articulee.

    Il est plante sur la crete de la levre, penche vers l'exterieur. Sa
    retraction (-60 deg) le REDRESSE vers l'avant, presque a la verticale
    au-dessus de la gueule, ou il n'y a que du vide : c'est la seule direction
    qui degage, et `NODE_TILT` a ete choisi pour elle (cf. le commentaire de la
    constante : deux autres placements ont ete refuses par la mesure).
    """
    bm = bmesh.new()
    base = node_base(index)
    a = math.radians(NODE_AZ[index])
    out = Vector((math.cos(a), math.sin(a), 0.0))
    tilt = math.radians(NODE_TILT)
    axis = (out * math.cos(tilt) + Vector((0.0, 0.0, 1.0)) * math.sin(tilt)).normalized()
    side = Vector((-math.sin(a), math.cos(a), 0.0))
    up = side.cross(axis).normalized()
    length = NODE_LEN[index]

    knuckle(bm, tuple(base), NODE_W * 0.95, "AA_Greeble")
    sections = ((0.10, 1.00), (0.34, 0.86), (0.62, 0.58), (0.84, 0.30))
    rings = []
    for s, w in sections:
        c = base + axis * (length * s)
        rings.append(ak.add_ring(bm, [
            tuple(c + side * (NODE_W * w) + up * (NODE_W * w * 0.55)),
            tuple(c - side * (NODE_W * w) + up * (NODE_W * w * 0.55)),
            tuple(c - side * (NODE_W * w * 0.72) - up * (NODE_W * w * 0.62)),
            tuple(c + side * (NODE_W * w * 0.72) - up * (NODE_W * w * 0.62)),
        ]))
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Trim")
        ak.set_material([band[2]], "AA_Panel")
        if i == 1:
            ak.set_material([band[1], band[3]], "AA_Emissive_Engine")
    tip = bm.verts.new(tuple(base + axis * length))
    ak.fan_to_point(bm, rings[-1], tip, "AA_Trim")
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    # ⚠️ BRIEF-0083 : le parent est le VOLET qui le porte, plus la levre — elle
    # n'existe plus. Le noeud recule et coulisse avec son volet ; laisse enfant
    # du noyau, il serait reste suspendu au-dessus du vide, iris ouvert.
    return ak.moving_part(f"Node_{index + 1:02d}", bm, tuple(base),
                          parent=shutter_of_node(index))


def build_ring(index: int) -> ak.MovingPart:
    """Un anneau interne du puits, perce de son ouverture (« OFFSET GATE »).

    C'est une bande annulaire incomplete : le joueur, aspire vers le fond, doit
    aligner sa position laterale sur l'ouverture au moment ou il la franchit.
    Le decalage d'un anneau au suivant interdit la descente en ligne droite.
    """
    z, gate, band = RINGS[index]
    r_out = ring_radius(index)
    r_in = r_out - band
    bm = bmesh.new()
    span = 360.0 - RING_GAP
    angles = [math.radians(gate + RING_GAP * 0.5 + span * i / RING_SEG)
              for i in range(RING_SEG + 1)]

    def ring_at(radius: float, dz: float):
        return ak.add_ring(bm, [(radius * math.cos(a), radius * math.sin(a), z + dz)
                                for a in angles])

    out_hi, out_lo = ring_at(r_out, RING_T * 0.5), ring_at(r_out, -RING_T * 0.5)
    in_hi, in_lo = ring_at(r_in, RING_T * 0.5), ring_at(r_in, -RING_T * 0.5)
    ak.bridge_rings(bm, in_hi, out_hi, "AA_Trim", closed=False)
    ak.bridge_rings(bm, out_lo, in_lo, "AA_Greeble", closed=False)
    ak.bridge_rings(bm, out_hi, out_lo, "AA_Hull", closed=False)
    # ⚠️ BRIEF-0041 : la paroi INTERNE de l'anneau — 26 quads par anneau, cinq
    # anneaux — n'est plus emissive. Elle l'etait sur toute sa longueur, ce qui
    # faisait du puits un tube de neon vu de dessus. Ne restent lumineuses que les
    # deux TRANCHES de l'ouverture : c'est la porte qui brille, et c'est elle que
    # le joueur doit trouver en phase 4. Un signal, plus un aplat.
    ak.bridge_rings(bm, in_lo, in_hi, "AA_Panel", closed=False)
    for j, rev in ((0, True), (RING_SEG, False)):
        ring = [out_hi[j], in_hi[j], in_lo[j], out_lo[j]]
        ak.cap_ring(bm, list(reversed(ring)) if rev else ring, "AA_Emissive_Engine")
    # Nervures : l'anneau lit comme une machine, pas comme un joint torique.
    # ⚠️ Elles saillent vers l'INTERIEUR du puits. Vers l'exterieur, elles
    # mangeaient le jeu radial calcule par `ring_radius()` — et c'est
    # exactement le detail pose « en coordonnee absolue » que le corollaire du
    # Specter-9 interdit.
    for k in range(0, RING_SEG, 4):
        a = angles[k]
        d = Vector((math.cos(a), math.sin(a), 0.0))
        seg_box(bm, tuple(d * (r_in + 0.03) + Vector((0.0, 0.0, z))),
                tuple(d * (r_in - 0.05) + Vector((0.0, 0.0, z))),
                0.040, RING_T * 0.62, "AA_Hull")
    return ak.moving_part(f"Ring_{index + 1:02d}", bm, (0.0, 0.0, z), parent="Core")


# ==========================================================================
# Coquille : anneau porteur, croissant, plaques
# ==========================================================================


def arc_ring(bm, radius: float, z: float, phi_a: float, phi_b: float,
             segments: int):
    """Boucle OUVERTE : la primitive de tout ce qui doit rester incomplet."""
    return ak.add_ring(bm, [
        (radius * math.cos(math.radians(phi_a + (phi_b - phi_a) * i / segments)),
         radius * math.sin(math.radians(phi_a + (phi_b - phi_a) * i / segments)),
         z)
        for i in range(segments + 1)
    ])


def build_shell_ring() -> ak.MovingPart:
    """L'anneau porteur : il ne porte que l'orbite, et rien d'autre.

    Deux rangees de tuiles tangentielles dephasees, posees dans la gorge du
    pont. La nappe emissive sous les tuiles n'est visible que par les fentes :
    la lumiere sort *d'entre* les ecailles, elle n'est pas peinte dessus.

    ⚠️ BRIEF-0041 — CE N'EST PLUS UN ANNEAU, C'EST UN ARC. C'etait la cause
    reelle de l'echec du critere « anneau incomplet » : le croissant avait bien
    ses 130 deg d'ouverture, mais cette piece-ci, complete a 360 deg et posee
    juste dessous, refermait le trou a l'oeil. On ne voyait pas une ouverture, on
    voyait une couronne concentrique de plus. L'arc deborde le croissant de
    `SR_MARGIN` degres de chaque cote — assez pour que la coquille garde une
    epaisseur lisible sur ses bords, trop peu pour reboucher quoi que ce soit.
    """
    bm = bmesh.new()
    rng = random.Random(SEED + 201)
    phi_a, phi_b = CR_PHI_A - SR_MARGIN, CR_PHI_B + SR_MARGIN
    n_glow = 30
    glow_lo = arc_ring(bm, 2.18, RING_Z_BASE + 0.02, phi_a, phi_b, n_glow)
    glow_hi = arc_ring(bm, 2.96, RING_Z_BASE + 0.02, phi_a, phi_b, n_glow)
    ak.bridge_rings(bm, glow_lo, glow_hi, "AA_Emissive_Engine", closed=False)
    glow_bot_lo = arc_ring(bm, 2.18, RING_Z_BASE - 0.06, phi_a, phi_b, n_glow)
    glow_bot_hi = arc_ring(bm, 2.96, RING_Z_BASE - 0.06, phi_a, phi_b, n_glow)
    ak.bridge_rings(bm, glow_bot_hi, glow_bot_lo, "AA_Greeble", closed=False)
    ak.bridge_rings(bm, glow_hi, glow_bot_hi, "AA_Greeble", closed=False)
    ak.bridge_rings(bm, glow_bot_lo, glow_lo, "AA_Greeble", closed=False)
    for quad, rev in (((glow_lo[0], glow_hi[0], glow_bot_hi[0], glow_bot_lo[0]),
                       True),
                      ((glow_lo[-1], glow_hi[-1], glow_bot_hi[-1],
                        glow_bot_lo[-1]), False)):
        ak.cap_ring(bm, list(reversed(quad)) if rev else list(quad), "AA_Hull")

    span = math.radians(phi_b - phi_a)
    for r_in, r_out, z_in, z_out, count, phase in RING_ROWS:
        step = span / count
        for k in range(count):
            a0 = math.radians(phi_a) + (k + phase * 0.5) * step
            a1 = min(a0 + step * RING_OVERLAP, math.radians(phi_b))
            if a1 - a0 < step * 0.35:
                continue
            tangential_tile(
                bm, rng, a0, a1,
                r_in + rng.uniform(-0.02, 0.03), r_out + rng.uniform(-0.05, 0.05),
                z_in + rng.uniform(-0.02, 0.04), z_out + rng.uniform(-0.03, 0.03),
                RING_Z_BASE, 0.030,
            )
    return ak.moving_part("Shell_Ring", bm, SHELL_PIVOT)


def cr_swell(phi_deg: float) -> float:
    """Facteur d'epaisseur radiale du croissant a l'azimut `phi_deg`.

    Interpole lineairement `CR_SWELL` d'un bout a l'autre de l'arc. C'est
    l'asymetrie principale de la silhouette : une extremite du croissant est
    epaisse de 49 % de plus que l'autre. Le facteur s'applique a la CORDE
    (`r_out - r_in`) et jamais au rayon interne, qui doit rester constant : c'est
    lui qui garantit que rien ne descend dans la gorge de la coque.
    """
    t = (phi_deg - CR_PHI_A) / (CR_PHI_B - CR_PHI_A)
    t = min(max(t, 0.0), 1.0)
    return CR_SWELL[0] + (CR_SWELL[1] - CR_SWELL[0]) * t


def build_crescent() -> ak.MovingPart:
    """Le croissant : l'anneau INCOMPLET de la charte, monte sur l'anneau porteur.

    Sa charniere est tangente a son bord arriere : toute sa matiere est en avant
    d'elle, donc la bascule de fin de phase 1 (0 -> 65 deg) la redresse sans
    qu'un seul point ne plonge vers la coque. Les 155 deg manquants ouvrent sur
    le quadrant avant-tribord — l'anneau est ouvert du cote ou le boss est le
    plus arme, et c'est le secteur que la camera montre en grand.

    ⚠️ BRIEF-0041 : il s'EPAISSIT d'un bout a l'autre (`cr_swell`). Un croissant
    d'epaisseur constante, quelle que soit son ouverture, se relit comme un
    anneau auquel il manque un morceau ; un croissant qui enfle se lit comme une
    carapace de creature. C'est la meme intention que le contour dissymetrique de
    `BODY_R`, portee jusqu'a la coquille.
    """
    bm = bmesh.new()
    rng = random.Random(SEED + 301)
    span = CR_PHI_B - CR_PHI_A

    # nappe emissive continue, sous les tuiles
    a0, a1 = math.radians(CR_PHI_A), math.radians(CR_PHI_B)
    n_glow = 26
    lo_ring, hi_ring = [], []
    for i in range(n_glow + 1):
        phi = CR_PHI_A + span * i / n_glow
        a = math.radians(phi)
        r_hi = 2.24 + 0.80 * cr_swell(phi)
        lo_ring.append((2.24 * math.cos(a), 2.24 * math.sin(a), CR_Z_BASE - 0.03))
        hi_ring.append((r_hi * math.cos(a), r_hi * math.sin(a), CR_Z_BASE - 0.03))
    lo = ak.add_ring(bm, lo_ring)
    hi = ak.add_ring(bm, hi_ring)
    ak.bridge_rings(bm, lo, hi, "AA_Emissive_Engine", closed=False)
    lo2 = ak.add_ring(bm, [(x, y, z - 0.10) for x, y, z in lo_ring])
    hi2 = ak.add_ring(bm, [(x, y, z - 0.10) for x, y, z in hi_ring])
    ak.bridge_rings(bm, hi2, lo2, "AA_Greeble", closed=False)
    ak.bridge_rings(bm, hi, hi2, "AA_Greeble", closed=False)
    ak.bridge_rings(bm, lo2, lo, "AA_Greeble", closed=False)
    for pair, rev in (((lo[0], hi[0], hi2[0], lo2[0]), True),
                      ((lo[-1], hi[-1], hi2[-1], lo2[-1]), False)):
        ak.cap_ring(bm, list(reversed(pair)) if rev else list(pair), "AA_Greeble")

    for r_in, r_out, count, lift, phase in CR_ROWS:
        step = math.radians(span) / count
        for k in range(-1, count):
            b0 = math.radians(CR_PHI_A) + (k + phase) * step
            b1 = min(b0 + step * CR_OVERLAP, math.radians(CR_PHI_B))
            b0 = max(b0, math.radians(CR_PHI_A))
            if b1 - b0 < step * 0.35:
                continue
            swell = cr_swell(math.degrees((b0 + b1) * 0.5))
            tangential_tile(
                bm, rng, b0, b1,
                r_in + rng.uniform(-0.02, 0.03),
                r_in + (r_out - r_in) * swell + rng.uniform(-0.04, 0.04),
                CR_TOP + lift + rng.uniform(-0.02, 0.02),
                CR_TOP + lift - 0.04 + rng.uniform(-0.02, 0.02),
                CR_Z_BASE, 0.028,
            )

    # cornes : deux pointes qui prolongent les extremites du croissant, l'une
    # bien plus longue que l'autre — les deux bouts de l'ouverture ne se
    # repondent pas, et c'est ce qui empeche l'oeil de la refermer.
    for phi, length, r_tip in ((CR_PHI_A, -24.0, 2.60), (CR_PHI_B, 9.0, 2.86)):
        a = math.radians(phi)
        r_out = 2.30 + 0.74 * cr_swell(phi)
        ring = ak.add_ring(bm, [
            (2.30 * math.cos(a), 2.30 * math.sin(a), CR_Z_BASE + 0.02),
            (r_out * math.cos(a), r_out * math.sin(a), CR_Z_BASE + 0.02),
            (r_out * math.cos(a), r_out * math.sin(a), CR_TOP + 0.02),
            (2.30 * math.cos(a), 2.30 * math.sin(a), CR_TOP + 0.02),
        ])
        b = math.radians(phi + length)
        tip = bm.verts.new((r_tip * math.cos(b), r_tip * math.sin(b),
                            CR_Z_BASE + 0.08))
        ak.fan_to_point(bm, ring, tip, "AA_Trim")
        ak.cap_ring(bm, list(reversed(ring)), "AA_Greeble")
    return ak.moving_part("Shell_Crescent", bm, CR_PIVOT, parent="Shell_Ring")


def plate_pivot(index: int) -> Vector:
    """Charniere d'une plaque : sur son bord INTERNE, tangente a l'anneau."""
    a = math.radians(PLATES[index][0])
    return Vector((PLATE_R[0] * math.cos(a), PLATE_R[0] * math.sin(a), PLATE_Z[0]))


def build_plate(index: int) -> ak.MovingPart:
    """Une plaque d'armure : ecailles superposees, couture de noyau magenta.

    ⚠️ La charniere est TANGENTIELLE et posee sur le bord INTERNE : a -80 deg
    autour de `UP x radial` (la convention du Choir Harvester pour son iris) la
    plaque se **souleve vers l'exterieur**. Elle ne peut pas tomber vers le bas :
    sous elle il y a la coquille, puis le pont — une chute vers l'interieur
    traverserait les deux. Le geste lit comme une ecaille qu'on arrache, ce que
    montre le panneau CORE EXPOSED.
    """
    center, half = PLATES[index]
    rng = random.Random(SEED + 401 + index)
    bm = bmesh.new()

    def point(f: float, s: float, dz: float) -> tuple[float, float, float]:
        """`f` : 0 a la charniere, 1 au bord externe. `s` : -1..1 en azimut."""
        a = math.radians(center + half * s)
        r = PLATE_R[0] + (PLATE_R[1] - PLATE_R[0]) * f
        z = lerp_table([(0.0, PLATE_Z[0]), (0.55, PLATE_Z[1]), (1.0, PLATE_Z[2])], f)
        # bombement transversal : la plaque est une ecaille, pas une planche
        z += 0.05 * (1.0 - s * s)
        return (r * math.cos(a), r * math.sin(a), z + dz)

    fs = [i / PLATE_SEG for i in range(PLATE_SEG + 1)]
    ss = (-1.0, -0.72, -0.30, 0.30, 0.72, 1.0)
    tops = [ak.add_ring(bm, [point(f, s, 0.0) for s in ss]) for f in fs]
    bots = [ak.add_ring(bm, [point(f, s, -PLATE_T) for s in ss]) for f in fs]
    for i in range(PLATE_SEG):
        band = ak.bridge_rings(bm, tops[i], tops[i + 1], "AA_Trim", closed=False)
        ak.bridge_rings(bm, bots[i + 1], bots[i], "AA_Greeble", closed=False)
        if i in (2, 5) and len(band) > 2:
            ak.inset_panel(bm, [band[1], band[2], band[3]], "AA_Panel",
                           thickness=0.045, depth=-0.028)
        if i % 3 == 1:
            ak.set_material([band[0], band[-1]], "AA_Hull")
    ak.bridge_rings(bm, tops[0], bots[0], "AA_Panel", closed=False)
    ak.bridge_rings(bm, bots[PLATE_SEG], tops[PLATE_SEG], "AA_Trim", closed=False)
    # ⚠️ BRIEF-0041 — LE CORE SEAM DE LA PLANCHE, SANS GEOMETRIE AJOUTEE. Il
    # etait fait de quatre reglettes emissives par plaque : 414 sommets, soit
    # **la moitie de chaque plaque en magenta**, pour une couture que le panneau
    # ARMOR PLATE montre comme un lisere. On assigne desormais le materiau au
    # flanc lateral deja modelise (`j = 0`, le bord tourne vers l'interieur du
    # croissant) : meme liseré, 16 sommets, aucun triangle de plus.
    for j, rev in ((0, False), (len(ss) - 1, True)):
        ring = [tops[i][j] for i in range(len(tops))]
        ring += [bots[i][j] for i in reversed(range(len(bots)))]
        ak.cap_ring(bm, list(reversed(ring)) if rev else ring,
                    "AA_Emissive_Engine" if j == 0 else "AA_Greeble")

    # bouche de tir de la plaque
    port = point(0.62, 0.0, 0.04)
    knuckle(bm, port, 0.11, "AA_Emissive_Engine")
    if rng.random() < 0.5:
        knuckle(bm, point(0.30, 0.55, 0.03), 0.09, "AA_Greeble")
    return ak.moving_part(f"Plate_{index + 1:02d}", bm, tuple(plate_pivot(index)),
                          parent="Shell_Crescent")


def plate_muzzle(index: int) -> tuple[float, float, float]:
    center, _ = PLATES[index]
    a = math.radians(center)
    r = PLATE_R[0] + (PLATE_R[1] - PLATE_R[0]) * 0.62
    return (r * math.cos(a), r * math.sin(a), PLATE_Z[1] + 0.14)


# ==========================================================================
# Epines — trois maillons chaines par bras
# ==========================================================================


def spike_radius(spec: dict, t: float) -> float:
    """Rayon a l'abscisse `t` : effilement global + relief de vertebre."""
    base = spec["r0"] * (1.0 - t) ** spec["taper"] + SPIKE_TIP_R
    frac = (t * spec["vertebrae"]) % 1.0
    return base * (1.0 + SPIKE_FLARE * (1.0 - frac) ** 1.6)


def spike_point(spec: dict, t: float) -> Vector:
    return _bezier(spec["root"], spec["ctrl"], spec["tip"], t)


def _spike_section(bm, spec: dict, t: float):
    center = spike_point(spec, t)
    right, up = _frame(_bezier_tangent(spec["root"], spec["ctrl"], spec["tip"], t))
    r = spike_radius(spec, t)
    rx, rz = r, r * spec["flat"]
    pts = []
    for j in range(spec["sides"]):
        a = 2.0 * math.pi * j / spec["sides"]
        pts.append(tuple(center + up * (rz * math.cos(a)) + right * (rx * math.sin(a))))
    return ak.add_ring(bm, pts)


def build_spike_segment(spec: dict, seg: int) -> ak.MovingPart:
    """Un maillon d'epine : sections elliptiques aplaties le long d'une Bezier.

    Le rayon repart en avant a chaque vertebre : chaque segment recouvre le
    suivant comme une ecaille, et l'anneau de jonction — le plus etroit — est
    emissif. C'est la « veine de magenta » de la planche, obtenue par la
    geometrie et non par une texture (ADR-0008).

    Chaque maillon commence par une rotule centree sur SON pivot et laisse un
    jeu (`SPIKE_GAP`) avant sa premiere section : une vertebre qui part du pivot
    balaie un cylindre autour de lui et rabote le maillon precedent des le
    premier degre de flexion.
    """
    t0, t1 = spec["splits"]
    bounds = ((0.0, t0), (t0, t1), (t1, 1.0))[seg]
    pivot = spike_point(spec, bounds[0])
    r_pivot = spike_radius(spec, bounds[0])

    bm = bmesh.new()
    knuckle(bm, tuple(pivot), r_pivot * 0.94, "AA_Panel")

    length = bounds[1] - bounds[0]
    gap = min(SPIKE_GAP * r_pivot / max(_arc_len(spec), 1e-3), length * 0.30)
    lo = bounds[0] + gap
    hi = bounds[1] - (0.0 if seg == 2 else gap * 0.7)
    n = max(int(round(spec["vertebrae"] * SPIKE_SAMPLES * (hi - lo))), 3)
    rings = [_spike_section(bm, spec, lo + (hi - lo) * i / n) for i in range(n + 1)]

    sides = spec["sides"]
    top_ks = (0, 1, sides - 1)
    side_ks = (2, sides - 2)
    bottom_k = sides // 2
    for i in range(n):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        phase = i % SPIKE_SAMPLES
        if phase == SPIKE_SAMPLES - 1:
            # ⚠️ BRIEF-0041 : la jonction de vertebres n'est plus emissive SUR
            # TOUT SON POURTOUR (9 faces), seulement sur les trois du dessus. Un
            # anneau complet, repete a chaque vertebre sur quatre bras, faisait a
            # lui seul ~850 sommets magenta — et sous une camera zenithale la
            # moitie n'etait meme pas visible. Ce qui se voit, c'est une VEINE
            # DORSALE qui court le long du dard : c'est ce que montre le panneau
            # DETACHED SPIKE.
            ak.set_material(band, "AA_Trim")
            ak.set_material([band[k] for k in top_ks[:1]], "AA_Emissive_Engine")
            continue
        if phase == 0:
            ak.set_material(band, "AA_Trim")              # collier ivoire
            continue
        ak.set_material([band[k] for k in top_ks], "AA_Trim")
        ak.set_material([band[k] for k in side_ks], "AA_Hull")
        ak.set_material([band[bottom_k]], "AA_Greeble")
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Panel")
    if seg == 2:
        tip = bm.verts.new(tuple(Vector(spec["tip"])))
        ak.fan_to_point(bm, rings[-1], tip, "AA_Trim")    # griffe ivoire
    else:
        ak.cap_ring(bm, rings[-1], "AA_Panel")
        # bouche de tir (le WEAPON PORT de la planche), sur le maillon median
        if seg == 1 and spec["port"] > bounds[0]:
            port = spike_point(spec, spec["port"])
            _, up = _frame(_bezier_tangent(spec["root"], spec["ctrl"],
                                           spec["tip"], spec["port"]))
            knuckle(bm, tuple(port + up * spike_radius(spec, spec["port"]) * 0.55),
                    0.075, "AA_Emissive_Engine")

    name = spec["name"] + ("", "_Mid", "_Tip")[seg]
    parent = None if seg == 0 else spec["name"] + ("", "", "_Mid")[seg]
    return ak.moving_part(name, bm, tuple(pivot), parent=parent)


def _arc_len(spec: dict) -> float:
    """Longueur approchee de la Bezier : sert a convertir un jeu metrique en t."""
    pts = [spike_point(spec, i / 16.0) for i in range(17)]
    return sum((pts[i + 1] - pts[i]).length for i in range(16))


def spike_muzzle(spec: dict) -> tuple[float, float, float]:
    port = spike_point(spec, spec["port"])
    _, up = _frame(_bezier_tangent(spec["root"], spec["ctrl"], spec["tip"],
                                   spec["port"]))
    return tuple(port + up * (spike_radius(spec, spec["port"]) * 0.55 + 0.10))


# ==========================================================================
# Points d'attache
# ==========================================================================


def build_attach_points() -> list:
    """Positions **derivees de la geometrie**, jamais devinees.

    ⚠️ `ak.attach_point()` ne sait pas parenter : ces marqueurs sont des noeuds
    RACINES fixes. Ils donnent un point d'apparition, pas une position suivie —
    une plaque qui bascule n'emmene pas sa bouche avec elle. C'est la meme
    limite que sur le Choir Harvester, et elle est sans consequence tant que le
    combat calcule la direction de tir a part.
    """
    points = [
        ak.attach_point("Core_Center", (0.0, 0.0, CORE_Z)),
        ak.attach_point("Maw_Center", (0.0, 0.0, CORE_Z + CORE_RZ + 0.10)),
        ak.attach_point("Tunnel_End", (0.0, 0.0, HEART_Z + 0.14)),
        ak.attach_point("Muzzle_C", MUZZLE_C),
    ]
    points += list(ak.attach_pair("Muzzle", *MUZZLE_LR))
    for i in range(len(PLATES)):
        points.append(ak.attach_point(f"Muzzle_Plate_{i + 1:02d}", plate_muzzle(i)))
    for spec in SPIKES:
        points.append(
            ak.attach_point(f"Muzzle_{spec['name']}", spike_muzzle(spec))
        )
    return points


# ==========================================================================
# Mesure de degagement — le livrable central de BRIEF-0040
#
# Le contrat d'`export_hull()` ne connait QUE la pose de repos. Une piece qui
# traverse la coque des qu'elle bouge le passe sans un mot : c'est exactement ce
# qui a coute quatre briefs au Specter-9 (un marquage a cheval sur une charniere
# avait fait tomber le debattement d'un volet de 18,5 a 2,8 deg — bounding box
# parfaite, volet dans la coque). On remesure donc a chaque build, sur le
# maillage REELLEMENT livre, en rejouant les rotations que le combat ecrira.
# ==========================================================================

#: Repere d'auteur -> repere Godot : (x, y, z) -> (-x, z, y). Rotation rigide
#: (determinant +1) : un axe se transporte comme un vecteur, un angle est
#: conserve. Toute la mesure se fait DANS LE REPERE GODOT, avec exactement les
#: rotations qu'ecrira le combat — un signe faux valide une piece qui traverse
#: la coque, et personne ne le verrait avant le jeu.
_TO_GODOT = Matrix(((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)))

#: Amplitudes exigees par le gameplay (BRIEF-0040 SS« Debattements »).
ORBIT_STEPS = 12          # echantillons de l'orbite 360 deg de la coquille
CRESCENT_DEG = 65.0
PLATE_DEG = -80.0
NODE_DEG = -60.0
#: Echantillons de la course de l'iris. ⚠️ Ce n'est PAS un angle : les volets ne
#: tournent pas. Chaque pose est une translation composee — enfoncement d'abord,
#: coulissement ensuite, dans cet ordre, comme le code l'ecrira.
IRIS_STEPS = 6
SPIKE_DEG = 40.0
FLEX_DEG = 25.0

#: Rayon d'exclusion de charniere, par piece. Une articulation reelle
#: s'interpenetre PAR CONSTRUCTION (rotule dans son logement, racine dans son
#: berceau) ; la mesure ecarte donc, des DEUX cotes, la matiere a moins de ce
#: rayon du pivot. C'est licite : une rotation autour d'un axe passant par le
#: pivot conserve la distance au pivot, donc rien de ce qui est exclu ne peut
#: rencontrer ce qui ne l'est pas.
#:
#: ⚠️ AUCUN RAYON D'EXCLUSION POUR LES VOLETS, et c'est une decision, pas un
#: oubli : l'argument qui rend un `skip` licite est l'invariance par ROTATION
#: autour du pivot. Une translation ne conserve aucune distance : rien ne
#: justifierait d'ecarter de la matiere. Les volets sont donc mesures entiers.
SKIP_NODE = 0.24
SKIP_PLATE = 0.16
SKIP_CRESCENT = 0.18


def _godot_euler(x: float, y: float, z: float) -> Matrix:
    """Basis Godot pour `rotation = Vector3(x, y, z)` — ordre YXZ, en radians."""
    return (Matrix.Rotation(y, 4, "Y") @ Matrix.Rotation(x, 4, "X")
            @ Matrix.Rotation(z, 4, "Z"))


def _tangent_axis(pivot: Vector) -> Vector:
    """L'axe `UP x radial` d'une piece posee en couronne, en repere Godot.

    C'est exactement ce que calcule `harvester_combat._bind_iris()` pour l'iris
    du mini-boss : le code deduit l'axe de la POSITION du noeud, sans donnee
    supplementaire. On mesure donc avec le meme axe que celui qui sera ecrit.
    """
    radial = Vector((pivot.x, 0.0, pivot.z))
    if radial.length < 1e-6:
        return Vector((1.0, 0.0, 0.0))
    return Vector((0.0, 1.0, 0.0)).cross(radial.normalized()).normalized()


def _clip_sphere(verts: list, tri: list, pivot: Vector, skip: float,
                 out: list, depth: int = 0) -> None:
    """Garde de `tri` ce qui est HORS de la sphere (`pivot`, `skip`), en coupant.

    Un simple test « tous les sommets dedans ? » ne suffit pas : un longeron
    modelise d'un seul tenant produit des triangles qui enjambent la sphere de
    charniere. Ils seraient conserves ENTIERS, avec la matiere du joint dedans —
    et la mesure crierait sur une interpenetration normale. On coupe donc
    l'arete la plus longue, recursivement.
    """
    d = [(verts[i] - pivot).length for i in tri]
    if min(d) >= skip:
        out.append(list(tri))
        return
    if max(d) <= skip or depth >= 4:
        return
    k = max(range(3), key=lambda i: (verts[tri[i]] - verts[tri[(i + 1) % 3]]).length)
    a, b, c = tri[k], tri[(k + 1) % 3], tri[(k + 2) % 3]
    mid = len(verts)
    verts.append((verts[a] + verts[b]) * 0.5)
    _clip_sphere(verts, [a, mid, c], pivot, skip, out, depth + 1)
    _clip_sphere(verts, [mid, b, c], pivot, skip, out, depth + 1)


def _soup(obj, skips: list | None = None):
    """(sommets, triangles) d'un objet, en repere GODOT, compactes.

    `skips` : liste de (centre, rayon) dont la geometrie est ecartee — une
    charniere reelle s'interpenetre par construction, ce qui doit degager c'est
    tout le reste. Les rayons retenus sont publies au compte-rendu.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.index_update()
    raw = [_TO_GODOT @ v.co for v in bm.verts]
    tris = [[loop.vert.index for loop in face.loops] for face in bm.faces]
    bm.free()
    for center, radius in (skips or []):
        kept: list = []
        for tri in tris:
            _clip_sphere(raw, tri, center, radius, kept)
        tris = kept
    keep, remap, out = [], {}, []
    for tri in tris:
        row = []
        for i in tri:
            if i not in remap:
                remap[i] = len(keep)
                keep.append(raw[i])
            row.append(remap[i])
        out.append(row)
    return keep, out


class Solid:
    """Soupe de triangles figee, prete a repondre « a quelle distance ? »."""

    def __init__(self, verts: list, tris: list):
        self.verts = verts
        self.tris = tris
        self.tree = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)

    def distance_to(self, verts: list, tris: list) -> float:
        """Distance minimale a une autre soupe ; 0.0 si elles se mordent.

        Deux sens de requete : un sommet mobile pres d'une face fixe, ET un
        sommet fixe pres d'une face mobile. Un seul sens laisserait passer une
        lame mince qui traverse une grande face sans qu'aucun de ses sommets
        n'en approche.
        """
        if not tris or not self.tris:
            return 9.9
        other = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)
        if other.overlap(self.tree):
            return 0.0
        best = 2.0
        for v in verts:
            hit = self.tree.find_nearest(v, best)
            if hit[3] is not None:
                best = min(best, hit[3])
        for v in self.verts:
            hit = other.find_nearest(v, best)
            if hit[3] is not None:
                best = min(best, hit[3])
        return best


class Rig:
    """Chaine articulee posable : pivots, parentage, maillages en repere Godot.

    Reproduit exactement ce que Godot fera du `.glb` : origine de la piece sur
    son pivot, position de l'enfant RELATIVE au parent, rotation en euler YXZ
    (ou basis explicite pour les charnieres tangentielles).
    """

    def __init__(self, parts: list, skips: dict | None = None):
        skips = skips or {}
        self.names = [p.obj.name for p in parts]
        self.pivot = {p.obj.name: _TO_GODOT @ Vector(p.pivot) for p in parts}
        self.parent = {p.obj.name: p.parent for p in parts}
        self.verts, self.tris = {}, {}
        for part in parts:
            name = part.obj.name
            verts, tris = _soup(part.obj, skips.get(name))
            self.verts[name] = [v - self.pivot[name] for v in verts]
            self.tris[name] = tris

    def pose(self, angles: dict) -> dict:
        """Sommets monde de chaque piece, pour un jeu de rotations locales."""
        world: dict = {}
        out: dict = {}
        for name in self.names:
            parent = self.parent[name]
            base_pivot = (Vector((0.0, 0.0, 0.0)) if parent not in self.pivot
                          else self.pivot[parent])
            offset = self.pivot[name] - base_pivot
            local = Matrix.Translation(offset)
            base = (Matrix.Identity(4) if parent not in world else world[parent])
            spin = angles.get(name, (0.0, 0.0, 0.0))
            if not isinstance(spin, Matrix):
                spin = _godot_euler(*spin)
            world[name] = base @ local @ spin
            out[name] = [world[name] @ v for v in self.verts[name]]
        return out

    def clearance(self, poses: list, obstacle: Solid, only=None) -> tuple[float, str]:
        """Marge minimale sur toutes les poses, et la pose ou elle est atteinte."""
        best, where = 9.9, "aucune pose"
        for label, angles in poses:
            posed = self.pose(angles)
            for name, verts in posed.items():
                if only is not None and name not in only:
                    continue
                d = obstacle.distance_to(verts, self.tris[name])
                if d < best:
                    best, where = d, f"{label} / {name}"
        return best, where

    def self_clearance(self, poses: list, pairs: list) -> tuple[float, str]:
        """Marge minimale entre deux pieces de la meme chaine."""
        best, where = 9.9, "aucune pose"
        for label, angles in poses:
            posed = self.pose(angles)
            for a, b in pairs:
                solid = Solid(posed[a], self.tris[a])
                d = solid.distance_to(posed[b], self.tris[b])
                if d < best:
                    best, where = d, f"{label} / {a}-{b}"
        return best, where


def _rad(deg: float) -> float:
    return math.radians(deg)


def _orbit_angles(step: int) -> float:
    return 2.0 * math.pi * step / ORBIT_STEPS


def _shell_poses(with_crescent: bool, with_plates: bool, plate_axes: dict) -> list:
    """Poses de la coquille : orbite x bascule x chute, comme le combat les ecrira."""
    poses = []
    tilts = (0.0, 0.35, 0.7, 1.0) if with_crescent else (0.0,)
    drops = (0.0, 0.35, 0.7, 1.0) if with_plates else (0.0,)
    for s in range(ORBIT_STEPS):
        orbit = _orbit_angles(s)
        for tilt in tilts:
            for drop in drops:
                angles = {"Shell_Ring": (0.0, orbit, 0.0)}
                if with_crescent:
                    angles["Shell_Crescent"] = (_rad(CRESCENT_DEG) * tilt, 0.0, 0.0)
                if with_plates:
                    for name, axis in plate_axes.items():
                        angles[name] = Matrix.Rotation(
                            _rad(PLATE_DEG) * drop, 4, axis
                        )
                poses.append((
                    f"orbite {math.degrees(orbit):3.0f} deg / bascule "
                    f"{CRESCENT_DEG * tilt:2.0f} deg / chute "
                    f"{PLATE_DEG * drop:+3.0f} deg", angles))
    return poses


def iris_travel(t: float, sink: float = IRIS_SINK,
                slide: float = IRIS_SLIDE) -> tuple[float, float]:
    """Course d'un volet a l'avancement `t` (0 = ferme, 1 = ouvert a fond).

    ⚠️ LES DEUX TEMPS NE SE RECOUVRENT PAS, et ce n'est pas un choix de style :
    c'est une mesure (cf. `IRIS_KNEE`). Le volet RECULE d'abord (t de 0 a
    IRIS_KNEE), il ne COULISSE qu'ensuite. Mener les deux de front ferait
    decrire a la piece une diagonale — donc, vu de dessus, un ecartement
    immediat, exactement la lecture « petale » qu'il s'agit d'eviter — et la
    ferait entrer dans le croissant des les premiers centimetres.

    Rend `(enfoncement, coulissement)` en metres, dans le repere d'auteur.
    """
    knee = IRIS_KNEE
    if t <= knee:
        return sink * (t / knee), 0.0
    return sink, slide * ((t - knee) / (1.0 - knee))


def _iris_matrix(index: int, t: float) -> Matrix:
    """Translation d'un volet, en repere GODOT, telle que le code l'ecrira.

    -Z d'auteur (l'enfoncement) devient -Y en jeu : le volet s'ecarte de la
    camera, il ne se souleve pas vers elle. Le coulissement est radial sortant
    dans le plan, direction donnee par la bissectrice — donc par la position du
    noeud lui-meme.
    """
    sink, slide = iris_travel(t)
    a = math.radians(IRIS_AZ[index])
    author = Vector((slide * math.cos(a), slide * math.sin(a), -sink))
    return Matrix.Translation(_TO_GODOT @ author)


def _maw_poses(with_iris: bool, with_nodes: bool,
               travel: float = 1.0, spins: int = ORBIT_STEPS) -> list:
    """Poses du noyau : rotation du noyau x course d'iris x repli des noeuds."""
    poses = []
    steps = ([i / IRIS_STEPS for i in range(IRIS_STEPS + 1)]
             if with_iris else (0.0,))
    for s in range(spins):
        spin = _orbit_angles(s) if spins > 1 else 0.0
        for t in steps:
            for node in ((0.0, 0.5, 1.0) if with_nodes else (0.0,)):
                angles = {"Core": (0.0, spin, 0.0)}
                if with_iris:
                    for k in range(IRIS_N):
                        angles[f"Shutter_{k + 1:02d}"] = _iris_matrix(
                            k, t * travel)
                    # Les anneaux tournent a leurs vitesses propres : sans ca,
                    # leur ouverture resterait sous le meme volet a chaque pose
                    # et le bord d'attaque plongerait dans un trou permanent.
                    for i in range(len(RINGS)):
                        angles[f"Ring_{i + 1:02d}"] = (
                            0.0, spin * (1.0 + 0.37 * i), 0.0)
                if with_nodes:
                    for i in range(3):
                        angles[f"Node_{i + 1:02d}"] = (_rad(NODE_DEG) * node, 0.0, 0.0)
                sink, slide = iris_travel(t * travel)
                poses.append((
                    f"noyau {math.degrees(spin):3.0f} deg / iris "
                    f"recul {sink * 1000:4.0f} mm + glissement {slide * 1000:4.0f} mm"
                    f" / noeuds {NODE_DEG * node:+3.0f} deg",
                    angles))
    return poses


def _spike_poses(spec: dict, flex_deg: float = FLEX_DEG,
                 axis: str = "y") -> list:
    """Pointage +/-40 deg (rotation.y) x flexion des deux maillons.

    ⚠️ La flexion du CONTRAT est celle du plan de jeu (`rotation.y`, le meme axe
    que le pointage) : le boss est un objet PLAT vu de dessus, et c'est dans ce
    plan que le fouettement d'une epine se lit. La flexion verticale
    (`rotation.x`) est mesuree a part, et ne va pas jusqu'a 25 deg — il n'y a
    pas un metre de vide sous une epine posee 30 cm au-dessus du pont.
    """
    name = spec["name"]
    poses = []
    for aim in (-1.0, -0.5, 0.0, 0.5, 1.0):
        for flex in (-1.0, -0.5, 0.0, 0.5, 1.0):
            bend = (_rad(flex_deg) * flex if axis == "x" else 0.0,
                    _rad(flex_deg) * flex if axis == "y" else 0.0, 0.0)
            poses.append((
                f"pointage {SPIKE_DEG * aim:+3.0f} deg / flexion "
                f"{flex_deg * flex:+3.0f} deg ({axis})",
                {name: (0.0, _rad(SPIKE_DEG) * aim, 0.0),
                 f"{name}_Mid": bend,
                 f"{name}_Tip": bend},
            ))
    return poses


def _ring_poses() -> list:
    """Les cinq anneaux tournent a des vitesses DISTINCTES : on echantillonne
    des dephasages premiers entre eux plutot qu'une rotation d'ensemble."""
    poses = []
    for s in range(ORBIT_STEPS):
        base = _orbit_angles(s)
        angles = {"Core": (0.0, base, 0.0)}
        for i in range(5):
            angles[f"Ring_{i + 1:02d}"] = (0.0, base * (1.0 + 0.37 * i), 0.0)
        poses.append((f"puits {math.degrees(base):3.0f} deg", angles))
    return poses


def _iris_bore(rig: Rig, t: float) -> tuple[float, str]:
    """RAYON du passage libre au centre, a l'avancement d'iris `t`.

    C'est la mesure du critere « passage central libre >= 3,0 m de diametre » :
    la distance HORIZONTALE minimale entre l'axe du puits et la matiere des
    volets (dents et noeuds compris), toutes rotations de noyau confondues. Elle
    est prise dans le plan de jeu — l'axe du puits est la verticale du repere
    Godot, donc `hypot(x, z)`.

    ⚠️ Le noyau est EXCLU de la mesure, et il faut le dire : la boule de 3,12 m
    occupe le centre au repos et c'est le combat qui l'escamote (elle est deja
    mise a l'echelle par `leviathan_combat.gd`). Ce qu'on mesure ici est le
    passage que L'IRIS laisse — le seul dont ce brief reponde.
    """
    worst, where = 9.9, ""
    for s in range(ORBIT_STEPS):
        spin = _orbit_angles(s)
        angles = {"Core": (0.0, spin, 0.0)}
        for k in range(IRIS_N):
            angles[f"Shutter_{k + 1:02d}"] = _iris_matrix(k, t)
        for i in range(3):
            angles[f"Node_{i + 1:02d}"] = (_rad(NODE_DEG), 0.0, 0.0)
        posed = rig.pose(angles)
        for name, verts in posed.items():
            if name == "Core" or name.startswith("Ring_"):
                continue
            for v in verts:
                d = math.hypot(v.x, v.z)
                if d < worst:
                    worst, where = d, f"{name} a noyau {math.degrees(spin):3.0f} deg"
    return worst, where


def _iris_first_touch(rig: Rig, body_solid: Solid) -> tuple[float, float]:
    """Enfoncement auquel un volet entre dans la coque, et la marge juste avant.

    Ce n'est pas un defaut : a fond de course les volets sont AVALES par
    l'epaisseur du pont — c'est leur logement, et c'est ce que demande le brief
    (« reculent dans l'epaisseur de la coque »). Ce qu'on veut savoir, c'est
    jusqu'ou la course reste VISIBLE et franche, hors matiere. On balaie donc
    l'enfoncement par pas de 2 cm et on rend la derniere valeur qui degage.
    """
    last, margin = 0.0, 9.9
    step = 0.02
    depth = 0.0
    while depth <= IRIS_SINK + 1e-9:
        t = min(depth / IRIS_SINK, 1.0) * IRIS_KNEE
        angles = {"Core": (0.0, 0.0, 0.0)}
        for k in range(IRIS_N):
            angles[f"Shutter_{k + 1:02d}"] = _iris_matrix(k, t)
        posed = rig.pose(angles)
        worst = 9.9
        for k in range(IRIS_N):
            name = f"Shutter_{k + 1:02d}"
            worst = min(worst, body_solid.distance_to(posed[name], rig.tris[name]))
        if worst <= 0.0:
            break
        last, margin = depth, worst
        depth += step
    return last, margin


def _clearance_table(body, parts: dict) -> list:
    """Le tableau exige par le brief : piece / debattement / marge minimale."""
    rows = []
    body_solid = Solid(*_soup(body))

    def body_around(skips):
        return Solid(*_soup(body, skips))

    # --- 1/2/3 : la coquille -----------------------------------------------
    shell_parts = [parts["Shell_Ring"], parts["Shell_Crescent"]] + \
                  [parts[f"Plate_{i + 1:02d}"] for i in range(4)]
    plate_axes = {}
    for i in range(4):
        name = f"Plate_{i + 1:02d}"
        plate_axes[name] = _tangent_axis(_TO_GODOT @ plate_pivot(i))
    skips = {f"Plate_{i + 1:02d}": [(Vector((0.0, 0.0, 0.0)), SKIP_PLATE)]
             for i in range(4)}
    skips["Shell_Crescent"] = [(Vector((0.0, 0.0, 0.0)), SKIP_CRESCENT)]
    shell = Rig(shell_parts, skips)

    margin, where = shell.clearance(
        _shell_poses(False, False, plate_axes), body_solid, only=("Shell_Ring",))
    rows.append(("Shell_Ring / coque", "orbite 360 deg", margin, where))

    crescent_skip = [(_TO_GODOT @ Vector(CR_PIVOT), SKIP_CRESCENT)]
    margin, where = shell.clearance(
        _shell_poses(True, False, plate_axes), body_around(crescent_skip),
        only=("Shell_Crescent",))
    rows.append(("Shell_Crescent / coque",
                 f"orbite 360 deg x bascule 0 -> {CRESCENT_DEG:.0f} deg",
                 margin, where))

    plate_skip = [(_TO_GODOT @ plate_pivot(i), SKIP_PLATE) for i in range(4)]
    margin, where = shell.clearance(
        _shell_poses(True, True, plate_axes), body_around(plate_skip),
        only=tuple(f"Plate_{i + 1:02d}" for i in range(4)))
    m2, w2 = shell.self_clearance(
        _shell_poses(True, True, plate_axes),
        [(f"Plate_{i + 1:02d}", f"Plate_{j + 1:02d}")
         for i, j in ((0, 1), (1, 2), (2, 3), (3, 0))]
        + [(f"Plate_{i + 1:02d}", "Shell_Ring") for i in range(4)])
    if m2 < margin:
        margin, where = m2, w2 + " (entre pieces)"
    rows.append(("Plate_01..04 / coque, coquille et entre elles",
                 f"chute 0 -> {PLATE_DEG:.0f} deg x orbite x bascule",
                 margin, where))

    # --- 4/5/6 : le noyau, l'iris, les noeuds -------------------------------
    #
    # ⚠️ L'iris est mesure SANS aucun rayon d'exclusion (cf. `SKIP_NODE`) : ses
    # volets ne tournent pas, rien ne justifierait d'ecarter de la matiere. Les
    # `Ring_01..05` entrent dans le meme gabarit parce que le bord d'attaque
    # d'un volet descend a leur altitude en s'enfoncant — c'est `Ring_01` qui
    # borne `IRIS_SINK`, et ce sera vrai a chaque fois qu'on y touchera.
    maw_parts = [parts["Core"]] \
        + [parts[f"Shutter_{k + 1:02d}"] for k in range(IRIS_N)] \
        + [parts[f"Node_{i + 1:02d}"] for i in range(3)] \
        + [parts[f"Ring_{i + 1:02d}"] for i in range(len(RINGS))]
    maw_skips = {}
    for i in range(3):
        maw_skips[f"Node_{i + 1:02d}"] = [
            (_TO_GODOT @ node_base(i), SKIP_NODE)]
    maw = Rig(maw_parts, maw_skips)

    margin, where = maw.clearance(_maw_poses(False, False), body_solid,
                                  only=("Core",))
    rows.append(("Core / coque", "rotation 360 deg", margin, where))

    # 5a. La part VISIBLE de la course : le volet se decolle, entierement hors
    #     de la coque. C'est elle qui doit degager, et le build bloque dessus.
    free_travel = IRIS_FREE_SINK / IRIS_SINK * IRIS_KNEE
    iris_names = tuple(f"Shutter_{k + 1:02d}" for k in range(IRIS_N))
    margin, where = maw.clearance(
        _maw_poses(True, False, travel=free_travel), body_solid, only=iris_names)
    rows.append((f"Shutter_01..06 / coque (recul libre {IRIS_FREE_SINK * 1000:.0f} mm)",
                 "course visible, hors logement", margin, where))

    # 5b. La course COMPLETE, mesuree contre le noyau, les anneaux du puits et
    #     les volets voisins — c'est-a-dire contre tout ce qui n'est pas le
    #     logement. Le volet finit dans l'epaisseur du pont, par construction ;
    #     il ne doit toucher NI la boule, NI un anneau, NI son voisin.
    full = _maw_poses(True, False)
    margin, where = 9.9, ""
    pairs = [(f"Shutter_{k + 1:02d}", "Core") for k in range(IRIS_N)]
    pairs += [(f"Shutter_{k + 1:02d}", f"Shutter_{(k + 1) % IRIS_N + 1:02d}")
              for k in range(IRIS_N)]
    pairs += [(f"Shutter_{k + 1:02d}", f"Ring_{i + 1:02d}")
              for k in range(IRIS_N) for i in range(2)]
    margin, where = maw.self_clearance(full, pairs)
    rows.append(("Shutter_01..06 / noyau, anneaux, volets voisins",
                 f"recul {IRIS_SINK * 1000:.0f} mm puis glissement "
                 f"{IRIS_SLIDE * 1000:.0f} mm", margin, where))

    # 5c. ⚠️ L'IRIS CONTRE LA COQUILLE — la mesure que le harnais n'avait jamais
    #     faite pour la gueule, et celle qui a fixe toute la course. `Shell_Ring`
    #     (r >= 2,18, z 0,28-0,68) et `Shell_Crescent` (r >= 2,24, z 0,75-1,16)
    #     bouchent l'exterieur sur toute la hauteur du volet : sans ce controle,
    #     n'importe quel glissement amorce trop tot passe la porte de qualite et
    #     se decouvre en jeu, la coquille traversant l'iris a chaque orbite.
    shell_solids = []
    # ⚠️ Pas de 30 deg, pas 60 : l'iris est 6 fois symetrique, un pas de 60 deg
    # le ramenerait sur lui-meme et ne mesurerait qu'UNE alignement sur deux.
    for st in range(ORBIT_STEPS):
        sp = shell.pose({"Shell_Ring": (0.0, _orbit_angles(st), 0.0)})
        for sn in ("Shell_Ring", "Shell_Crescent"):
            shell_solids.append((f"{sn} a {math.degrees(_orbit_angles(st)):3.0f} deg",
                                 Solid(sp[sn], shell.tris[sn])))
    margin, where = 9.9, "aucune pose"
    for label, angles in _maw_poses(True, True, spins=1):
        posed = maw.pose(angles)
        for name in iris_names + tuple(f"Node_{i + 1:02d}" for i in range(3)):
            for slabel, solid in shell_solids:
                d = solid.distance_to(posed[name], maw.tris[name])
                if d < margin:
                    margin, where = d, f"{label} / {name} vs {slabel}"
    rows.append(("Shutter_01..06 + Node_01..03 / coquille",
                 "course complete x orbite de la coquille", margin, where))

    node_skip = [(_TO_GODOT @ node_base(i), SKIP_NODE) for i in range(3)]
    margin, where = maw.clearance(
        _maw_poses(True, True, travel=free_travel), body_around(node_skip),
        only=tuple(f"Node_{i + 1:02d}" for i in range(3)))
    m2, w2 = maw.self_clearance(
        _maw_poses(True, True),
        [(f"Node_{i + 1:02d}", shutter_of_node(i)) for i in range(3)]
        + [(f"Node_{i + 1:02d}", "Core") for i in range(3)]
        + [("Node_01", "Node_02"), ("Node_02", "Node_03")])
    if m2 < margin:
        margin, where = m2, w2 + " (contre volet/noyau/voisin)"
    rows.append(("Node_01..03 / volet, noyau, coque",
                 f"retraction 0 -> {NODE_DEG:.0f} deg x iris x noyau",
                 margin, where))

    # --- 7 : les anneaux du puits -------------------------------------------
    ring_parts = [parts["Core"]] + [parts[f"Ring_{i + 1:02d}"] for i in range(5)]
    rings = Rig(ring_parts)
    margin, where = rings.clearance(
        _ring_poses(), body_solid,
        only=tuple(f"Ring_{i + 1:02d}" for i in range(5)))
    m2, w2 = rings.self_clearance(
        _ring_poses(),
        [(f"Ring_{i + 1:02d}", f"Ring_{i + 2:02d}") for i in range(4)])
    if m2 < margin:
        margin, where = m2, w2 + " (entre anneaux)"
    rows.append(("Ring_01..05 / paroi du puits et entre eux",
                 "360 deg continu, vitesses distinctes", margin, where))

    # --- 8/9 : les epines ----------------------------------------------------
    worst_root, where_root = 9.9, ""
    worst_flex, where_flex = 9.9, ""
    vertical_limit, vertical_where = FLEX_DEG, "toute la course"
    for spec in SPIKES:
        name = spec["name"]
        chain = [parts[name], parts[f"{name}_Mid"], parts[f"{name}_Tip"]]
        # Exclusion de charniere : le rayon de l'epine a l'articulation, majore
        # de 20 %. C'est la rotule (invariante par rotation) plus son jeu.
        ts = (0.0,) + spec["splits"]
        skips = {}
        for seg, part in enumerate(chain):
            radius = spike_radius(spec, ts[seg]) * 1.20
            skips[part.obj.name] = [(_TO_GODOT @ Vector(part.pivot), radius)]
            if seg < 2:   # la piece porte aussi le joint de son enfant
                child = chain[seg + 1]
                skips[part.obj.name].append(
                    (_TO_GODOT @ Vector(child.pivot),
                     spike_radius(spec, ts[seg + 1]) * 1.20))
        rig = Rig(chain, skips)
        obstacle = Solid(*_soup(body, [
            (_TO_GODOT @ Vector(parts[name].pivot),
             spike_radius(spec, 0.0) * 1.20)]))
        poses = _spike_poses(spec)
        m, w = rig.clearance(poses, obstacle, only=(name,))
        if m < worst_root:
            worst_root, where_root = m, f"{name} : {w}"
        m, w = rig.clearance(poses, obstacle,
                             only=(f"{name}_Mid", f"{name}_Tip"))
        m2, w2 = rig.self_clearance(
            poses, [(name, f"{name}_Mid"), (f"{name}_Mid", f"{name}_Tip"),
                    (name, f"{name}_Tip")])
        if m2 < m:
            m, w = m2, w2 + " (dans la chaine)"
        if m < worst_flex:
            worst_flex, where_flex = m, f"{name} : {w}"
        # Flexion VERTICALE : on cherche le plafond reel, par pas de 5 deg.
        for deg in range(5, int(FLEX_DEG) + 1, 5):
            mv, wv = rig.clearance(_spike_poses(spec, float(deg), "x"), obstacle)
            if mv <= 0.010 and deg < vertical_limit:
                vertical_limit, vertical_where = deg - 5, f"{name} : {wv}"
                break
    rows.append(("Spike_01..04 / coque", f"pointage +/-{SPIKE_DEG:.0f} deg",
                 worst_root, where_root))
    rows.append(("Spike_0X_Mid et _Tip / coque et chaine",
                 f"flexion +/-{FLEX_DEG:.0f} deg chacun (plan de jeu)",
                 worst_flex, where_flex))
    print(f"  [i  ] flexion VERTICALE (rotation.x) encaissee sans morsure : "
          f"+/-{vertical_limit:.0f} deg  ({vertical_where})")

    # --- recette de la plongee : le passage libre au centre -----------------
    #
    # Le critere du brief est un DIAMETRE, pas une marge : >= 3,0 m au centre a
    # l'ouverture maximale, pour un chasseur large de 1,29 m. On mesure donc le
    # rayon du passage que laisse l'iris, ouvert puis ferme, et on publie les
    # deux — la difference EST la course utile.
    bore_open, where_open = _iris_bore(maw, 1.0)
    bore_shut, _ = _iris_bore(maw, 0.0)
    rows.append(("Iris ouvert / passage central libre",
                 f"diametre {bore_open * 2.0:.3f} m (ferme : "
                 f"{bore_shut * 2.0:.3f} m) — seuil {IRIS_BORE_MIN * 2.0:.3f}",
                 bore_open - IRIS_BORE_MIN, where_open))

    # ⚠️ CE QUE L'IRIS NE COMMANDE PAS. Le passage que le JOUEUR voit n'est pas
    # celui que l'iris laisse : la coque a sa propre ouverture, bornee par la
    # denture fixe de la levre du puits (`_build_rim_teeth`, qui mord jusqu'a
    # r = 1,75). On la publie a chaque build, sans quoi on croira que le seuil
    # d'iris decrit le trou visible — il ne le decrit pas.
    hull_bore = 9.9
    for vert in Solid(*_soup(body)).verts:
        if vert.y >= -0.10:
            hull_bore = min(hull_bore, math.hypot(vert.x, vert.z))
    print(f"  [i  ] gueule : ouverture de la COQUE {hull_bore * 2.0:.3f} m "
          f"(denture fixe de la levre du puits) — l'iris, lui, degage "
          f"{bore_open * 2.0:.3f} m")

    depth, dmargin = _iris_first_touch(maw, body_solid)
    print(f"  [i  ] iris : recul libre hors coque {depth * 1000:4.0f} mm "
          f"(marge {dmargin * 1000:.1f} mm au dernier pas) ; au-dela le volet "
          f"entre dans son logement — recul total {IRIS_SINK * 1000:.0f} mm")
    print(f"  [i  ] iris : passage libre ferme {bore_shut * 2.0:.3f} m, "
          f"ouvert {bore_open * 2.0:.3f} m "
          f"(+{(bore_open - bore_shut) * 2.0 * 1000:.0f} mm)")
    return rows


# ==========================================================================
# Assemblage
# ==========================================================================


def _triangulate_ngons(obj) -> None:
    """Coupe les n-gons — sans quoi l'export n'a AUCUNE tangente.

    L'exporteur glTF de Blender refuse le calcul mikktspace des que le maillage
    porte une face de plus de quatre sommets : « Tangent space can only be
    computed for tris/quads, aborting ». Il le dit dans le flot de sortie et
    exporte quand meme — silencieusement, sans l'attribut TANGENT. Une coque
    livree comme ca a des UV, donc l'air texturable, et un shader de relief y
    reste plat. Les `cap_ring` de ce script (culots, tranches de secteur) en
    produisent des dizaines : la passe est obligatoire, pas cosmetique.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(obj.data)
    bm.free()


def _finish(obj, bevel: float = 0.006, angle: float = 34.0) -> None:
    """Finition commune : soudure, chanfrein, lissage, decoupe, **depliage UV**.

    Le chanfrein a UN segment reste nettement sous la profondeur des panneaux
    (24-30 mm) : la marche reste franche. Le depliage vient en dernier parce que
    le chanfrein et la triangulation creent des faces — les deplier avant les
    laisserait sans UV coherente.
    """
    ak.cleanup(obj)
    if bevel > 0.0:
        ak.bevel_sharp_edges(obj, width=bevel, segments=1, angle_deg=angle)
    ak.shade_smooth_by_angle(obj, angle_deg=angle)
    _triangulate_ngons(obj)
    # UV par projection en boite (ADR-0011 SS2) : le support des feuilles de
    # detail repetables, appliquees cote Godot. Aucune texture n'est embarquee
    # dans le `.glb` — seulement les coordonnees.
    ak.box_project_uv(obj, TEXELS_PER_METER)


def _bounds(objs: list) -> tuple[Vector, Vector]:
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    for obj in objs:
        for vert in obj.data.vertices:
            for a in range(3):
                lo[a] = min(lo[a], vert.co[a])
                hi[a] = max(hi[a], vert.co[a])
    return lo, hi


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)

    body = build_body()
    parts = [
        build_shell_ring(),
        build_crescent(),
        *[build_plate(i) for i in range(len(PLATES))],
        build_core(),
        *[build_shutter(k) for k in range(IRIS_N)],
        *[build_node(i) for i in range(3)],
        *[build_ring(i) for i in range(len(RINGS))],
        build_heart(),
    ]
    for spec in SPIKES:
        parts += [build_spike_segment(spec, seg) for seg in range(3)]
    by_name = {p.obj.name: p for p in parts}

    _finish(body)
    for part in parts:
        # Le noyau reste lisse : un chanfrein sur ses ~200 ecailles de croute
        # couterait plus de 4 000 triangles pour un gain nul sur une sphere
        # emissive.
        _finish(part.obj, bevel=0.0 if part.obj.name == "Core" else 0.005,
                angle=30.0 if part.obj.name == "Core" else 34.0)

    # --- controle en repere d'auteur, avant tout export --------------------
    objs = [body] + [p.obj for p in parts]
    lo, hi = _bounds(objs)
    print("--- mesures en repere d'auteur (avant correction d'axe) ---")
    for obj in objs:
        o_lo, o_hi = _bounds([obj])
        print(f"  {obj.name:<16} x[{o_lo.x:+.3f} {o_hi.x:+.3f}] "
              f"y[{o_lo.y:+.3f} {o_hi.y:+.3f}] z[{o_lo.z:+.3f} {o_hi.z:+.3f}] "
              f"{len(obj.data.polygons)} faces")
    print(f"  TOTAL            x[{lo.x:+.3f} {hi.x:+.3f}] y[{lo.y:+.3f} {hi.y:+.3f}] "
          f"z[{lo.z:+.3f} {hi.z:+.3f}]  ->  {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} "
          f"x {hi.z - lo.z:.3f} m")

    # --- degagement a fond de course (BRIEF-0040) --------------------------
    print("--- degagement des pieces mobiles (maillage livre, poses du combat) ---")
    failures = []
    for name, travel, margin, where in _clearance_table(body, by_name):
        verdict = "OK " if margin > 0.0 else "MORD"
        print(f"  [{verdict}] {name:<44} {travel:<48} {margin * 1000:8.1f} mm  ({where})")
        if margin <= 0.0:
            failures.append(f"{name} : {where}")
    if failures:
        raise ak.ContractError(
            "pieces mobiles qui mordent la coque ou leur voisine :\n"
            + "\n".join(f"  - {f}" for f in failures)
        )

    ak.export_hull(body, build_attach_points(), OUTPUT, CONTRACT, parts=parts)


if __name__ == "__main__":
    main()
