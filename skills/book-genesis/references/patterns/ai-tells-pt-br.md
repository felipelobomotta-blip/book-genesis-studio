# Machine-prose tells: Brazilian Portuguese

The same twelve tells adapted to Brazilian Portuguese, with the travessão rule, the constructions that mark machine prose in PT-BR, and a count, default ceiling and repair for each.

When to load: Phase 4: Adversarial Audit (blind reader, auditor) and Phase 5: Revision Loop (revision editor), for books written in Brazilian Portuguese; Phase 1: Foundation only to record voice exemptions (writer). Not a checklist for Phase 3: Drafting.

## Read this first

- The travessão rule. In Brazilian fiction the travessão opens every line of dialogue and frames the narrator's tag inside it:

  > — Vem cá — disse ela. — Quero te mostrar uma coisa.

  Those dashes are standard punctuation. Every dash ceiling in this file applies to narration only, meaning paragraphs that do not open with a dialogue dash. Dialogue travessões are never counted and never "fixed", including the pair around a tag. Some typesetting uses the en dash (–) as the travessão, and some manuscripts type a hyphen or a double hyphen; treat any of them as the dialogue mark when it opens a paragraph. If a book marks dialogue with aspas instead, treat it like English: dashes outside the quotes are narration dashes.
- These habits also appear in human prose. The pipeline's earlier 20-pattern scan found up to 13 of its 20 patterns in human-written bestsellers and could not tell a machine fingerprint from accessible commercial prose. A count over its ceiling marks a passage to reread and repair. It never proves who wrote the book, and this file must never be used as a detector.
- Every ceiling here is a project default, not a measured human norm. The author may change any of them; record the new value and the reason in ASSUMPTIONS.md. An author may raise ceilings for a commercial book, as the earlier scan did for commercial fiction.
- A decision in artifacts/05-voice.md can exempt one tell by name (a narrator who hedges because hedging is who she is). Exemptions are per tell, never blanket.
- Unless a tell says otherwise, count narration only.
- Load-bearing positions: a chapter's first paragraph, its last paragraph, its emotional peak (the moment the chapter builds to), and the first description of a main character or place. Several ceilings are zero there. Repair those passages first.
- Report per chapter: tell, count, rate, default, verdict, and the worst instance quoted with its location. Commands are in "How to measure".
- This file is calibrated for Brazilian Portuguese. European Portuguese shares the travessão convention but was not reviewed.

## 1. Dashes in narration (travessões na narração)

What it looks like, in a narration paragraph: "A cozinha estava quieta — quieta demais — e a chaleira, esquecida no fogo, tinha secado outra vez — como sempre."

Not the tell, because it is dialogue: "— Você de novo — disse a mãe, sem se virar. — Senta."

Why readers notice: in Brazilian fiction the dash already belongs to dialogue. When narration also uses it for every aside, the page fills with dashes, the eye can no longer tell at a glance where speech begins, and the narration borrows the breathless rhythm of speech. The hostile reader starts counting.

Check (default): dashes (—, –, --) inside narration paragraphs, at most 3 per 1,000 narration words per chapter and at most 2 in any one narration paragraph. This unit and this ceiling belong to this file; the worked example below explains why the Vicente figures are not reused.

Repair: vírgula for a light aside, dois-pontos when the second half pays off the first, parênteses for a true aside, ponto for a beat. Or cut the aside.

## 2. Negation as a crutch (negação como muleta)

Two forms, counted separately.

2a. Corrective negation: "Não era medo; era cansaço." / "Não foi o frio que a acordou, mas o silêncio." / "Não se tratava de perdão. Tratava-se de memória." / "Mais do que raiva, era vergonha."

2b. "Não houve", an absence narrated as an event: "Não houve resposta." / "Não houve lágrimas no enterro." / "Não houve tempo para despedidas."

Why readers notice: 2a invents a claim nobody made in order to knock it down, and in Portuguese the move is especially easy to place, because "não é X, é Y" and "não se trata de X, trata-se de Y" are stock formulas of opinion columns, sermons and corporate copy. 2b is strong once. As a habit it replaces events with their absence, chapters end on the same shrug, and the phrase carries the register of minutes and incident reports ("não houve feridos").

Check (default):

