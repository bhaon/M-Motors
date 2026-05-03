"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/apiClient";
import { setAuth, type StoredUser } from "@/lib/authStorage";

/**
 * Connexion gestionnaire / superviseur / admin pour accéder au formulaire US-05-01.
 */
export default function BackOfficeLoginPage() {
  const router = useRouter();
  const [redirectTo, setRedirectTo] = useState(
    "/back-office/vehicules/nouveau",
  );

  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    const r = q.get("redirect");
    if (r?.startsWith("/")) setRedirectTo(r);
  }, []);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      const res = await apiFetch("/auth/login", {
        method: "POST",
        skipAuth: true,
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => ({}))) as {
          detail?: string;
        };
        setError(data.detail ?? `Erreur ${res.status}`);
        return;
      }
      const data = (await res.json()) as {
        access_token: string;
        user: StoredUser;
      };
      setAuth(data.access_token, data.user);
      router.push(redirectTo);
      router.refresh();
    } catch {
      setError("Impossible de joindre le serveur.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <h1 className="font-[family-name:Syne] mb-2 text-2xl font-bold text-[var(--navy)]">
        Connexion back-office
      </h1>
      <p className="mb-6 text-sm text-[var(--muted)]">
        Compte gestionnaire, superviseur ou administrateur requis pour ajouter
        un véhicule (
        <Link href="/" className="text-[var(--cyan2)] underline">
          retour au catalogue
        </Link>
        ).
      </p>

      <form
        onSubmit={onSubmit}
        className="mx-auto max-w-md space-y-4 rounded-[var(--radius)] border border-[var(--border)] bg-white p-6 shadow-[var(--shadow)]"
      >
        {error ? (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
            {error}
          </p>
        ) : null}
        <div>
          <label htmlFor="email" className="mb-1 block text-sm font-medium">
            E-mail
          </label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="password" className="mb-1 block text-sm font-medium">
            Mot de passe
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-lg bg-[var(--cyan)] py-2.5 text-sm font-semibold text-white hover:bg-[var(--cyan2)] disabled:opacity-60"
        >
          {pending ? "Connexion…" : "Se connecter"}
        </button>
      </form>
    </div>
  );
}
