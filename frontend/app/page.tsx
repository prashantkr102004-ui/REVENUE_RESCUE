import { BackendStatus } from "./components/backend-status";
import { CreateOrderTester } from "./components/create-order-tester";

export default function Home() {
  return (
    <main className="min-h-screen px-6 py-8 text-slate-950">
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-6xl flex-col justify-between">
        <nav className="flex items-center justify-between border-b border-slate-200 pb-5">
          <div className="text-sm font-semibold tracking-[0.18em] text-emerald-700">
            RAZORPAY HACKATHON
          </div>
          <BackendStatus />
        </nav>

        <div className="grid gap-10 py-16 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <p className="mb-4 text-sm font-semibold uppercase tracking-[0.18em] text-emerald-700">
              Merchant revenue operations
            </p>
            <h1 className="max-w-3xl text-5xl font-bold leading-tight text-slate-950 md:text-6xl">
              RevenueRescue AI
            </h1>
            <p className="mt-5 max-w-2xl text-xl leading-8 text-slate-700">
              Autonomous Revenue Recovery Engine
            </p>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white/80 p-6 shadow-sm backdrop-blur">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-950">Recovery Pipeline</h2>
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                Foundation
              </span>
            </div>
            <div className="space-y-3 text-sm text-slate-600">
              {[
                "Failed payment intake",
                "Recovery probability scoring",
                "Policy-validated action",
                "Merchant dashboard update",
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-center justify-between rounded-md border border-slate-100 bg-slate-50 px-4 py-3"
                >
                  <span>{item}</span>
                  <span className="text-xs font-medium text-slate-400">Soon</span>
                </div>
              ))}
            </div>
            <CreateOrderTester />
          </div>
        </div>
      </section>
    </main>
  );
}