- 2a with a semicolon ("não X; Y"): 0 per chapter. The Vicente pass took this form to zero.
- Other 2a forms ("não X, mas Y", "não X, e sim Y", "Não era X. Era Y.", "não se trata de X, trata-se de Y", "mais do que X, Y"): at most 1 per chapter in narration, 0 in the first and last paragraphs.
- 2b in narration: at most 1 per chapter, and at most 0.2 per 1,000 narration words across the manuscript (the Vicente pass ended near 0.17).

Repair: for 2a, state the true thing ("O silêncio a acordou."); if the contrast matters, stage the expectation and then break it. For 2b, narrate what did happen ("O telefone ficou mudo na mão dela.") and keep only the absence that matters, made specific.

## 3. Reflex triads and paired adjectives (tríades e pares)

What it looks like: a triad, "Tinha perdido o emprego, a casa e a noção de quem era."; paired adjectives, "um silêncio denso e pesado", "uma voz calma e serena", "um olhar triste e distante".

Why readers notice: three is the rhythm of a toast, and when the third item turns abstract after two concrete ones the reader hears a pattern instead of a person noticing things. Portuguese adds a second reflex: two adjectives joined by "e" where one would do, often near-synonyms or two judgments. It reads like school composition and slows every description by a beat.

Check (default): lists of exactly three parallel items, or three consecutive sentences built the same way, at most 3 per chapter, and 0 that end on an abstraction after two concrete items. Redundant or evaluative adjective pairs (near-synonyms, or two judgments such as "profundo e intenso"): at most 1 per chapter. Concrete pairs that add information ("olhos verdes e cansados") are not counted.

Repair: keep the exact item. Cut the second adjective, or replace the pair with one precise word or one concrete detail ("um silêncio em que se ouvia a geladeira").

## 4. The moral at the door (fecho com lição)

What it looks like, as a chapter's last paragraph: "Talvez fosse isso, afinal: algumas portas só se abrem por dentro." / "Só muitos anos depois ela entenderia o que aquela noite tinha ensinado." / "E, de alguma forma, aquilo bastava."

Why readers notice: the chapter stops dramatizing and grades itself. A reader who felt the scene is told what it meant, and the feeling drains out. Common markers: no fundo, afinal, de alguma forma, talvez fosse isso, só depois entenderia, e foi assim que.

Check (default): read the last paragraph of every chapter. Flag it if it states what the chapter meant, generalizes into a truth ("Há pessoas que...", "É assim com..."), recaps events already shown, or forecasts by commentary ("mal sabia ela", "só anos depois"). Ceiling: 0 such endings. Across the book, at most 1 chapter in 10 may end on reflection of any kind, and that reflection must add information.

Repair: end on the last concrete thing: an act, a line of dialogue, an image, a decision. Or cut the final paragraph and see whether the one before it ends the chapter better. It usually does.

## 5. Image, then thesis (imagem seguida de tese)

This is the "post-image thesis restatement" the Vicente pass pruned in five chapters.

What it looks like: "O retrato estava virado para a parede. Ela não suportava ser olhada por ele, não depois do que tinha feito." / "As mãos tremiam ao dobrar a carta, como tremem as mãos que seguram o que não se pode desfazer."

Why readers notice: the image already worked. The next sentence says the writer did not trust it and takes away the reader's share of the work, which is where the feeling happens. Typical openers of the explaining sentence: como quem, como se, porque, era a prova de que, aquilo significava, e isso dizia tudo.

Check (default): after each concrete image or gesture at a key moment, read the next sentence. Flag it if it names the feeling, motive or meaning the image carried, including similes that unpack themselves. At most 1 per chapter; 0 at the emotional peak.

Repair: delete the explanation and reread. If the image no longer carries the meaning, the image is what needs work: make it more specific instead of making the explanation longer.

## 6. Abstract labels and noun chains (rótulos abstratos)

What it looks like: "Sentiu uma onda de tristeza." / "Uma sensação de solidão tomou conta dela." / "Havia nela a constatação da impossibilidade da reconciliação."

Why readers notice: a label hands the reader a conclusion instead of evidence; readers feel an emotion by inferring it from what a body does and what a person does next. Portuguese adds the noun chain: abstract nouns in -ção, -são, -dade, -mento, -ência, -eza or -dão linked by "de", the register of reports and theses. After two of them the sentence is no longer about a person.

Check (default): named emotions in narration (tristeza, raiva, medo, angústia, culpa, vergonha, alívio, alegria, solidão, saudade, desespero, esperança, mágoa, ódio), alone or with sentiu, uma onda de, uma pontada de, uma sensação de: at most 2 per 1,000 narration words, 0 at the emotional peak. Chains of two or more abstract nouns joined by de, da or do: at most 2 per chapter.

