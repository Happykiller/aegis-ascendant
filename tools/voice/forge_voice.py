#!/usr/bin/env python3
"""Forge les répliques enregistrées d'Aegis Ascendant à partir d'une demande VOX-NNNN.

    python3 tools/voice/forge_voice.py docs/forge/voice/VOX-0001-lyra-accueil.json --preview
    python3 tools/voice/forge_voice.py docs/forge/voice/VOX-0001-lyra-accueil.json --deposer

⚠️ LA DEMANDE FAIT FOI, ET ELLE SEULE. Le texte n'est jamais retapé ici : il est lu dans le
JSON, qui le tient lui-même du `.tres` que le jeu affiche (garde
`test_the_voice_request_asks_for_exactly_what_the_game_says`). Trois copies d'une phrase, ce
sont trois occasions de faire enregistrer autre chose que ce qui s'affiche.

⚠️ CE QU'ON DÉPOSE EST **BRUT**, JAMAIS FILTRÉ. La chaîne comms (passe-haut 300 Hz, passe-bas
3400 Hz, distorsion, compresseur) vit dans le jeu, sur le bus `Voice`. Déposer une voix déjà
filtrée la ferait passer DEUX fois — bande étroite sur bande étroite, inintelligible — et le
réglage du filtre ne serait plus modifiable. C'est la règle 3 du contrat
`docs/forge/voice/README.md`, et c'est celle qu'on enfreint sans s'en apercevoir.

⚠️ MAIS ON ÉCOUTE FILTRÉ. `--preview` produit les DEUX versions : le brut (ce qui est déposé)
et le rendu comms (ce que le joueur entendra). Juger la voix brute, c'est juger autre chose
que le jeu.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
# ⚠️ HORS DU DÉPÔT. Les modèles pèsent 60 à 80 Mo pièce : versionnés, ils gonfleraient le LFS
# pour un outil, pas pour le jeu. Ils se retéléchargent en une commande.
ATELIER = Path(os.environ.get("AEGIS_VOICE_HOME", Path.home() / ".local/share/aegis-voice"))
VENV = ATELIER / "venv"
MODELES = ATELIER / "modeles"
DEPOT_VOIX = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

VOIX = {
    "fr_FR-siwis-medium": "fr/fr_FR/siwis/medium/fr_FR-siwis-medium",
    "fr_FR-upmc-medium": "fr/fr_FR/upmc/medium/fr_FR-upmc-medium",
    "fr_FR-tom-medium": "fr/fr_FR/tom/medium/fr_FR-tom-medium",
}

# La chaîne comms du bus `Voice`, reproduite pour l'ÉCOUTE seulement. Elle doit suivre
# `resources/audio/default_bus_layout.tres` : si l'un bouge, l'autre ment.
COMMS = ("highpass=f=300,lowpass=f=3400,acompressor=threshold=-16dB:ratio=4,"
         "volume=2.2,alimiter=limit=0.7")
# Silences de tête et de queue sous 100 ms (règle 4 du contrat), puis crête à -3 dBFS.
TAILLE = ("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,"
          "areverse,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,"
          "areverse,loudnorm=I=-16:TP=-3")


def dire(message: str) -> None:
    print("[voix] %s" % message, flush=True)


def bureau_windows() -> Path:
    """Où déposer les essais à écouter, côté Windows.

    ⚠️ LE NOM D'UTILISATEUR NE S'ÉCRIT PAS EN DUR. Il l'a été (`/mnt/c/Users/faro/Desktop`) et
    `--preview` mourait sur un `PermissionError` après avoir synthétisé les répliques : le
    travail était fait, seul le dépôt échouait. On demande le profil à Windows lui-même ; à
    défaut, on retombe sur le home WSL, qui existe toujours mais ne s'ouvre pas d'un
    double-clic.
    """
    try:
        # ⚠️ OCTETS, PAS TEXTE. Lancé depuis un chemin WSL, `cmd.exe` avertit sur stderr dans
        # la page de code Windows (cp850) : décoder en UTF-8 lève, et la préversion meurt sur
        # un message qu'on n'allait même pas lire.
        brut = subprocess.run(["cmd.exe", "/c", "echo %USERPROFILE%"],
                              capture_output=True, timeout=10, cwd="/").stdout
        profil = brut.decode("utf-8", errors="replace").strip()
        if profil.startswith("C:\\"):
            bureau = Path("/mnt/c") / profil[3:].replace("\\", "/") / "Desktop"
            if bureau.is_dir():
                return bureau
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.home() / "essais-voix"


def outil(nom: str) -> str:
    chemin = shutil.which(nom)
    if not chemin:
        sys.exit("[voix] %s introuvable — il est requis" % nom)
    return chemin


def atelier_pret() -> Path:
    """Le venv et piper, installés une fois pour toutes. Idempotent."""
    piper = VENV / "bin" / "piper"
    if piper.exists():
        return piper
    dire("premier passage : installation de la chaîne dans %s" % ATELIER)
    ATELIER.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    subprocess.run([str(VENV / "bin" / "pip"), "install", "--quiet", "piper-tts"], check=True)
    if not piper.exists():
        sys.exit("[voix] piper ne s'est pas installé")
    return piper


def modele_pret(nom: str) -> Path:
    if nom not in VOIX:
        sys.exit("[voix] voix inconnue : %s (connues : %s)" % (nom, ", ".join(VOIX)))
    MODELES.mkdir(parents=True, exist_ok=True)
    onnx = MODELES / ("%s.onnx" % nom)
    for suffixe in (".onnx", ".onnx.json"):
        cible = MODELES / (nom + suffixe)
        if cible.exists():
            continue
        url = "%s/%s%s" % (DEPOT_VOIX, VOIX[nom], suffixe)
        dire("téléchargement de %s" % cible.name)
        urllib.request.urlretrieve(url, cible)
    return onnx


def synthese(piper: Path, modele: Path, texte: str, sortie: Path,
             locuteur: int | None, cadence: float) -> None:
    # ⚠️ LES SAUTS DE LIGNE DEVIENNENT DES ESPACES. Piper lit stdin LIGNE PAR LIGNE : un texte
    # sur deux lignes donnerait deux fichiers, dont le second écraserait le premier. La
    # ponctuation porte déjà la respiration.
    commande = [str(piper), "-m", str(modele), "-f", str(sortie),
                "--length-scale", str(cadence)]
    if locuteur is not None:
        commande += ["-s", str(locuteur)]
    subprocess.run(commande, input=texte.replace("\n", " ").encode("utf-8"),
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def rendu(ffmpeg: str, source: Path, cible: Path, filtre: str) -> None:
    cible.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(source),
                    "-ar", "48000", "-ac", "1", "-af", filtre, str(cible)], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("demande", help="docs/forge/voice/VOX-NNNN-*.json")
    ap.add_argument("--voix", default="fr_FR-siwis-medium", choices=sorted(VOIX))
    ap.add_argument("--locuteur", type=int, default=None,
                    help="index du locuteur pour un modèle multi-voix (upmc : 0 jessica, 1 pierre)")
    ap.add_argument("--cadence", type=float, default=1.15,
                    help="length_scale de piper ; >1 ralentit. Le débit fait autant que le timbre")
    ap.add_argument("--preview", action="store_true",
                    help="produit brut ET comms dans un dossier d'écoute, sans toucher au dépôt")
    ap.add_argument("--ecoute", default=None, help="où déposer les essais de --preview")
    ap.add_argument("--deposer", action="store_true",
                    help="écrit les .ogg BRUTS dans le dépôt et rend les lignes de provenance")
    args = ap.parse_args()

    if not (args.preview or args.deposer):
        sys.exit("[voix] choisir --preview (écouter) ou --deposer (intégrer)")

    demande = json.loads(Path(args.demande).read_text(encoding="utf-8"))
    repliques = demande["lines"]
    cible_depot = RACINE / demande["x_delivery"]["target_dir"]
    ffmpeg = outil("ffmpeg")
    piper = atelier_pret()
    modele = modele_pret(args.voix)

    ecoute = Path(args.ecoute) if args.ecoute else \
        bureau_windows() / ("%s-essais-voix" % demande["slug"])
    brut_dir = ATELIER / "brut" / demande["slug"]
    brut_dir.mkdir(parents=True, exist_ok=True)

    dire("%s — %d répliques, voix %s, cadence %.2f"
         % (demande["id"], len(repliques), args.voix, args.cadence))
    provenance = []
    for replique in repliques:
        cue = replique["cue"]
        wav = brut_dir / ("%s.wav" % cue)
        synthese(piper, modele, replique["text"], wav, args.locuteur, args.cadence)
        if args.preview:
            rendu(ffmpeg, wav, ecoute / ("%s_brut.ogg" % cue), TAILLE)
            rendu(ffmpeg, wav, ecoute / ("%s_comms.ogg" % cue), COMMS + "," + TAILLE)
        if args.deposer:
            rendu(ffmpeg, wav, cible_depot / ("%s.ogg" % cue), TAILLE)
            provenance.append(
                demande["x_delivery"]["provenance_csv_line"]
                .replace("<cue>", cue)
                .replace("<outil>", "piper %s" % args.voix)
                .replace("<date>", __import__("datetime").date.today().isoformat()))
        dire("  %-16s %s" % (cue, replique["text"].replace("\n", " ")[:58]))

    if args.preview:
        dire("à ÉCOUTER : %s" % ecoute)
        dire("⚠️ juger les `_comms` — c'est ce que le joueur entendra. Le `_brut` est ce qu'on dépose.")
    if args.deposer:
        dire("déposé dans %s" % cible_depot)
        dire("lignes à coller dans assets/licenses/ASSET_PROVENANCE.csv :")
        for ligne in provenance:
            print(ligne)
        dire("⚠️ reste à reporter chaque `cue` dans le champ `voice_cue` du .tres correspondant")
    return 0


if __name__ == "__main__":
    sys.exit(main())
