class_name CortegeSkin
## Habille les matériaux nommés de la coque du Long Cortège avec les cartes dérivées.
##
## ⚠️ CE N'EST PAS `HullDetail`, ET LA DIFFÉRENCE EST TOUT LE FICHIER. `HullDetail` pose UNE
## feuille de détail sur TOUTES les surfaces d'un chasseur ; ici c'est une carte par matériau,
## parce que le bordé, les greffes, la machinerie et l'artère racontent quatre choses
## différentes — c'est même le seul moyen qu'a le niveau de dire que ce vaisseau est *agrégé*
## et non construit.
##
##
## ⚠️ RIEN N'EST `preload`. Les cartes viennent de l'opérateur (`ADR-0028` : la texture est sa
## voie) et n'existent pas tant qu'il ne les a pas fournies. Un `preload` sur un fichier absent
## est une erreur de COMPILATION en GDScript : le niveau entier cesserait de se monter, et la
## porte de qualité tomberait, pour un habillage qui est censé être facultatif. Chargement au
## runtime, matériau par matériau : ce qui manque est simplement sauté, et le journal le dit.

## Le dossier des cartes dérivées, tel que l'annoncent les `integration_notes` des demandes
## `TEX-0010` à `TEX-0014`.
const MAPS_DIR := "res://assets/imported/textures/cortege/"

## Quel jeu de cartes pour quel matériau du `.glb`. La clé est le `resource_name` importé,
## c'est-à-dire le nom donné par `aegis_kit` — le contrat de nommage de la forge.
const SKINS: Dictionary = {
	&"AA_Hull": "cortege_hull",
	&"AA_Panel": "cortege_panel",
	&"AA_Greeble": "cortege_greeble",
	# ⚠️ POSÉ PAR `BRIEF-0090`, ET SA RAISON N'EST PAS LA COULEUR : c'est l'ÉCHELLE. Ambry est
	# déplié à 0,700 tuile/m contre 0,200 pour le bordé ; toute face d'Ambry restée sur un slot
	# du bordé aurait reçu sa carte 3,5 fois trop fine — un défaut latent qu'on n'aurait
	# découvert qu'une fois les images générées, et qui aurait demandé une reforge.
	&"AA_Hull_Ambry": "ambry_hull",
	# ⚠️ LES ONZE AUTRES NATURES D'AMBRY N'ONT PAS D'ENTRÉE, ET C'EST LE DÉPÔT QUI L'EXIGE.
	# `BRIEF-0115` a livré douze slots ; je les avais tous déclarés d'avance, et
	# `test_every_declared_skin_finds_its_maps_on_disk` a rougi sur les onze. Sa règle est juste :
	# une peau déclarée sans ses images est une promesse que rien ne tient — on ne le verrait
	# qu'à l'écran, sur une surface restée nue au milieu d'une coque habillée.
	# Chaque nature prend son entrée le jour où ses cartes entrent au dépôt, pas avant.
}

## Le suffixe qui dit « cette matière est dépliée à l'échelle d'Ambry ».
##
## ⚠️ C'ÉTAIT UNE ÉGALITÉ SUR UN SEUL NOM, ET ÇA N'ALLAIT PLUS TENIR. Tant qu'Ambry n'avait qu'un
## slot, `name == &"AA_Hull_Ambry"` suffisait. Le `BRIEF-0115` en a livré DOUZE, tous dépliés à
## 0,700 tuile/m — et onze seraient retombés sur l'échelle du bordé, c'est-à-dire 3,5 fois trop
## fine, à l'instant où on leur aurait donné une image. Le défaut ne se serait vu qu'APRÈS la
## génération, et il aurait fait accuser les images.
##
## La règle vient donc du NOM et non d'une liste : toute matière d'Ambry porte son suffixe, et
## une treizième héritera de l'échelle sans que personne n'ait à y penser.
const AMBRY_SUFFIX := "_Ambry"

