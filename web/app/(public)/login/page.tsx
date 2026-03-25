export default function LoginPage() {
  return (
    <section className="flex min-h-[calc(100vh-14rem)] items-center justify-center px-4 py-8">
      <div className="w-full max-w-md rounded-card border border-white/10 bg-kinnoo-surface/70 p-6 shadow-xl sm:p-8">
        <h1 className="mb-6 text-3xl font-semibold tracking-tight text-kinnoo-text">Login</h1>

        <form className="space-y-4" noValidate>
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
            />
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
            />
          </div>

          <button
            type="submit"
            className="mt-2 inline-flex w-full items-center justify-center rounded-button border border-kinnoo-accent/70 bg-kinnoo-accent/10 px-4 py-2 text-sm font-semibold text-kinnoo-text transition hover:bg-kinnoo-accent/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-kinnoo-accent"
          >
            Login
          </button>

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
