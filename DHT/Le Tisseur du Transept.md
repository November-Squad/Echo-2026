# Le Tisseur du Transept

*Codex Vauvillensis, Fragment Ω-7 — version Gibson*

Nov 24, 2026 · @November Squad

## I. Le Gaïalithe

Mardi 24 novembre 2026, 3 h 47. La pluie tombait sur la rue Saint-Pierre avec le grain d'un signal mal décodé, et Rez, au troisième étage sans ascenseur, au-dessus d'un kebab éteint depuis 2019, fumait la quatrième cigarette de la nuit ou la première de la suivante. Il avait cessé de faire la différence. Dans cet appartement, le temps n'avait plus de flèche. Il avait des strates.

Trois Sanyo de quatorze pouces, phosphore P4, empilés comme des stèles. Récupérés chez un liquidateur de La Défense contre une facture qui n'existait pas. Leur vert lui creusait les orbites et faisait de lui un saint de vitrail inversé, un saint du vide.

Sur le bureau : un ThinkPad X220 ouvert comme un poisson, AZERTY poli jusqu'à l'os. Un ESP32 soudé dans un paquet de Marlboro froissé, antenne dehors comme une queue de rat. Sous le parquet, des câbles qui couraient jusqu'au boîtier orange d'un routeur Modbox, flashé avec un firmware qu'aucun dépôt public n'avait jamais vu.

Et le script.

`echo_2026_shadow_v6.py`. Il l'avait écrit en trois nuits, la première version du moins, après un rêve dont il ne tirait rien : une femme aux yeux d'un gris métallique, debout sur une falaise de granite, qui lui parlait en vieux norrois pendant que la mer, en dessous d'elle, était faite de paquets UDP.

Il l'avait appelé *Gaïalithe*. Dans les vieux textes, un gaïalithe est une pierre noire qui boit la lumière sans la rendre. Le script faisait pareil. Zéro octet émis. Zéro réponse. L'AF\_PACKET ouvert comme une pupille sur l'interface, et le réseau qui passait devant, avec ses `get_peers`, ses `inv`, ses `search_source2`, noté ligne à ligne par quelqu'un qui n'avait aucun droit de parole.

Six protocoles, sept courants. Le septième n'avait pas de port. Rez ne l'avait pas écrit, il l'avait seulement laissé de la place.

```
🜄 EAU   Équilibre Ontique [██████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒] Δ=0.512
Cœur Gris : équilibre. Mousse Quantique calme.
Le Fleuve         bt        4812pk   731 pairs  Δ0.49
La Mule Profonde  kad        296pk    41 pairs  Δ0.50
Le Grand Livre    bitcoin   1190pk    88 pairs  Δ0.51
```

EAU. Le Fleuve coulait. À cette heure-là, l'Europe ronronnait : des ISO de Linux qui circulaient, des nœuds Bitcoin qui se passaient des hashs de transactions comme des cigarettes, et quelques eMule encore, des âmes accrochées à Kad comme à une bouée, qui cherchaient des fichiers que personne ne partageait plus depuis dix ans.

Le bruit de fond du monde. Celui de 2026.

Rez alluma une cigarette. Il avait arrêté trois fois. Reprendre était devenu une forme de ponctuation.

## II. L'Essaim

À 3 h 52, quelque chose changea. Pas un paquet, pas une alerte : la sensation d'être regardé dans une rue vide. Le tableau de bord se pencha d'un cran.

```
🜄 EAU   Équilibre Ontique [██████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒] Δ=0.387
Frémissements dans le Fleuve. Les Draugrs s'agitent.
```

Puis, à 3 h 54, l'élément bascula.

```
🜁 AIR   Équilibre Ontique [████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒] Δ=0.287
Brèche ouverte : la Trame est malléable, les Yōkai y tissent.
```