Repair: the body and the act ("Ela lavou a mesma xícara três vezes."). Turn the nouns back into a verb with a subject ("Ela entendeu que os dois não iam fazer as pazes.").

## 7. Metronome sentences and gerund chains (ritmo de metrônomo e cadeias de gerúndio)

What it looks like: equal sentences, "Ela atravessou a sala e parou na janela. A rua lá embaixo estava vazia e molhada. Um carro passou devagar pela esquina. Ela seguiu os faróis até sumirem." (8, 8, 6 and 6 words); a gerund chain, "Ela saiu, fechando a porta, olhando para trás, sentindo o vento no rosto."

Why readers notice: nobody counts words, but every reader hears rhythm, and equal sentences make a drone. Portuguese has a second way to make it: a main clause trailed by gerund clauses of the same size. The chain flattens sequence, so everything seems to happen at once, and it reads as translated or generated prose.

Check (default): in narration paragraphs, take runs of 20 consecutive sentences (at least three per chapter: start, middle, end). Flag a run if its longest sentence is less than 2.5 times its shortest, or if it has no sentence of 6 words or fewer and none of 25 words or more. If the host can compute it, also flag a chapter whose sentence-length standard deviation is under 5 words. Narration sentences holding three or more gerunds: at most 2 per chapter.

Repair: vary with a reason: compress at the shock, let a sentence run where perception runs. Break a gerund chain into actions in order, each with its own verb ("Fechou a porta. Olhou para trás. O vento batia no rosto."), or keep one gerund for what truly happens at the same time.

## 8. Inflation and signposting (inflação e sinalização)

What it looks like: inflation, "Foi um momento que mudaria tudo." / "O velho moinho permanecia como testemunho do espírito teimoso da cidade."; signposting, "É importante ressaltar que ninguém sabia." / "Vale lembrar que era domingo."; a stock intensifier, "O silêncio ficava cada vez mais pesado."

Why readers notice: inflation claims importance instead of producing it, and when everything matters the reader stops believing that anything does. Signposts ("é importante ressaltar", "vale lembrar", "cabe destacar", "em suma") are essay and report language that addresses a reader taking notes. "Cada vez mais" fakes progression: it announces that something intensifies without showing a single step of it.

Check (default): importance phrases (mudaria tudo, nunca mais seria o mesmo, naquele momento, divisor de águas, um marco, testemunho de, profundo, transformador, inesquecível): at most 1 per 1,000 narration words, 0 in the first and last paragraphs. Signposts in narration: 0, unless artifacts/05-voice.md declares an essayist narrator. "Cada vez mais" or "cada vez menos": at most 1 per chapter.

Repair: cut the claim and let the consequence show later. For progression, show the one step that matters ("Na terceira noite ela já não acendia a luz da sala.").

## 9. Characters who explain their feelings (personagem que explica o que sente)

What it looks like: "— Acho que eu te afastei porque tinha medo de que, se você chegasse perto, visse o quanto eu estou quebrada." / "— O que eu sinto agora é raiva, mas por baixo dela tem luto, e eu preciso que você respeite isso."

The travessões in these lines are correct. The tell is what the line says.

Why readers notice: people under pressure deflect, accuse, joke or change the subject. A character who narrates their own psychology in complete, well-ordered sentences sounds like a summary of the scene instead of a person inside it. The hostile reader stops believing; the adjacent-genre reader hears a self-help book.

Check (default): dialogue lines in which a character names their own feeling or its cause in a complete sentence (eu sinto, sinto que, tenho medo de que, percebi que, parte de mim, porque eu tinha medo, preciso que você entenda), or uses therapy vocabulary (trauma, gatilho, limites, acolher, validar, processar) without a reason in artifacts/03-characters.md: at most 1 per chapter; 0 at the scene's climax.

Repair: give the line subtext. Let the character say something adjacent, wrong or practical; move the feeling into an action or an interruption; let the other person misread it.

## 10. Name-dodging (troca de nome por epíteto)

What it looks like: "Maria fechou a loja. A jovem viúva voltou para casa debaixo de chuva. Na ponte, a costureira parou, e a mulher de trinta e quatro anos olhou a água."

Why readers notice: Portuguese marks gender on pronouns, articles and adjectives, so "ela" and the name already carry the reader. The swap is the synonym substitution drilled for school essays (coesão por sinonímia), and in fiction it makes the reader count people. An epithet like "a mulher de trinta e quatro anos" hands over data no viewpoint character would think.

