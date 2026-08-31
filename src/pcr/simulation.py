"""Ce que la formule réglementaire ignore : le portefeuille fini.

**L'hypothèse cachée.** La formule du chapitre 5 suppose que la banque a une infinité de prêts, tous
minuscules. Sous cette hypothèse, la seule chose qui compte est la conjoncture : le hasard propre à
chaque emprunteur s'annule dans la moyenne. C'est ce qu'on appelle un portefeuille infiniment
granulaire.

**Ce que fait une vraie banque.** Elle a quelques centaines de gros dossiers d'entreprise, pas une
infinité. Le hasard propre à chaque emprunteur ne s'annule donc pas, et il ajoute du risque que la
formule ne compte pas. Ce risque en plus s'appelle le **risque de concentration**.

Ce module le mesure. Il tire cinq millions d'années possibles, chacune avec sa conjoncture
et ses défauts individuels, et regarde la perte de la millième pire année. Cette perte-là est le vrai
capital nécessaire. La différence avec la formule est ce que le régulateur ne compte pas.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import binom, norm

from .bale import CONFIANCE, capital_unitaire, correlation_entreprise

GRAINES = tuple(range(1, 11))   # les dix tirages indépendants sur lesquels le tableau est mesuré


@dataclass(frozen=True)
class Portefeuille:
    """Un portefeuille de prêts d'entreprise, décrit par ce qui suffit à le simuler."""

    montants: np.ndarray               # ce qui est prêté à chaque emprunteur
    pd_defaut: np.ndarray              # la probabilité de non-remboursement de chacun
    perte_en_cas_de_defaut: float = 0.40
    chiffre_affaires: float | None = 50.0

    @property
    def nombre(self) -> int:
        return len(self.montants)

    @property
    def total(self) -> float:
        return float(self.montants.sum())

    @property
    def parts(self) -> np.ndarray:
        return self.montants / self.total

    @property
    def concentration(self) -> float:
        """L'indice de Herfindahl : la somme des carrés des parts.

        Il vaut un sur le nombre de prêts quand ils sont tous de la même taille, et un quand un seul
        prêt fait tout le portefeuille. Son inverse se lit comme un « nombre de prêts équivalent » :
        un portefeuille de 500 prêts dont dix font la moitié se comporte comme s'il en avait bien
        moins.
        """
        return float((self.parts ** 2).sum())

    @property
    def nombre_equivalent(self) -> float:
        return 1.0 / self.concentration


def homogene(nombre: int, pd_defaut: float = 0.01, montant: float = 1.0,
             perte_en_cas_de_defaut: float = 0.40) -> Portefeuille:
    """Un portefeuille de prêts tous identiques : le cas le plus favorable à la formule."""
    return Portefeuille(montants=np.full(nombre, montant),
                        pd_defaut=np.full(nombre, pd_defaut),
                        perte_en_cas_de_defaut=perte_en_cas_de_defaut)


def concentre(nombre: int, part_des_dix_plus_gros: float = 0.5, pd_defaut: float = 0.01,
              perte_en_cas_de_defaut: float = 0.40) -> Portefeuille:
    """Un portefeuille où dix dossiers pèsent une part imposée du total.

    C'est la forme d'un vrai livre de banque commerciale : quelques gros clients, une longue traîne
    de petits. Le reste est réparti également entre les autres emprunteurs.
    """
    if nombre <= 10:
        raise ValueError("il faut plus de dix prêts pour en concentrer dix")
    montants = np.empty(nombre)
    montants[:10] = part_des_dix_plus_gros / 10.0
    montants[10:] = (1.0 - part_des_dix_plus_gros) / (nombre - 10)
    return Portefeuille(montants=montants, pd_defaut=np.full(nombre, pd_defaut),
                        perte_en_cas_de_defaut=perte_en_cas_de_defaut)


def capital_asymptotique(portefeuille: Portefeuille, echeance: float | None = None) -> float:
    """Le capital que la formule réglementaire exige, par dollar prêté.

    L'échéance est laissée à None par défaut : l'ajustement d'échéance couvre le risque que la note
    se dégrade, ce que la simulation ne modélise pas. Les comparer avec l'ajustement reviendrait à
    reprocher à la formule de couvrir quelque chose de plus.
    """
    correlation = correlation_entreprise(portefeuille.pd_defaut, portefeuille.chiffre_affaires)
    unitaire = capital_unitaire(portefeuille.pd_defaut, portefeuille.perte_en_cas_de_defaut,
                                correlation, echeance)
    return float((portefeuille.parts * unitaire).sum())


