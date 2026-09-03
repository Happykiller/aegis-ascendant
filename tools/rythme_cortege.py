import re, io, math, random
src = io.open("tools/blender/build_long_cortege.py", encoding="utf-8").read()
def pairs(name):
    m = re.search(name + r": tuple\[tuple\[float, float\], \.\.\.\] = \((.*?)\n\)", src, re.S)
    return [(float(a), float(b)) for a, b in re.findall(r"\((-?[\d.]+), (-?[\d.]+)\)", m.group(1))]
def triples(name):
    m = re.search(name + r": tuple\[tuple\[float, float, float\], \.\.\.\] = \((.*?)\n\)", src, re.S)
    return [tuple(float(v) for v in t) for t in re.findall(r"\(([\d.]+), ([\d.]+), ([\d.]+)\)", m.group(1))]

TURRETS, BAYS = pairs("TURRETS"), pairs("BAYS")
TAPER, ASYM = triples("TAPER"), triples("ASYMMETRY")
SPINES = [50.0,150.0,250.0,350.0,450.0]
PITS = [(136.0,6.0,1.0),(228.0,6.0,1.0),(292.0,6.0,-1.0),(393.0,6.0,1.0)]
PIT_X = (2.20, 6.80)
AT, AB, AS_, AA = 4.2, 5.4, 3.8, 2.0
AMBRY = (446.0, 474.0); HALF = 14.0; PROW = 88.0
FROZEN_T = {68.0, 173.0, 336.0, 410.0, 470.0}      # hotes de batterie
FROZEN_B = {126.0, 290.0}
TURRET_R, BAY_HS, BAY_HX, PIT_KEEP = 2.08, 4.25, 3.00, 2.20
PAD_RADIUS = (2.30, 2.55, 2.75, 3.00, 3.20)
def pad_of(s_): return PAD_RADIUS[min(int(s_//100), 4)]

def ss(t): t=min(1.,max(0.,t)); return t*t*(3-2*t)
def interp(tab, s):
    if s <= tab[0][0]: return tab[0][1], tab[0][2]
    if s >= tab[-1][0]: return tab[-1][1], tab[-1][2]
    for (s0,a0,b0),(s1,a1,b1) in zip(tab, tab[1:]):
        if s <= s1:
            if s1-s0 < 1e-9: return a1,b1
            t = ss((s-s0)/(s1-s0)); return a0+(a1-a0)*t, b0+(b1-b0)*t
    return 1.,1.
def side_scale(s, sd):
    kx = interp(TAPER, s)[0]
    if s <= PROW: return kx
    tri, bab = interp(ASYM, s)
    return kx * (tri if sd >= 0 else bab)

def merge(sp):
    sp = sorted(sp); out=[]
    for a,b in sp:
        if out and a <= out[-1][1]: out[-1]=(out[-1][0], max(out[-1][1], b))
        else: out.append((a,b))
    return out
def calm_spans(T,B,S):
    sp  = [(s-AT,s+AT) for s,_ in T] + [(s-AB,s+AB) for s,_ in B]
    sp += [(s-AS_,s+AS_) for s in S] + [(AMBRY[0]-AA, AMBRY[1]+AA)]
    m = merge(sp); res=[]; cur=0.0
    for a,b in m:
        a,b = max(0.,a), min(500.,b)
        if a>cur: res.append((cur,a))
        cur = max(cur,b)
    if cur<500.: res.append((cur,500.))
    return res
def density(T,B,S,win=20.0):
    pts = sorted([s for s,_ in T]+[s for s,_ in B]+list(S))
    return max(sum(1 for q in pts if p<=q<p+win) for p in pts)

def feasible(T,B,S):
    # 1) baies : la coque ne respire pas dans leur garde (tolerance 3 pct)
    for s,x in B:
        for v in (s-BAY_HS-3.75, s, s+BAY_HS+3.75):
            if abs(side_scale(v, 1.0 if x>=0 else -1.0) - 1.0) > 0.03: return False
        if not (s+BAY_HS+3.75 < AMBRY[0] or s-BAY_HS-3.75 > AMBRY[1]):
            if x >= 0: return False
    # 2) fosses libres — MEME LOGIQUE QUE `_assert_pits_are_clear` : s ET x ET bord.
    #    Une baie a babord n'est pas concernee par une fosse a tribord.
    for pc, ph, side in PITS:
        lo, hi = pc-ph-PIT_KEEP, pc+ph+PIT_KEEP
        x_lo = min(PIT_X[0]*side, PIT_X[1]*side) - PIT_KEEP
        x_hi = max(PIT_X[0]*side, PIT_X[1]*side) + PIT_KEEP
        def touches(ps, px, r):
            return lo-r <= ps <= hi+r and x_lo-r <= px <= x_hi+r
        for ts, tx in T:
            mx = tx if ts <= PROW else tx * side_scale(ts, 1.0 if tx>=0 else -1.0)
            if touches(ts, mx, TURRET_R): return False
        for bs, bx in B:
            if touches(bs, bx, max(BAY_HS, BAY_HX)): return False
        for ns in S:
            if lo-AS_ <= ns <= hi+AS_ and x_lo <= 0.0 <= x_hi: return False
    # 3) ⚠️ SOCLES ET OUVERTURES, EN 2D ET AVEC LE BON RAYON. Le premier modele
    #    testait le seul `s` avec un rayon fixe de 2,08 : le generateur a refuse
    #    quatre tourelles entrees dans l'ouverture d'un pont d'envol, parce que le
    #    socle grandit d'un troncon au suivant (2,30 a 3,20) et que la collision
    #    se joue aussi en x.
    # ⚠️ LE COAMING DEBORDE L'OUVERTURE DE 0,80 m, et le generateur distingue les
    #    deux : entrer dans l'ouverture est INTERDIT, toucher le coaming doit etre
    #    DECLARE dans ACCEPTED_PAD_BAY_PROXIMITY avec sa raison. Trois proximites
    #    de plus auraient ete trois arbitrages a ecrire — alors que celui qui
    #    existe est deja note perime au backlog. On ecarte.
    COAMING = 0.80
    for ts, tx in T:
        r = pad_of(ts)
        for bs, bx in B:
            if (abs(ts-bs) < BAY_HS + COAMING + r
                    and abs(tx-bx) < BAY_HX + COAMING + r): return False
    for i in range(len(T)):
        for j in range(i+1, len(T)):
            if (abs(T[i][0]-T[j][0]) < pad_of(T[i][0]) + pad_of(T[j][0])
                    and abs(T[i][1]-T[j][1]) < pad_of(T[i][0]) + pad_of(T[j][0])): return False
    for i in range(len(B)):
        for j in range(i+1, len(B)):
            if abs(B[i][0]-B[j][0]) < 2*BAY_HS and abs(B[i][1]-B[j][1]) < 2*BAY_HX: return False
    # 4) densite pas pire qu'aujourd'hui
    if density(T,B,S) > 3: return False
    # 5) ⚠️ TOUT RESTE SUR LA COQUE. Le recuit a d'abord pousse `Turret_17` a
    #    s = 503 — hors des 500 m — parce que rien ne le lui interdisait.
    for s_,_ in T:
        if not (56.0 <= s_ <= 494.0): return False
    # ⚠️ AUCUNE BAIE AU-DESSUS DE s = 86, ET LA RAISON EST SUBTILE. L'emprise d'une
    #    ouverture est en x ABSOLU (xc +/- 3,00), mais la coque RESPIRE : plus on
    #    remonte vers la proue, plus la facette exterieure se rapproche de l'axe.
    #    A s = 81,6, elle entre dans l'emprise de `Bay_01` — et le harnais compte
    #    alors trois triangles « DANS l'emprise d'un pont d'envol », c'est-a-dire
    #    une peau qui s'est refermee sur le hangar. 86 est la station d'origine :
    #    c'est la limite ou la facette reste dehors.
    for s_,_ in B:
        if not (86.0 <= s_ <= 492.0): return False
    # ⚠️ UN NŒUD NE DESCEND PAS DANS LE FUSEAU DE PROUE. Le recuit avait pose
    #    Spine_01 a s = 36,4, ou la coque ne fait que 63 pct de sa largeur : le
    #    generateur a refuse deux fois — « le berceau (1,32 m) ne tient pas dans
    #    le fond plat du canal (1,12 m) a cette station » et « le rebord n'est
    #    qu'a 0,055 m au-dessus de l'assise, le nœud ne siegerait plus dans une
    #    tranchee ». Le nœud vit DANS l'artere : il lui faut une artere a taille
    #    reelle.
    for s_ in S:
        if not (48.0 <= s_ <= 490.0): return False
    # 6) ⚠️ LA REPARTITION PAR TRONCON NE BOUGE PAS. Elle porte la montee en
    #    densite (2, 3, 3, 4, 5 tourelles) ET la taille des socles, qui grandit
    #    d'un troncon au suivant : une tourelle qui change de troncon change de
    #    socle, donc d'emprise, donc de tout ce qui a ete arbitre au BRIEF-0092.
    def per_section(vals):
        out = [0]*5
        for v in vals: out[min(int(v//100), 4)] += 1
        return out
    if per_section([s_ for s_,_ in T]) != [2,3,3,4,5]: return False
    if per_section([s_ for s_,_ in B]) != [1,2,2,1,1]: return False
    if per_section(S) != [1,1,1,1,1]: return False
    # 6 bis) ⚠️ L'OUVERTURE NE DOIT PAS ETRE VIDE — ET C'EST UN TEST DU JEU QUI
    #    L'A DIT, PAS LE GENERATEUR. Maximiser le calme pousse tout vers la poupe :
    #    le recuit avait dégagé 61 m nus a la proue, magnifique pour la mesure et
    #    desastreux pour le rythme. `test_the_survey_does_not_open_on_dead_air`
    #    borne des DEUX cotes : la reception de proue doit passer le relais a la
    #    coque (premiere piece <= dernier depart + 8 s) sans deborder dessus.
    #    Traduit en station : la premiere installation ne descend pas sous 56 m.
    if min([s_ for s_,_ in T] + [s_ for s_,_ in B] + list(S)) > 56.0: return False
    # 7) ⚠️ LA ZONE INTERDITE D'AMBRY. Le generateur la declare
    #    (AMBRY_KEEPOUT_X 6,90-14,10 ; AMBRY_KEEPOUT_S 443,5-476,5) : le recuit y
    #    avait pose Turret_17 a (474,2 ; +9,00), en plein dans l'avant-poste.
    for s_, x_ in T:
        mx = x_ if s_ <= PROW else x_ * side_scale(s_, 1.0 if x_>=0 else -1.0)
        if 443.5-TURRET_R <= s_ <= 476.5+TURRET_R and 6.90-TURRET_R <= mx <= 14.10+TURRET_R:
            return False
    for s_, x_ in B:
        if 443.5-BAY_HS <= s_ <= 476.5+BAY_HS and 6.90-BAY_HX <= x_ <= 14.10+BAY_HX:
            return False
    # 8) ⚠️ AUCUNE PAIRE FACE A FACE — LA CONSIGNE 14, CONTRE L'OPTIMISEUR.
    #    Grouper maximise le calme, et le groupement le PLUS efficace est
    #    d'apparier une piece a babord avec une piece a tribord a la meme
    #    station : les deux tabliers se recouvrent entierement. Le recuit y est
    #    alle droit — Turret_01/02 et Turret_11/12 exactement alignees — et
    #    produisait ainsi la symetrie que le lot B2 vient de supprimer.
    #    « Ne pas systematiquement placer une tourelle a droite lorsqu'il y en a
    #    une a gauche » est donc une CONTRAINTE, pas une preference : sans elle
    #    l'optimisation la viole par construction.
    inst = [(s_, x_) for s_, x_ in T] + [(s_, x_) for s_, x_ in B]
    for i in range(len(inst)):
        for j in range(i+1, len(inst)):
            if inst[i][1] * inst[j][1] < 0 and abs(inst[i][0] - inst[j][0]) < 5.0:
                return False
    return True

def score(T,B,S):
    c = calm_spans(T,B,S)
    tot = sum(b-a for a,b in c)
    n15 = len([1 for a,b in c if b-a>=15]); n20 = len([1 for a,b in c if b-a>=20])
    return tot + 14*n15 + 10*n20

random.seed(7)
T, B, S = list(TURRETS), list(BAYS), list(SPINES)
base_T, base_B, base_S = list(T), list(B), list(S)
# ⚠️ L'ETAT DE DEPART EST LUI-MEME INFAISABLE sous la garde du coaming : c'est
# exactement ce que `ACCEPTED_PAD_BAY_PROXIMITY` declare aujourd'hui (Turret_14
# frole Bay_07). On part donc d'un etat non conforme, et l'on n'accepte comme
# solution qu'un etat qui l'est devenu.
start_ok = feasible(T,B,S)
print("etat de depart faisable :", start_ok)
best = (-1e9, None, None, None)
cur = (score(T,B,S), list(T), list(B), list(S))
temp = 6.0
for step in range(120000):
    temp = 6.0 * (1 - step/120000) + 0.2
    nT, nB, nS = list(cur[1]), list(cur[2]), list(cur[3])
    kind = random.random()
    if kind < 0.55:
        i = random.randrange(len(nT))
        if nT[i][0] in FROZEN_T: continue
        s0 = base_T[i][0]
        nT[i] = (round(max(s0-15, min(s0+15, nT[i][0] + random.uniform(-4,4))),1), nT[i][1])
    elif kind < 0.8:
        i = random.randrange(len(nB))
        if nB[i][0] in FROZEN_B: continue
        s0 = base_B[i][0]
        nB[i] = (round(max(s0-15, min(s0+15, nB[i][0] + random.uniform(-4,4))),1), nB[i][1])
    else:
        i = random.randrange(len(nS))
        s0 = base_S[i]
        nS[i] = round(max(s0-15, min(s0+15, nS[i] + random.uniform(-4,4))),1)
    ok = feasible(nT,nB,nS)
    sc = score(nT,nB,nS) - (0.0 if ok else 400.0)
    if sc > cur[0] or random.random() < math.exp((sc-cur[0])/max(temp,1e-6)):
        cur = (sc, nT, nB, nS)
        if ok and sc > best[0]: best = (sc, list(nT), list(nB), list(nS))

assert best[1] is not None, "aucun etat faisable trouve"
_, T, B, S = best
c = calm_spans(T,B,S); tot = sum(b-a for a,b in c)
print(f"OPTIMISE  score {best[0]:.1f}")
print(f"  calme {tot:.1f} m ({tot/5:.1f} %)  plages {len(c)}  >=8m {len([1 for a,b in c if b-a>=8])}  >=15m {len([1 for a,b in c if b-a>=15])}  >=20m {len([1 for a,b in c if b-a>=20])}")
print(f"  plage max {max(b-a for a,b in c):.1f} m   densite max {density(T,B,S)}")
print("  TURRETS =", tuple((s,x) for s,x in T))
print("  BAYS =", tuple((s,x) for s,x in B))
print("  SPINES =", tuple(S))