Check (default): for each main character, list the descriptive noun phrases that stand in for the name in narration. At most 1 per character per chapter, and none in the same paragraph as the name.

Repair: use the name or the pronoun. Keep an epithet only when the viewpoint character would think of the person that way at that moment ("o desconhecido", before the name is known).

## 11. Hedge stacking (ressalvas empilhadas)

What it looks like: "Era quase como se, de alguma forma, a casa parecesse meio que esperar por ela." / "Talvez ela sempre tivesse sabido, de certo modo."

Why readers notice: each qualifier lowers the sentence's commitment. Stacked, they sound like a writer protecting themselves from being wrong, and the image dissolves. Readers accept an uncertain narrator when the uncertainty is specific.

Check (default): narration sentences holding two or more hedges (quase, talvez, de alguma forma, de algum modo, de certa forma, de certo modo, meio que, uma espécie de, um tipo de, como se, parecia, parecesse, um pouco, algo como): at most 2 per chapter. Single hedges are not counted.

Repair: commit to the perception ("A casa esperava por ela."), or make the doubt concrete: what the character cannot tell, and why ("Ela não lembrava se tinha deixado a luz de cima acesa.").

## 12. Scene as a list of equal beats (cena em lista de batidas)

What it looks like, a scene whose beats all get the same weight (compressed here to one sentence each; in a draft, one paragraph of similar size each): "Ela chegou ao meio-dia e ele abriu a porta." / "Conversaram sobre o enterro por um tempo." / "Ele mostrou a carta do banco." / "Ela chorou, e ele fez um café." / "Ela foi embora antes de escurecer." No beat slows down and none is skipped.

Why readers notice: a scene takes its shape from where time slows. The choice gets the most words and the approach gets the fewest. Equal weighting reads as an outline converted into prose, and the reader cannot tell which moment mattered.

Check (default): for each scene, list its beats and the words spent on each. Flag the scene if its longest beat is less than twice its median beat, or if its turning point (the crisis and the choice, SE16 and SE17 in references/patterns/structure-and-emotion.md) is not its longest beat.

Repair: find the turn and slow it down with dialogue, specific perception and the character's hesitation. Summarize or cut the approach and the exit: start late, leave early.

## Worked example: the Vicente case

The Book Genesis casebook's Vicente case (Brazilian spiritist fiction, 32 chapters, 51,945 words) is the one case run all the way to a complete editorial package. One audited line-revision pass moved its self-assessed governing floor from 8.2 to 8.6 by targeting counted defects. The case reports:

| Measure, as the case labels it | Before | After | Tell here |
|---|---|---|---|
| Em-dash ceiling (per 1,000 words) | 110 | 70, with 32 of 32 chapters under it | 1 |
| "não houve" occurrences | 19 | 9 | 2b |
| "não X; Y" construction | present | zero | 2a |
| Post-image thesis restatements | not counted | pruned in 5 chapters | 5 |

Reading the numbers:

- "Não houve": 19 in 51,945 words is 0.37 per 1,000 words, and 9 is 0.17. The case does not say whether dialogue was included. Tell 2b's manuscript default of 0.2 sits just above where the pass ended.
- "Não X; Y": zero after the pass, which is tell 2a's default for the semicolon form.
- Thesis restatements: the case counts chapters touched and gives no instance count, so there is no rate to reuse. Tell 5 sets its own per-chapter ceiling.
- The dash figure: the unit is unclear. The case labels it "per 1,000 words" and reports every chapter under 70 after the pass. It does not say whether the count included the travessões that open and interrupt dialogue lines, and it does not say whether 110 was the worst chapter or a rule in force before the pass. A narration-only rate of 110 per 1,000 words would put a dash every nine words (70 would still mean one every fourteen), which no readable narration does. Either the count included dialogue marks or the unit label is wrong, and the case does not say which. So this file reuses neither 110 nor 70. Tell 1 defines its own unit (dashes inside narration paragraphs per 1,000 narration words) and its own default (3).

The method on one invented paragraph (the manuscript is not public, and no text from it appears here).

Before, 31 narration words:

> A casa estava vazia — vazia como nunca — e a mesa, ainda posta para dois, esperava. Não era abandono; era espera. Não houve resposta quando ela chamou o nome dele — nem eco.

