# Dictation error taxonomy and diagnosis

The aligner reports observable text differences. The learner's listening cause is an evidence-based hypothesis, not a fact inferred from text alone.

## Observable categories

| Category | Observable evidence | Typical possible causes | Confidence rule |
|---|---|---|---|
| `omission` | Source token absent from dictation | unknown word, weak form, linking, attention lag | Ask whether the learner knows the word and whether replay reveals it |
| `misheard` | Different word recorded | similar sounds, context guess, incomplete parsing | Use audio evidence before naming a phoneme pattern |
| `spelling` | Same normalized word, different spelling | spelling/typing | Never count as a listening failure |
| `extra` | Dictation contains text not in source | anticipation, paraphrase, intrusion | Check whether the learner was summarizing |
| `vocabulary` | Word or term was not understood after transcript check | vocabulary gap | High confidence if learner confirms meaning is unknown |
| `phrase` | Words known separately but chunk was not recognized | collocation, idiom, formulaic language | High confidence when meaning becomes clear only after chunk explanation |
| `weak_form` | Function word or reduction is missed in audio | weak forms, contractions | Requires audio/timestamp evidence |
| `linking` | Boundary between words is missed or merged | liaison, assimilation, elision | Requires replay or timing evidence |
| `grammar` | Main clause, clause boundary, negation, comparison, or relation is misparsed | syntax load, discourse structure | High confidence when the words are individually recognized |
| `unclassified` | Evidence is insufficient | unknown | Leave as a question rather than overdiagnosing |

## Daily priority

Select only the top 2-3 categories or concrete patterns. A useful report names:

1. the repeated pattern;
2. one source example;
3. one listening action;
4. one short shadowing/retrieval task.

Example:

```text
Primary hypothesis: weak forms and linking
Evidence: to / at / and were omitted in three sentences around 00:08:42
Confidence: medium-high
Action: replay the three chunks at 0.8x, then shadow at 1.0x without looking
```

## Rules

- Preserve blanks such as `____`, `?`, and `没听出来`.
- Separate spelling from hearing.
- Do not infer pronunciation deficits from a written dictation.
- Use `annotations.json` to refine script-generated categories when audio evidence supports it.
- Do not turn every correction into an error category. Optional style improvements are not listening errors.
- Across sessions, repeat the same cause only when the evidence repeats.
