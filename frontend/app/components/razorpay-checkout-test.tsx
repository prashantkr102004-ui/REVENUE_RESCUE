"use client";

import { FormEvent, useState } from "react";

type CreateOrderResponse = {
  internal_order_id: string;
  razorpay_order_id: string;
  amount: number;
  currency: string;
  razorpay_key_id: string;
};

type VerifyPaymentResponse = {
  status: "verified";
  payment_id: string;
  order_id: string;
};

type OrderPaymentStateResponse = {
  status: string | null;
  failure_reason: string | null;
  payment_method: string | null;
  external_payment_id: string | null;
  amount: number;
  currency: string;
};

type DemoCustomerResponse = {
  customer_id: string;
  name: string | null;
  email: string | null;
};

type RazorpaySuccessResponse = {
  razorpay_payment_id: string;
  razorpay_order_id: string;
  razorpay_signature: string;
};

type RazorpayFailureResponse = {
  error?: {
    description?: string;
    reason?: string;
    metadata?: {
      payment_id?: string;
      order_id?: string;
    };
  };
};

type RazorpayOptions = {
  key: string;
  amount: number;
  currency: string;
  order_id: string;
  name: string;
  description: string;
  handler: (response: RazorpaySuccessResponse) => void;
  modal: {
    ondismiss: () => void;
  };
};

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => {
      on: (event: "payment.failed", callback: (response: RazorpayFailureResponse) => void) => void;
      open: () => void;
    };
  }
}

type PaymentResult =
  | { status: "idle" }
  | { status: "loading"; message: string }
  | { status: "verified"; amount: string; paymentId: string; orderId: string; internalPaymentId: string }
  | {
      status: "failed";
      amount: string;
      failureReason: string;
      paymentMethod: string;
      paymentId: string;
    }
  | { status: "error"; message: string };

export function RazorpayCheckoutTest() {
  const [customerId, setCustomerId] = useState("");
  const [amountRupees, setAmountRupees] = useState("4999");
  const [result, setResult] = useState<PaymentResult>({ status: "idle" });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setResult({ status: "loading", message: "Creating Razorpay order..." });

    const amountPaise = rupeesToPaise(amountRupees);
    if (amountPaise === null || amountPaise <= 0) {
      setResult({ status: "error", message: "Enter a valid rupee amount." });
      return;
    }
    if (!isUuid(customerId)) {
      setResult({ status: "error", message: "Use a valid customer UUID. Click Use Demo Customer to fill one." });
      return;
    }

    try {
      const order = await createOrder({ customerId, amountPaise });
      setResult({ status: "loading", message: "Opening Razorpay Checkout..." });
      await loadRazorpayCheckout();
      openCheckout(order, amountRupees, setResult);
    } catch (error) {
      setResult({ status: "error", message: error instanceof Error ? error.message : "Payment setup failed." });
    }
  }

  const isLoading = result.status === "loading";

  async function handleUseDemoCustomer() {
    setResult({ status: "loading", message: "Loading demo customer..." });
    try {
      const demoCustomer = await getDemoCustomer();
      setCustomerId(demoCustomer.customer_id);
      setResult({ status: "idle" });
    } catch (error) {
      setResult({ status: "error", message: error instanceof Error ? error.message : "Could not load demo customer." });
    }
  }

  return (
    <div className="mt-8 rounded-lg border border-slate-200 bg-white/85 p-6 shadow-sm">
      <form onSubmit={handleSubmit} className="space-y-5">
        <label className="block">
          <span className="flex items-center justify-between gap-3 text-sm font-medium text-slate-700">
            Customer UUID
            <button
              className="rounded-md border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 hover:border-emerald-600 hover:text-emerald-700"
              type="button"
              onClick={handleUseDemoCustomer}
              disabled={isLoading}
            >
              Use Demo Customer
            </button>
          </span>
          <input
            className="mt-2 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-600"
            placeholder="Click Use Demo Customer or paste a UUID"
            value={customerId}
            onChange={(event) => setCustomerId(event.target.value)}
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-slate-700">Amount in rupees</span>
          <input
            className="mt-2 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-600"
            inputMode="decimal"
            placeholder="4999"
            value={amountRupees}
            onChange={(event) => setAmountRupees(event.target.value)}
          />
        </label>

        <button
          className="w-full rounded-md bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
          type="submit"
          disabled={isLoading || !customerId || !amountRupees}
        >
          {isLoading ? result.message : "Create Test Payment"}
        </button>
      </form>

      <ResultPanel result={result} />
    </div>
  );
}

