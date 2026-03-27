import type { ReactNode } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { fetchAuthMeServer } from "../../lib/auth-client";

export default async function AuthLayout({ children }: { children: ReactNode }) {
  const cookieStore = await cookies();
  const auth = await fetchAuthMeServer(cookieStore.toString());

  if (!auth.ok && auth.status === 401) {
    redirect("/login");
  }

  if (!auth.ok && auth.status === 429) {
    throw new Error("AUTH_RATE_LIMITED_429");
  }

  if (!auth.ok) {
    throw new Error("AUTH_API_UNAVAILABLE");
  }

  return <>{children}</>;
}
