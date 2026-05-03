"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/apiClient";
import {
  canManageCatalog,
  clearAuth,
  getStoredToken,
  getStoredUser,
} from "@/lib/authStorage";

const MOTEURS = ["Essence", "Diesel", "Hybride", "Électrique"] as const;

type ModeOffre = "achat" | "location";

type AuthGate = "loading" | "ready" | "no-token" | "forbidden";

/**
 * Formulaire US-05-01 — création d’un véhicule (POST /api/v1/vehicules).
 * Photo principale : URL obligatoire ; upload fichier hors périmètre MVP (même logique que le seed).
 */
export default function VehicleCreateForm() {
  const router = useRouter();
  const [gate, setGate] = useState<AuthGate>("loading");

  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [year, setYear] = useState<number>(new Date().getFullYear());
  const [km, setKm] = useState(0);
  const [moteur, setMoteur] = useState<string>(MOTEURS[0]);
  const [prix, setPrix] = useState<number>(0);
  const [modeOffre, setModeOffre] = useState<ModeOffre>("achat");
  const [mensualite, setMensualite] = useState<number | "">("");
  const [img, setImg] = useState("");
  const [specCarburant, setSpecCarburant] = useState("");
  const [specBoite, setSpecBoite] = useState("");
  const [specCouleur, setSpecCouleur] = useState("");
  const [specPlaces, setSpecPlaces] = useState(5);
  const [specPuissance, setSpecPuissance] = useState("");
  const [visibleCatalogue, setVisibleCatalogue] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const [userLabel, setUserLabel] = useState<{
    first_name: string;
    last_name: string;
    role: string;
  } | null>(null);

  useEffect(() => {
    const t = getStoredToken();
    const u = getStoredUser();
    if (!t || !u) {
      setGate("no-token");
      return;
    }
    if (!canManageCatalog(u.role)) {
      setGate("forbidden");
      return;
    }
    setUserLabel({
      first_name: u.first_name,
      last_name: u.last_name,
      role: u.role,
    });
    setGate("ready");
  }, []);

  if (gate === "loading") {
    return (
      <p className="text-sm text-[var(--muted)]">Chargement de la session…</p>
    );
  }

  if (gate === "no-token") {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm">
        <p className="mb-2 font-medium text-amber-900">
          Connexion requise pour ajouter un véhicule.
        </p>
        <Link
          href="/back-office/login?redirect=/back-office/vehicules/nouveau"
          className="font-semibold text-[var(--cyan2)] underline"
        >
          Se connecter (back-office)
        </Link>
      </div>
    );
  }

  if (gate === "forbidden") {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-900">
        <p className="mb-2">
          Votre compte ne permet pas de gérer le catalogue (rôle client ou
          autre).
        </p>
        <button
          type="button"
          onClick={() => {
            clearAuth();
            router.push("/back-office/login");
          }}
          className="text-sm underline"
        >
          Changer de compte
        </button>
      </div>
    );
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const lld = modeOffre === "location";
    const mensNum = mensualite === "" ? null : Number(mensualite);

    if (!img.trim()) {
      setError("L’URL de la photo principale est obligatoire.");
      return;
    }
    if (lld && (mensNum === null || Number.isNaN(mensNum) || mensNum <= 0)) {
      setError(
        "Indiquez une mensualité LLD HT valide pour une offre en location.",
      );
      return;
    }

    const payload = {
      make: make.trim(),
      model: model.trim(),
      year,
      km,
      moteur,
      prix,
      lld,
      mensualite: lld ? mensNum : null,
      img: img.trim(),
      spec_carburant: specCarburant.trim(),
      spec_boite: specBoite.trim(),
      spec_couleur: specCouleur.trim(),
      spec_places: specPlaces,
      spec_puissance: specPuissance.trim(),
      visible_catalogue: visibleCatalogue,
    };

    setPending(true);
    try {
      const res = await apiFetch("/vehicules", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => ({}))) as {
          detail?: string | { msg?: string }[];
        };
        const msg =
          typeof data.detail === "string"
            ? data.detail
            : Array.isArray(data.detail)
              ? data.detail.map((d) => d.msg ?? "").join(" ")
              : `Erreur ${res.status}`;
        setError(msg || `Erreur ${res.status}`);
        return;
      }
      const created = (await res.json()) as { id: number };
      setSuccess(
        `Véhicule #${created.id} créé avec succès. Il est maintenant ${lld ? "disponible en LLD" : "proposé à l’achat"}${visibleCatalogue ? " et visible dans le catalogue public." : " (masqué du catalogue jusqu’à activation)."}`,
      );
      setMake("");
      setModel("");
      setKm(0);
      setPrix(0);
      setMensualite("");
      setImg("");
      setSpecCarburant("");
      setSpecBoite("");
      setSpecCouleur("");
      setSpecPuissance("");
      setModeOffre("achat");
    } catch {
      setError("Impossible de joindre l’API.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-[var(--muted)]">
          Connecté en tant que{" "}
          <strong>
            {userLabel?.first_name} {userLabel?.last_name}
          </strong>{" "}
          ({userLabel?.role})
        </p>
        <button
          type="button"
          onClick={() => {
            clearAuth();
            router.push("/back-office/login");
          }}
          className="text-sm text-[var(--muted)] underline"
        >
          Déconnexion
        </button>
      </div>

      <form
        onSubmit={onSubmit}
        className="space-y-6 rounded-[var(--radius)] border border-[var(--border)] bg-white p-6 shadow-[var(--shadow)]"
      >
        <h2 className="font-[family-name:Syne] text-lg font-bold text-[var(--navy)]">
          Nouveau véhicule
        </h2>

        {error ? (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
            {error}
          </p>
        ) : null}
        {success ? (
          <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
            {success}
          </p>
        ) : null}

        <fieldset className="grid gap-4 sm:grid-cols-2">
          <legend className="col-span-full mb-1 text-sm font-semibold text-[var(--navy)]">
            Identification
          </legend>
          <div className="sm:col-span-1">
            <label className="mb-1 block text-sm">Marque *</label>
            <input
              required
              value={make}
              onChange={(e) => setMake(e.target.value)}
              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm">Modèle *</label>
            <input
              required
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm">Année *</label>
            <input
              type="number"
              required
              min={1990}
              max={2035}
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm">Kilométrage *</label>
            <input
              type="number"
              required
              min={0}
              value={km}
              onChange={(e) => setKm(Number(e.target.value))}
              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm">Motorisation *</label>
            <select
              value={moteur}
              onChange={(e) => setMoteur(e.target.value)}
              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
            >
              {MOTEURS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm">Prix de vente HT (€) *</label>
            <input
              type="number"
              required
              min={0}
              step={0.01}
              value={prix}
              onChange={(e) => setPrix(Number(e.target.value))}
              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
            />
          </div>
        </fieldset>

        <fieldset>
          <legend className="mb-2 text-sm font-semibold text-[var(--navy)]">
            Offre (US-05-01)
          </legend>
          <div className="flex flex-wrap gap-4">
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="radio"
                name="mode"
                checked={modeOffre === "achat"}
                onChange={() => setModeOffre("achat")}
              />
              En vente (achat uniquement)
            </label>
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="radio"
                name="mode"
                checked={modeOffre === "location"}
                onChange={() => setModeOffre("location")}
              />
              En location (LLD)
            </label>
          </div>
          {modeOffre === "location" ? (
            <div className="mt-3 max-w-xs">
              <label className="mb-1 block text-sm">
                Mensualité LLD HT (€) *
              </label>
              <input
                type="number"
                min={0}
                step={1}
                value={mensualite}
                onChange={(e) =>
                  setMensualite(
                    e.target.value === "" ? "" : Number(e.target.value),
                  )
                }
                className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
              />
            </div>
          ) : null}
        </fieldset>

        <fieldset className="grid gap-4 sm:grid-cols-2">
          <legend className="col-span-full mb-1 text-sm font-semibold text-[var(--navy)]">
            Photo &amp; fiche technique
          </legend>
          <div className="sm:col-span-2">
            <label className="mb-1 block text-sm">
              URL photo principale *{" "}
              <span className="font-normal text-[var(--muted)]">
                (obligatoire — ex. hébergement image publique)
              </span>
            </label>
            <input
              type="url"
              required
              value={img}
              onChange={(e) => setImg(e.target.value)}
              placeholder="https://…"
              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm">
              Carburant / motorisation détail *
            </label>
            <input
              required
              value={specCarburant}
              onChange={(e) => setSpecCarburant(e.target.value)}
              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm">Boîte *</label>
            <input
              required
              value={specBoite}
              onChange={(e) => setSpecBoite(e.target.value)}
              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm">Couleur *</label>
            <input
              required
              value={specCouleur}
              onChange={(e) => setSpecCouleur(e.target.value)}
              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm">Places *</label>
            <input
              type="number"
              min={2}
              max={9}
              required
              value={specPlaces}
              onChange={(e) => setSpecPlaces(Number(e.target.value))}
              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="mb-1 block text-sm">Puissance *</label>
            <input
              required
              value={specPuissance}
              onChange={(e) => setSpecPuissance(e.target.value)}
              placeholder="ex. 130 ch"
              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
            />
          </div>
        </fieldset>

        <label className="flex cursor-pointer items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={visibleCatalogue}
            onChange={(e) => setVisibleCatalogue(e.target.checked)}
          />
          Visible dans le catalogue public immédiatement
        </label>

        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-lg bg-[var(--gold)] py-3 text-sm font-semibold text-[var(--navy)] hover:opacity-95 disabled:opacity-60"
        >
          {pending ? "Enregistrement…" : "Créer le véhicule"}
        </button>
      </form>
    </div>
  );
}
