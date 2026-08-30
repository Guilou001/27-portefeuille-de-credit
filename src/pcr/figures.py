"""Cinq figures, chacune portant un résultat du dépôt."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from gvf.style import GRIS, OKABE_ITO, appliquer, enregistrer, formateur, fr

from .granularite import capital_ajuste
from .reference import COLONNES, POIDS_BSIF, PROBABILITES, ecarts
from .simulation import capital_asymptotique, concentre, erreur_type_du_quantile, homogene, simuler

DEST = Path("results/figures")


def fig_courbes(dest: Path = DEST) -> dict:
    """Les quatre courbes de poids de risque, recalculées, avec les points publiés par le BSIF."""
    appliquer()
    from .bale import poids_detail, poids_entreprise, poids_habitation, poids_renouvelable

    grille = np.logspace(np.log10(0.0003), np.log10(0.25), 400)
    courbes = [("Entreprise, perte 40 %", poids_entreprise(grille, 0.40, 2.5, 50.0), 0),
               ("Prêt à l'habitation, perte 45 %", poids_habitation(grille, 0.45), 2),
               ("Détail hors habitation, perte 45 %", poids_detail(grille, 0.45), 4),
               ("Crédit renouvelable, perte 50 %", poids_renouvelable(grille, 0.50), 6)]

    fig, ax = plt.subplots(figsize=(9.4, 5.6))
    for rang, (nom, valeurs, colonne) in enumerate(courbes):
        ax.plot(100 * grille, valeurs, color=OKABE_ITO[rang], linewidth=2.0, label=nom)
        ax.scatter(100 * PROBABILITES, POIDS_BSIF[:, colonne], s=22, color=OKABE_ITO[rang],
                   zorder=5, edgecolors="white", linewidths=0.5)
    ax.set_xscale("log")
    ax.set_xlabel("Probabilité qu'un emprunteur ne rembourse pas, sur un an (%, échelle "
                  "logarithmique)")
    ax.set_ylabel("Capital exigé, en % du montant prêté\n(poids de risque)")
    ax.yaxis.set_major_formatter(formateur(0, " %"))
    ax.legend(loc="upper left")
    ax.set_title("Les quatre courbes de la règle, et les 72 points publiés par le BSIF qui tombent "
                 "dessus")
    enregistrer(fig, dest, "courbes_reglementaires")
    plt.close(fig)
    return {"points": int(POIDS_BSIF.shape[0] * 4)}


def fig_verification(dest: Path = DEST) -> dict:
    """Les 144 cases de l'annexe, écart au chiffre imprimé, en carte."""
    appliquer()
    ecart = ecarts()
    plafond = float(np.abs(ecart).max())

    fig, ax = plt.subplots(figsize=(10.6, 6.2))
    image = ax.imshow(np.abs(ecart), cmap="Blues", vmin=0.0, vmax=plafond, aspect="auto")
    for i in range(ecart.shape[0]):
        for j in range(ecart.shape[1]):
            if abs(ecart[i, j]) > 0.01:
                ax.text(j, i, fr(ecart[i, j], 2), ha="center", va="center", fontsize=9,
                        color="white", weight="bold")
    courts = ["Entreprise\n50 M$", "Entreprise\n5 M$", "Habitation\nperte 45 %",
              "Habitation\nperte 25 %", "Détail\nperte 45 %", "Détail\nperte 85 %",
              "Renouvelable\nperte 50 %", "Renouvelable\nperte 85 %"]
    ax.set_xticks(range(len(COLONNES)), courts, fontsize=8)
    ax.set_yticks(range(len(PROBABILITES)), [fr(100 * p, 2) + " %" for p in PROBABILITES],
                  fontsize=8)
    ax.set_ylabel("Probabilité de non-remboursement")
    ax.grid(False)
    barre = fig.colorbar(image, ax=ax, fraction=0.03)
    barre.set_label("Écart au chiffre imprimé, en points de pourcentage", fontsize=8.5)
    hors = int((np.abs(ecart) > 0.01).sum())
    ax.set_title(f"{ecart.size - hors} des {ecart.size} cases sont retrouvées ; la seule qui "
                 "manque est une coquille du BSIF")
    enregistrer(fig, dest, "verification_annexe")
    plt.close(fig)
    return {"hors_tolerance": hors, "ecart_max": plafond}


def fig_capital_par_taille(table, dest: Path = DEST) -> dict:
    """Le capital selon le nombre de prêts : ce que la règle exige, ce qu'il faudrait, et la
    correction."""
    appliquer()
    # trié par nombre équivalent : la table mêle les portefeuilles homogènes et les concentrés, et
    # une ligne tracée dans l'ordre du tableau reviendrait sur elle-même
    table = table.sort_values("nombre_equivalent")
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    ax.plot(table["nombre_equivalent"], 100 * table["capital_simule"], marker="o", markersize=5,
            color=OKABE_ITO[3], linewidth=2.0, label="ce qu'il faudrait vraiment (simulation)")
    ax.fill_between(table["nombre_equivalent"],
                    100 * (table["capital_simule"] - 1.96 * table["erreur_type"]),
                    100 * (table["capital_simule"] + 1.96 * table["erreur_type"]),
                    color=OKABE_ITO[3], alpha=0.18, linewidth=0)
    ax.plot(table["nombre_equivalent"], 100 * table["capital_ajuste"], marker="s", markersize=4,
            color=OKABE_ITO[2], linewidth=1.8, linestyle="--",
            label="la règle plus l'ajustement de granularité")
    ax.axhline(100 * table["capital_regle"].iloc[0], color=OKABE_ITO[0], linewidth=2.0,
               label="ce que la règle exige, quel que soit le nombre de prêts")
    ax.set_xscale("log")
    ax.set_xlabel("Nombre de prêts équivalent du portefeuille (échelle logarithmique)")
    ax.set_ylabel("Capital exigé, en % du montant prêté")
    ax.yaxis.set_major_formatter(formateur(1, " %"))
    ax.legend(loc="upper right")
    pire = table.loc[table["ecart_pct"].idxmax()]
    ax.set_title("Moins la banque a de prêts, plus la règle manque de capital : jusqu'à "
                 f"{fr(pire['ecart_pct'], 0)} % sur ce portefeuille")
    enregistrer(fig, dest, "capital_par_taille")
    plt.close(fig)
    return {"ecart_max_pct": float(table["ecart_pct"].max())}


