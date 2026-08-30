"""La règle recalculée contre l'annexe du BSIF, et la simulation contre ses propres identités."""

import numpy as np
import pytest
from scipy.stats import norm

from pcr.bale import (
    CONFIANCE,
    capital_unitaire,
    correlation_detail,
    correlation_entreprise,
    perte_conditionnelle,
    poids_entreprise,
    poids_habitation,
)
from pcr.granularite import ajustement, capital_ajuste
from pcr.reference import (
    CASE_DIVERGENTE,
    CHIFFRE_AFFAIRES_TABLEAU,
    CHIFFRE_AFFAIRES_TEXTE,
    POIDS_BSIF,
    cases_hors_tolerance,
    poids_calcules,
)
from pcr.simulation import capital_asymptotique, concentre, homogene, simuler


def test_cent_quarante_trois_des_cent_quarante_quatre_cases_sont_retrouvees():
    """Le test qui porte le dépôt : la règle du chapitre 5, appliquée aux dix-huit probabilités et
    aux huit types de prêts de l'annexe, retrouve tout sauf une case."""
    rates = cases_hors_tolerance(tolerance=0.01)
    assert len(rates) == 1
    assert rates[0]["colonne"] == "Prêt à l'habitation, perte 45 %"
    assert rates[0]["probabilite_pct"] == pytest.approx(6.0)


def test_la_case_qui_manque_est_celle_que_bale_imprime_autrement():
    """Le BSIF imprime 165,52 %, le comité de Bâle imprime 162,52 %, et notre calcul donne 162,52 %.
    Le BSIF a donc mal recopié un chiffre en le transcrivant."""
    calcule = poids_calcules()[CASE_DIVERGENTE["ligne"], CASE_DIVERGENTE["colonne"]]
    assert POIDS_BSIF[CASE_DIVERGENTE["ligne"], CASE_DIVERGENTE["colonne"]] == CASE_DIVERGENTE["bsif"]
    assert calcule == pytest.approx(CASE_DIVERGENTE["bale"], abs=0.01)


def test_le_texte_du_bsif_contredit_son_propre_tableau():
    """Le paragraphe explicatif annonce un chiffre d'affaires de 7,5 millions, l'en-tête du tableau
    en annonce 5. Les nombres imprimés sont ceux de 5 : avec 7,5, dix-huit cases de plus tombent."""
    avec_texte = cases_hors_tolerance(chiffre_affaires_petite_entreprise=CHIFFRE_AFFAIRES_TEXTE)
    avec_tableau = cases_hors_tolerance(chiffre_affaires_petite_entreprise=CHIFFRE_AFFAIRES_TABLEAU)
    assert len(avec_tableau) == 1
    assert len(avec_texte) == 19


def test_la_sensibilite_a_la_conjoncture_baisse_quand_le_risque_monte():
    """Le sens voulu par la règle : une entreprise déjà fragile dépend plus de son propre sort que
    du cycle. La sensibilité va donc de 24 % vers 12 %, jamais l'inverse."""
    grille = np.array([0.0005, 0.01, 0.05, 0.20])
    valeurs = correlation_entreprise(grille)
    assert np.all(np.diff(valeurs) < 0.0)
    assert 0.12 <= valeurs[-1] < valeurs[0] <= 0.24


def test_l_ajustement_de_taille_retranche_quatre_points_au_plus():
    """Il est plein sous cinq millions de chiffre d'affaires et nul au-dessus de cinquante."""
    grande = correlation_entreprise(0.01, 50.0)
    petite = correlation_entreprise(0.01, 5.0)
    tres_petite = correlation_entreprise(0.01, 1.0)
    assert grande - petite == pytest.approx(0.04)
    assert tres_petite == pytest.approx(petite)


def test_la_sensibilite_du_detail_reste_entre_trois_et_seize_pour_cent():
    valeurs = correlation_detail(np.array([1e-5, 0.01, 0.5]))
    assert 0.03 <= valeurs[-1] < valeurs[0] <= 0.16


