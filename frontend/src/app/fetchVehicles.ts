import { VEHICLES } from "@/data/vehicles";
import type { Vehicle } from "@/types";

/**
 * Résout l'URL de base pour l'API catalogue : env public, même origine (navigateur),
 * ou URL interne (SSR Docker derrière nginx).
 */
function resolveVehiclesApiUrl(): string {
  const pub = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (pub) return `${pub.replace(/\/$/, "")}/api/v1/vehicules`;
  if (typeof window !== "undefined") return "/api/v1/vehicules";
  const internal = (process.env.API_INTERNAL_URL ?? "http://backend:8000").replace(
    /\/$/,
    "",
  );
  return `${internal}/api/v1/vehicules`;
}

/**
 * Récupère le catalogue depuis l'API ; retourne les données statiques en secours.
 */
export async function fetchVehicles(): Promise<Vehicle[]> {
  try {
    const response = await fetch(resolveVehiclesApiUrl(), { cache: "no-store" });
    if (!response.ok) return VEHICLES;

    const payload = (await response.json()) as { items?: Vehicle[] };
    return payload.items?.length ? payload.items : VEHICLES;
  } catch {
    return VEHICLES;
  }
}
