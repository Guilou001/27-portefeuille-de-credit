"""La formule de capital réglementaire, écrite depuis le chapitre 5 de la ligne directrice du BSIF.

**Le problème, en mots simples.** Une banque prête à des entreprises. Certaines ne rembourseront pas.
La banque doit donc garder de l'argent de côté, appelé du capital, pour absorber ces pertes sans
faire faillite. La question du régulateur est : combien ?

**La réponse réglementaire tient en une idée.** On suppose que toutes les entreprises du pays sont
touchées par une seule et même conjoncture. Quand l'économie va mal, elles vont toutes moins bien en
même temps, plus ou moins fortement selon leur sensibilité. Le capital exigé est alors la perte que
la banque subirait dans une conjoncture si mauvaise qu'elle n'arrive qu'une année sur mille.

**Trois nombres suffisent pour un prêt.** La probabilité qu'il ne soit pas remboursé, la part du
montant qui serait perdue en cas de non-remboursement, et sa sensibilité à la conjoncture. Le
troisième n'est pas estimé par la banque : le régulateur l'impose, et il le fait baisser quand la
probabilité de défaut monte, parce qu'une entreprise déjà fragile dépend plus de ses propres
difficultés que de la conjoncture générale.

Cette formule a un défaut connu, qui est le sujet du dépôt : elle suppose que la banque a une
infinité de tout petits prêts. Le module `simulation` mesure ce que cette hypothèse coûte.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

CONFIANCE = 0.999      # une année sur mille, le niveau imposé par la règle


def _part_faible_correlation(pd_defaut, vitesse: float) -> np.ndarray:
    """Le poids qui fait glisser la sensibilité de sa valeur haute vers sa valeur basse.

    Il vaut un quand la probabilité de défaut tend vers zéro et zéro quand elle est grande, avec une
    vitesse de bascule que le régulateur fixe : cinquante pour les entreprises, trente-cinq pour la
    clientèle de détail.
    """
    pd_defaut = np.asarray(pd_defaut, dtype=float)
    return (1.0 - np.exp(-vitesse * pd_defaut)) / (1.0 - np.exp(-vitesse))


def correlation_entreprise(pd_defaut, chiffre_affaires: float | None = None) -> np.ndarray:
    """La sensibilité d'un prêt d'entreprise à la conjoncture, entre 12 % et 24 %.

    L'ajustement de taille retranche jusqu'à quatre points pour les entreprises dont le chiffre
    d'affaires du groupe est petit : une PME dépend davantage de son propre sort que du cycle.
    L'ajustement est plein sous 5 millions et nul au-dessus de 50.
    """
    part = _part_faible_correlation(pd_defaut, 50.0)
    correlation = 0.12 * part + 0.24 * (1.0 - part)
    if chiffre_affaires is not None:
        borne = min(max(float(chiffre_affaires), 5.0), 50.0)
        correlation = correlation - 0.04 * (1.0 - (borne - 5.0) / 45.0)
    return correlation


def correlation_detail(pd_defaut) -> np.ndarray:
    """La sensibilité d'un prêt de détail hors habitation, entre 3 % et 16 %."""
    part = _part_faible_correlation(pd_defaut, 35.0)
    return 0.03 * part + 0.16 * (1.0 - part)


def ajustement_echeance(pd_defaut, echeance: float) -> np.ndarray:
    """Le supplément pour les prêts longs : plus l'échéance est lointaine, plus la note peut se
    dégrader avant le remboursement, et ce risque de dégradation coûte du capital."""
    b = (0.11852 - 0.05478 * np.log(np.asarray(pd_defaut, dtype=float))) ** 2
    return (1.0 + (echeance - 2.5) * b) / (1.0 - 1.5 * b)


def capital_unitaire(pd_defaut, perte_en_cas_de_defaut, correlation, echeance=None) -> np.ndarray:
    """Le capital exigé pour un dollar prêté, sous la formule dite asymptotique.

    Le coeur est la perte que subirait la banque dans une conjoncture d'une année sur mille. On en
    retranche la perte attendue en temps normal, qui est déjà couverte par les provisions
    comptables : le capital ne couvre que la surprise.
    """
    pd_defaut = np.asarray(pd_defaut, dtype=float)
    correlation = np.asarray(correlation, dtype=float)
    conditionnel = norm.cdf((1.0 - correlation) ** -0.5 * norm.ppf(pd_defaut)
                            + (correlation / (1.0 - correlation)) ** 0.5 * norm.ppf(CONFIANCE))
    capital = perte_en_cas_de_defaut * (conditionnel - pd_defaut)
    if echeance is not None:
        capital = capital * ajustement_echeance(pd_defaut, echeance)
    return capital


def poids_entreprise(pd_defaut, perte_en_cas_de_defaut=0.40, echeance: float = 2.5,
                     chiffre_affaires: float | None = None) -> np.ndarray:
    """Le poids de risque d'un prêt d'entreprise, en pourcentage du montant prêté."""
    correlation = correlation_entreprise(pd_defaut, chiffre_affaires)
    return 1250.0 * capital_unitaire(pd_defaut, perte_en_cas_de_defaut, correlation, echeance)


def poids_habitation(pd_defaut, perte_en_cas_de_defaut=0.45) -> np.ndarray:
    """Le poids de risque d'un prêt à l'habitation. Sa sensibilité est figée à 15 %, et il n'y a
    aucun ajustement d'échéance, la règle considérant le bien immobilier comme la vraie garantie."""
    return 1250.0 * capital_unitaire(pd_defaut, perte_en_cas_de_defaut, 0.15)


def poids_detail(pd_defaut, perte_en_cas_de_defaut=0.45) -> np.ndarray:
    """Le poids de risque d'un prêt de détail hors habitation."""
    return 1250.0 * capital_unitaire(pd_defaut, perte_en_cas_de_defaut, correlation_detail(pd_defaut))


def poids_renouvelable(pd_defaut, perte_en_cas_de_defaut=0.50) -> np.ndarray:
    """Le poids de risque d'un crédit renouvelable, une carte de crédit par exemple. Sa sensibilité
    est figée à 4 %, la plus basse de toutes : ces pertes sont surtout individuelles."""
    return 1250.0 * capital_unitaire(pd_defaut, perte_en_cas_de_defaut, 0.04)


def perte_conditionnelle(pd_defaut, perte_en_cas_de_defaut, correlation, facteur: float) -> np.ndarray:
    """La perte moyenne d'un prêt pour une conjoncture donnée.

    Le facteur est l'état de l'économie, mesuré en écarts types : zéro est une année ordinaire, moins
    trois une année très mauvaise. C'est la brique que la simulation empile pour construire un
    portefeuille entier.
    """
    pd_defaut = np.asarray(pd_defaut, dtype=float)
    correlation = np.asarray(correlation, dtype=float)
    seuil = (norm.ppf(pd_defaut) - np.sqrt(correlation) * facteur) / np.sqrt(1.0 - correlation)
    return perte_en_cas_de_defaut * norm.cdf(seuil)