function ResultPanel({ result }: { result: PaymentResult }) {
  if (result.status === "idle") {
    return <p className="mt-5 text-sm text-slate-500">Ready to create a Razorpay Test Mode payment.</p>;
  }

  if (result.status === "loading") {
    return <p className="mt-5 text-sm text-slate-500">{result.message}</p>;
  }

  if (result.status === "error") {
    return <p className="mt-5 rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">{result.message}</p>;
  }

  if (result.status === "failed") {
    return (
      <div className="mt-5 space-y-4">
        <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
          <p className="font-semibold tracking-wide">PAYMENT FAILED</p>
          <dl className="mt-3 space-y-2">
            <ResultRow label="Amount" value={result.amount} />
            <ResultRow label="Payment Status" value="Failed" />
            <ResultRow label="Failure Reason" value={result.failureReason} />
            <ResultRow label="Payment Method" value={result.paymentMethod} />
            <ResultRow label="Razorpay Payment ID" value={result.paymentId} />
          </dl>
        </div>
        <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
          <p className="font-semibold tracking-wide">REVENUE RESCUE</p>
          <dl className="mt-3 space-y-2">
            <ResultRow label="Failure Detected" value="Yes" />
            <ResultRow label="Recovery Status" value="Pending Analysis" />
            <ResultRow
              label="Next Step"
              value="Recovery engine will classify the failure and determine the best recovery action."
            />
          </dl>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-5 rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
      <p className="font-semibold">Payment Verified</p>
      <dl className="mt-3 space-y-2">
        <ResultRow label="Amount" value={result.amount} />
        <ResultRow label="Razorpay Payment ID" value={result.paymentId} />
        <ResultRow label="Razorpay Order ID" value={result.orderId} />
      </dl>
    </div>
  );
}

function ResultRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-1 sm:grid-cols-[180px_1fr]">
      <dt className="font-medium">{label}</dt>
      <dd className="break-all">{value}</dd>
    </div>
  );
}

async function createOrder({ customerId, amountPaise }: { customerId: string; amountPaise: number }) {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${apiBaseUrl}/api/payments/create-order`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customer_id: customerId, amount: amountPaise, currency: "INR" }),
  });

  const body = await response.json();
  if (!response.ok) {
    throw new Error(formatApiError(body, "Order creation failed."));
  }

  return body as CreateOrderResponse;
}

async function getDemoCustomer() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${apiBaseUrl}/api/dev/demo-customer`, { method: "POST" });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(formatApiError(body, "Could not load demo customer."));
  }

  return body as DemoCustomerResponse;
}