def test_le_capital_ne_couvre_que_la_surprise():
    """La perte attendue en temps ordinaire est retranchée : elle est déjà dans les provisions
    comptables, et la compter deux fois doublerait le coût du crédit."""
    pd_defaut, lgd = 0.02, 0.45
    correlation = correlation_entreprise(pd_defaut)
    capital = capital_unitaire(pd_defaut, lgd, correlation)
    # la mauvaise conjoncture est celle qui n'arrive qu'une année sur mille, donc très en dessous
    # de la moyenne : le signe compte, et l'inverser rendrait un capital négatif
    mauvaise_annee = -norm.ppf(CONFIANCE)
    perte_a_la_mauvaise_annee = perte_conditionnelle(pd_defaut, lgd, correlation, mauvaise_annee)
    assert capital == pytest.approx(perte_a_la_mauvaise_annee - pd_defaut * lgd, rel=1e-9)


def test_le_poids_croit_avec_la_perte_en_cas_de_defaut_proportionnellement():
    """Sans ajustement d'échéance, doubler la perte en cas de défaut double le poids."""
    assert poids_habitation(0.01, 0.50) == pytest.approx(2.0 * poids_habitation(0.01, 0.25))


def test_le_pret_long_coute_plus_cher_que_le_pret_court():
    court = poids_entreprise(0.01, 0.40, 1.0, 50.0)
    long = poids_entreprise(0.01, 0.40, 5.0, 50.0)
    assert long > court


def test_la_simulation_rejoint_la_regle_quand_les_prets_sont_tres_nombreux():
    """C'est la définition même de la formule : elle est la limite du portefeuille quand le nombre
    de prêts tend vers l'infini. Sur cinq mille prêts, l'écart doit tenir dans le bruit de tirage."""
    portefeuille = homogene(5000)
    mesures = simuler(portefeuille, tirages=1_000_000)
    regle = capital_asymptotique(portefeuille)
    assert mesures["capital_simule"] == pytest.approx(regle, abs=0.002)


def test_moins_de_prets_exige_toujours_plus_de_capital():
    """Le résultat du dépôt, dans sa forme la plus simple : la règle est un plancher, jamais un
    plafond."""
    regle = capital_asymptotique(homogene(1000))
    petit = simuler(homogene(50), tirages=1_000_000)["capital_simule"]
    grand = simuler(homogene(1000), tirages=1_000_000)["capital_simule"]
    assert petit > grand > regle * 0.99


def test_la_concentration_se_lit_dans_le_nombre_equivalent():
    """Cinq cents prêts dont dix font la moitié se comportent comme un portefeuille de trente-neuf
    prêts égaux, et l'indice le dit sans qu'on ait à simuler."""
    egal = homogene(500)
    concentre_ = concentre(500, 0.5)
    assert egal.nombre_equivalent == pytest.approx(500.0)
    assert 35 < concentre_.nombre_equivalent < 45


def test_dix_prets_ne_peuvent_pas_etre_concentres_sur_dix():
    with pytest.raises(ValueError, match="plus de dix"):
        concentre(10)


def test_l_ajustement_de_granularite_tend_vers_zero_avec_la_taille():
    """Il corrige un défaut qui n'existe que sur un portefeuille fini : sur un portefeuille immense
    il doit s'effacer."""
    petit = ajustement(homogene(50))["ajustement"]
    grand = ajustement(homogene(10_000))["ajustement"]
    assert petit > grand > 0.0
    assert grand < 0.0005


def test_l_ajustement_rapproche_la_regle_de_la_verite():
    """Sur un portefeuille concentré, la règle plus l'ajustement doit être plus proche de la
    simulation que la règle seule."""
    portefeuille = concentre(500, 0.5)
    vrai = simuler(portefeuille, tirages=2_000_000)["capital_simule"]
    regle = capital_asymptotique(portefeuille)
    ajuste = capital_ajuste(portefeuille)["capital_ajuste"]
    assert abs(ajuste - vrai) < abs(regle - vrai)
    assert ajuste > regle