def fig_rattrapage(table, dest: Path = DEST) -> dict:
    """La part de l'écart que l'ajustement de granularité rattrape, cas par cas."""
    appliquer()
    fiable = table[table["ecart"] > 3.0 * table["erreur_type"]]
    positions = np.arange(len(fiable))

    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.barh(positions, fiable["part_rattrapee_pct"], color=OKABE_ITO[2], height=0.62)
    ax.axvline(100, color=GRIS, linewidth=1.2, linestyle="--")
    ax.annotate("rattrapage complet", (100, len(fiable) - 0.4), xytext=(-6, 0),
                textcoords="offset points", ha="right", fontsize=9, color=GRIS)
    for i, (_, ligne) in enumerate(fiable.iterrows()):
        ax.annotate(f"la règle manque {fr(ligne['ecart_pct'], 0)} %",
                    (ligne["part_rattrapee_pct"], i), xytext=(-8, 0), textcoords="offset points",
                    ha="right", va="center", fontsize=8.5, color="white")
    ax.set_yticks(positions, fiable["portefeuille"], fontsize=9)
    ax.set_xlim(0, 118)
    ax.set_xlabel("Part de l'écart que l'ajustement de granularité rattrape (%)")
    ax.set_title(f"L'ajustement rattrape {fr(fiable['part_rattrapee_pct'].min(), 0)} à "
                 f"{fr(fiable['part_rattrapee_pct'].max(), 0)} % de ce que la règle manque")
    enregistrer(fig, dest, "rattrapage")
    plt.close(fig)
    return {"minimum_pct": float(fiable["part_rattrapee_pct"].min()),
            "maximum_pct": float(fiable["part_rattrapee_pct"].max())}


def fig_distributions(dest: Path = DEST) -> dict:
    """La perte du portefeuille sur des millions d'années, pour trois tailles."""
    appliquer()
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    resultats = {}
    for rang, (nom, portefeuille) in enumerate(
            [("5 000 prêts identiques", homogene(5000)),
             ("200 prêts identiques", homogene(200)),
             ("500 prêts, dix font la moitié", concentre(500, 0.5))]):
        mesures = simuler(portefeuille)
        pertes = 100 * mesures["pertes"]
        ax.hist(pertes, bins=np.linspace(0, 12, 240), density=True, histtype="step",
                linewidth=1.9, color=OKABE_ITO[rang], label=nom)
        ax.axvline(100 * mesures["quantile"], color=OKABE_ITO[rang], linewidth=1.2, linestyle=":")
        resultats[nom] = {"quantile_pct": 100 * mesures["quantile"]}
    ax.set_yscale("log")
    ax.set_xlim(0, 12)
    ax.set_xlabel("Perte de l'année, en % du montant prêté")
    ax.set_ylabel("Densité (échelle logarithmique)")
    ax.legend(loc="upper right")
    ax.set_title("Trois portefeuilles de même qualité moyenne : les traits pointillés marquent la "
                 "millième pire année")
    enregistrer(fig, dest, "distributions")
    plt.close(fig)
    return resultats


def table_par_taille():
    """Le tableau qui nourrit deux des figures et le README."""
    import pandas as pd

    cas = [("5 000 prêts identiques", homogene(5000)), ("2 000 prêts identiques", homogene(2000)),
           ("1 000 prêts identiques", homogene(1000)), ("500 prêts identiques", homogene(500)),
           ("200 prêts identiques", homogene(200)), ("100 prêts identiques", homogene(100)),
           ("50 prêts identiques", homogene(50)),
           ("500 prêts, dix font 30 %", concentre(500, 0.3)),
           ("500 prêts, dix font 50 %", concentre(500, 0.5))]
    lignes = []
    for nom, portefeuille in cas:
        mesures = simuler(portefeuille)
        ajuste = capital_ajuste(portefeuille)
        regle = capital_asymptotique(portefeuille)
        ecart = mesures["capital_simule"] - regle
        reste = mesures["capital_simule"] - ajuste["capital_ajuste"]
        lignes.append({
            "portefeuille": nom, "nombre": portefeuille.nombre,
            "nombre_equivalent": portefeuille.nombre_equivalent,
            "capital_regle": regle, "capital_simule": mesures["capital_simule"],
            "capital_ajuste": ajuste["capital_ajuste"],
            "erreur_type": erreur_type_du_quantile(mesures["pertes"]),
            "ecart": ecart, "ecart_pct": 100.0 * ecart / regle,
            "reste_apres_ajustement": reste,
            "part_rattrapee_pct": 100.0 * (1.0 - reste / ecart) if abs(ecart) > 1e-9 else np.nan,
        })
    return pd.DataFrame(lignes)
