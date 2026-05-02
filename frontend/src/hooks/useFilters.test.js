import { act, renderHook } from "@testing-library/react";
import { useFilters } from "./useFilters";
import { VEHICLES } from "@/data/vehicles";

describe("useFilters", () => {
  it("retourne les marques triées et uniques", () => {
    const { result } = renderHook(() => useFilters());
    const expected = [...new Set(VEHICLES.map((v) => v.make))].sort((a, b) =>
      a.localeCompare(b),
    );

    expect(result.current.marques).toEqual(expected);
  });

  it("filtre les véhicules par marque et réinitialise le modèle", () => {
    const { result } = renderHook(() => useFilters());

    act(() => {
      result.current.setField("modele", "Test");
      result.current.setField("marque", "Peugeot");
    });

    expect(result.current.filters.modele).toBe("");
    expect(result.current.filtered.every((v) => v.make === "Peugeot")).toBe(
      true,
    );
  });

  it("filtre par type lld uniquement", () => {
    const { result } = renderHook(() => useFilters());

    act(() => {
      result.current.setType("lld");
    });

    expect(result.current.filtered.length).toBeGreaterThan(0);
    expect(result.current.filtered.every((v) => v.lld)).toBe(true);
  });
});
