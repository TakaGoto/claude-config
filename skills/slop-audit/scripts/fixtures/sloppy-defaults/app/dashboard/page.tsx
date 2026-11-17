import { Inter } from "next/font/google";

const inter = Inter({ subsets: ["latin"] });
const theme = { canvas: "#0B0B0B", accent: "#C6FF00" };

export default function Dashboard() {
  return (
    <main className={inter.className} style={{ background: theme.canvas }}>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="text-violet-500">Total Revenue</div>
        <div className="text-violet-500">Active Users</div>
        <div className="text-violet-500">Conversion</div>
        <div className="text-violet-500">Churn</div>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <a href="#" className="bg-violet-600">View all</a>
        <a href="#" className="bg-violet-600">Export</a>
        <a href="#" className="border-indigo-500">Settings</a>
      </div>
    </main>
  );
}
