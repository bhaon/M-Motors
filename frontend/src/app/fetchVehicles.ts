import { VEHICLES } from "@/data/vehicles";
import type { Vehicle } from "@/types";

/**
 * Récupère le catalogue depuis l'API ; retourne les données statiques en secours.
 */
export async function fetchVehicles(): Promise<Vehicle[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) return VEHICLES;

  try {
    const response = await fetch(`${apiUrl}/api/v1/vehicules`, {
      cache: "no-store",
    });
    if (!response.ok) return VEHICLES;

    const payload = (await response.json()) as { items?: Vehicle[] };
    return payload.items?.length ? payload.items : VEHICLES;
  } catch {
    return VEHICLES;
  }
}