async function verifyPayment(response: RazorpaySuccessResponse) {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const verifyResponse = await fetch(`${apiBaseUrl}/api/payments/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(response),
  });
  console.log("verification response status", verifyResponse.status);

  const body = await verifyResponse.json();
  if (!verifyResponse.ok) {
    throw new Error(formatApiError(body, "Payment verification failed."));
  }

  return body as VerifyPaymentResponse;
}

async function getOrderPaymentState(internalOrderId: string) {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const response = await fetch(`${apiBaseUrl}/api/payments/order/${internalOrderId}`);
  const body = await response.json();
  if (!response.ok) {
    throw new Error(formatApiError(body, "Could not load payment state."));
  }

  return body as OrderPaymentStateResponse;
}

function openCheckout(
  order: CreateOrderResponse,
  amountRupees: string,
  setResult: (result: PaymentResult) => void,
) {
  let successCallbackFired = false;
  let failureCallbackFired = false;
  const checkout = new window.Razorpay!({
    key: order.razorpay_key_id,
    amount: order.amount,
    currency: order.currency,
    order_id: order.razorpay_order_id,
    name: "RevenueRescue AI",
    description: "Revenue Recovery Test Payment",
    handler: async (response) => {
      successCallbackFired = true;
      console.log("Razorpay success callback fired", {
        hasPaymentId: Boolean(response.razorpay_payment_id),
        hasOrderId: Boolean(response.razorpay_order_id),
        hasSignature: Boolean(response.razorpay_signature),
      });
      setResult({ status: "loading", message: "Verifying payment..." });
      try {
        console.log("Calling backend verification");
        const verified = await verifyPayment(response);
        setResult({
          status: "verified",
          amount: `INR ${amountRupees}`,
          paymentId: response.razorpay_payment_id,
          orderId: response.razorpay_order_id,
          internalPaymentId: verified.payment_id,
        });
      } catch (error) {
        setResult({ status: "error", message: error instanceof Error ? error.message : "Verification failed." });
      }
    },
    modal: {
      ondismiss: () => {
        if (successCallbackFired || failureCallbackFired) {
          return;
        }
        setResult({ status: "error", message: "Payment cancelled or checkout closed" });
      },
    },
  });

  checkout.on("payment.failed", async (response) => {
    failureCallbackFired = true;
    console.log("Razorpay payment.failed callback fired", {
      hasPaymentId: Boolean(response.error?.metadata?.payment_id),
      hasOrderId: Boolean(response.error?.metadata?.order_id),
    });
    setResult({ status: "loading", message: "Checking failed payment state..." });

    const fallbackReason = response.error?.description ?? response.error?.reason ?? "Failure reason unavailable";
    const fallbackPaymentId = response.error?.metadata?.payment_id ?? "Not available";

    try {
      const paymentState = await getOrderPaymentState(order.internal_order_id);
      setResult({
        status: "failed",
        amount: formatMoney(paymentState.currency, paymentState.amount),
        failureReason: paymentState.failure_reason ?? fallbackReason,
        paymentMethod: paymentState.payment_method ?? "Not available",
        paymentId: paymentState.external_payment_id ?? fallbackPaymentId,
      });
    } catch {
      setResult({
        status: "failed",
        amount: formatMoney(order.currency, order.amount),
        failureReason: fallbackReason,
        paymentMethod: "Not available",
        paymentId: fallbackPaymentId,
      });
    }
  });

  checkout.open();
  console.log("Checkout opened");
}

function loadRazorpayCheckout() {
  if (window.Razorpay) {
    return Promise.resolve();
  }

  return new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Checkout script failed to load."));
    document.body.appendChild(script);
  });
}

function rupeesToPaise(value: string) {
  const normalized = value.trim();
  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) {
    return null;
  }

  const [rupees, paise = ""] = normalized.split(".");
  return Number.parseInt(rupees, 10) * 100 + Number.parseInt(paise.padEnd(2, "0"), 10);
}

function isUuid(value: string) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value.trim());
}

function formatMoney(currency: string, amountInSmallestUnit: number) {
  const rupees = Math.trunc(amountInSmallestUnit / 100);
  const paise = Math.abs(amountInSmallestUnit % 100).toString().padStart(2, "0");
  return `${currency} ${rupees}.${paise}`;
}

function formatApiError(body: unknown, fallback: string) {
  if (!body || typeof body !== "object") {
    return fallback;
  }

  const detail = "detail" in body ? body.detail : undefined;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item && typeof item.msg === "string") {
          return item.msg;
        }
        return null;
      })
      .filter(Boolean)
      .join(" ");
  }

  return fallback;
}
