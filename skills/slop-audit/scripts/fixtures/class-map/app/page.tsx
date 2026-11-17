import localFont from "next/font/local";

const display = localFont({ src: "./fonts/SpaceGrotesk-Variable.woff2", variable: "--font-display" });

export default function Shop() {
  return (
    <main className={display.variable}>
      <p className="kicker">Every game</p>
      <h2>Singles</h2>
      <p className="kicker">This week</p>
      <h2>Events</h2>
      <p className="kicker">Visit</p>
      <h2>Hours</h2>
      <a className="lift" href="/a">A</a>
      <a className="lift" href="/b">B</a>
      <a className="lift" href="/c">C</a>
      <span className="label">Not an eyebrow: uppercase without tracking</span>
    </main>
  );
}
