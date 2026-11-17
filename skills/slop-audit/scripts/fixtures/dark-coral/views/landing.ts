const STYLE = `
  :root {
    --bg:#141311; --fg:#ecebe6;
    --accent:#f0875e;
    --font-sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  }
  .eyebrow{margin:0 0 12px;font:13px/1.4 ui-monospace,monospace;color:var(--accent)}
`;

export function landing(): string {
  return `<style>${STYLE}</style>
    <p class="eyebrow">api</p>
    <h1>Card data your agent can call.</h1>
    <p class="eyebrow">what you get</p>
    <h2>Start free. Pay for the layer you need.</h2>
    <p class="eyebrow">pricing</p>
    <h2>REST and JSON, with the pieces already written.</h2>`;
}