## Les greffes. ⚠️ ELLES SONT ASSOMBRIES ICI, ET PAS REPEINTES À LA FORGE. Deux raisons : le
## violet de `AA_Panel` est la teinte de faction de l'Unisson, partagée par tous les assets du
## jeu — la changer dans la palette toucherait des coques qui vont bien ; et ce qui ne va pas
## n'est pas la teinte, c'est ce que le NIVEAU en fait à l'écran.
##
## ⚠️ CE QU'ON CORRIGE EST UNE INVERSION DE HIÉRARCHIE, PAS UNE COULEUR. Vu en capture au
## tronçon 2 : la dalle qui porte une tourelle est plus claire que la tourelle. Le socle crie
## plus fort que le canon, et la règle de production du `BRIEF-0094` dit l'inverse — la couleur
## ne sert qu'à renforcer une fonction déjà lisible en géométrie. Le coupable est le `lift` de
## 1,25 du post-traitement rétro, qui relève les noirs : un violet sombre en linéaire (0,06 /
## 0,02 / 0,13) en ressort en aplat vif, exactement comme les grandes surfaces teintées du
## howto de vérification.
##
## Multiplication et non mélange vers le gris : le rapport des canaux est conservé, donc la
## teinte et la saturation aussi. La greffe reste violette et reste plus claire que le bordé —
## elle cesse seulement de passer devant ce qu'elle porte.
const PANEL_MATERIAL := &"AA_Panel"
const PANEL_DAMP := 0.45

static func _damped(colour: Color) -> Color:
	return Color(colour.r * PANEL_DAMP, colour.g * PANEL_DAMP, colour.b * PANEL_DAMP, colour.a)

## L'émissif est à part : c'est une COULEUR, pas une hauteur. Aucune normale n'en est dérivée
## (règle 2 du contrat de texture), et la même image sert d'albédo et d'émission.
const EMISSIVE_MATERIAL := &"AA_Emissive_Engine"

## Le liseré clair du vaisseau — et LE SEUL MATÉRIAU DU NIVEAU QUE PERSONNE N'HABILLAIT.
##
## ⚠️ IL EST LA CAUSE MESURÉE D'UNE BARRE DE BLANC PUR DANS LE CADRE. Sur les huit matériaux
## du Long Cortège, sept ont un albédo quasi noir (0,018 pour `AA_Hull`, 0,007 pour
## `AA_Greeble`). `AA_Trim` porte l'ivoire de la charte — 0,723 — avec `metallic 0,85` et
## `roughness 0,28`. Or le spéculaire d'un métal EST son albédo : ce liseré réfléchit la
## lumière clé à quarante fois la réflectance de la tôle qui l'entoure, dans un lobe serré.
## Sur la lèvre d'un coaming de hangar, présentée en rasance à la clé, ça écrête.
##
## Mesuré sur une capture du tronçon 2 : **5 595 pixels de (255, 255, 255)** d'un seul tenant,
## soit 0,28 % du cadre — et 0,32 % sur la capture que l'opérateur a rapportée du tronçon 4.
const TRIM_MATERIAL := &"AA_Trim"

## ⚠️ ET LA CORRECTION N'EST PAS DANS LA LUMIÈRE, C'EST MESURÉ AUSSI. Quatre essais en jeu,
## même station, même instant, `light_specular` clé / rim / remplissage :
##
##   0,5 / 0,5 / 0,5  (l'état d'avant)  |  5 595 px écrêtés  |  écart de la tôle nue : 224,6
##   0,5 / 0,0 / 0,0                    |  4 365             |                         214,3
##   0,25 / 0,0 / 0,0                   |  3 655             |                         171,3
##   0,0 / 0,0 / 0,0                    |      0             |                          52,7
##
## Les deux lumières d'appoint ne pèsent que 22 % du défaut ; la clé le porte, et la descendre
## assez bas pour l'éteindre **efface le relief de toute la coque** — l'écart de luminance de
## la tôle nue tombe de 224 à 53, c'est-à-dire exactement le détail de surface que les cartes
## `cortege_*` sont là pour donner. Une lumière ne sait pas distinguer un liseré d'un pont.
##
## ⚠️ ET `metallic` NE DOIT PAS BAISSER, CONTRE L'INTUITION. Un métal n'a presque pas de
## diffus : à 0,85, l'ivoire ne rayonne qu'à 15 %. Mesuré spéculaire coupé, la zone crête
## quand même à 224,6 — le diffus seul frôle déjà l'écrêtage. Descendre `metallic` à 0,25
## quintuplerait ce diffus et remplacerait une barre brillante par une barre laiteuse.
##
## On garde donc le métal, on élargit son lobe et on assombrit sa couleur — qui est aussi,
## sur un métal, sa couleur SPÉCULAIRE. Le pic varie comme l'inverse de la puissance
## quatrième de la rugosité : 0,28 -> 0,60 le divise par 21, et l'amortissement par 2,2 de
## plus. Même geste et même chiffre que `PANEL_DAMP`, pour la même raison écrite plus haut :
## ce n'est pas la teinte de la charte qui est fausse, c'est ce que CE niveau en fait.
const TRIM_ROUGHNESS := 0.60
const TRIM_DAMP := PANEL_DAMP
const EMISSIVE_MAP := "cortege_emissive"