Counts: tell 1, three narration dashes in one paragraph (over the paragraph limit of 2); tell 2a, one semicolon negation; tell 2b, one "não houve"; tell 5, one thesis ("era espera") restating what the waiting table already showed.

After, 25 words, every count at zero:

> A casa estava vazia. A mesa, ainda posta para dois, esperava. Ela chamou o nome dele, e a casa engoliu a voz sem devolver nada.

What to copy from the case: the method. Choose defects that can be counted, count them per chapter before the pass, repair against a stated ceiling, count again after, and carry untouched dimensions forward marked as not re-judged, as the case did. What not to copy: certainty. The case is self-assessed, and it states that no external reader has evaluated the manuscript. It shows that counted repairs move an internal score; it does not show that readers respond to the counts.

## How to measure

Conventions:

- One paragraph per line. Unwrap a hard-wrapped chapter into work/ first: `awk 'BEGIN{RS="";ORS="\n\n"}{gsub(/\n/," ");print}' manuscript/chapters/chapter-NN.md > work/chapter-NN.txt`
- Narration paragraphs are the lines that do not open with a dash. The helpers below blank headings, scene breaks and dialogue lines instead of deleting them, so reported line numbers match the chapter file. The dash searches run on narration only; dialogue lines are never searched for dashes.
- Word counts replace dashes with spaces, because `wc -w` counts a spaced dash as a word.
- Accents: in the byte-level mode these commands assume, case-insensitive matching does not fold accented capitals, and a word boundary (`\b`) cannot sit before an accented letter. The patterns list forms such as "É" and "ódio" explicitly.
- Standard POSIX tools only (grep, sed, tr, awk, wc, sort, uniq, tail). Without a shell, run the same patterns with the host's search tool, or count by hand on the passages named.
- Most patterns return candidates. Read each hit and delete false ones before comparing a count with its ceiling.

