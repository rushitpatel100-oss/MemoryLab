# MemoryLab Phase 8 — Decision rubric v2 (freeze before review)

**Purpose:** Make the four relation labels and storage action separately auditable. This rubric is written before new H01–H24 reviewer labels or predictions are collected. It is a **human judgement guide**, not a new or verified classification algorithm.

## Four evidence axes — fill these before choosing a relation

| Axis | Yes means | No means | Unknown means |
|---|---|---|---|
| `same_entity` | The text establishes the same specific person, object or event. | The text establishes different referents. | A generic pronoun or role could refer to more than one item. |
| `same_attribute` | Both claims concern the same particular property (e.g. meeting **day**, not general club news). | The properties are different (e.g. desk lamp versus desk plant). | The new statement only says something vague changed. |
| `old_fact_known_obsolete` | The text clearly invalidates that exact **old assertion** at a relevant time. | The old assertion could remain true or is repeated. | A change is reported, but it is not clear that this particular fact is outdated. |
| `new_value_known` | A specific replacement value for **that same attribute** is explicitly available. | No replacement value is provided (including a repeated same value). | The proposed value is incomplete or its attribute unclear. |

**Important distinctions:** Referring to `my cousin` does not prove it is a named cousin. One of several bikes is not automatically the described bike. `Meeting details changed` does not establish that the meeting **day** changed. Replacing a red collar may make the old collar obsolete but does not state the new collar's **colour**. A different role or different place alone does not imply replacement. A sentence that repeats an old value is not a new replacement value.

## Relation labels (D/R/C/U)

- **D — Duplicate:** same supported assertion, including clear paraphrases. Typically `same_entity=yes`, `same_attribute=yes`, `old_fact_known_obsolete=no`. Use storage action **D = Skip duplicate**.
- **R — Replaces:** text explicitly supports that the **same entity's same specific attribute** has been superseded, with a new value or explicit cessation of the old value. Requires `same_entity=yes`, `same_attribute=yes` and `old_fact_known_obsolete=yes`. `new_value_known` may be `no` for explicit cessation (e.g. `I stopped ...`), but the old assertion must be clearly invalid. Use **S = Supersede old** only when those three positive evidence axes hold; otherwise mark U instead.
- **C — Coexists:** both statements are independently compatible, and the new one does not cast plausible doubt on the specific old fact. They may refer to the same entity but different clearly named properties, or to two unambiguously distinct entities. Choose **K = Keep both**.
- **U — Uncertain:** a plausible update might invalidate the older fact but a missing referent, changed attribute, time or object makes supersession unresolved. Use **R = Review needed**; never automatically delete the old fact.

**Boundary rule:** When a new statement signals a change but its target is ambiguous, choose **U** rather than assuming **C** or **R**. When two facts clearly concern different properties that cannot invalidate each other, choose **C**, even if both involve the same person. `new_value_known=no` does not *by itself* force U if the text clearly says the old behaviour ended.

## Separate storage action

Record the relation and then select a storage recommendation. **D → Skip duplicate**, **R → Supersede old** (only if evidence axes support it), **C → Keep both**, **U → Review needed**. A storage action is not automatically executed by any evaluation tool. It is an annotation of what a cautious memory manager should recommend.

## Review protocol

1. Two humans should review the 24 new fictional cases separately, without seeing each other's answers, model outputs, or the original Experiment 010 labels.
2. Answer the **four evidence axes first**, then choose the relationship label, give a short explanation, and choose the storage action.
3. Each reviewer works in an independent local file, and locks it only after all 24 cases are complete. Warnings about internally inconsistent answers should be resolved before locking; unresolved ambiguity should receive U / Review needed, not a forced confident choice.
4. Only after **both** reviewer files are locked may the evaluator call Qwen. It compares raw Qwen with the existing safety gate using the same output per case. It reports predictions versus the **reviewer-consensus subset only**, plus the disagreement count. Do **not** treat consensus as expert-confirmed truth.
5. Record all prediction errors, abstention rate, false replacement suggestions and missed supported updates. If reviewers disagree, do not score that case as ground truth; adjudicate separately afterward. Never tune the gate to this set then continue calling it held out.

## Known limitations

These examples were authored within MemoryLab after seeing earlier results, not externally sampled. Although no labels or model predictions are distributed, this is a **fresh, author-created evaluation candidate**, not an independently designed or gold-standard benchmark. Independence of reviewers cannot be technically guaranteed. Cases do not measure the downstream effect on answers, long histories, memory deletion or privacy.

**Preservation:** No new classifier, Qwen prompts, storage rules, SQLite schema, or previous Experiment 010/011 records are modified by this phase.
