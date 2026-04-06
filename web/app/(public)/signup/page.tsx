"use client";

import Link from "next/link";

export default function SignupPage() {
  return (
    <section className="flex min-h-[calc(100vh-14rem)] items-center justify-center px-4 py-8">
      <div className="w-full max-w-md rounded-card border border-white/10 bg-kinnoo-surface/70 p-6 shadow-xl sm:p-8">
        <h1 className="mb-2 text-3xl font-semibold tracking-tight text-kinnoo-text">Sign Up</h1>
        <p className="mb-6 text-sm text-white/70">Sign up is currently invite-only. Please contact me for early access.</p>

        <a
          href="https://twitter.com/messages/compose?recipient_id=4118511499"
          target="_blank"
          rel="noreferrer"
          className="inline-flex w-full items-center justify-center rounded-button border border-kinnoo-accent/70 bg-kinnoo-accent/10 px-4 py-2 text-sm font-semibold text-kinnoo-text transition hover:bg-kinnoo-accent/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
        >
          Contact Me
        </a>

        <p className="pt-5 text-sm text-white/70">
          Already have an account?{" "}
          <Link href="/login" className="underline decoration-white/40 underline-offset-4 hover:text-kinnoo-accent">
            Login
          </Link>
        </p>
      </div>
    </section>
  );
}
