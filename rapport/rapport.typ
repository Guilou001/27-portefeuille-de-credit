#set document(title: "La règle de capital du BSIF suppose une infinité de prêts : ce que cela coûte", author: "Guillaume Vaudescal")
#set page(
  paper: "a4",
  margin: (x: 2.2cm, y: 2.4cm),
  numbering: "1 / 1",
  footer: context [
    #set text(size: 8pt, fill: luma(90))
    #grid(columns: (1fr, auto), align: (left, right),
      [portefeuille-credit], [#counter(page).display("1 / 1", both: true)])
  ],
)
#set text(font: ("Helvetica", "Arial", "DejaVu Sans"), size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.68em, spacing: 1.1em)
#set heading(numbering: none)
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.8em, text(size: 13pt, it))
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.6em, text(size: 11pt, it))
#show raw.where(block: true): it => block(
  fill: luma(246), inset: 8pt, radius: 3pt, width: 100%, text(size: 8.5pt, it))
#show raw.where(block: false): it => text(size: 9pt, fill: rgb("#1a3f66"), it)
#show quote.where(block: true): it => block(
  inset: (left: 10pt), stroke: (left: 1.5pt + luma(180)),
  text(style: "italic", fill: luma(45), it.body))
// la table NE DOIT PAS être enfermée dans un par() : Typst 0.15 la supprime alors
// entièrement, sans erreur. Le réglage se pose donc dans la portée du bloc.
#show table: it => block(above: 1.1em, below: 1.1em,
  [#set par(justify: false); #text(size: 8.8pt, it)])
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[La règle de capital du BSIF suppose une infinité de prêts : ce que cela coûte]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-08-30 · #link("https://github.com/Guilou001/27-portefeuille-de-credit")[Guilou001/27-portefeuille-de-credit]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Une banque doit garder de l'argent de côté pour le jour où ses emprunteurs ne remboursent pas. La règle canadienne calcule cette somme avec une formule qui suppose que la banque prête à une infinité de tout petits clients. Une banque commerciale, elle, a quelques centaines de dossiers, dont une poignée de très gros. Ce dépôt mesure ce que l'hypothèse coûte.

*Résultat en une phrase.* Sur un portefeuille de 500 prêts dont dix clients font la moitié du montant, la règle exige *5,21 %* de capital alors qu'il en faudrait *7,11 %*, soit *36 % de moins que nécessaire* ; un terme correctif que le comité de Bâle avait proposé en 2001 puis retiré rattrape *83 à 90 %* de ce manque, sans aucune simulation.

_Summary in English. The Basel/OSFI IRB capital formula assumes an infinitely granular portfolio. This repository reproduces 143 of the 144 published illustrative risk weights exactly, shows the 144th to be a transcription error by OSFI against the Basel source, then measures by simulation how much capital the formula misses on finite portfolios: up to 36 % on a book of 500 loans where ten clients hold half the exposure. The granularity adjustment recovers 83 to 90 % of that shortfall._

== 1. La question posée

*En mots simples.* Imaginez deux banques qui prêtent le même montant total à des clients de même qualité. La première a dix mille petits prêts, la seconde en a cinquante gros. Si l'économie va mal, la première perdra à peu près ce qu'on attend. La seconde peut très bien perdre beaucoup plus, parce qu'il suffit que deux ou trois de ses gros clients tombent en même temps.

La règle canadienne demande pourtant *exactement le même capital* aux deux. La question est de savoir combien cela coûte, et si un correctif simple suffit à réparer.

== 2. D'où vient le projet, et ce qu'il apporte

La règle de capital de crédit repose sur une idée unique : toutes les entreprises d'un pays sont touchées par une même conjoncture, plus ou moins fortement. Le capital exigé est la perte que la banque subirait dans une conjoncture si mauvaise qu'elle n'arrive qu'une année sur mille.

Cette formule ne tient que si le hasard propre à chaque emprunteur s'annule dans la moyenne, ce qui demande une infinité de prêts. Le comité de Bâle le savait : il avait proposé en 2001 un terme correctif, appelé *ajustement de granularité*, avant de le retirer de la règle finale.

Trois apports.

- *Les 144 poids de risque de l'annexe du BSIF recalculés* depuis les formules du chapitre 5, dont

143 retrouvés à un centième de point près.

- *Deux contradictions relevées dans le document du BSIF*, tranchées en allant lire la table de

Bâle dont il reprend les chiffres.

- *La mesure de ce que la règle manque*, par simulation exacte, et le test du correctif abandonné.

Aucune donnée n'est téléchargée : tout le dépôt tourne sur des formules et des portefeuilles construits. Le risque que la source disparaisse est donc nul.

== 3. Les résultats

=== 3.1 La règle recalculée : 143 cases sur 144

L'annexe 5-1 du chapitre 5 donne, pour dix-huit niveaux de risque et huit types de prêts, le poids que la formule doit produire. Ce sont les 144 cases que le code doit retrouver.

#figure(image("../results/figures/courbes_reglementaires.png", width: 100%), caption: [Les quatre courbes de la règle, et les points publiés])

Comment lire cette figure : chaque courbe est une famille de prêts, calculée par notre code sur quatre cents niveaux de risque. Les points sont les valeurs publiées par le BSIF. Ils tombent sur les courbes.

#figure(image("../results/figures/verification_annexe.png", width: 100%), caption: [Les 144 cases, écart au chiffre imprimé])

Comment lire cette figure : une case par valeur de l'annexe, la couleur donne l'écart entre notre calcul et le chiffre imprimé. Cent quarante-trois cases sont blanches, donc retrouvées à moins d'un centième de point. Une seule ne l'est pas.

=== 3.2 Deux contradictions dans le document du BSIF

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Contradiction*],
    [*Ce que le BSIF imprime*],
    [*Ce que Bâle imprime*],
    [*Ce que le calcul donne*],
    [Prêt à l'habitation, perte 45 %, risque 6,00 %],
    [165,52 %],
    [*162,52 %*],
    [*162,52 %*],
    [Chiffre d'affaires de la deuxième colonne],
    [7,5 M\$ dans le texte, 5 dans l'en-tête],
    [5 millions d'euros],
    [5],
)

Comment lire ce tableau, en trois constats. Le premier est que la première ligne est une erreur de recopie : le comité de Bâle imprime 162,52 %, notre calcul donne 162,52 %, et le BSIF imprime 165,52 %. Un 2 est devenu un 5 lors de la transcription, dans la version de septembre 2025 de la ligne directrice. Le deuxième est que la seconde ligne est une contradiction interne : le paragraphe explicatif du BSIF annonce un chiffre d'affaires de 7,5 millions de dollars, l'en-tête de son propre tableau annonce 5, et les nombres imprimés sont ceux de 5. Le troisième est que ces deux points se vérifient par le calcul et non par l'opinion : avec 7,5 millions, *19 cases* de l'annexe seraient fausses au lieu d'une.

=== 3.3 Ce que la règle manque sur un portefeuille fini

Tous les prêts ont ici le même risque, un pour cent de non-remboursement par an, et la même perte en cas de défaut, 40 %. Seul le nombre de prêts et leur répartition changent.

#table(
  columns: 6,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Portefeuille*],
    [*Nombre équivalent*],
    [*La règle exige*],
    [*Il en faudrait*],
    [*Manque*],
    [*L'ajustement rattrape*],
    [5 000 prêts identiques],
    [5 000],
    [5,21 %],
    [5,22 %],
    [0,1 %],
    [dans le bruit],
    [1 000 prêts identiques],
    [1 000],
    [5,21 %],
    [5,28 %],
    [1,3 %],
    [95 %],
    [500 prêts identiques],
    [500],
    [5,21 %],
    [5,36 %],
    [2,9 %],
    [88 %],
    [200 prêts identiques],
    [200],
    [5,21 %],
    [5,60 %],
    [7,5 %],
    [84 %],
    [100 prêts identiques],
    [100],
    [5,21 %],
    [6,00 %],
    [15,1 %],
    [83 %],
    [50 prêts identiques],
    [50],
    [5,21 %],
    [6,80 %],
    [30,5 %],
    [83 %],
    [500 prêts, dix font 30 %],
    [100],
    [5,21 %],
    [5,94 %],
    [14,0 %],
    [90 %],
    [*500 prêts, dix font 50 %*],
    [*39*],
    [*5,21 %*],
    [*7,11 %*],
    [*36,4 %*],
    [*88 %*],
)

Comment lire ce tableau, en trois constats. Le premier est la colonne du *nombre équivalent* : elle mesure la concentration, et se lit comme le nombre de prêts égaux qui donnerait le même risque. Cinq cents prêts dont dix font la moitié du montant se comportent comme trente-neuf prêts égaux, et c'est pour cela que leur manque de capital est le plus grand du tableau. Le deuxième est que le manque disparaît quand les prêts sont très nombreux, ce qui confirme que la formule est bien la limite d'un portefeuille infini et non une approximation de plus. Le troisième est que la dernière ligne est la forme réelle d'un livre de banque commerciale, et que c'est là que la règle se trompe le plus.

#figure(image("../results/figures/capital_par_taille.png", width: 100%), caption: [Le capital selon le nombre de prêts])

Comment lire cette figure : la ligne bleue horizontale est ce que la règle exige, la même quel que soit le nombre de prêts. La courbe rouge est ce qu'il faudrait vraiment, avec sa marge d'incertitude de simulation. La courbe verte est la règle plus le correctif.

#figure(image("../results/figures/rattrapage.png", width: 100%), caption: [La part de l'écart que le correctif rattrape])

Comment lire cette figure : chaque barre est un portefeuille, et sa longueur est la part du manque que le correctif comble. Les cas dont le manque est plus petit que trois fois l'incertitude de simulation sont retirés, parce que sur eux la part rattrapée n'aurait pas de sens.

#figure(image("../results/figures/distributions.png", width: 100%), caption: [La perte de l'année, sur cinq millions d'années simulées])

Comment lire cette figure : trois portefeuilles de même qualité moyenne. Les traits pointillés marquent la millième pire année, celle sur laquelle le capital se calcule. Plus le portefeuille est concentré, plus la queue de droite s'allonge, alors que le centre de la distribution ne bouge pas.

== 4. La méthode, pas à pas

+ *Écrire la règle* depuis le chapitre 5 : la sensibilité à la conjoncture, l'ajustement de taille pour les petites entreprises, l'ajustement d'échéance, et la perte de la millième pire année.
+ *La vérifier* sur les 144 cases publiées.
+ *Simuler un portefeuille fini.* Chaque année tirée a d'abord sa conjoncture, commune à tous. Une fois cette conjoncture connue, les emprunteurs font défaut indépendamment les uns des autres : le nombre de défauts d'un groupe de prêts identiques suit donc une loi binomiale, et se tire d'un seul coup. C'est ce qui permet de tirer cinq millions d'années au lieu de deux cent mille.
+ *Mesurer l'incertitude de la simulation elle-même*, sans quoi un écart ne prouverait rien.
+ *Appliquer le correctif* et regarder ce qu'il reste.

== 5. Reproduire

#raw("uv sync --locked --all-extras\nuv run pytest                 # 15 tests fermés, sans réseau\nuv run pcr tout               # les trois calculs et les cinq figures, environ deux minutes", block: true, lang: "bash")

Aucun téléchargement n'est nécessaire. Tous les chiffres de ce README viennent des fichiers de #raw("results/").

== 6. Limites, avec leur statut

#table(
  columns: 2,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Limite*],
    [*Statut*],
    [La simulation ne modélise pas la dégradation de note, seulement le défaut],
    [déclaré ; c'est pourquoi la comparaison se fait sans l'ajustement d'échéance, qui couvre précisément ce risque en plus],
    [La perte en cas de défaut est prise fixe, alors qu'elle monte dans les mauvaises années],
    [reconnu ; la tenir fixe sous-estime le vrai capital, donc le manque mesuré est un plancher],
    [Un seul niveau de risque par portefeuille],
    [déclaré ; mélanger des risques différents ajouterait de la concentration, donc creuserait encore l'écart],
    [Les 144 cases du BSIF sont recopiées à la main dans le code],
    [déclaré ; elles sont vérifiées contre la table de Bâle, qui est la source du BSIF],
    [L'incertitude de la simulation vaut environ 0,07 point de capital],
    [mesuré ; les écarts sous 0,2 point ne sont donc pas interprétables, ce qui exclut la première ligne du tableau],
    [Le correctif est implémenté par dérivées numériques et non par sa forme analytique],
    [déclaré ; la forme analytique change dès qu'on modifie la façon dont la sensibilité dépend du risque, la dérivée numérique non],
)

== 7. Crédits, licence, citation

Ligne directrice sur les normes de fonds propres du Bureau du surintendant des institutions financières, chapitre 5, version de septembre 2025. Table équivalente du comité de Bâle, CRE 99. Ajustement de granularité d'après les travaux de Michael Gordy et Tom Wilde. Code sous licence MIT, rapport sous licence CC BY 4.0. Figures produites par #link("https://github.com/Guilou001/gv-fintools")[gv-fintools].

Voisinage dans le portefeuille : #link("https://github.com/Guilou001/10-credit-bancaire")[10-credit-bancaire] porte le modèle qui estime la probabilité de défaut d'un emprunteur et le dossier de crédit d'une entreprise, et c'est le dépôt à lire pour un poste en banque commerciale. Celui-ci prend la probabilité comme donnée et regarde ce que la règle en fait au niveau du portefeuille. Le rapport #raw("rapport/rapport.pdf") est engendré depuis ce README.
