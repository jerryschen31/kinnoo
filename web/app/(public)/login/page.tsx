"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { loginWithPassword } from "../../../lib/auth-client";
import { validateLoginFields } from "../../../lib/auth-validation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    const nextFieldErrors = validateLoginFields(email, password);
    setFieldErrors(nextFieldErrors);

    if (Object.keys(nextFieldErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await loginWithPassword({ email, password });

      if (response.ok) {
        router.push("/registry");
      } else {
        setSubmitError("Unable to sign in. Check your credentials and try again.");
      }
    } catch {
      setSubmitError("Unable to sign in right now. Please try again shortly.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="flex min-h-[calc(100vh-14rem)] items-center justify-center px-4 py-8">
      <div className="w-full max-w-md rounded-card border border-white/10 bg-kinnoo-surface/70 p-6 shadow-xl sm:p-8">
        <h1 className="mb-6 text-3xl font-semibold tracking-tight text-kinnoo-text">Login</h1>

        <form className="space-y-4" method="post" action="/login" noValidate onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label htmlFor="email" className="block text-sm font-medium text-white/85">
              Username (E-mail)
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              className="w-full rounded-button border border-white/20 bg-black/40 px-3 py-2 text-sm text-kinnoo-text placeholder:text-white/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              aria-invalid={Boolean(fieldErrors.email)}
              aria-describedby={fieldErrors.email ? "email-error" : undefined}
            />
            {fieldErrors.email ? (
              <p id="email-error" role="alert" className="text-sm text-red-300">
                {fieldErrors.email}
              </p>
            ) : null}
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="block text-sm font-medium text-white/85">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              className="w-full rounded-button border border-white/20 bg-black/40 px-3 py-2 text-sm text-kinnoo-text placeholder:text-white/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
              placeholder="Enter your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              aria-invalid={Boolean(fieldErrors.password)}
              aria-describedby={fieldErrors.password ? "password-error" : undefined}
            />
            {fieldErrors.password ? (
              <p id="password-error" role="alert" className="text-sm text-red-300">
                {fieldErrors.password}
              </p>
            ) : null}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-2 inline-flex w-full items-center justify-center rounded-button border border-kinnoo-accent/70 bg-kinnoo-accent/10 px-4 py-2 text-sm font-semibold text-kinnoo-text transition hover:bg-kinnoo-accent/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
          >
            {isSubmitting ? "Logging in..." : "Login"}
          </button>

          {submitError ? (
            <p role="alert" className="text-sm text-red-300">
              {submitError}
            </p>
          ) : null}

          <p className="pt-1 text-sm text-white/70">
            <a
              href="/forgot-password"
              className="underline decoration-white/40 underline-offset-4 transition hover:text-kinnoo-accent"
            >
              Forgot your password?
            </a>
          </p>
        </form>
      </div>
    </section>
  );
}
