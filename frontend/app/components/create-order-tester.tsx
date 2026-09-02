"use client";

import { FormEvent, useState } from "react";

type OrderResponse = {
  internal_order_id: string;
  razorpay_order_id: string;
  amount: number;
  currency: string;
  razorpay_key_id: string;
};

export function CreateOrderTester() {
  const [customerId, setCustomerId] = useState("");
  const [amount, setAmount] = useState("499900");
  const [currency, setCurrency] = useState("INR");
  const [result, setResult] = useState<string>("Idle");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setResult("Creating order...");

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

    try {
      const response = await fetch(`${apiBaseUrl}/api/payments/create-order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: customerId,
          amount: Number.parseInt(amount, 10),
          currency: currency.toUpperCase(),
        }),
      });

      const body = await response.json();
      if (!response.ok) {
        setResult(body.detail ?? "Order creation failed");
        return;
      }

      const order = body as OrderResponse;
      setResult(`Created ${order.razorpay_order_id}`);
    } catch {
      setResult("Backend unavailable");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 space-y-3 border-t border-slate-200 pt-4">
      <h3 className="text-sm font-semibold text-slate-950">Create Test Order</h3>
      <input
        className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-600"
        placeholder="Customer UUID"
        value={customerId}
        onChange={(event) => setCustomerId(event.target.value)}
      />
      <div className="grid grid-cols-[1fr_96px] gap-3">
        <input
          className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-600"
          inputMode="numeric"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
        />
        <input
          className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm uppercase outline-none focus:border-emerald-600"
          maxLength={3}
          value={currency}
          onChange={(event) => setCurrency(event.target.value)}
        />
      </div>
      <button
        className="w-full rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
        type="submit"
        disabled={isSubmitting || !customerId || !amount || !currency}
      >
        {isSubmitting ? "Creating..." : "Create Razorpay Order"}
      </button>
      <p className="min-h-5 text-xs text-slate-500">{result}</p>
    </form>
  );
}