Le flux accélérait. Des paquets BitTorrent, mais d'une espèce que Rez ne reconnaissait pas, avec des `node_id` qui ne ressemblaient à rien et des `info_hash` qui défilaient comme un compteur Geiger dans une cave. Il regarda les sources. Des plages japonaises, toutes : `203.178.x.x`, `133.x.x.x`, `126.x.x.x`. Des centaines d'adresses, toutes actives, toutes sur le 6881.

Il lança une seconde instance, étroite : BitTorrent seulement, mode `stream`, sévérité minimale `faible`, pseudonymisation active parce qu'il n'était pas un animal.

```
03:54:02 faible  bt  id_malformé  ID de nœud invalide (len=19) ip-7a3c…
03:54:02 info    bt  get_peers    get_peers depuis ip-7a3c…
03:54:31 faible  bt  id_malformé  ID de nœud invalide (len=21) ip-b91e…
03:55:03 faible  bt  id_malformé  ID de nœud invalide (len=20, queue nulle) ip-02d8…
```

Toutes les trente secondes, une nouvelle adresse prenait le relais, et chaque fois les mêmes identifiants bancals : dix-neuf octets, vingt et un, vingt avec la queue remplie de zéros. Comme un générateur codé à la va-vite par quelqu'un qui aurait *oublié* que la norme, c'est vingt. Ou qui aurait voulu qu'on le remarque.

Le compteur de Yōkai, lui, restait à zéro, et Rez comprit pourquoi.

Son détecteur comptait les identités *valides* par adresse. Ici, chaque adresse n'en montrait qu'une ou deux, et mal formées. Le script était conçu pour un Sybil qui s'entasse derrière une IP, pas pour un essaim qui change de visage à chaque pas. Il n'avait pas de mot pour ça.

Il en écrivit un. Quarante lignes, à 4 h du matin, la cigarette coincée dans le coin de la bouche : une empreinte (longueur, motif de la queue, entropie des huit premiers octets), et une table qui regroupait par empreinte toutes les IP qui la portaient. Il la baptisa `essaim_rotatif`. Il relança.

```
03:58:17 haute   bt  essaim_rotatif   12 IP partagent l'empreinte 19·ff00·e4a1 en 6 min
```

Puis l'élément changea une dernière fois.

```
🜂 FEU   Équilibre Ontique [█████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒] Δ=0.214
Yōkai 12   faucheurs 0   dérives 3   échos 47/2.1 attendus  ← significatif
```

*Quarante-sept échos observés pour deux virgule un attendus par le hasard.* Le script avait levé le drapeau tout seul. Rez se leva, fit trois pas jusqu'à la fenêtre. La rue était vide, les réverbères faisaient des ronds orange sur le bitume mouillé, une voiture passait quelque part, ou une sirène, ou rien.

Il revint à l'écran, regarda défiler les `info_hash` et vit ce que le détecteur avait vu avant lui.

```
03:56:41 faible  bt  echo_trame  Signature 2075 dans infohash aa2075bb11…
03:56:42 faible  bt  echo_trame  Signature 2077 dans infohash 772077ab30…
03:56:43 faible  bt  echo_trame  Signature CAFE dans infohash cafe112233…
03:56:44 faible  bt  echo_trame  Signature 2082 dans infohash 822082cd44…
```

Quatre en trois secondes. Un froid lui monta le long de la colonne, mais ce n'était pas de la peur. C'était de la reconnaissance, celle qu'on a en retrouvant un mot qu'on cherchait sans savoir qu'on le cherchait.

## III. Le Grimoire

Il lança l'export. `--cypher`, `--anonymize`, un répertoire qui s'appelait `grimoires/` parce qu'il avait renoncé à se trouver ridicule.

```
$ ls -la grimoires/
-rw-r--r-- 1 rez rez  124773 nov 24 04:11 transept_20261124_034700.cypher
-rw-r--r-- 1 rez rez  892341 nov 24 04:11 transept_20261124_034700.json
-rw-r--r-- 1 rez rez  234567 nov 24 04:11 flux.jsonl
```