## ⚠️ Discret. Le relief d'un bordé de 500 m se lit à 23 px/m après le post-traitement rétro :
## au-delà, la coque prend l'aspect martelé qu'`ADR-0011` a déjà payé sur le Specter-9 à 1,5.
const NORMAL_SCALE := 0.45

## Agrandissement des tuiles du bordé de l'Unisson. **< 1 agrandit** : `uv1_scale` multiplie les
## coordonnées, donc 0,5 fait couvrir DEUX FOIS plus de monde à la même image.
##
## ⚠️ IL A FALLU MESURER POUR LE VOULOIR. À l'échelle livrée — 5,00 m par tuile —, une plaque de
## 2 m fait 46 px à l'écran mais un joint de 10 cm n'en fait que 2 : une fois les mipmaps
## activées (et il le fallait, sans elles la coque SCINTILLE), le filtrage moyenne ce détail
## jusqu'à le faire disparaître. Résultat mesuré : la coque perdait **33 % de luminance** — le
## prix du relief et de l'occlusion — pour un détail qu'on ne voyait plus. C'est exactement le
## marché qu'`ADR-0016` a déjà refusé une fois sur ce projet.
##
## ⚠️ ET C'EST AUTORISÉ, CONTRE TOUTE ATTENTE. La règle de la forge n'interdit pas de mettre à
## l'échelle : elle exige que `100 × densité` reste ENTIER, sans quoi `v` saute d'une demi-tuile
## à chaque jonction de tronçon (`BRIEF-0089-report.md`). Or 0,200 × 0,5 = 0,100, et
## 100 × 0,100 = 10 — entier. Les cinq jonctions restent invisibles. Toute autre valeur doit
## refaire ce calcul : 0,5 et 0,25 passent, 0,4 (densité 0,08, produit 8) passe aussi, 0,3 non.
const HULL_UV_SCALE := 0.5

## ⚠️ AMBRY GARDE LA SIENNE. Elle est un objet unique, sans jonction à assurer, et son dépliage
## serré (1,43 m par tuile) EST la révélation du niveau : c'est lui qui la fait lire construite
## à l'échelle de la main. L'agrandir la ramènerait à l'échelle du vaisseau qui l'a emportée.
const AMBRY_UV_SCALE := 1.0

## Habille la coque. Renvoie le nombre de surfaces effectivement retexturées — zéro quand
## l'opérateur n'a pas encore fourni les images, et c'est un état normal, pas une panne.
static func apply(hull: Node) -> int:
	var dressed := 0
	for mesh in _meshes(hull):
		for i in mesh.get_surface_override_material_count():
			var base := mesh.get_active_material(i) as StandardMaterial3D
			if base == null:
				continue
			var name := StringName(base.resource_name)
			var tuned: StandardMaterial3D = null
			if name == EMISSIVE_MATERIAL:
				tuned = _skin_emissive(base)
			elif SKINS.has(name):
				var scale := AMBRY_UV_SCALE if String(name).ends_with(AMBRY_SUFFIX) \
					else HULL_UV_SCALE
				tuned = _skin_surface(base, String(SKINS[name]), scale)
				if tuned != null and name == PANEL_MATERIAL:
					tuned.albedo_color = _damped(tuned.albedo_color)
			elif name == TRIM_MATERIAL:
				tuned = tamed(base)
			if tuned == null:
				continue
			mesh.set_surface_override_material(i, tuned)
			dressed += 1
	return dressed

