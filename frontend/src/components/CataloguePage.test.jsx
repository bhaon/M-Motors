import { fireEvent, render, screen } from "@testing-library/react";
import CataloguePage from "./CataloguePage";
import { VEHICLES } from "@/data/vehicles";

describe("CataloguePage", () => {
  it("affiche l'état vide si aucun véhicule", () => {
    render(<CataloguePage vehicles={[]} />);
    expect(screen.getByText("Aucun véhicule trouvé")).toBeInTheDocument();
  });

  it("affiche les cartes et ouvre la fiche au clic", () => {
    const v = VEHICLES[0];
    render(<CataloguePage vehicles={[v]} />);

    fireEvent.click(document.querySelector(".vehicle-card"));
    expect(screen.getByRole("button", { name: "Fermer" })).toBeInTheDocument();
  });

  it("déclenche le toast après dépôt de dossier", () => {
    const v = VEHICLES[0];
    render(<CataloguePage vehicles={[v]} />);

    fireEvent.click(document.querySelector(".vehicle-card"));
    fireEvent.click(screen.getByText("Déposer un dossier LLD"));

    expect(screen.getByText(/Dossier LLD initié/i)).toBeInTheDocument();
  });

  it("met à jour les filtres via la barre de recherche", () => {
    render(<CataloguePage vehicles={VEHICLES} />);
    fireEvent.change(screen.getAllByRole("combobox")[0], {
      target: { value: "Peugeot" },
    });
    expect(screen.getAllByText("Peugeot").length).toBeGreaterThan(0);
  });

  it("ferme la modale via le bouton Fermer", () => {
    const v = VEHICLES[0];
    render(<CataloguePage vehicles={[v]} />);

    fireEvent.click(document.querySelector(".vehicle-card"));
    fireEvent.click(screen.getByRole("button", { name: "Fermer" }));
    expect(
      screen.queryByRole("button", { name: "Fermer" }),
    ).not.toBeInTheDocument();
  });
});