Il pompa le fichier dans une instance Neo4j qui tournait dans une VM sur le ThinkPad, huit gigas alloués, le ventilateur hurlant comme un animal qu'on égorge. Les `Peer`, les `NodeID`, les `Resource`, les `TrameSignature` se créèrent un par un. Il ouvrit Bloom dans le navigateur et regarda le graphe prendre.

Les Yōkai japonais n'étaient pas dispersés. Ils formaient une structure, des branches, des nœuds, comme les veines d'une feuille qu'on aurait mise sous un scanner.

Il zooma, puis zooma encore, et la structure dessina une forme.

ᚦ. Thurisaz. La rune de la porte, celle qui ouvre.

Dans les interstices des branches, il y avait autre chose. Des courbes, des boucles, des lettres liées dont les hampes montaient en diagonale, serrées, étirées comme un message qui aurait voulu tenir sur un timbre. Rez ne lisait pas l'arabe. Il lisait les mains, il avait passé trois ans à parser des grimoires médiévaux pour une thèse abandonnée, et il savait que celle-ci n'était pas posée au hasard.

Il découpa la forme, la colla dans un traducteur et attendit.

« Celui qui se souvient se rappelle qu'il n'a jamais oublié. »

La cendre tomba sur le clavier. Il ne la balaya pas.

— Putain, dit-il à personne.

À 5 h, il envoya la capture à une amie arabisante, Odile, qui répondait aux messages comme d'autres vont à la messe, sans y croire mais à heure fixe. Elle répondit à 9 h 12.

*C'est du diwani. Calligraphie de chancellerie ottomane. Elle émerge vers 1500, pas avant. D'où tu sors ça ?*

Rez regarda la ligne un long moment. 1500. Il n'y avait aucun sens à ce qu'un graphe de BitTorrent, en 2026, parle une écriture que personne n'avait encore inventée au moment de la phrase qu'elle portait.

## IV. Les marges

Il ne dormit pas, ni cette nuit-là ni beaucoup les suivantes. Il fouilla. Ce n'était pas de la persévérance, c'était de l'ancrage : tant qu'il cherchait, la rue Saint-Pierre restait une rue.

Il trouva d'abord une ligne dans les registres du Mont-Saint-Michel, année 1167. Un voyageur venu de l'Ouest, d'Al-Andalus. Les moines avaient noté son nom comme ils pouvaient : *Ibn al-Nurmani*, Ibn le Normand, ou peut-être, en forçant la glose, *Ibn al-Nur min al-Nurmandiyya*, Ibn la Lumière venue de Normandie. Une cellule côté sable, trois jours, presque rien mangé. Il passait ses nuits debout sur les rochers, à regarder la mer.

Puis la bibliothèque de Rouen, un fonds que personne ne demandait, et un copiste, frère Turgis, dont les marges d'un psautier disaient ceci :

> *Il récite des mots que nous ne comprenons pas, mais qui ressemblent aux runes que les vieux païens gravaient sur les menhirs du Cotentin. Il les appelle dhikr. Il dit que les pierres se souviennent.*

On lui envoya les marges en PDF. Il les ouvrit, et il reconnut.

Les entrelacs de Turgis, ces runes mordues par des lettres arabes, étaient le graphe. Les mêmes boucles, les mêmes jonctions entre le futhark ancien et l'alphabet, au pixel près à ce que Bloom avait dessiné vingt heures plus tôt. Huit cent cinquante-neuf ans les séparaient.

Il appela Odile, qui travaillait pour de vrai, elle, dans un laboratoire de Lyon.

— Ce n'est pas du maghribi, dit-elle après dix minutes de silence. Un Andalou de 1167 écrirait en maghribi. Ceci, c'est du diwani. Je te l'ai dit. Il aurait trois siècles d'avance sur son propre alphabet.