## Le liseré, adouci — ou le matériau tel quel s'il n'en est pas un.
##
## ⚠️ UNE SEULE COPIE POUR TOUT LE NIVEAU, ET C'EST VOULU. Contrairement au conduit émissif,
## que l'on duplique par tronçon parce qu'il doit pouvoir s'éteindre seul, le liseré n'a aucun
## état : dix-sept tourelles, sept hangars, cinq nœuds et cinq tronçons partagent la même. En
## dupliquer une par maillage ferait trente-quatre matériaux pour trente-quatre fois le même
## réglage.
## ⚠️ LE CACHE EST INDEXÉ SUR LE MATÉRIAU SOURCE, PAS GLOBAL. Une seule copie pour tout le
## niveau aurait suffi en jeu — les quatre binaires importent le même `AA_Trim` — mais elle
## rendrait la fonction dépendante de l'ORDRE des appels : le premier venu figerait la valeur
## pour tous les suivants, y compris dans un test qui en passerait deux différents. Un cache
## qui ment sur son entrée est un piège, pas une optimisation.
static var _tamed_trim: Dictionary = {}

static func tamed(base: StandardMaterial3D) -> StandardMaterial3D:
	if base == null or StringName(base.resource_name) != TRIM_MATERIAL:
		return base
	var cle := base.get_instance_id()
	if not _tamed_trim.has(cle):
		var doux: StandardMaterial3D = base.duplicate()
		doux.roughness = TRIM_ROUGHNESS
		doux.albedo_color = Color(doux.albedo_color.r * TRIM_DAMP,
			doux.albedo_color.g * TRIM_DAMP, doux.albedo_color.b * TRIM_DAMP,
			doux.albedo_color.a)
		_tamed_trim[cle] = doux
	return _tamed_trim[cle]

## Une surface de relief : hauteur dérivée en normale, rugosité et AO, plus la carte de
## multiplication en albédo.
static func _skin_surface(base: StandardMaterial3D, stem: String,
		uv_scale: float) -> StandardMaterial3D:
	var nrm := _map(stem, "nrm")
	var mul := _map(stem, "mul")
	# ⚠️ TOUT OU RIEN, PAR MATÉRIAU. Poser la multiplication sans la normale donnerait des
	# rainures PEINTES que la lumière ne voit pas — la coque resterait un aplat, et l'on
	# conclurait que la texture ne sert à rien. C'est mot pour mot la leçon d'`ADR-0013`,
	# écrite en tête de `hull_detail.gd`.
	if nrm == null or mul == null:
		return null
	# On DUPLIQUE : le matériau importé appartient au `.glb`, et l'écrire en place mute une
	# ressource partagée que rien ne remettra en état.
	var tuned: StandardMaterial3D = base.duplicate()
	tuned.uv1_scale = Vector3(uv_scale, uv_scale, uv_scale)
	tuned.albedo_texture = mul
	tuned.normal_enabled = true
	tuned.normal_texture = nrm
	tuned.normal_scale = NORMAL_SCALE
	var rough := _map(stem, "rough")
	if rough != null:
		tuned.roughness_texture = rough
		tuned.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	var ao := _map(stem, "ao")
	if ao != null:
		tuned.ao_enabled = true
		tuned.ao_texture = ao
		tuned.ao_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
		# 0 = l'AO n'assombrit que l'ambiante. Au-delà elle mange la lumière directe et la
		# coque vire au gris sale sous la clé.
		tuned.ao_light_affect = 0.0
	return tuned

