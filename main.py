
import asyncio
import base64
import textwrap
from io import BytesIO
from pathlib import Path

import flet as ft
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ==========================================================
# PROFIL AFFICHE — FLET 1.0.4
# ==========================================================

LARGEUR, HAUTEUR = 1080, 1920

BLEU = "#1769D2"
OR = "#E8C65A"
FOND = "#F1F5FB"
TEXTE = "#172B4D"
GRIS = "#63748B"
BLANC = "#FFFFFF"
BORDURE = "#E2EAF5"
VERT = "#16865B"
ROUGE = "#C0392B"

photo_bytes = None
affiche_bytes = None


# ==========================================================
# OUTILS
# ==========================================================

def encoder_image(donnees):
    """Convertit les données d'une image en URL lisible par Flet."""
    return "data:image/png;base64," + base64.b64encode(
        donnees
    ).decode("ascii")


def charger_police(taille, gras=False):
    if gras:
        chemins = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        chemins = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for chemin in chemins:
        if Path(chemin).is_file():
            try:
                return ImageFont.truetype(chemin, taille)
            except OSError:
                continue

    return ImageFont.load_default()


def lire_photo(donnees):
    """Vérifie la photo et la convertit en PNG."""
    with Image.open(BytesIO(donnees)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")

        sortie = BytesIO()
        image.save(sortie, format="PNG", optimize=True)

    return sortie.getvalue()


# ==========================================================
# GÉNÉRATION DE L'AFFICHE
# ==========================================================

def generer_affiche(nom, contact, adresse, groupe, donnees_photo):
    W, H = LARGEUR, HAUTEUR

    with Image.open(BytesIO(donnees_photo)) as source:
        photo = ImageOps.exif_transpose(source).convert("RGB")

    photo = ImageOps.fit(
        photo,
        (W, H),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.40),
    )

    fond = photo.convert("RGBA")

    # Dégradé sombre en bas pour rendre les textes lisibles.
    masque = Image.new("L", (1, H), 0)
    pixels = masque.load()
    debut_ombre = 850

    for y in range(debut_ombre, H):
        progression = (y - debut_ombre) / (H - debut_ombre)
        pixels[0, y] = int(205 * progression)

    masque = masque.resize((W, H))
    ombre = Image.new("RGBA", (W, H), (3, 8, 20, 0))
    ombre.putalpha(masque)
    fond = Image.alpha_composite(fond, ombre)

    dessin = ImageDraw.Draw(fond)

    def texte_centre(texte, y, taille, couleur=BLANC,
                     gras=False, marge=70):
        texte = str(texte)
        taille_actuelle = taille

        while True:
            police = charger_police(taille_actuelle, gras)
            boite = dessin.textbbox((0, 0), texte, font=police)
            largeur = boite[2] - boite[0]

            if largeur <= W - 2 * marge or taille_actuelle <= 24:
                break

            taille_actuelle -= 2

        x = (W - largeur) / 2 - boite[0]
        dessin.text(
            (x, y),
            texte,
            font=police,
            fill=couleur,
        )

    def separateur(y):
        dessin.line((85, y, 995, y), fill=OR, width=3)
        centre = W // 2

        dessin.polygon(
            [
                (centre, y - 17),
                (centre + 13, y),
                (centre, y + 17),
                (centre - 13, y),
            ],
            outline=OR,
            width=3,
        )

        dessin.ellipse(
            (centre - 34, y - 5, centre - 24, y + 5),
            fill=OR,
        )
        dessin.ellipse(
            (centre + 24, y - 5, centre + 34, y + 5),
            fill=OR,
        )

    separateur(1250)

    texte_centre(
        (nom or "").strip().upper(),
        1280, 76, OR, True, 35
    )

    texte_centre(
        "Contact : " + ((contact or "").strip() or "Non renseigné"),
        1390, 48, OR, True
    )

    texte_centre(
        "Adresse des parents",
        1485, 39, OR, True
    )

    adresse = (adresse or "").strip() or "Non renseignée"

    lignes = textwrap.wrap(
        adresse,
        width=36,
        break_long_words=True,
    ) or ["Non renseignée"]

    y = 1540

    for ligne in lignes[:3]:
        texte_centre(ligne, y, 36, OR, True)
        y += 45

    texte_centre(
        "Groupe sanguin : " + ((groupe or "").strip() or "Inconnu"),
        y + 20, 34, BLANC, True
    )

    separateur(1795)

    sortie = BytesIO()
    fond.convert("RGB").save(
        sortie,
        format="PNG",
        optimize=True,
    )

    return sortie.getvalue()


