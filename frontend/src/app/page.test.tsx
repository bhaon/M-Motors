import { render, screen } from "@testing-library/react";
import { VEHICLES } from "@/data/vehicles";
import { fetchVehicles } from "./fetchVehicles";
import Home from "./page";

jest.mock("./fetchVehicles", () => ({
  fetchVehicles: jest.fn(),
}));

const mockedFetch = jest.mocked(fetchVehicles);

describe("Home (page.tsx)", () => {
  beforeEach(() => {
    mockedFetch.mockResolvedValue(VEHICLES.slice(0, 2));
  });

  it("compose la page catalogue à partir des véhicules récupérés", async () => {
    const tree = await Home();
    render(tree);
    expect(mockedFetch).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("navigation")).toBeInTheDocument();
    expect(screen.getByText(/Trouvez votre véhicule/i)).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
  });
});
