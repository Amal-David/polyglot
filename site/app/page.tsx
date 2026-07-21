const githubUrl = "https://github.com/Amal-David/polyglot";

const hostEvidence = [
  ["Codex Desktop + CLI", "One plugin surface", "Packaged skill and fail-soft Stop hook"],
  ["Claude Code", "The same cadence", "Strictly validated optional Stop adapter"],
  ["Pi", "Broader support", "Canonical skill and native end-of-turn extension"],
  ["Hermes", "Broader support", "Namespaced skill, hook, and command registration"],
];

export default function Home() {
  return (
    <main>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Polyglot home">
          <span className="brand-mark" aria-hidden="true">P</span>
          <span>Polyglot</span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#ambient">Watch</a>
          <a href="#data">Data</a>
          <a href="#hosts">Hosts</a>
          <a className="github-link" href={githubUrl}>GitHub ↗</a>
        </nav>
      </header>

      <div id="main-content">
        <section className="hero" id="top">
          <div className="hero-copy">
            <p className="eyebrow">Polyglot for Codex + Claude Code</p>
            <h1>Learn a language in the <em>pauses</em> between agent turns.</h1>
            <p className="hero-lede">
              Instead of staring at terminal churn, collect one useful word or
              phrase every few completed turns. No extra tab. No streak pressure.
              Just something small that adds up.
            </p>
            <div className="hero-actions">
              <a className="button button-primary" href={githubUrl}>Add Polyglot to your agent ↗</a>
              <a className="button button-secondary" href="#ambient">Watch five real turns</a>
            </div>
          </div>
          <aside className="phrase-card" aria-label="Ambient learning example">
            <div className="phrase-card-top"><span>TURN 5</span><span>EN → DE</span></div>
            <p className="catalog-count">hello → hallo</p>
            <p className="meaning">one small thing that compounds</p>
            <p className="privacy-tag">ungraded · local · quiet</p>
          </aside>
        </section>

        <section className="stat-strip" aria-label="Ambient learning summary">
          <div><strong>5</strong><span>completed turns</span></div>
          <div><strong>1</strong><span>useful phrase</span></div>
          <div><strong>74</strong><span>language directions</span></div>
          <div><strong>0</strong><span>model calls</span></div>
        </section>

        <section className="demo-section" id="ambient">
          <div className="section-heading">
            <p className="eyebrow">Real CLI capture</p>
            <h2>Five completed turns. One phrase worth keeping.</h2>
            <p>The shipped Stop hook stays quiet for four turns, then returns one small language-learning moment through the same path packaged for Codex and Claude Code.</p>
          </div>
          <div className="video-frame">
            <div className="video-bar"><span>Polyglot / Codex + Claude Code compatible Stop hook</span><span>Real terminal capture</span></div>
            <video controls playsInline preload="metadata" poster="/polyglot-poster.png">
              <source src="/polyglot-demo.mp4" type="video/mp4" />
              Your browser does not support the demo video.
            </video>
          </div>
          <details className="transcript"><summary>Read the demo transcript and summary</summary><p>A real isolated CLI capture invokes five completed-turn Stop events. The first four return no visible message. On the fifth, Polyglot emits <code>Polyglot starter · hello → hallo</code>. The video intentionally shows only the CLI behavior, while the packaged hook is shared by Codex and Claude Code.</p></details>
        </section>

        <section className="demo-section" id="review">
          <div className="section-heading">
            <p className="eyebrow">When you want deliberate practice</p>
            <h2>Recall it. Grade it. See it again when it matters.</h2>
            <p>The terminal review flow is optional and secondary: it turns ambient exposure into locally scheduled learning.</p>
          </div>
          <div className="review-terminal" aria-label="Actual Polyglot German typed recall sequence">
            <div className="video-bar"><span>polyglot / review</span><span>en-de · reverse</span></div>
            <pre><code>$ polyglot review --pair en-de --direction reverse{`\n\n`}Prompt: sehen{`\n`}Your answer: to see{`\n`}Answer: to see{`\n`}Grade [again/hard/good/easy]: good</code></pre>
            <dl className="review-ledger">
              <div><dt>Local due state</dt><dd>Next review: tomorrow</dd></div>
              <div><dt>Progress ledger</dt><dd>seen 1 · good 1 · due 0</dd></div>
            </dl>
          </div>
          <p className="annotation"><strong>Why “tomorrow”?</strong> The CLI displays the answer and accepts the grade. The due-tomorrow line explains the shipped deterministic new-card <code>good</code> interval—one day—not invented CLI output.</p>
        </section>

        <section className="how-section">
          <div className="section-heading">
            <p className="eyebrow">Privacy / token boundary</p>
            <h2>A narrow learning signal, kept local.</h2>
            <p>Practice state and the ambient companion have deliberately separate responsibilities.</p>
          </div>
          <div className="steps boundary-grid">
            <article><span>01 / TYPED INPUT</span><h3>Not retained</h3><p>Typed answers are not persisted. Explicit grades schedule local SQLite state.</p></article>
            <article><span>02 / AMBIENT</span><h3>Ungraded, then due-only</h3><p>A fresh pair can show one starter without creating learner state. After review begins, ambient reads due state only and never mutates mastery, grades, or intervals.</p></article>
            <article><span>03 / ISOLATION</span><h3>No injection</h3><p>No model or network call; no learner history, prompt, or transcript is injected into an agent turn.</p></article>
            <article><span>04 / AUDIT</span><h3>Inspectable</h3><p>The largest audited ambient line is 85 characters, about 43 tokens.</p></article>
          </div>
        </section>

        <section className="install-section" id="data">
          <div className="section-heading">
            <p className="eyebrow">Catalog / provenance</p>
            <h2>Broad coverage. Conservative new learning facts.</h2>
            <p>The 19,281-entry catalog supports the ambient moment. German already existed; the new metadata is automated and not native-speaker reviewed.</p>
          </div>
          <div className="fact-grid">
            <article><strong>520</strong><p>German learning-metadata records</p></article>
            <article><strong>119</strong><p>conservative exact-lemma article/gender facts</p></article>
            <article><strong>79</strong><p>exact-text clozes</p></article>
          </div>
          <p className="direction-note"><strong>New reverse directions:</strong> PL→EN 264, UK→EN 265, SV→EN 261, EL→EN 256. They are mechanically derived from existing shipped source records; no new translation or transliteration claims. Polyglot does not claim an official Duolingo top 20.</p>
        </section>

        <section className="education-note" id="hosts">
          <span className="note-index">INSIDE YOUR SESSION</span>
          <div><p className="eyebrow">Where it meets you</p><h2>Inside the coding session. Not in another tab.</h2></div>
          <p>Codex Desktop, Codex CLI, and Claude Code share the central Stop-hook experience. Pi and Hermes support extends the same idea to more agent workflows.</p>
          <div className="host-grid">
            {hostEvidence.map(([host, kind, evidence]) => <article key={host}><span>{kind}</span><h3>{host}</h3><p>{evidence}</p></article>)}
          </div>
        </section>

        <section className="final-cta">
          <p className="eyebrow">Make the waiting useful</p>
          <h2>Let every few turns teach you one thing.</h2>
          <div className="hero-actions"><a className="button button-light" href={githubUrl}>Add Polyglot to your agent ↗</a></div>
        </section>
      </div>
      <footer><span>Polyglot · educational content</span><span>Terminal CLI · experimental host adapters</span></footer>
    </main>
  );
}
