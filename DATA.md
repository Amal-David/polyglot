# Data notes and corrections

Polyglot 1.1.0 contains 19,281 educational entries across 74 language
directions. The collection lives in `polyglot/data/pair_*.py`; each entry stores
a source phrase, target phrase, pronunciation hint, category, subcategory, and
optional note.

## Provenance

The current collection was authored and curated directly for Polyglot and
entered into the repository's pair modules. It was not imported from a named
dictionary, standards body, certified translation memory, or single external
corpus. Git history preserves when each pair module entered the project and how
later corrections changed it.

That provenance is intentionally modest: the repository can prove the source
files and review history, but it must not imply professional translation or
native-speaker verification where none is recorded.

## V2 staged learning metadata

The v2 German path applies metadata to the pre-existing `en-de` and `de-en`
records; it does not replace them and does not call German newly added. Every
revised record carries a stable staging record ID, locale/script, learning
stage, topic, register state, provenance mapping, and reviewer state. German
noun article/gender facts are only attached to exact conservative lemma
matches. Word-order and contextual-cloze annotations are automated staging
facts and remain `not_native_reviewed`.

`pl-en`, `uk-en`, `sv-en`, and `el-en` are one-to-one reversals of existing
English-source records. They preserve original scripts and source mappings;
they contain no newly generated translations, transliterations, or
native-review claims. The bundled validation manifest records 520 German
learning-metadata records, including 119 conservative exact-lemma
article/gender facts and 79 exact-text clozes. Those annotations are automated
and **not native-speaker reviewed**. The four reverse directions contain 1,046
records: `pl-en` 264, `uk-en` 265, `sv-en` 261, and `el-en` 256. See the
code-level
`polyglot.data.content_v2.STAGING_MANIFEST` and `validate_v2_content` release
gates for reproducible integrity facts.

The expansion is evidence-informed rather than a claimed universal ranking.
The [2025 Duolingo Language Report](https://blog.duolingo.com/2025-duolingo-language-report/)
provides the demand context for the existing core (including English and
German); it is not used to claim an unsupported official top-20 list.

## What automated tests establish

The data tests verify structural properties:

- Exactly 74 registered directions and exactly 19,281 entries load.
- Pair ids and target strings are unique within their required scopes.
- Required fields are non-empty.
- Categories use the supported schema.
- Every pair has a minimum useful content budget.

These checks do **not** establish semantic accuracy, naturalness, regional
appropriateness, register, pronunciation quality, or safety for consequential
communication.

## Pronunciation and regional limits

Pronunciation values are approachable reading hints, not IPA transcriptions or
audio-backed guarantees. Languages vary by region, community, formality, and
speaker. Some entries choose one common form without claiming it is universal.

Polyglot is not suitable as the sole translation source for medical, legal,
emergency, immigration, financial, safety-critical, or other high-stakes use.

## Submit a correction

Open a **Language correction** issue and include:

1. Pair id, for example `en-es`.
2. Exact current source, target, pronunciation, and note.
3. Proposed replacement.
4. Language variety, region, script, and register.
5. A short rationale and a reliable reference when available.
6. Whether the same correction applies to a reverse-direction pair.

Native-speaker and language-educator review is strongly preferred. A
maintainer may request a second review when a change is regional, contested, or
affects many entries.

Corrections should edit the source pair module and add or adjust a focused
regression test when the error could recur. Do not patch generated output or
the host adapters.

Accepted contributions are provided under the repository's MIT license.