def _groupes(portefeuille: Portefeuille):
    """Les prêts rassemblés par couple identique de montant et de probabilité de défaut.

    C'est ce qui rend la simulation rapide. Une fois la conjoncture fixée, les emprunteurs font
    défaut indépendamment les uns des autres. Le nombre de défauts dans un groupe de prêts
    identiques suit donc une loi binomiale, et il se tire d'un coup au lieu d'être tiré prêt par
    prêt. Sur un portefeuille de mille prêts en deux groupes, cela remplace mille tirages par deux.
    """
    cles = {}
    for montant, pd_defaut in zip(portefeuille.montants, portefeuille.pd_defaut, strict=True):
        cles[(float(montant), float(pd_defaut))] = cles.get((float(montant), float(pd_defaut)), 0) + 1
    montants = np.array([k[0] for k in cles])
    pds = np.array([k[1] for k in cles])
    effectifs = np.array(list(cles.values()))
    return montants, pds, effectifs


def simuler(portefeuille: Portefeuille, tirages: int = 5_000_000, graine: int = 1) -> dict:
    """La perte du portefeuille sur des millions d'années possibles.

    Chaque année tirée a d'abord sa conjoncture, commune à tous les emprunteurs. Sachant cette
    conjoncture, chaque emprunteur fait défaut indépendamment des autres, avec une probabilité qui
    dépend de la conjoncture : le nombre de défauts d'un groupe de prêts identiques suit donc une loi
    binomiale. La perte de l'année est la somme des montants perdus.
    """
    rng = np.random.default_rng(graine)
    montants, pds, effectifs = _groupes(portefeuille)
    correlation = correlation_entreprise(pds, portefeuille.chiffre_affaires)
    seuils = norm.ppf(pds)
    racine, complement = np.sqrt(correlation), np.sqrt(1.0 - correlation)
    attendue = float((portefeuille.parts * portefeuille.pd_defaut).sum()
                     * portefeuille.perte_en_cas_de_defaut)

    pertes = np.empty(tirages)
    bloc = 500_000
    debut = 0
    while debut < tirages:
        taille = min(bloc, tirages - debut)
        conjoncture = rng.standard_normal((taille, 1))
        conditionnelles = norm.cdf((seuils - racine * conjoncture) / complement)
        defauts = rng.binomial(effectifs, conditionnelles)
        pertes[debut:debut + taille] = (defauts * montants).sum(axis=1)
        debut += taille
    pertes *= portefeuille.perte_en_cas_de_defaut / portefeuille.total

    quantile = float(np.quantile(pertes, CONFIANCE))
    return {"perte_attendue": attendue, "quantile": quantile, "capital_simule": quantile - attendue,
            "pertes": pertes, "groupes": len(effectifs)}


def erreur_type_du_quantile(pertes: np.ndarray, niveau: float = CONFIANCE) -> float:
    """De combien le quantile simulé peut se tromper, faute d'avoir tiré assez d'années.

    Le calcul passe par les rangs et non par une densité. Sur les pertes triées, le rang qui porte le
    quantile est aléatoire, et il suit une loi binomiale de paramètres le nombre de tirages et le
    niveau. Cette loi est exacte quelle que soit la loi des pertes. On lit donc les deux pertes triées
    dont les rangs bornent cette binomiale à 95 %, et la demi-largeur de leur intervalle, divisée par
    1,96, est l'erreur type cherchée.

    Cette voie évite l'estimation d'une densité, qui n'existe pas ici : la perte d'un portefeuille de
    prêts égaux ne prend qu'un nombre fini de valeurs. C'est aussi sa limite. Quand ces valeurs sont
    espacées, les deux rangs tombent sur la même, et la fonction rend zéro alors que le quantile
    saute encore d'une valeur à l'autre d'un tirage à l'autre. L'incertitude publiée dans
    `results/capital_par_taille.csv` est donc celle de `dispersion_du_capital`, mesurée sur dix
    tirages, et cette formule-ci ne sert qu'à la contrôler sur les portefeuilles fins.
    """
    n = len(pertes)
    tries = np.sort(pertes)
    bas = int(np.clip(binom.ppf(0.025, n, niveau), 0, n - 1))
    haut = int(np.clip(binom.ppf(0.975, n, niveau), 0, n - 1))
    return float((tries[haut] - tries[bas]) / (2.0 * norm.ppf(0.975)))


def dispersion_du_capital(portefeuille: Portefeuille, graines=GRAINES,
                          tirages: int = 5_000_000) -> dict:
    """Le capital simulé, mesuré sur plusieurs tirages indépendants plutôt que sur un seul.

    Un tirage unique donne un nombre dont on ignore la précision, et rien n'interdit qu'il soit le
    plus haut ou le plus bas de ceux qu'on aurait obtenus. La moyenne de plusieurs tirages est
    publiée à la place, et leur dispersion donne l'incertitude, mesurée et non calculée. L'erreur
    type rendue est celle de cette moyenne, donc la dispersion divisée par la racine du nombre de
    tirages.
    """
    valeurs = np.array([simuler(portefeuille, tirages=tirages, graine=g)["capital_simule"]
                        for g in graines])
    ecart_type = float(valeurs.std(ddof=1))
    return {"capital_simule": float(valeurs.mean()),
            "ecart_type_entre_graines": ecart_type,
            "erreur_type": ecart_type / float(np.sqrt(len(valeurs))),
            "valeurs": valeurs}
