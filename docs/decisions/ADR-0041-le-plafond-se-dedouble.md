# ADR-0041 — Le plafond du décor et celui du gameplay ne sont pas le même

- **Statut** : accepté
- **Date** : 2026-08-29
- **Prime sur** : le lot B du plan d'exécution du niveau 2, qui écrivait « `CEILING_Y = -3.0` :
  rien de la coque ne monte dans le plan de jeu », et sur le harnais de forge qui le tenait
- **Ne touche pas** : le plafond du **décor inerte**, qui reste à −3,00 et n'a jamais bougé

## Le constat

La forge, en livrant le kit de tourelle (`BRIEF-0093`), a mesuré et refusé de décider seule :

> « LA HAUTEUR DU BRIEF NE TIENT PAS SOUS LE PLAFOND À 10 DES 17 EMPLACEMENTS : 1,70 m demandés
> pour 1,28 m offerts. »

Elle avait raison sur les deux points — le chiffre, et le fait que ce n'était pas à elle de
trancher.

## Les trois issues, et pourquoi deux étaient mauvaises

| Issue | Ce qu'elle coûte |
|---|---|
| Écarter les dix marqueurs concernés | Ils portent de l'équilibrage **mesuré** — fenêtres d'engagement, arbitrages du `BRIEF-0092`. Les bouger refait toutes ces mesures |
| Rabaisser la tourelle à 1,25 m | Elle redevient le **jeton** que `BRIEF-0093` venait de supprimer. On paierait une reforge pour revenir au défaut d'origine |
| **Lire la règle pour ce qu'elle dit** | Retenue |

## La décision

Ce que le plafond protège tient en une phrase, et elle était déjà écrite : *« masquerait le
combat SANS JAMAIS POUVOIR ÊTRE TOUCHÉ »*. **Une tourelle se tire dessus.** Elle n'est pas le
décor que cette règle vise.

- `CEILING_Y = -3.00` — le **décor inerte**. Inchangé.
- `GAMEPLAY_CEILING_Y = -2.40` — les **pièces qu'on peut détruire**.

À −2,40, la tourelle reste **2,40 unités sous le plan de vol** : elle ne peut ni masquer le
chasseur ni le heurter. Le dégagement vaut une fois et demie sa propre hauteur.

## Ce qui empêche la décision de dériver

Un test, et pas un commentaire : `test_no_turret_ever_reaches_the_flight_plane` charge
`turret_kit.glb`, assemble la pièce la plus haute avec ses offsets réels, cherche le **pire**
marqueur `Turret_NN` de la coque livrée et exige les deux bornes. Une reforge qui remonterait
une pièce ou une chine échouerait ici, pas en jeu.

⚠️ Le nœud d'épine, livré ensuite (`BRIEF-0094`), **n'a pas eu besoin de ce relèvement** : la
tranchée lui mange un demi-mètre et il culmine sous −3,00. Son propre test le vérifie. C'est la
preuve que le relèvement est une exception motivée et non un assouplissement général.

## Ce que ça n'autorise pas

Un décor **inerte** ne monte toujours pas au-dessus de −3,00. La distinction n'est pas « on a de
la marge », c'est « on peut tirer dessus ». Une pièce qui gagnerait de la hauteur en perdant sa
destructibilité repasse sous −3,00.
