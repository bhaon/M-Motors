import { fireEvent, render, screen } from "@testing-library/react";
import VehicleCard from "./VehicleCard";
import { VEHICLES } from "@/data/vehicles";

describe("VehicleCard", () => {
  it("déclenche onClick sur la carte et le bouton", () => {
    const onClick = jest.fn();
    const vehicle = VEHICLES[0];

    render(<VehicleCard vehicle={vehicle} onClick={onClick} />);

    fireEvent.click(screen.getByText("Voir la fiche"));
    expect(onClick).toHaveBeenCalledWith(vehicle);

    fireEvent.click(screen.getByText(vehicle.model, { exact: false }));
    expect(onClick).toHaveBeenCalledTimes(2);
  });
});
