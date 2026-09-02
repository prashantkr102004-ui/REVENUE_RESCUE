import { RazorpayCheckoutTest } from "../../components/razorpay-checkout-test";

export default function TestPaymentPage() {
  return (
    <main className="min-h-screen px-6 py-8 text-slate-950">
      <section className="mx-auto w-full max-w-3xl">
        <div className="border-b border-slate-200 pb-6">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-700">
            RevenueRescue AI
          </p>
          <h1 className="mt-3 text-4xl font-bold text-slate-950">Test Payment Simulator</h1>
        </div>
        <RazorpayCheckoutTest />
      </section>
    </main>
  );
}
