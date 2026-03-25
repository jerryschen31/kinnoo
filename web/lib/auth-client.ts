export type LoginCredentials = {
  email: string;
  password: string;
};

export type LoginResult = {
  ok: boolean;
  status: number;
};

export async function loginWithPassword(credentials: LoginCredentials): Promise<LoginResult> {
  const response = await fetch("/api/bff/login", {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email: credentials.email.trim(),
      password: credentials.password,
    }),
  });

  return {
    ok: response.ok,
    status: response.status,
  };
}
