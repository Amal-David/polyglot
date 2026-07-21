# Data notes and corrections

Polyglot 1.0.0 contains 18,235 educational entries across 70 language
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

## What automated tests establish

The data tests verify structural properties:

- Exactly 70 pair modules and 18,235 entries load.
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
