import { fireEvent, render, screen } from "@testing-library/react";
import FiltersRow from "./FiltersRow";

describe("FiltersRow", () => {
  it("affiche le compteur et déclenche les callbacks", () => {
    const onType = jest.fn();
    const onReset = jest.fn();

    render(
      <FiltersRow activeType="all" count={2} onType={onType} onReset={onReset} />,
    );

    expect(screen.getByText("2 véhicules")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Achat"));
    expect(onType).toHaveBeenCalledWith("achat");

    fireEvent.click(screen.getByText("Réinitialiser les filtres"));
    expect(onReset).toHaveBeenCalledTimes(1);
  });
});