# ==========================================================
# APPLICATION
# ==========================================================

def main(page: ft.Page):
    global photo_bytes, affiche_bytes

    photo_bytes = None
    affiche_bytes = None

    page.title = "Profil Affiche"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = FOND
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    # ------------------------------------------------------
    # NOTIFICATIONS INTÉGRÉES À LA PAGE
    # Aucun appel à page.open() ou SnackBar nécessaire.
    # ------------------------------------------------------

    texte_message = ft.Text(
        "",
        color=BLANC,
        size=13,
        selectable=True,
    )

    banniere_message = ft.Container(
        content=texte_message,
        bgcolor=BLEU,
        padding=12,
        border_radius=12,
        visible=False,
    )

    def notifier(message, succes=True):
        texte_message.value = str(message)
        banniere_message.bgcolor = VERT if succes else ROUGE
        banniere_message.visible = True
        page.update()

    # ------------------------------------------------------
    # CHAMPS
    # ------------------------------------------------------

    def style_champ():
        return {
            "border": ft.OutlineInputBorder(
                border_radius=14
            )
        }

    champ_nom = ft.TextField(
        label="Nom et prénoms",
        hint_text="Ex. : Berangoto Anice",
        filled=True,
        bgcolor="#FAFBFE",
        **style_champ(),
    )

    champ_contact = ft.TextField(
        label="Contact personnel",
        hint_text="Numéro de téléphone",
        keyboard_type=ft.KeyboardType.PHONE,
        filled=True,
        bgcolor="#FAFBFE",
        **style_champ(),
    )

    champ_adresse = ft.TextField(
        label="Adresse des parents",
        hint_text="Adresse ou contact des parents",
        multiline=True,
        min_lines=2,
        max_lines=3,
        filled=True,
        bgcolor="#FAFBFE",
        **style_champ(),
    )

    champ_groupe = ft.Dropdown(
        label="Groupe sanguin",
        filled=True,
        bgcolor="#FAFBFE",
        options=[
            ft.dropdown.Option(groupe)
            for groupe in [
                "A+", "A-", "B+", "B-", "AB+", "AB-",
                "O+", "O-", "Inconnu",
            ]
        ],
        value="Inconnu",
        border=ft.OutlineInputBorder(
            border_radius=14
        ),
    )

    # Toujours fournir src à ft.Image sous Flet 1.0.4.
    apercu_photo = ft.Image(
        src="",
        width=125,
        height=145,
        fit=ft.BoxFit.COVER,
    )

    apercu_affiche = ft.Image(
        src="",
        width=300,
        fit=ft.BoxFit.CONTAIN,
        visible=False,
    )

    texte_photo = ft.Text(
        "Aucune photo sélectionnée",
        size=13,
        color=GRIS,
    )

    texte_resultat = ft.Text(
        "Ton affiche apparaîtra ici après sa génération.",
        size=13,
        color=GRIS,
        text_align=ft.TextAlign.CENTER,
    )

    bouton_generer = ft.Button(
        content="Générer mon affiche",
        icon=ft.Icons.AUTO_AWESOME,
        width=float("inf"),
    )

    bouton_enregistrer = ft.Button(
        content="Enregistrer l'affiche",
        icon=ft.Icons.DOWNLOAD,
        width=float("inf"),
        disabled=True,
    )

    # ------------------------------------------------------
    # TRAITEMENT D'UNE PHOTO SÉLECTIONNÉE
    # ------------------------------------------------------

    async def traiter_fichier(fichier):
        global photo_bytes, affiche_bytes

        donnees = getattr(fichier, "bytes", None)

        if donnees:
            donnees = bytes(donnees)
        else:
            chemin = getattr(fichier, "path", None)

            if chemin and Path(chemin).is_file():
                donnees = await asyncio.to_thread(
                    Path(chemin).read_bytes
                )
            else:
                raise ValueError(
                    "Aucune donnée photo reçue. "
                    "Réessaie de sélectionner l'image."
                )

        nouvelle_photo = await asyncio.to_thread(
            lire_photo,
            donnees,
        )

        # Ne modifier l'état qu'après lecture réussie.
        photo_bytes = nouvelle_photo
        affiche_bytes = None

        apercu_photo.src = encoder_image(photo_bytes)
        texte_photo.value = (
            getattr(fichier, "name", None)
            or "Photo importée"
        )

        apercu_affiche.src = ""
        apercu_affiche.visible = False
        bouton_enregistrer.disabled = True

        texte_resultat.value = (
            "Photo importée. Tu peux générer ton affiche."
        )

        notifier("Photo importée avec succès.")
        page.update()

    # ------------------------------------------------------
    # SÉLECTEUR DE FICHIERS
    # ------------------------------------------------------

    async def photo_selectionnee(e):
        fichiers = getattr(e, "files", None)

        if not fichiers:
            return

        try:
            await traiter_fichier(fichiers[0])
        except Exception as erreur:
            notifier(
                f"Impossible de lire la photo : {erreur}",
                succes=False,
            )

    selecteur = ft.FilePicker(
        on_result=photo_selectionnee
    )

    # Dans Flet 1.0.4, FilePicker est un service de la page.
    if hasattr(page, "services"):
        page.services.append(selecteur)
    elif hasattr(page, "overlay"):
        page.overlay.append(selecteur)
    else:
        raise RuntimeError(
            "Impossible d'enregistrer le sélecteur de fichiers."
        )

    async def importer_photo(e):
        try:
            resultat = await selecteur.pick_files(
                dialog_title="Choisir une photo",
                allow_multiple=False,
                file_type=ft.FilePickerFileType.IMAGE,
                with_data=True,
            )

            # Si cette version renvoie directement les fichiers,
            # les traiter. Sinon, on_result les prendra en charge.
            if resultat:
                await traiter_fichier(resultat[0])

        except Exception as erreur:
            notifier(
                f"Impossible d'ouvrir les photos : {erreur}",
                succes=False,
            )

    # ------------------------------------------------------
    # GÉNÉRATION
    # ------------------------------------------------------

    async def creer_affiche(e):
        global affiche_bytes

        nom = (champ_nom.value or "").strip()

        if not nom:
            notifier(
                "Entre le nom et les prénoms.",
                succes=False,
            )
            return

        if not photo_bytes:
            notifier(
                "Importe d'abord une photo.",
                succes=False,
            )
            return

        bouton_generer.disabled = True
        bouton_generer.content = "Génération en cours..."
        page.update()

        try:
            nouvelle_affiche = await asyncio.to_thread(
                generer_affiche,
                nom,
                champ_contact.value or "",
                champ_adresse.value or "",
                champ_groupe.value or "Inconnu",
                photo_bytes,
            )

            affiche_bytes = nouvelle_affiche

            apercu_affiche.src = encoder_image(affiche_bytes)
            apercu_affiche.visible = True
            bouton_enregistrer.disabled = False

            texte_resultat.value = (
                "Affiche prête ! Vérifie le résultat avant de l'enregistrer."
            )

            notifier("Affiche générée avec succès.")

        except Exception as erreur:
            affiche_bytes = None
            apercu_affiche.src = ""
            apercu_affiche.visible = False
            bouton_enregistrer.disabled = True

            notifier(
                f"Erreur de génération : {erreur}",
                succes=False,
            )

        finally:
            bouton_generer.disabled = False
            bouton_generer.content = "Générer mon affiche"
            page.update()

    bouton_generer.on_click = creer_affiche

    # ------------------------------------------------------
    # ENREGISTREMENT
    # ------------------------------------------------------

    async def enregistrer_affiche(e):
        if not affiche_bytes:
            notifier(
                "Génère d'abord l'affiche.",
                succes=False,
            )
            return

        try:
            resultat = await selecteur.save_file(
                dialog_title="Enregistrer mon affiche",
                file_name="profil_affiche.png",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["png"],
                src_bytes=affiche_bytes,
            )

            if resultat:
                notifier("Affiche enregistrée avec succès.")
            else:
                notifier(
                    "Vérifie le dossier Téléchargements de ton navigateur."
                )

        except Exception as erreur:
            notifier(
                f"Erreur d'enregistrement : {erreur}",
                succes=False,
            )

    bouton_enregistrer.on_click = enregistrer_affiche

    # ------------------------------------------------------
    # CARTES
    # ------------------------------------------------------

    def creer_carte(titre, icone, contenu):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(
                                    icone,
                                    color=BLEU,
                                    size=22,
                                ),
                                width=42,
                                height=42,
                                bgcolor="#EAF2FF",
                                border_radius=13,
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Text(
                                titre,
                                size=17,
                                weight=ft.FontWeight.BOLD,
                                color=TEXTE,
                                expand=True,
                            ),
                        ],
                        spacing=11,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(color=BORDURE, height=8),
                    contenu,
                ],
                spacing=14,
                tight=True,
            ),
            bgcolor=BLANC,
            padding=17,
            border_radius=20,
            border=ft.Border.all(1, BORDURE),
        )

    carte_formulaire = creer_carte(
        "Informations personnelles",
        ft.Icons.PERSON,
        ft.Column(
            controls=[
                champ_nom,
                champ_contact,
                champ_adresse,
                champ_groupe,
            ],
            spacing=13,
        ),
    )

    carte_photo = creer_carte(
        "Photo personnelle",
        ft.Icons.ADD_A_PHOTO,
        ft.Row(
            controls=[
                ft.Container(
                    content=apercu_photo,
                    width=125,
                    height=145,
                    bgcolor="#EAF0FA",
                    border_radius=14,
                    alignment=ft.Alignment.CENTER,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            "Choisis une photo nette.",
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=TEXTE,
                        ),
                        texte_photo,
                        ft.Button(
                            content="Importer une photo",
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=importer_photo,
                        ),
                    ],
                    spacing=10,
                    expand=True,
                ),
            ],
            spacing=13,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    carte_resultat = creer_carte(
        "Aperçu de l'affiche",
        ft.Icons.IMAGE,
        ft.Column(
            controls=[
                texte_resultat,
                ft.Container(
                    content=apercu_affiche,
                    alignment=ft.Alignment.CENTER,
                    padding=5,
                ),
                bouton_enregistrer,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=15,
        ),
    )

    # ------------------------------------------------------
    # EN-TÊTE ET MISE EN PAGE
    # ------------------------------------------------------

    entete = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.PERSON_PIN,
                        size=32,
                        color=BLANC,
                    ),
                    bgcolor=BLEU,
                    width=56,
                    height=56,
                    border_radius=17,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            "Profil Affiche",
                            size=25,
                            weight=ft.FontWeight.BOLD,
                            color=TEXTE,
                        ),
                        ft.Text(
                            "Crée ton affiche personnelle",
                            size=13,
                            color=GRIS,
                        ),
                    ],
                    spacing=3,
                    expand=True,
                ),
            ],
            spacing=13,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.only(
            left=18,
            right=18,
            top=22,
            bottom=18,
        ),
    )

    contenu = ft.Column(
        controls=[
            entete,
            ft.Container(
                content=ft.Column(
                    controls=[
                        banniere_message,
                        carte_formulaire,
                        carte_photo,
                        ft.Container(
                            content=bouton_generer,
                            padding=ft.Padding.symmetric(horizontal=2),
                        ),
                        carte_resultat,
                        ft.Container(
                            content=ft.Text(
                                "PROFIL AFFICHE • Création personnelle",
                                size=11,
                                color=GRIS,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            padding=ft.Padding.only(
                                top=5,
                                bottom=20,
                            ),
                        ),
                    ],
                    spacing=16,
                    expand=True,
                ),
                padding=ft.Padding.only(
                    left=15,
                    right=15,
                    bottom=20,
                ),
            ),
        ],
        spacing=0,
        expand=True,
    )

    page.add(
        ft.SafeArea(
            content=contenu,
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.run(main)
