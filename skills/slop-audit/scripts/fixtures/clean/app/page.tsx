import { Bricolage_Grotesque, Literata } from "next/font/google";

const display = Bricolage_Grotesque({ subsets: ["latin"], variable: "--font-display" });
const text = Literata({ subsets: ["latin"], variable: "--font-text" });

const shops = [
  { name: "Eastside Cards", city: "Berwyn", tables: 14 },
  { name: "Third Floor Games", city: "Oak Park", tables: 9 },
];

export default function Ledger() {
  return (
    <main className={`${display.variable} ${text.variable} bg-paper text-ink`}>
      <header className="border-b border-rule px-6 py-4">
        <a href="/" className="font-display text-lg">Tableside</a>
      </header>
      <section className="grid gap-8 px-6 py-16 lg:grid-cols-[2fr_1fr]">
        <div>
          <h1 className="font-display text-5xl leading-tight">Run Friday night without the clipboard.</h1>
          <p className="mt-4 max-w-prose font-text text-lg">
            Pair players, post standings and close out prize support from one tablet at the counter.
          </p>
          <a href="/start" className="mt-6 inline-block rounded-sm bg-ink px-4 py-2 text-paper focus-visible:outline">
            Set up your first event
          </a>
        </div>
        <table className="w-full font-text text-sm">
          <thead>
            <tr><th className="text-left">Shop</th><th className="text-left">City</th><th className="text-right">Tables</th></tr>
          </thead>
          <tbody>
            {shops.map((s) => (
              <tr key={s.name} className="border-t border-rule">
                <td>{s.name}</td><td>{s.city}</td><td className="text-right tabular-nums">{s.tables}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="px-6 py-10">
        <h2 className="font-display text-2xl">What changes on game night</h2>
        <ul className="mt-4 list-disc pl-5 font-text">
          <li>Round timers run on the tablet, so judges stop shouting the time.</li>
          <li>Players see their pairing on their phone when the round starts.</li>
          <li>Store credit for prizes posts to Square when you close the event.</li>
        </ul>
      </section>
    </main>
  );
}
