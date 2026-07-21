import assert from "node:assert/strict";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the complete Polyglot landing page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(
    html,
    /<title>Polyglot — Ambient language learning for coding agents<\/title>/i,
  );
  assert.match(html, /Every finished task can teach you/);
  assert.match(html, /18,235/);
  assert.match(html, /70 language pairs/);
  assert.match(html, /ありがとうございます/);
  assert.match(html, /Codex/);
  assert.match(html, /Claude/);
  assert.match(html, /Hermes/);
  assert.match(html, />Pi</);
  assert.match(html, /polyglot-demo\.mp4/);
  assert.match(html, /github\.com\/Amal-David\/polyglot/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape/);
});