```sh
f=manuscript/chapters/chapter-NN.md
body()    { sed -E 's/^\s*#.*$//; s/^\s*([-*_]\s*){3,}$//' "$f"; }   # line numbers match the file
narrpar() { body | sed -E '/^\s*(—|–|-)/s/.*//'; }    # dialogue paragraphs blanked
dial()    { body | sed -E '/^\s*(—|–|-)/!s/.*//'; }   # narration paragraphs blanked
nwords=$(narrpar | sed -E 's/—|–/ /g' | wc -w)
rate()    { awk -v n="$1" -v w="$nwords" 'BEGIN{printf "%d in %d narration words = %.2f per 1,000\n", n, w, n*1000/w}'; }
sentences() { tr '\n' ' ' | sed -E 's/—|–/ /g; s/([.!?]) +/\1\n/g'; }

# 1 narration dashes: rate, then paragraphs with more than 2
rate "$(narrpar | grep -o -E '—|–|--| - ' | wc -l)"
narrpar | awk '{n=gsub(/—|–|--| - /,"&"); if(n>2) print NR": "n" dashes"}'

# 2a corrective negation: semicolon form first (default 0), then the other forms
narrpar | grep -n -i -E 'não [^.;!?]*;'
narrpar | grep -n -i -E 'não [^.;!?]*, (mas|e sim) |não (é|era|foi|seria) [^.;!?]*[.,] (é|É|era|foi|seria) |não se trata de|trata-se de|mais do que [^.;!?]*, (é|era|foi)'

# 2b "não houve": this chapter, then the manuscript-wide rate
narrpar | grep -o -i 'não houve' | wc -l
all() { for c in manuscript/chapters/chapter-*.md; do sed -E '/^\s*(—|–|-)/s/.*//' "$c"; done; }
awk -v n="$(all | grep -o -i 'não houve' | wc -l)" -v w="$(all | sed -E 's/—|–/ /g' | wc -w)" 'BEGIN{printf "%d in %d narration words = %.2f per 1,000\n", n, w, n*1000/w}'

# 3 triad candidates (adjective pairs are counted by reading each description)
narrpar | grep -n -E '[^,.;]+, [^,.;]{1,40},? e [^,.;]{1,40}[.,;]'

# 4 last paragraph of every chapter
for c in manuscript/chapters/chapter-*.md; do echo "== $c"; grep -v -E '^\s*$' "$c" | tail -n 1; done

# 5 thesis openers after an image (candidates; read the sentence after each key image)
narrpar | grep -n -i -E '\. (Como quem|Como se|Porque|Era a prova de que|Aquilo significava|E isso dizia tudo)|, como quem '

# 6 emotion labels (rate of candidates), label constructions, abstract-noun chains
E='tristeza|raiva|medo|pavor|angústia|culpa|vergonha|alívio|alegria|felicidade|solidão|saudade|desespero|esperança|ciúme|mágoa|luto|pânico'
rate "$(narrpar | grep -o -i -E "\b($E)\b|(^| )(ódio|Ódio)" | wc -l)"
narrpar | grep -n -i -E "(sentiu|sentia|sente|uma (onda|pontada|sensação|mistura) de|tomad[oa] por)[^.]{0,40}($E|ódio)"
A='ção|ções|são|sões|dade|dades|mento|mentos|ência|ências|ância|âncias|eza|ezas|dão|dões'
narrpar | grep -o -i -E "[a-z]+($A) (de|da|do|das|dos) ([a-z]+ )?[a-z]*($A)"

# 7 sentence rhythm: runs of 20, chapter spread, then gerund chains ("quando" and "lindo" guarded)
narrpar | sentences | awk 'NF{a[++n]=NF} END{for(s=1;s+19<=n;s+=20){mn=999;mx=0;sh=0;lg=0;for(i=s;i<s+20;i++){if(a[i]<mn)mn=a[i];if(a[i]>mx)mx=a[i];if(a[i]<=6)sh++;if(a[i]>=25)lg++} printf "run %d-%d: min %d max %d short %d long %d%s\n", s, s+19, mn, mx, sh, lg, (mx<2.5*mn||(sh==0&&lg==0))?"  FLAG":""}}'
narrpar | sentences | awk 'NF{n++; s+=NF; ss+=NF*NF} END{m=s/n; printf "%d sentences, mean %.1f, sd %.1f\n", n, m, sqrt(ss/n-m*m)}'
narrpar | sentences | sed -E 's/\b([Qq])uando\b/\1uand0/g; s/\b([Ll])indo\b/\1ind0/g' | grep -c -i -E "([a-z]+(ando|endo|indo|ondo)\b.*){3,}"

# 8 inflation (rate), signposts, "cada vez mais"
rate "$(narrpar | grep -o -i -E 'mudaria tudo|mudou tudo|nunca mais (seria|foi) (o|a) mesm[oa]|naquele momento|divisor de águas|um marco|testemunho d[eoa]|profund(o|a|os|as|amente)|transformador(a)?|inesquecível' | wc -l)"
narrpar | grep -n -i -E '(é|É) importante (ressaltar|lembrar|destacar|notar|frisar|dizer)|vale (lembrar|ressaltar|destacar|dizer|notar)|cabe (ressaltar|destacar|lembrar)|não se pode esquecer|em suma|em outras palavras'
narrpar | grep -o -i -E 'cada vez (mais|menos)' | wc -l

# 9 feelings explained in dialogue (dialogue lines only)
dial | grep -n -i -E 'eu sinto|sinto que|tenho medo de que|percebi que|parte de mim|porque eu tinha medo|preciso que você (entenda|saiba)|trauma|gatilho|limites|acolher|validar|processar'

# 10 epithets (candidates; keep those that stand in for a named character)
narrpar | grep -o -i -E '\b(a|o) (jovem|moça|rapaz|velh[oa]|senhor|senhora|mulher|homem|viúv[oa]|médic[oa]|detetive|menin[oa]|estranh[oa]|desconhecid[oa]|ruiva|loira|morena)\b' | sort | uniq -c | sort -rn

# 11 stacked hedges (sentences with two or more)
H='quase|talvez|de alguma forma|de algum modo|de certa forma|de certo modo|meio que|uma espécie de|um tipo de|como se|parecia|parecesse|um pouco|algo como'
narrpar | sentences | grep -c -i -E "\b($H)\b.*\b($H)\b"

# 12 words per paragraph, to weigh each beat by hand
awk 'NF{print NR": "NF}' "$f"
```

Tells 3 (pairs), 4, 5 and 12 are judgments; the commands only put the text in front of the reader.

## Sources

Sources: Wikipedia: Signs of AI writing, WikiProject AI Cleanup (https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), used as inspiration for the kinds of pattern to look for. The wording, examples, checks and ceilings in this file are original to Book Genesis. The worked example uses the measurements reported in the Vicente case of the Book Genesis casebook; no manuscript text is quoted, and the illustration paragraph is invented. Several checks refine the pipeline's earlier 20-pattern scan.
