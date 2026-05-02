/** @jest-environment node */

import { fetchVehicles } from "@/app/fetchVehicles";
import { VEHICLES } from "@/data/vehicles";

describe("fetchVehicles (SSR)", () => {
  const original = process.env.NEXT_PUBLIC_API_URL;
  const originalInternal = process.env.API_INTERNAL_URL;

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_URL = original;
    process.env.API_INTERNAL_URL = originalInternal;
    jest.restoreAllMocks();
  });

  it("appelle API_INTERNAL_URL sans NEXT_PUBLIC_API_URL côté Node", async () => {
    delete process.env.NEXT_PUBLIC_API_URL;
    process.env.API_INTERNAL_URL = "http://internal.test";
    const apiVehicle = { ...VEHICLES[0], id: 701 };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ items: [apiVehicle] }),
    });

    await expect(fetchVehicles()).resolves.toEqual([apiVehicle]);
    expect(global.fetch).toHaveBeenCalledWith(
      "http://internal.test/api/v1/vehicules",
      { cache: "no-store" },
    );
  });

  it("utilise http://backend:8000 par défaut côté Node", async () => {
    delete process.env.NEXT_PUBLIC_API_URL;
    delete process.env.API_INTERNAL_URL;
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ items: [{ ...VEHICLES[0], id: 702 }] }),
    });

    await fetchVehicles();
    expect(global.fetch).toHaveBeenCalledWith(
      "http://backend:8000/api/v1/vehicules",
      { cache: "no-store" },
    );
  });
});
