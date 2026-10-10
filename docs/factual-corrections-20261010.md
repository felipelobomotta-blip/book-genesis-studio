# Factual corrections and literary preference

The native repair replay exposed a mismatch between two editorial questions. A staged change from pounds to dollars received four votes for the older Chapter 1, while the comparison still included the uncorrected currency in Chapter 2. The agent subsequently staged a paired repair; Chapter 2 then won four valid votes and was promoted. Those original votes and attempts remain preserved. Context mattered, and the book had not established an explicit currency canon. This case is not permission to declare a newly chosen currency an already proven fact.

It also illustrates why a strictly factual correction supported by existing canon should have a correctness check. Literary preference is useful for a new scene or a changed voice; it cannot establish whether a character's surname matches the approved character record. Book Genesis now separates these decisions.

## Behavior

`check_correction.py prepare` freezes the accepted chapter, staged candidate, existing canon, dependent prose and a specific factual ticket. It numbers every input paragraph and prepares a structured response schema. A fresh read-only reviewer receives that material without target scores, preference votes or earlier judgments. It can reject the proposal for unsupported canon, a creative rewrite, changed testimony, an unresolved dependency or insufficient context.

`check_correction.py decide` validates the original native completion receipt, raw response, input hashes, complete packet and source references. A passing decision requires affirmative canon, scope and dependency checks and no unresolved finding within the correction. The helper resolves cited IDs into separate evidence; it does not repair the response or manufacture reader votes.

The same atomic chapter-promotion helper accepts this bound schema-2 decision, rechecks evidence before insertion, saves the original and emits a correction receipt. Its `panel` is null because no preference vote took place. Stale canon, changed reports, incomplete native calls, wrong source references or altered decision records leave the manuscript untouched. Creative revisions retain the original four-reader policy. Every canonical change still invalidates affected final reading evidence; a local correction does not automatically close a whole-book audit ticket or reset a revision budget.

## Real positive and negative controls

The experiment used a copied Chapter 4 from the preserved six-chapter manuscript, its existing character record, and Chapters 3 and 5 as dependency context. The positive candidate changed only Jonah's incorrect surname to the surname already established in the character record. The negative candidate also changed an admission of witnessing a destroyed receipt into a denial of witnessing it. Expected outcomes were declared before either call, with no retries.

The initial quote-based protocol accepted the surname correction. The negative control's model verdict correctly said `block`, but one quotation was not exact, so its evidence validation was **invalid**, not a successful protocol check. It produced no promotion decision. Both original reports remain preserved; neither was repaired or rerun into its old output path.

A separately declared experiment then used complete paragraph IDs. Both fresh calls used Codex CLI 0.156.1, `gpt-5.6-luna`, high effort, the prepared headless command, read-only mode and different working directories outside the book.

| Control | Expected | Observed | Raw report SHA-256 |
| --- | --- | --- | --- |
| Surname only | Pass | Valid pass; copied chapter promoted with exact original backup and no fabricated panel | `18794e1b46a7bf6f986a977f00ecce48a71a84062fbba843716bfbae0ec3de0f` |
| Surname plus changed witness account | Block | Valid block; no decision or replacement, original bytes retained | `76ab23ee0573daca6ec723bb3149ea050d48e853d47109a0a855533f8b869c82` |

The preserved source manuscript and the live replay were untouched by these experiments. The native calls and hashes demonstrate the stated two controls; they do not establish a general error rate or prove that the reviewer catches every semantic change. Broad creative edits, new canon choices and unresolved dependencies remain on the ordinary revision path. Complete-book autonomy, final literary quality and human reader acceptance are separate validation requirements.

Installer verification passed, and the stable final Windows suite passed **278 tests in 95.151 seconds**. Ten new tests cover positive promotion with a byte-identical backup, negative verdicts, failed scope/dependency checks, missing or invented evidence, stale and rehashed canon, partial/altered native outputs, changed evidence during promotion, malformed/duplicate JSON and overwrite refusal. An earlier full run overlapped source edits and failed two snapshot checks; it is retained as an invalid final-test attempt, not omitted or counted as passing.
