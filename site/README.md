# Polyglot landing page

The public Polyglot landing page is a Vinext site built for OpenAI Sites.
It includes the final Hyperframes demo, responsive product copy, installation
commands for Codex, Claude, Hermes, and Pi, and the host-native ambient support
contract.

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
The social preview, poster, fonts, and MP4 live under `public/`.
