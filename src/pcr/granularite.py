"""L'ajustement de granularité : une formule qui prétend rattraper ce que la règle oublie.

**L'idée.** La formule réglementaire donne la perte de la millième pire conjoncture, en supposant que
le hasard propre à chaque emprunteur a disparu dans la moyenne. Sur un portefeuille fini il ne
disparaît pas. L'ajustement de granularité est un terme correctif qui estime, sans simulation, de
combien il faut relever le capital.

**Comment il marche.** Autour de la mauvaise conjoncture, la perte du portefeuille se comporte comme
sa moyenne conditionnelle, plus un bruit dont on connaît la variance. L'ajustement est le premier
terme du développement qui tient compte de ce bruit. Il fait intervenir trois choses : la variance
de la perte sachant la conjoncture, la vitesse à laquelle la perte moyenne bouge quand la conjoncture
bouge, et la forme de la loi de la conjoncture.

Le comité de Bâle avait proposé un tel ajustement en 2001, puis l'a retiré de la règle finale. Ce
module l'implémente pour répondre à une question simple : rattrape-t-il vraiment l'écart que la
simulation mesure ?
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .bale import CONFIANCE, correlation_entreprise
from .simulation import Portefeuille

PAS = 1e-4      # le pas des dérivées numériques, en écarts types de conjoncture


def _conditionnelles(portefeuille: Portefeuille, mauvaise_conjoncture):
    """La perte moyenne et la variance de la perte, sachant l'état de l'économie.

    L'état est compté à l'envers : une valeur élevée est une mauvaise année. Ce retournement rend la
    perte croissante avec la variable, ce qui est la forme sous laquelle l'ajustement se démontre.
    """
    y = np.atleast_1d(np.asarray(mauvaise_conjoncture, dtype=float))[:, None]
    pds = portefeuille.pd_defaut[None, :]
    parts = portefeuille.parts[None, :]
    lgd = portefeuille.perte_en_cas_de_defaut
    correlation = correlation_entreprise(portefeuille.pd_defaut,
                                         portefeuille.chiffre_affaires)[None, :]
    conditionnelle = norm.cdf((norm.ppf(pds) + np.sqrt(correlation) * y)
                              / np.sqrt(1.0 - correlation))
    moyenne = (parts * lgd * conditionnelle).sum(axis=1)
    variance = (parts ** 2 * lgd ** 2 * conditionnelle * (1.0 - conditionnelle)).sum(axis=1)
    return moyenne, variance


def ajustement(portefeuille: Portefeuille, niveau: float = CONFIANCE, pas: float = PAS) -> dict:
    """Le supplément de capital dû au nombre fini de prêts, et ses trois pièces.

    Les dérivées sont prises numériquement par différences centrées : la formule analytique existe,
    mais elle change dès qu'on modifie la façon dont la sensibilité dépend de la probabilité de
    défaut, alors que la dérivée numérique reste juste dans tous les cas.
    """
    y = norm.ppf(niveau)
    grille = np.array([y - 2 * pas, y - pas, y, y + pas, y + 2 * pas])
    moyennes, variances = _conditionnelles(portefeuille, grille)

    derivee_moyenne = (moyennes[3] - moyennes[1]) / (2 * pas)
    if derivee_moyenne <= 0.0:
        raise ValueError("la perte doit croître avec la mauvaise conjoncture")

    def facteur(indice: int) -> float:
        """La quantité dont la dérivée porte l'ajustement : densité fois variance sur pente."""
        pente = (moyennes[indice + 1] - moyennes[indice - 1]) / (2 * pas)
        return float(norm.pdf(grille[indice]) * variances[indice] / pente)

    derivee = (facteur(3) - facteur(1)) / (2 * pas)
    supplement = -derivee / (2.0 * norm.pdf(y))
    return {"moyenne_conditionnelle": float(moyennes[2]),
            "variance_conditionnelle": float(variances[2]),
            "pente": float(derivee_moyenne),
            "ajustement": float(supplement)}


def capital_ajuste(portefeuille: Portefeuille, niveau: float = CONFIANCE) -> dict:
    """Le capital de la règle, celui de la règle plus l'ajustement, et la perte attendue.

    Le capital est toujours la perte de la millième pire année moins la perte attendue en temps
    ordinaire, celle-ci étant déjà couverte par les provisions comptables.
    """
    pieces = ajustement(portefeuille, niveau)
    attendue = float((portefeuille.parts * portefeuille.pd_defaut).sum()
                     * portefeuille.perte_en_cas_de_defaut)
    regle = pieces["moyenne_conditionnelle"] - attendue
    return {"perte_attendue": attendue, "capital_regle": regle,
            "supplement": pieces["ajustement"],
            "capital_ajuste": regle + pieces["ajustement"],
            "variance_conditionnelle": pieces["variance_conditionnelle"]}
