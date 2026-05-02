"use client";

import { useState } from "react";
import { Vehicle } from "@/types";
import { useFilters } from "@/hooks/useFilters";
import { useToast } from "@/hooks/useToast";
import SearchBar from "@/components/SearchBar";
import FiltersRow from "@/components/FiltersRow";
import VehicleCard from "@/components/VehicleCard";
import VehicleModal from "@/components/VehicleModal";
import Toast from "@/components/Toast";

export default function CataloguePage() {
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const { filters, filtered, marques, modeles, setType, setField, reset } =
    useFilters();
  const { toast, showToast } = useToast();

  function handleDossier(v: Vehicle, type: "lld" | "achat") {
    setSelectedVehicle(null);
    showToast(
      `Dossier ${type.toUpperCase()} initié pour ${v.make} ${v.model} — Redirection vers EP-03`,
    );
  }

  return (
    <>
      <SearchBar
        marques={marques}
        modeles={modeles}
        marque={filters.marque}
        modele={filters.modele}
        moteur={filters.moteur}
        kmMax={filters.kmMax}
        prixMax={filters.prixMax}
        onField={(field, value) =>
          setField(field as keyof typeof filters, value)
        }
        onSearch={() => {}}
      />

      <FiltersRow
        activeType={filters.type}
        count={filtered.length}
        onType={setType}
        onReset={reset}
      />

      {/* Grid */}
      {filtered.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "4rem 2rem",
            color: "var(--muted)",
          }}
        >
          <div style={{ fontSize: "3rem", marginBottom: "1rem", opacity: 0.4 }}>
            🔍
          </div>
          <h3
            style={{
              fontFamily: "Syne, sans-serif",
              fontSize: "1.1rem",
              color: "var(--navy)",
              marginBottom: ".5rem",
            }}
          >
            Aucun véhicule trouvé
          </h3>
          <p>Essayez d&apos;élargir vos critères de recherche</p>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: "1.25rem",
            padding: "0 2rem 3rem",
          }}
        >
          {filtered.map((v) => (
            <VehicleCard key={v.id} vehicle={v} onClick={setSelectedVehicle} />
          ))}
        </div>
      )}

      <VehicleModal
        vehicle={selectedVehicle}
        onClose={() => setSelectedVehicle(null)}
        onDossier={handleDossier}
      />

      <Toast message={toast.message} visible={toast.visible} />
    </>
  );
}
