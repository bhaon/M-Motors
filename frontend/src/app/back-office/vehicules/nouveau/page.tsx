import VehicleCreateForm from "@/components/back-office/VehicleCreateForm";

/** US-05-01 — Page back-office : ajouter un véhicule au catalogue. */
export default function NouveauVehiculePage() {
  return (
    <div>
      <h1 className="font-[family-name:Syne] mb-2 text-2xl font-bold text-[var(--navy)]">
        Ajouter un véhicule
      </h1>
      <p className="mb-8 text-sm text-[var(--muted)]">
        Renseignez les informations ci-dessous. Une URL de photo principale est
        obligatoire. Choisissez si le véhicule est proposé à la vente ou en LLD.
      </p>
      <VehicleCreateForm />
    </div>
  );
}
