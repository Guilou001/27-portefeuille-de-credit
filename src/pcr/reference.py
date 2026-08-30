"""Les 144 poids de risque publiés par le BSIF, et les deux endroits où son document se contredit.

Le chapitre 5 de la ligne directrice sur les normes de fonds propres se termine par une annexe qui
donne, pour dix-huit niveaux de probabilité de défaut et huit types de prêts, le poids de risque que
la formule doit produire. C'est le point de repère du dépôt : un code qui retrouve ces 144 cases
applique bien la règle canadienne.

Deux contradictions ont été relevées en les recalculant, et toutes deux se tranchent en allant voir
la source, la table équivalente du comité de Bâle, dont le BSIF reprend les chiffres.
"""

from __future__ import annotations

import numpy as np

URL_BSIF = "https://www.osfi-bsif.gc.ca/sites/default/files/documents/2026-car-nfp-chap5-en.pdf"
URL_BALE = ("https://www.bis.org/basel_framework/chapter/CRE/99.htm"
            "?inforce=20230101&published=20200327")

PROBABILITES = np.array([0.0005, 0.0010, 0.0025, 0.0040, 0.0050, 0.0075, 0.0100, 0.0130, 0.0150,
                         0.0200, 0.0250, 0.0300, 0.0400, 0.0500, 0.0600, 0.1000, 0.1500, 0.2000])

# Les huit colonnes de l'annexe, dans l'ordre du document.
COLONNES = [
    ("Entreprise, chiffre d'affaires 50 M$", "entreprise", 0.40, 50.0),
    ("Entreprise, chiffre d'affaires 5 M$", "entreprise", 0.40, 5.0),
    ("Prêt à l'habitation, perte 45 %", "habitation", 0.45, None),
    ("Prêt à l'habitation, perte 25 %", "habitation", 0.25, None),
    ("Détail hors habitation, perte 45 %", "detail", 0.45, None),
    ("Détail hors habitation, perte 85 %", "detail", 0.85, None),
    ("Crédit renouvelable, perte 50 %", "renouvelable", 0.50, None),
    ("Crédit renouvelable, perte 85 %", "renouvelable", 0.85, None),
]

# Le tableau tel qu'il est imprimé dans le document du BSIF, en pourcentage.
POIDS_BSIF = np.array([
    [17.47, 13.69, 6.23, 3.46, 6.63, 12.52, 1.68, 2.86],
    [26.36, 20.71, 10.69, 5.94, 11.16, 21.08, 3.01, 5.12],
    [43.97, 34.68, 21.30, 11.83, 21.15, 39.96, 6.40, 10.88],
    [55.75, 43.99, 29.94, 16.64, 28.42, 53.69, 9.34, 15.88],
    [61.88, 48.81, 35.08, 19.49, 32.36, 61.13, 11.16, 18.97],
    [73.58, 57.91, 46.46, 25.81, 40.10, 75.74, 15.33, 26.06],
    [82.06, 64.35, 56.40, 31.33, 45.77, 86.46, 19.14, 32.53],
    [89.73, 70.02, 67.00, 37.22, 50.80, 95.95, 23.35, 39.70],
    [93.86, 72.99, 73.45, 40.80, 53.37, 100.81, 25.99, 44.19],
    [102.09, 78.71, 87.94, 48.85, 57.99, 109.53, 32.14, 54.63],
    [108.58, 83.05, 100.64, 55.91, 60.90, 115.03, 37.75, 64.18],
    [114.17, 86.74, 111.99, 62.22, 62.79, 118.61, 42.96, 73.03],
    [124.07, 93.37, 131.63, 73.13, 65.01, 122.80, 52.40, 89.08],
    [133.20, 99.79, 148.22, 82.35, 66.42, 125.45, 60.83, 103.41],
    [141.88, 106.21, 165.52, 90.29, 67.73, 127.94, 68.45, 116.37],
    [171.63, 130.23, 204.41, 113.56, 75.54, 142.69, 93.21, 158.47],
    [196.92, 152.81, 235.72, 130.96, 88.60, 167.36, 115.43, 196.23],
    [211.76, 167.48, 253.12, 140.62, 100.28, 189.41, 131.09, 222.86],
])

# La seule case où le comité de Bâle et le BSIF impriment deux nombres différents. Vérifié le
# 2026-08-30 en lisant les deux tables : prêt à l'habitation, perte de 45 %, probabilité de 6,00 %.
CASE_DIVERGENTE = {"ligne": 14, "colonne": 2, "bsif": 165.52, "bale": 162.52}

# La seconde contradiction est interne au document du BSIF. Son paragraphe 2 écrit que le chiffre
# d'affaires retenu pour la deuxième colonne est de 7,5 millions, alors que l'en-tête du tableau
# écrit 5 et que les nombres imprimés sont ceux d'un chiffre d'affaires de 5. Le document de Bâle
# écrit 5 partout, en millions d'euros.
CHIFFRE_AFFAIRES_TEXTE = 7.5
CHIFFRE_AFFAIRES_TABLEAU = 5.0


def poids_calcules(chiffre_affaires_petite_entreprise: float = CHIFFRE_AFFAIRES_TABLEAU
                   ) -> np.ndarray:
    """Les 144 poids recalculés depuis les formules du chapitre 5."""
    from .bale import poids_detail, poids_entreprise, poids_habitation, poids_renouvelable

    sortie = np.empty((len(PROBABILITES), len(COLONNES)))
    for j, (_, genre, lgd, taille) in enumerate(COLONNES):
        if genre == "entreprise":
            ca = 50.0 if taille == 50.0 else chiffre_affaires_petite_entreprise
            sortie[:, j] = poids_entreprise(PROBABILITES, lgd, 2.5, ca)
        elif genre == "habitation":
            sortie[:, j] = poids_habitation(PROBABILITES, lgd)
        elif genre == "detail":
            sortie[:, j] = poids_detail(PROBABILITES, lgd)
        else:
            sortie[:, j] = poids_renouvelable(PROBABILITES, lgd)
    return sortie


def ecarts(chiffre_affaires_petite_entreprise: float = CHIFFRE_AFFAIRES_TABLEAU) -> np.ndarray:
    """L'écart entre le recalculé et l'imprimé, en points de pourcentage."""
    return poids_calcules(chiffre_affaires_petite_entreprise) - POIDS_BSIF


def cases_hors_tolerance(tolerance: float = 0.01,
                         chiffre_affaires_petite_entreprise: float = CHIFFRE_AFFAIRES_TABLEAU
                         ) -> list[dict]:
    """Les cases que le recalcul ne retrouve pas, avec leur coordonnée et leur écart."""
    ecart = ecarts(chiffre_affaires_petite_entreprise)
    lignes = []
    for i in range(ecart.shape[0]):
        for j in range(ecart.shape[1]):
            if abs(ecart[i, j]) > tolerance:
                lignes.append({"probabilite_pct": 100 * PROBABILITES[i], "colonne": COLONNES[j][0],
                               "imprime": POIDS_BSIF[i, j],
                               "recalcule": POIDS_BSIF[i, j] + ecart[i, j], "ecart": ecart[i, j]})
    return lignes
