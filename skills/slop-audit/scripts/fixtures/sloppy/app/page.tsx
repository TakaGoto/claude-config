import { Inter } from "next/font/google";
import { Sparkles, Zap, Rocket, Shield, BarChart3 } from "lucide-react";
import { NumberTicker } from "@/components/magicui/number-ticker";
import { motion } from "framer-motion";

const inter = Inter({ subsets: ["latin"] });

export default function Home() {
  return (
    <main className={inter.className}>
      {/* Hero Section */}
      <section id="hero" className="max-w-7xl mx-auto px-4 py-24 text-center">
        <div className="absolute -top-40 left-1/2 h-96 w-96 rounded-full bg-purple-500/30 blur-3xl" />
        <p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">Introducing</p>
        <span className="inline-flex rounded-full border px-3 py-1 text-xs">New in v2</span>
        <h1 className="text-7xl font-bold tracking-tight">
          Ship faster with <span className="bg-gradient-to-r from-purple-600 to-blue-500 bg-clip-text text-transparent">AI</span>
        </h1>
        <p>Seamlessly elevate your workflow and unlock the power of your team — all in one place.</p>
        <button className="rounded-2xl bg-indigo-600 px-6 py-3 shadow-xl shadow-indigo-500/50 transition-all hover:scale-105">Get Started</button>
        <a href="#" className="text-indigo-600">See how it works →</a>
        <p>Trusted by 10,000+ teams worldwide</p>
      </section>
      {/* Features Section */}
      <section id="features" className="max-w-7xl mx-auto px-4 py-24">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} className="rounded-2xl border border-white/10 bg-zinc-950 p-6 shadow-lg backdrop-blur-xl transition-all hover:-translate-y-1">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10"><Zap /></div>
            <h3>🚀 Lightning-fast</h3>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} className="rounded-2xl border border-white/10 bg-zinc-950 p-6 shadow-lg backdrop-blur-xl transition-all hover:-translate-y-1">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10"><Shield /></div>
            <h3>✨ Robust security</h3>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} className="rounded-2xl border border-white/10 bg-zinc-950 p-6 shadow-lg backdrop-blur-xl transition-all hover:-translate-y-1">
            <div className="rounded-2xl border-l-4 border-l-indigo-500 bg-violet-600 p-4">Insights</div>
          </motion.div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 rounded-2xl bg-indigo-600 shadow-lg bg-gradient-to-br from-indigo-500 to-purple-600" />
        <div className="rounded-2xl border-l-4 border-l-violet-500 bg-zinc-950 shadow-lg bg-gradient-to-r">Card</div>
        <div className="flex gap-1.5"><span className="h-3 w-3 rounded-full bg-red-500" /><span className="h-3 w-3 rounded-full bg-yellow-500" /><span className="h-3 w-3 rounded-full bg-green-500" /></div>
        <span className="h-2 w-2 rounded-full bg-green-500 animate-ping" />
        <div className="rounded-2xl bg-violet-500 shadow-lg bg-gradient-to-tr border-white/10 bg-zinc-950" />
        <div className="rounded-2xl bg-violet-500 shadow-lg bg-gradient-to-tl border-white/10 bg-zinc-950" />
        <div className="rounded-2xl bg-violet-500 shadow-lg bg-gradient-to-b border-white/10 bg-zinc-950" />
        <div className="rounded-2xl text-violet-500 shadow-lg bg-gradient-to-t border-white/10 max-w-7xl mx-auto py-24" />
        <div className="rounded-2xl text-violet-500 shadow-lg bg-gradient-to-l max-w-7xl mx-auto py-24 transition-all hover:scale-105" />
        <div className="rounded-2xl max-w-7xl mx-auto py-24 transition-all font-mono text-xs uppercase tracking-wider" />
        <div className="rounded-2xl max-w-7xl mx-auto py-24 font-mono text-xs uppercase tracking-wider" />
        <span className="font-mono text-xs">updated</span>
        <span className="font-mono text-xs">synced</span>
        <span className="font-mono text-xs">beta</span>
        <span className="font-mono text-xs">v2</span>
        <div className="bg-[linear-gradient(to_right,#8882_1px,transparent_1px)]" />
        <NumberTicker value={99} />
        <img src="https://i.pravatar.cc/150?u=sarah" alt="" />
      </section>
      {/* Testimonials Section */}
      <section id="testimonials">
        <p>Sarah Chen, CEO at Acme</p>
        <p>Faster. Smarter. Simpler.</p>
        <p>No setup. Just results.</p>
      </section>
      <div className="rounded-2xl bg-gradient-to-r from-pink-500 to-orange-500 p-px"><div>Pro</div></div>
      <section id="pricing"><span>Most Popular</span><a href="#">Learn More</a><a href="#">Start Free Trial</a></section>
      <h2>Ten games, one wall.</h2>
      <h2>Come sit down.</h2>
      <h2>Built for the long run.</h2>
      <section id="faq"><p>Whether you're a startup or an enterprise — we have you covered.</p></section>
      <section id="cta"><p>Ready to supercharge your growth — today?</p><p>Docs · Changelog · Status</p></section>
      <p>Built with care · Made in SF · Since 2024</p>
      <p>Privacy · Terms · Cookies</p>
      <p>Pricing — simple</p>
      <p>Support — always on</p>
      <p>Uptime — 99.99%</p>
      <ol><li>01</li><li>02</li><li>03</li></ol>
      <a href="/docs" className="link">Read the docs →</a>
      <a href="/blog" className="link">Read the blog →</a>
      <p>✅ Instant setup 🎯</p>
    </main>
  );
}
