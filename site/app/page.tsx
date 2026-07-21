const githubUrl = "https://github.com/Amal-David/polyglot";

const installs = [
  {
    host: "Codex",
    command:
      "codex plugin marketplace add Amal-David/polyglot\ncodex plugin add polyglot@polyglot",
  },
  {
    host: "Claude",
    command:
      "claude plugin marketplace add Amal-David/polyglot\nclaude plugin install polyglot@polyglot",
  },
  {
    host: "Hermes",
    command: "hermes plugins install Amal-David/polyglot --enable",
  },
  {
    host: "Pi",
    command: "pi install git:github.com/Amal-David/polyglot",
  },
];

const surfaces = [
  ["Codex", "Open Agent Skill", "Stop event banner"],
  ["Claude", "Plugin skill", "Stop system event"],
  ["Hermes", "Namespaced skill", "Response footer"],
  ["Pi", "Skill + command", "Native notification"],
];

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Polyglot home">
          <span className="brand-mark" aria-hidden="true">
            P
          </span>
          <span>Polyglot</span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#demo">Demo</a>
          <a href="#install">Install</a>
          <a className="github-link" href={githubUrl}>
            GitHub ↗
          </a>
        </nav>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow">Language learning inside the work</p>
          <h1>
            Every finished task can teach you{" "}
            <em>one useful phrase.</em>
          </h1>
          <p className="hero-lede">
            Polyglot brings 18,235 phrases across 70 language pairs into Codex,
            Claude, Hermes, and Pi—with pronunciation, context, and no extra
            model call.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="#install">
              Install Polyglot
            </a>
            <a className="button button-secondary" href={githubUrl}>
              View source ↗
            </a>
          </div>
        </div>

        <aside className="phrase-card" aria-label="Featured Japanese phrase">
          <div className="phrase-card-top">
            <span>EN → JA</span>
            <span>COURTESY · 001</span>
          </div>
          <p className="japanese" lang="ja">
            ありがとうございます
          </p>
          <p className="pronunciation">arigatou gozaimasu</p>
          <p className="meaning">thank you</p>
          <div className="phrase-card-bottom">
            <span>18,235 phrases</span>
            <span>70 language pairs</span>
          </div>
        </aside>
      </section>

      <section className="stat-strip" aria-label="Polyglot catalog summary">
        <div>
          <strong>18,235</strong>
          <span>bundled entries</span>
        </div>
        <div>
          <strong>70</strong>
          <span>language pairs</span>
        </div>
        <div>
          <strong>4</strong>
          <span>agent hosts</span>
        </div>
        <div>
          <strong>0</strong>
          <span>extra model calls</span>
        </div>
      </section>

      <section className="demo-section" id="demo">
        <div className="section-heading">
          <p className="eyebrow">See the lesson arrive</p>
          <h2>Finish the task. Learn the phrase.</h2>
          <p>
            Ambient mode is optional. When it is enabled and the cadence is
            due, Polyglot chooses an unseen phrase from your active pair and
            presents it through the host’s native surface.
          </p>
        </div>
        <div className="video-frame">
          <div className="video-bar">
            <span>Polyglot · EN → JA</span>
            <span>20 sec · sound on</span>
          </div>
          <video
            controls
            playsInline
            preload="metadata"
            poster="/polyglot-poster.png"
          >
            <source src="/polyglot-demo.mp4" type="video/mp4" />
            Your browser does not support the demo video.
          </video>
        </div>
      </section>

      <section className="how-section">
        <div className="section-heading">
          <p className="eyebrow">A tiny learning loop</p>
          <h2>Useful exposure without opening another app.</h2>
          <p>
            Polyglot remembers your pair and recent history, prioritizing
            unseen material before repeats. On-demand practice works even when
            ambient mode is off.
          </p>
        </div>
        <div className="steps">
          <article>
            <span>01</span>
            <h3>Choose a pair</h3>
            <code>polyglot pair en-ja</code>
            <p>Pick from 52 English-to-language and 18 reverse directions.</p>
          </article>
          <article>
            <span>02</span>
            <h3>Ask on demand</h3>
            <code>polyglot sample</code>
            <p>Get the phrase, pronunciation, meaning, and useful context.</p>
          </article>
          <article>
            <span>03</span>
            <h3>Opt into ambient</h3>
            <code>polyglot ambient enable --pair en-ja --cadence 5</code>
            <p>One due phrase after a finished turn—never during the work.</p>
          </article>
        </div>
      </section>

      <section className="install-section" id="install">
        <div className="section-heading">
          <p className="eyebrow">One skill, four hosts</p>
          <h2>Install it where you already build.</h2>
          <p>
            The canonical skill is shared. The ambient presentation stays
            host-native, because Codex, Claude, Hermes, and Pi expose different
            extension surfaces.
          </p>
        </div>
        <div className="install-grid">
          {installs.map((install) => (
            <article className="install-card" key={install.host}>
              <h3>{install.host}</h3>
              <pre>
                <code>{install.command}</code>
              </pre>
            </article>
          ))}
        </div>

        <div className="surface-table" role="table" aria-label="Host support">
          <div className="surface-row surface-head" role="row">
            <span role="columnheader">Host</span>
            <span role="columnheader">On demand</span>
            <span role="columnheader">Ambient</span>
          </div>
          {surfaces.map(([host, onDemand, ambient]) => (
            <div className="surface-row" role="row" key={host}>
              <strong role="cell">{host}</strong>
              <span role="cell">{onDemand}</span>
              <span role="cell">{ambient}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="education-note">
        <span className="note-index">EDU / 01</span>
        <div>
          <p className="eyebrow">Educational content</p>
          <h2>Practice, not authoritative translation.</h2>
        </div>
        <p>
          Polyglot is for lightweight exposure and practice. It is not a
          substitute for a qualified translator or native-speaker review in
          medical, legal, emergency, financial, or safety-critical contexts.
        </p>
      </section>

      <section className="final-cta">
        <div className="glyph-wall" aria-hidden="true">
          あ · A · अ · ب · 한 · Ж
        </div>
        <p className="eyebrow">Learn as you build</p>
        <h2>Let the next finished task teach you something.</h2>
        <div className="hero-actions">
          <a className="button button-light" href={githubUrl}>
            Get Polyglot on GitHub ↗
          </a>
          <a className="text-link" href="#top">
            Back to the beginning ↑
          </a>
        </div>
      </section>

      <footer>
        <span>Polyglot · MIT-licensed software</span>
        <span>Codex · Claude · Hermes · Pi</span>
      </footer>
    </main>
  );
}
