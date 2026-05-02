import { fireEvent, render, screen } from "@testing-library/react";
import VehicleModal from "./VehicleModal";
import { VEHICLES } from "@/data/vehicles";

describe("VehicleModal", () => {
  it("n'affiche rien si aucun véhicule n'est sélectionné", () => {
    const { container } = render(
      <VehicleModal vehicle={null} onClose={jest.fn()} onDossier={jest.fn()} />,
    );

    expect(container.firstChild).toBeNull();
  });

  it("gère fermeture clavier et actions dossier", () => {
    const onClose = jest.fn();
    const onDossier = jest.fn();
    const vehicle = VEHICLES.find((v) => v.lld) || VEHICLES[0];

    const { unmount } = render(
      <VehicleModal
        vehicle={vehicle}
        onClose={onClose}
        onDossier={onDossier}
      />,
    );

    expect(document.body.classList.contains("modal-open")).toBe(true);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Fermer" }));
    expect(onClose).toHaveBeenCalledTimes(2);

    fireEvent.click(screen.getByText("Déposer un dossier LLD"));
    expect(onDossier).toHaveBeenCalledWith(vehicle, "lld");

    fireEvent.click(screen.getByText("Déposer un dossier Achat"));
    expect(onDossier).toHaveBeenCalledWith(vehicle, "achat");

    unmount();
    expect(document.body.classList.contains("modal-open")).toBe(false);
  });
});
