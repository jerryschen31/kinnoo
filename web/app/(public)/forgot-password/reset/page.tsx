"use client";

import Link from "next/link";
import type { FormEvent } from "react";
import { useMemo, useState } from "react";

import FormField from "../../../../components/ui/form-field";
import {
  PASSWORD_MAX_LENGTH,
  PASSWORD_MIN_LENGTH,
  validateResetPasswords,
} from "../../../../lib/auth-validation";

type PageProps = {
  searchParams?: {
    token?: string;
  };
};

export default function ResetPasswordPage({ searchParams }: PageProps) {
  const token = typeof searchParams?.token === "string" ? searchParams.token : "";
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [newPasswordError, setNewPasswordError] = useState<string | undefined>(undefined);
  const [confirmPasswordError, setConfirmPasswordError] = useState<string | undefined>(undefined);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const tokenMissing = useMemo(() => token.trim().length === 0, [token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    const validation = validateResetPasswords(newPassword, confirmPassword);
    setNewPasswordError(validation.newPassword);
    setConfirmPasswordError(validation.confirmPassword);

    if (validation.newPassword || validation.confirmPassword) {
      return;
    }

    if (tokenMissing) {
      setSubmitError("Reset link is invalid or missing.");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/password-reset-confirm", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ token, new_password: newPassword }),
      });

      if (!response.ok) {
        setSubmitError("Unable to reset password. The link may be invalid or expired.");
        return;
      }

      setSuccess(true);
      setNewPassword("");
      setConfirmPassword("");
    } catch {
      setSubmitError("Unable to reset password. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="flex min-h-[calc(100vh-14rem)] items-center justify-center px-4 py-8">
      <div className="w-full max-w-md rounded-card border border-white/10 bg-kinnoo-surface/70 p-6 shadow-xl sm:p-8">
        <h1 className="mb-2 text-3xl font-semibold tracking-tight text-kinnoo-text">Reset Password</h1>
        <p className="mb-6 text-sm text-white/70">
          Choose a new password between {PASSWORD_MIN_LENGTH} and {PASSWORD_MAX_LENGTH} characters.
        </p>

        {success ? (
          <div className="space-y-3">
            <p role="status" className="text-sm text-emerald-300">
              Password reset complete.
            </p>
            <Link className="text-sm font-medium text-kinnoo-accent hover:underline" href="/login">
              Continue to login
            </Link>
          </div>
        ) : (
          <form className="space-y-4" noValidate onSubmit={handleSubmit}>
            <FormField
              id="reset-password"
              name="new-password"
              label="New password"
              type="password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              error={newPasswordError}
              helperText={`Use ${PASSWORD_MIN_LENGTH}-${PASSWORD_MAX_LENGTH} characters.`}
            />

            <FormField
              id="reset-confirm-password"
              name="confirm-password"
              label="Confirm new password"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              error={confirmPasswordError}
            />

            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex w-full items-center justify-center rounded-button border border-kinnoo-accent/70 bg-kinnoo-accent/10 px-4 py-2 text-sm font-semibold text-kinnoo-text transition hover:bg-kinnoo-accent/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
            >
              {isSubmitting ? "Resetting..." : "Reset Password"}
            </button>

            {submitError ? (
              <p role="alert" className="text-sm text-red-300">
                {submitError}
              </p>
            ) : null}
          </form>
        )}
      </div>
    </section>
  );
}
