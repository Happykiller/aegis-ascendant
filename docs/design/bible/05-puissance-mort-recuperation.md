---
titre: Puissance, mort, récupération — la spirale et ses garde-fous
type: reference
statut: actif
maj: 2026-08-25
---

# Puissance, mort, récupération

## Ce que le genre dit

### L'arme monte, et c'est la moitié du plaisir

Le tir le plus courant est une **ligne de projectiles** qui devient un **tir en éventail** en montant
en puissance — « un pisto-pois peu impressionnant au départ, nettement plus satisfaisant une fois
étalé ». Cinq niveaux est une échelle répandue.

Autre grande famille : le **laser**, faisceau linéaire qui s'élargit — petite surface de couverture,
visée exigeante, compensée par la puissance brute.

Et les **options / satellites** (l'école *Gradius*) : des modules qui suivent le vaisseau et dont la
**position** change ce qu'ils apportent.

### La mort ne doit pas enterrer le joueur

C'est le problème structurel du genre : mourir enlève la puissance, donc rend la suite plus dure,
donc fait remourir. Trois garde-fous documentés :

- **Perte partielle** — on ne redescend que d'un ou deux niveaux, pas à zéro.
- **Nettoyage à la mort** — les balles ennemies sont annulées, puis quelques secondes
  d'invulnérabilité **généreuse** : c'est ce qui « prévient les morts en chaîne ».
- **Bomb buffer** — bombarder dans les quelques images **après** le coup fatal annule quand même la
  mort. Pure anti-frustration.

## Chez nous — état au 2026-08-25

| Point | État réel |
|---|---|
| Montée en puissance | ✅ Cinq niveaux (`LV.1` à l'écran), ramassage `Pickup.Kind.POWER` |
| Familles d'armes | ⚠️ **Une seule.** Pas de laser, pas d'options. Le chasseur a ses canons de nez, et c'est tout |
| Invulnérabilité après mort | ✅ **2 s**, après 1,2 s de renaissance — soit 3,2 s pendant lesquelles un second coup ne porte pas. La valeur est connue au point d'avoir servi à régler un drapeau de démonstration |
| Nettoyage des balles à la mort | ✅ **Ajouté le 2026-08-25** après cette vérification : il **manquait**. `BulletManager.clear_team(ENEMY)` est appelé sur la mort du joueur — les tirs du joueur survivent, ils n'ont jamais tué personne |
| Perte de puissance à la mort | ✅ **Aucune, et c'est volontaire** : `_destroy()` et `_respawn()` ne touchent pas à `_power_level`. Nous sommes plus généreux que le genre (spec §5.3, « forgiving ») — le vecteur de spirale qu'il redoute n'existe pas ici |
| Bomb buffer | ❌ Sans objet : **il n'y a pas de bombe** |
| Écran d'échec | ❌ **Il n'en existe aucun.** Perdre tous les chasseurs appelle `continue_run()` et la partie repart, sans écran ni choix. C'est au P0 du backlog depuis longtemps |

## L'écart, et ce qu'on en fait

**L'invulnérabilité est bien tenue**, et pour la bonne raison — elle a été mesurée en concevant le
drapeau `--defeat-demo`, pas devinée.

**Les deux vérifications ont été faites le jour même**, et elles n'ont pas donné le même verdict :
le **nettoyage des balles manquait** — c'est le meilleur retour sur investissement qu'ait produit
cette bible, une vingtaine de lignes contre la mort en chaîne — tandis que la **puissance
préservée** est un choix assumé, plus généreux que le genre. ⚠️ **La leçon dépasse ces deux
points** : un écart au genre n'est pas un défaut tant qu'on n'a pas lu le code. L'un des deux
« manques » n'en était pas un.

**L'écran d'échec est le manque le plus visible**, et il est déjà au backlog. Le genre n'a rien à en
dire de particulier — mais une partie qui repart toute seule sans rien annoncer n'est pas un choix
de conception, c'est un trou.

⚠️ **Ce que la bible ne recommande PAS** : ajouter une bombe, un laser ou des options parce que le
genre les emploie. `ADR-0010` a supprimé une transformation de vaisseau pour cause de flow cassé ;
un projet qui ajoute des systèmes parce qu'ils existent ailleurs refait cette erreur. Ces lignes
sont ici pour dire **ce qu'on n'a pas**, pas pour demander de le combler.