## L'artère et le fond des puits : la même image en albédo et en émission.
##
## ⚠️ L'INTENSITÉ BAISSE AVEC L'ARRIVÉE DE LA TEXTURE, ET C'EST L'INVERSE DE CE QUE J'AVAIS
## ÉCRIT ICI. `aegis_kit` pose l'émissif à 2,5, et ce réglage a été jugé en capture sur une
## COULEUR PLATE : il fallait 2,5 pour qu'un aplat sombre lise comme une lumière. La texture,
## elle, porte déjà ses propres canaux quasi blancs sur un fond noir — 2,5 par-dessus les fait
## sortir de la plage, le bloom achève le travail, et l'artère devient une barre BLANCHE. Elle
## perd alors sa couleur, c'est-à-dire son appartenance à l'Unisson. Vu en capture.
##
## ⚠️ Et l'enjeu n'est pas que l'ambiance : les signaux que le moteur pose PAR-DESSUS — le bulbe
## d'un nœud d'épine, le couvercle d'un puits — doivent rester distinguables de la matière. Une
## artère saturée les noie, et le joueur ne voit plus ce qu'il a détruit.
## ⚠️ ET ELLE BAISSE UNE SECONDE FOIS AVEC LA REFONTE DE LA GÉOMÉTRIE (`BRIEF-0094`), POUR LA
## MÊME RAISON LUE À L'ENVERS. 1,0 a été jugé sur une artère qui était une BANDE LARGE : la
## texture y étalait ses canaux clairs et ses fonds sombres, et c'est ce mélange qui tenait
## l'intensité. La bande est devenue quatre conduits de 12 à 18 cm au fond d'une tranchée : sur
## douze centimètres, la carte ne livre plus qu'une tranche quasi constante — son cœur clair —
## et l'écran reçoit quatre traits pleins. Le bloom les soude, et l'on retrouve exactement le
## « laser géant » que la refonte devait supprimer. Vu en capture, tronçon 2, le 2026-08-29.
##
## La géométrie porte désormais le rythme (les coupures sont des travées de MATIÈRE) : la carte
## n'a plus à le porter, et l'énergie n'a plus à compenser un fond sombre qui n'existe plus.
const EMISSIVE_ENERGY := 0.45

## Ce que l'albédo d'un conduit mort garde de sa couleur.
##
## ⚠️ SANS LUI L'EXTINCTION NE SE VOYAIT PAS, ET LA MESURE LE DIT : 4 à 5 % d'écart de
## luminance entre un conduit alimenté et un conduit éteint. Le moteur ne baissait que
## l'ÉMISSION — or `_skin_emissive()` pose la même carte en ALBÉDO, et sous la lumière clé
## directionnelle c'est le terme diffus qui domine. On éteignait donc une lampe en gardant
## sa peinture fluo.
##
## Un conduit mort perd les deux : il ne rayonne plus, et sa couleur retombe vers le bordé.
##
## ⚠️ VALEURS DURCIES LE 2026-09-06 APRÈS UN VERDICT EN JEU : « quand je détruis un nœud, pas
## de changement, je ne vois pas les chemins lumineux s'éteindre ». La première tentative
## gardait 30 % de couleur et 0,06 d'émission — assez pour que la mesure bouge, pas assez pour
## que l'œil le voie sous le bloom du niveau. On descend à 12 % et 0,015.
const DEAD_ALBEDO := 0.12

## Ce qu'il reste d'un conduit dont le nœud d'épine est tombé.
##
## ⚠️ IL NE VA PAS À ZÉRO, ET C'EST DÉLIBÉRÉ. Une ligne éteinte pour de bon disparaît dans
## l'anthracite du bordé, et le joueur ne lit plus « ce circuit est mort » mais « il n'y a
## rien ici ». À 0,06 le conduit reste une VEINE SOMBRE : on voit qu'il existe et qu'il ne
## porte plus rien. C'est la même règle que l'œil d'une tourelle abattue.
const EMISSIVE_DEAD := 0.015

