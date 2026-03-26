"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { useSearchParams } from "next/navigation";

import FormField from "../../../../components/ui/form-field";
import { validateSignupPasswords } from "../../../../lib/auth-validation";

export default function SignupVerifyPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{ password?: string; confirmPassword?: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [confirmationMessage, setConfirmationMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    if (!token) {
      setSubmitError("Verification link is missing or invalid.");
      return;
    }

    const nextErrors = validateSignupPasswords(password, confirmPassword);
    setFieldErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/register-confirm", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ token, password: password.trim() }),
      });

      if (!response.ok) {
        setSubmitError("Unable to create your account right now. Please retry.");
        return;
      }

      setConfirmationMessage("Account created. Redirecting to your registry...");
    } catch {
      setSubmitError("Unable to create your account right now. Please retry.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="flex min-h-[calc(100vh-14rem)] items-center justify-center px-4 py-8">
      <div className="w-full max-w-md rounded-card border border-white/10 bg-kinnoo-surface/70 p-6 shadow-xl sm:p-8">
        <h1 className="mb-2 text-3xl font-semibold tracking-tight text-kinnoo-text">Create Account</h1>
        <p className="mb-6 text-sm text-white/70">Use a passphrase with 10 to 128 characters.</p>

        <form className="space-y-4" noValidate onSubmit={handleSubmit}>
          <FormField
            id="signup-password"
            name="password"
            label="Create Password"
            type="password"
            autoComplete="new-password"
            placeholder="Create a passphrase"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            error={fieldErrors.password}
            helperText="Long passphrases are easier to remember and harder to crack."
          />

          <FormField
            id="signup-confirm-password"
            name="confirmPassword"
            label="Confirm Password"
            type="password"
            autoComplete="new-password"
            placeholder="Confirm your passphrase"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            error={fieldErrors.confirmPassword}
          />

          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex w-full items-center justify-center rounded-button border border-kinnoo-accent/70 bg-kinnoo-accent/10 px-4 py-2 text-sm font-semibold text-kinnoo-text transition hover:bg-kinnoo-accent/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
          >
            {isSubmitting ? "Creating account..." : "Create Account"}
          </button>

          {confirmationMessage ? (
            <p role="status" className="text-sm text-emerald-300">
              {confirmationMessage}
            </p>
          ) : null}

          {submitError ? (
            <p role="alert" className="text-sm text-red-300">
              {submitError}
            </p>
          ) : null}
        </form>
      </div>
    </section>
  );
}
