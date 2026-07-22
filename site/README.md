# Polyglot landing page

The public Polyglot landing page is a Vinext site with the current typed-recall
story, catalog provenance, and evidence-scoped host support. The Pagecast-safe
static handoff lives in `pagecast/`; it is dependency-free and references its
own local assets.

## Local development

```bash
npm ci
npm run dev
```

## Validation

```bash
npm test
```

The test performs a production build and verifies the server-rendered HTML.
The app preview assets live under `public/`. The canonical public Pagecast
bundle is self-contained under `pagecast/`, including local fonts, licenses,
favicon, the final video, the poster, and a hash-and-size manifest.

Published Pagecast URL:
<https://polyglot-5os.pages.dev/>
