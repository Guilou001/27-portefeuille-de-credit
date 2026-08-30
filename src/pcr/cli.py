"""Les commandes du dépôt. Chaque chiffre du README sort d'une de ces commandes, dans `results/`."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer

from .reference import (
    CASE_DIVERGENTE,
    CHIFFRE_AFFAIRES_TABLEAU,
    CHIFFRE_AFFAIRES_TEXTE,
    COLONNES,
    POIDS_BSIF,
    PROBABILITES,
    URL_BALE,
    URL_BSIF,
    cases_hors_tolerance,
    poids_calcules,
)

app = typer.Typer(add_completion=False, help=__doc__)
RESULTATS = Path("results")


def _ecrire(table: pd.DataFrame, nom: str) -> Path:
    RESULTATS.mkdir(parents=True, exist_ok=True)
    chemin = RESULTATS / nom
    table.to_csv(chemin, index=False)
    typer.echo(f"écrit {chemin}")
    return chemin


@app.command()
def annexe():
    """Recalculer les 144 poids de risque de l'annexe du BSIF et écrire les écarts."""
    calcules = poids_calcules()
    lignes = []
    for i, probabilite in enumerate(PROBABILITES):
        for j, (nom, *_) in enumerate(COLONNES):
            lignes.append({"probabilite_pct": 100 * probabilite, "colonne": nom,
                           "imprime_bsif": POIDS_BSIF[i, j], "recalcule": calcules[i, j],
                           "ecart": calcules[i, j] - POIDS_BSIF[i, j]})
    _ecrire(pd.DataFrame(lignes), "annexe_bsif.csv")
    rates = cases_hors_tolerance()
    typer.echo(f"cases : {len(lignes)}, hors tolérance : {len(rates)}")
    for r in rates:
        typer.echo(f"  {r['colonne']}, probabilité {r['probabilite_pct']:.2f} % : "
                   f"imprimé {r['imprime']:.2f} %, recalculé {r['recalcule']:.2f} %")
    typer.echo(f"source BSIF : {URL_BSIF}")


@app.command()
def coquilles():
    """Trancher les deux contradictions du document du BSIF, en allant voir la table de Bâle."""
    lignes = [
        {"contradiction": "poids du prêt à l'habitation, perte 45 %, probabilité 6,00 %",
         "imprime_bsif": CASE_DIVERGENTE["bsif"], "imprime_bale": CASE_DIVERGENTE["bale"],
         "recalcule": float(poids_calcules()[CASE_DIVERGENTE["ligne"], CASE_DIVERGENTE["colonne"]]),
         "verdict": "le BSIF a mal recopié Bâle"},
    ]
    avec_texte = cases_hors_tolerance(chiffre_affaires_petite_entreprise=CHIFFRE_AFFAIRES_TEXTE)
    avec_tableau = cases_hors_tolerance(chiffre_affaires_petite_entreprise=CHIFFRE_AFFAIRES_TABLEAU)
    lignes.append({
        "contradiction": "chiffre d'affaires de la deuxième colonne",
        "imprime_bsif": CHIFFRE_AFFAIRES_TEXTE, "imprime_bale": CHIFFRE_AFFAIRES_TABLEAU,
        "recalcule": CHIFFRE_AFFAIRES_TABLEAU,
        "verdict": f"le texte dit {CHIFFRE_AFFAIRES_TEXTE} M$ et laisse "
                   f"{len(avec_texte)} cases fausses ; l'en-tête dit "
                   f"{CHIFFRE_AFFAIRES_TABLEAU:.0f} et n'en laisse que {len(avec_tableau)}"})
    _ecrire(pd.DataFrame(lignes), "coquilles.csv")
    for ligne in lignes:
        typer.echo(f"- {ligne['contradiction']} : {ligne['verdict']}")
    typer.echo(f"source Bâle : {URL_BALE}")


@app.command()
def concentration():
    """Mesurer ce que la règle manque sur des portefeuilles finis, et ce que l'ajustement rattrape."""
    from .figures import table_par_taille

    table = table_par_taille()
    _ecrire(table, "capital_par_taille.csv")
    for _, ligne in table.iterrows():
        typer.echo(f"{ligne['portefeuille']:26s} règle {100*ligne['capital_regle']:.3f} %  "
                   f"vrai {100*ligne['capital_simule']:.3f} %  manque "
                   f"{ligne['ecart_pct']:5.1f} %  rattrapé {ligne['part_rattrapee_pct']:5.0f} %")


@app.command()
def figures():
    """Les cinq figures, en PNG pour le README et en PDF vectoriel pour le rapport."""
    from . import figures as fig

    typer.echo(f"courbes      : {fig.fig_courbes()}")
    typer.echo(f"vérification : {fig.fig_verification()}")
    table = pd.read_csv(RESULTATS / "capital_par_taille.csv")
    typer.echo(f"capital      : {fig.fig_capital_par_taille(table)}")
    typer.echo(f"rattrapage   : {fig.fig_rattrapage(table)}")
    typer.echo(f"distributions: {fig.fig_distributions()}")


@app.command()
def tout():
    """Tous les calculs et toutes les figures. Aucun téléchargement n'est nécessaire."""
    annexe()
    coquilles()
    concentration()
    figures()


if __name__ == "__main__":
    app()
