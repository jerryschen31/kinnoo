export type LoginCredentials = {
  email: string;
  password: string;
};

export type LoginResult = {
  ok: boolean;
  status: number;
};

export type AuthMeResult = {
  ok: boolean;
  status: number;
};

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  const encodedName = `${encodeURIComponent(name)}=`;
  const cookie = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(encodedName));

  if (!cookie) {
    return null;
  }

  return decodeURIComponent(cookie.slice(encodedName.length));
}

function extractLoginCsrfToken(html: string): string | null {
  const match = html.match(/name="csrf_token"\s+value="([^"]+)"/i);
  return match?.[1] ?? null;
}

async function fetchLoginCsrfToken(): Promise<string | null> {
  const response = await fetch("/api/login", {
    method: "GET",
    credentials: "include",
    cache: "no-store",
  });

  if (!response.ok) {
    return null;
  }

  const html = await response.text();
  return extractLoginCsrfToken(html);
}

function isSuccessfulLoginResponse(response: Response): boolean {
  if (response.ok) {
    return true;
  }

  // With redirect: "manual", successful auth redirects can appear as opaque
  // redirects (status 0) depending on browser/runtime behavior.
  if (response.type === "opaqueredirect") {
    return true;
  }

  // Backend currently returns 303 on successful form login.
  return response.status === 303;
}

export async function loginWithPassword(credentials: LoginCredentials): Promise<LoginResult> {
  const csrfToken = await fetchLoginCsrfToken();

  const form = new URLSearchParams();
  form.set("username", credentials.email.trim());
  form.set("password", credentials.password);
  if (csrfToken) {
    form.set("csrf_token", csrfToken);
  }

  const response = await fetch("/api/login", {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    redirect: "manual",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: form.toString(),
  });

  return {
    ok: isSuccessfulLoginResponse(response),
    status: response.status,
  };
}

export async function postWithSessionCsrf(path: string): Promise<Response> {
  const csrfToken = readCookie("kinnoo_csrf");
  const form = new URLSearchParams();
  if (csrfToken) {
    form.set("csrf_token", csrfToken);
  }

  return fetch(path, {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
    },
    body: form.toString(),
  });
}

export async function logoutWithSessionCsrf(): Promise<LoginResult> {
  const response = await postWithSessionCsrf("/api/logout");
  return {
    ok: response.ok,
    status: response.status,
  };
}

export async function fetchAuthMeServer(cookieHeader: string): Promise<AuthMeResult> {
  const backendBaseUrl = (
    process.env.BACKEND_URL ?? process.env.KINNOO_API_BASE_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");

  const response = await fetch(`${backendBaseUrl}/api/auth/me`, {
    method: "GET",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(cookieHeader ? { Cookie: cookieHeader } : {}),
    },
  });

  return {
    ok: response.ok,
    status: response.status,
  };
}