## Les matériaux ÉMISSIFS d'un tronçon, pour pouvoir l'éteindre seul.
##
## ⚠️ ILS SONT DÉJÀ PROPRES À CHAQUE TRONÇON, et c'est ce qui rend l'extinction possible sans
## toucher à la géométrie. `apply()` duplique le matériau importé **par maillage** — la boucle
## est dans le `for mesh`, pas au-dessus. Les cinq tronçons portent donc cinq copies, et
## baisser l'une n'éteint pas les autres. Sans cette propriété il aurait fallu un kit de
## conduits, comme il a fallu un kit d'épine pour que les bulbes meurent un par un.
## Éteint un conduit : l'émission ET l'albédo, dans le même geste.
##
## ⚠️ LES DEUX ENSEMBLE, ET C'EST TOUT L'INTÉRÊT D'AVOIR UNE FONCTION. Baisser la seule
## émission depuis l'appelant marchait « en théorie » et ne se voyait pas : le savoir sur ce
## qu'est un conduit mort vit ici, avec la fonction qui l'a allumé.
static func extinguish(mat: StandardMaterial3D) -> void:
	mat.emission_energy_multiplier = EMISSIVE_DEAD
	mat.albedo_color = Color(mat.albedo_color.r * DEAD_ALBEDO,
		mat.albedo_color.g * DEAD_ALBEDO, mat.albedo_color.b * DEAD_ALBEDO,
		mat.albedo_color.a)

static func emissives_of(section: Node) -> Array[StandardMaterial3D]:
	var out: Array[StandardMaterial3D] = []
	for mesh in _hull_meshes(section):
		for i in mesh.get_surface_override_material_count():
			var mat := mesh.get_surface_override_material(i) as StandardMaterial3D
			if mat != null and StringName(mat.resource_name) == EMISSIVE_MATERIAL:
				out.append(mat)
	return out

static func _skin_emissive(base: StandardMaterial3D) -> StandardMaterial3D:
	var map := _map(EMISSIVE_MAP, "")
	if map == null:
		return null
	var tuned: StandardMaterial3D = base.duplicate()
	tuned.uv1_scale = Vector3(HULL_UV_SCALE, HULL_UV_SCALE, HULL_UV_SCALE)
	tuned.albedo_texture = map
	tuned.emission_enabled = true
	tuned.emission_texture = map
	tuned.emission_energy_multiplier = EMISSIVE_ENERGY
	return tuned

## Une carte, ou `null` si l'opérateur ne l'a pas encore fournie.
static func _map(stem: String, suffix: String) -> Texture2D:
	var path := MAPS_DIR + stem + ("_" + suffix if suffix != "" else "") + ".png"
	if not ResourceLoader.exists(path):
		return null
	return load(path) as Texture2D

## Les maillages de la COQUE d'un tronçon — et pas ce que le moteur y a accroché.
##
## ⚠️ CETTE FRONTIÈRE A ÉTÉ TROUVÉE PAR UN COMPTE, ET ELLE COMPTAIT. `emissives_of()` marchait
## d'abord sur tous les descendants : abattre un nœud d'épine éteignait **36 matériaux** au
## lieu d'un. Les trente-cinq autres n'étaient pas des conduits — c'étaient les YEUX DES
## TOURELLES, les feux des ponts et les bulbes d'épine, que le moteur accroche aux marqueurs.
##
## Deux dégâts, dont un invisible. Le visible : l'œil d'une tourelle dit « cette pièce est
## vivante / affaiblie / morte », un signal qui n'a rien à voir avec l'alimentation du tronçon.
## L'invisible : `CortegeTurret._set_eye()` réécrit cette énergie à CHAQUE TIR, donc
## l'extinction y était défaite dans la seconde — on éteignait beaucoup, et rien ne restait.
##
## La règle est donc : on ne descend pas dans un marqueur. Ce qui pend sous `Turret_NN`,
## `Bay_NN` ou `Spine_NN` appartient à la pièce, pas au bordé.
static func _hull_meshes(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	var mesh := node as MeshInstance3D
	if mesh != null:
		out.append(mesh)
	for child in node.get_children():
		var nom := String(child.name)
		if nom.begins_with("Turret_") or nom.begins_with("Bay_") or nom.begins_with("Spine_"):
			continue
		_hull_meshes(child, out)
	return out

static func _meshes(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	var mesh := node as MeshInstance3D
	if mesh != null:
		out.append(mesh)
	for child in node.get_children():
		_meshes(child, out)
	return out