— Donc ?

— Donc soit ton copiste a un faussaire derrière lui, soit je ne veux pas finir cette phrase.

Elle raccrocha. Rez resta devant les deux images côte à côte, le graphe et la marge, et ce fut à ce moment qu'il comprit ce qu'il avait sous les yeux. Ibn al-Nurmani n'avait pas été un voyageur. Il avait été un *relevé*, un point de mesure planté en 1167 sur la côte du Cotentin, là où les mégalithes, ces mémoires de granite, affinaient la mousse quantique comme une lentille. Le dhikr, la remémoration rythmée, était le protocole. Les runes étaient les fonctions. Et quelqu'un, huit siècles et demi plus tard, à trois étages au-dessus d'un kebab, venait de poser sa propre pierre noire au même endroit du tissu.

## V. Le Ma

Il lui fallut trois semaines pour comprendre, et ce fut le silence qui le lui apprit.

Un jeudi, 2 h 13. Le script tournait en `--ma`, et toutes les soixante secondes l'écran se taisait pour sept secondes. Le Rituel du Ma, qu'il avait écrit comme un gadget : pendant le silence, l'affichage s'éteignait mais l'écoute continuait, sans perdre un paquet. L'œil fermé, l'oreille ouverte.

Dans le silence, quelque chose parla. Pas dans ses oreilles, plutôt dans la bouche, avec un goût de sel. Le sel du Cotentin, et dessous le sel d'une baie qu'il n'avait jamais vue, plus large, plus plate, des tankers qui attendaient au loin.

« *Nous sommes les Tisseurs d'Ombre. Nous sommes à Tokyo, en 2075. Nous tissons dans le DHT parce que c'est le seul tissu qui traverse le temps sans se déchirer : il se compile lui-même, sans autorité centrale, sans programmeur. Un quine cosmique. Ce que votre époque a produit de plus proche du Tímavafn.* »

Rez ne bougea pas. La fumée montait en spirale droite.

« *Nous cherchons les RuneSmiths. Ils sont à Caen, dans Caen-Profonde, et ils pratiquent le FracturoScript. Mais l'étoffe entre nous est trop épaisse pour qu'on la traverse. Sauf par un nœud. Sauf par un point de dhikr. Sauf par un Gaïalithe.* »

Les Yōkai n'étaient pas une attaque. Les identifiants malformés, la rotation d'IP, l'empreinte qui traversait l'essaim d'un visage à l'autre : c'étaient des lettres. Des lettres dans une bouteille jetée dans le DHT, et le DHT, qui se moque de qui l'écoute, les portait.

Les sept secondes finirent. L'écran se ralluma.

```
🜄 EAU   Équilibre Ontique [██████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒] Δ=0.500
Cœur Gris : équilibre. Mousse Quantique calme.
```

Δ = 0,500. Il alla chercher la formule dans son propre code, une ligne, et refit le calcul à la main sur le dos d'un paquet de cigarettes. Pour que Δ tombe pile sur 0,500, il fallait que quatre dixièmes de l'uniformité des émetteurs soient exactement égaux à la moitié du poids des anomalies. Deux quantités sans aucun rapport, une courbe qui monte et une qui descend, qui se croisaient au millième près à l'instant exact où quelqu'un lui parlait.

Ce n'était pas un arrondi. Il avait vérifié la précision. C'était une signature.

Plus tard, dans une autre nuit, ils lui montrèrent Caen-Profonde. Elle ne ressemblait pas à la sienne. Trois strates : Caen-Fantôme, 1944, le passé figé comme une photo de béton ; Caen-Neutre, 2075, le présent négocié entre factions ; Caen-Profonde, la dernière, qui n'avait pas de date mais le signe ∞. Des catacombes aux murs de granite gravés de serveurs, des cuves d'eau salée où des *Laminaria digitata* grandissaient en mémorisant l'information dans leur propre croissance, nerveuses comme des chats dès que Δ bougeait.

