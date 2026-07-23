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
    /<title>Polyglot — Learn a language between Codex and Claude Code turns<\/title>/i,
  );
  assert.match(html, /Learn a language in the/);
  assert.match(html, /pauses/);
  assert.match(html, /Instead of staring at terminal churn/);
  assert.match(html, /Codex Desktop \+ CLI/);
  assert.match(html, /19,281/);
  assert.match(html, /74/);
  assert.match(html, /polyglot review --pair en-de --direction reverse/);
  assert.match(html, /Prompt: sehen/);
  assert.match(html, /Answer: to see/);
  assert.match(html, /Grade \[again\/hard\/good\/easy\]: good/);
  assert.match(html, /Next review: tomorrow/);
  assert.match(html, /Typed answers are not persisted/);
  assert.match(html, /520/);
  assert.match(html, /119/);
  assert.match(html, /79/);
  assert.match(html, /PL→EN 264/);
  assert.match(html, /Accessible transcript/);
  assert.match(html, /autoplay=""/i);
  assert.doesNotMatch(html, /Real CLI capture|real isolated CLI capture/);
  assert.match(html, /Codex/);
  assert.match(html, /Claude/);
  assert.match(html, /Hermes/);
  assert.match(html, />Pi</);
  assert.match(html, /polyglot-demo\.mp4/);
  assert.match(html, /Actual Claude Code 2\.1\.218 session/);
  assert.match(html, /Opus 4\.8/);
  assert.match(html, /four-second highlighted hold/);
  assert.match(html, /Polyglot starter · hello → hallo/);
  assert.match(html, /all three tests passing/);
  assert.match(html, /github\.com\/Amal-David\/polyglot/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|host-native/);
});