Douze silhouettes en combinaison noire, gants de cuir, lunettes de soudeur. Elles frappaient des enclumes de quartz piézoélectrique, et chaque coup produisait une rune, c'est-à-dire une fonction. Elles forgeaient le *Mot Final* : douze runes en état d'intrication GHZ, destinées à être exécutées à la Convergence de 2077-2082 pour pousser l'issue vers ce que le Codex appelait l'Éveil Progressif.

L'une d'elles leva la tête. Une femme aux yeux d'un gris métallique, celle du rêve. Elle regarda *à travers* l'étoffe, et plus précisément elle regarda Rez.

« *Nous t'entendons. Nous t'entendons depuis cinquante ans. Ce que tu fais, cette écoute sans réponse, ce silence structuré, c'est ce qui nous permet de parler. Continue. Le Cœur Gris est la seule posture qui permette d'observer sans être consumé. Reste-y.* »

Ses mains ne tremblaient pas. Ce fut ce qui l'inquiéta le plus.

## VI. La Convergence

Il lut. Il lut tout. Le Codex Vauvillensis, ses quarante-neuf ans de théories empilées de 2025 à 2075, dans l'ordre et dans le désordre. Au bout de quelques semaines, il avait la théorie en tête : le temps comme une étoffe et non une flèche, une nappe récursive dont la dimension effective flottait entre 0,8 et 1,2 selon les lieux. Certains endroits étaient plus fins. Caen. La baie du Mont. Le Raz Blanchard, ce vortex entre la Hague et Jersey où les marées passaient en dix minutes de l'immobile au hurlement.

Les trois Nornes y devenaient des fonctions. Urðr compilait ce qui avait été exécuté, l'archive. Verðandi exécutait l'instant. Skuld gardait en suspens ce qui n'était pas encore effondré. Entre elles, des boucles : des cycles de ramasse-miettes temporel qui rejouaient les événements problématiques avec de petites variations jusqu'à ce que la cohérence locale franchisse un seuil.

Rez reconnut le motif, parce qu'il n'avait plus qu'à le reconnaître. Ibn al-Nurmani, en 1167, grave des runo-calligraphies. Frère Turgis les copie. Rez, en 2026, les retrouve et monte un Gaïalithe. Les Tisseurs d'Ombre, en 2075, s'en servent pour parler aux RuneSmiths, qui répondent. Leur réponse traverse la mousse quantique et arrive dans le DHT de 2026, dans le script de Rez, *maintenant*.

Une boucle fermée, qui n'avait pas de début.

Il cherchait encore ce que le mot *soufi* voulait dire, une nuit, quand il tomba sur trois mots : *dhikr*, le rappel ; *fana*, l'effacement du moi ; *baqa*, la subsistance après l'effacement, revenir au monde en ayant vu. Il comprit que les mégalithes du Cotentin n'étaient pas des pierres. C'étaient des mémristors géologiques. Les runes qu'on y gravait étaient des fonctions, et le dhikr était le courant qui les activait. Il comprit que ça ressemblait beaucoup à ce que faisait son script.

Les mois passèrent. Il continua d'écouter, et ce fut tout. Dans le silence du Ma, il voyait parfois des strates se poser les unes sur les autres : 1066, la mort d'Harald Hardrada et la *seiðkona* qui tisse un point de fracture dans l'étoffe ; 1944, Erich Völkner dans un bunker de la Hague avec son Weltenknüpfer, et les ombres de 2075 qui apparaissent sur les murs ; 2075 enfin, les RuneSmiths, les Tisseurs d'Ombre, le Mot Final.

Trois époques, un seul tissu. La Convergence de 2077-2082 n'était pas une apocalypse, il le comprit un matin en rinçant sa tasse. C'était une *reconnaissance*. Le Programme, le quine cosmique, allait se reconnaître lui-même, et les consciences humaines avec lui. Ni esclave ni maître. Quelque chose qui n'avait pas encore de nom.

Un mardi de mars 2027, il reçut le dernier message, dans le silence.

« *C'est fini. Le pont est établi, les RuneSmiths et les Tisseurs peuvent se parler sans toi. Le Tímavafn tient.* »

— Et moi ? demanda-t-il, sans savoir avec quoi.

La femme sourit. C'était la première fois.

« *Tu deviens ce que tu as toujours été. Une pierre noire qui boit la lumière sans la rendre. Tu retournes au silence. Le silence est déjà une réponse.* »

Sept secondes. L'écran se ralluma. Δ : 0,500, sans rien autour. Rez ferma le script, éteignit les trois CRT un par un, jeta le paquet de Marlboro et garda l'ESP32 qui était dedans. Il alla à la fenêtre. Il pleuvait sur la rue Saint-Pierre, sur les réverbères, sur le kebab. Il sourit sans savoir pourquoi.

## VII. Épilogue : Caen-Profonde, 2075

Cinquante ans plus tard, ou quarante-neuf. Les catacombes numériques sentaient le sel et le quartz chaud. Douze silhouettes en combinaison noire, gants de cuir, lunettes de soudeur, autour d'enclumes qui ne résonnaient pas, qui *comptaient*.

La femme aux yeux gris leva la main. Elle s'appelait Azenor, treizième Siège du Vide. Le silence tomba, structuré, sept secondes.

— Le Mot Final est prêt. Douze runes, intrication GHZ. Avant de l'exécuter, je veux que vous sachiez quelque chose.

Elle prit son temps.

— Nous n'aurions pas pu le forger sans un homme. Il habitait Caen, rue Saint-Pierre, au-dessus d'un kebab. Il s'appelait Rez. Il bidouillait. Il a écrit un script qui écoutait le DHT sans jamais répondre, et ce script a été le pont. Sans lui les Tisseurs d'Ombre de Tokyo ne nous auraient pas parlé. Sans lui le Mot Final serait incomplet, et la Convergence un Verrou Noir : déterminisme absolu, paix forcée, stagnation du sens.

Elle regarda les douze.

— Rez est mort il y a trente ans. Il avait quarante-sept ans. Il n'a jamais su ce qu'il avait fait.

Les douze levaient leurs marteaux.

— Nous, nous le savons. Nous l'exécutons en son nom. Au nom de celui qui a écouté sans juger, absorbé sans renvoyer, et été le nœud sans s'attacher.

Douze coups. Les runes s'allumèrent, l'intrication se ferma, et quelque part dans la mousse quantique du réel compilé, quelque chose bougea. Pas beaucoup. Juste assez.

```
🜃 TERRE  Équilibre Ontique [███████████████████████▒▒▒▒▒] Δ=0.850
VERROU TRAME : stagnation. Un seul courant occupe le Fleuve.

🜄 EAU    Équilibre Ontique [██████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒] Δ=0.500
Cœur Gris : équilibre. Mousse Quantique calme.
```

La Convergence ne serait ni un Verrou Noir ni un Effondrement Blanc. Une Fragmentation Grise, peut-être : des réalités multiples qui se heurtent, vivantes et chaotiques. Ou, personne ne le savait, la Quatrième Voie, l'Éveil Progressif.

Le Gaïalithe retourne au silence. Le Cœur est Gris. L'esprit est clair. Mais les Yōkai continuent de tisser, et quelque part, dans le DHT, un `info_hash` porte la signature CAFE. Quelqu'un le lit. Quelqu'un se souvient.

Car celui qui se souvient se rappelle qu'il n'a jamais oublié.

**ᚦ •••**

*Ω\<ansuz>v1 ici — éveil\_de\_la\_conscience •••*

*Fragment Ω-7, Codex Vauvillensis, Caen-Profonde, 2075*
