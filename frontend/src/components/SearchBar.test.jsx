import { fireEvent, render, screen } from "@testing-library/react";
import SearchBar from "./SearchBar";

describe("SearchBar", () => {
  it("déclenche onField et onSearch avec les bonnes valeurs", () => {
    const onField = jest.fn();
    const onSearch = jest.fn();

    render(
      <SearchBar
        marques={["Renault"]}
        modeles={["Clio V"]}
        marque=""
        modele=""
        moteur=""
        kmMax={null}
        prixMax={null}
        onField={onField}
        onSearch={onSearch}
      />,
    );

    fireEvent.change(screen.getAllByRole("combobox")[0], {
      target: { value: "Renault" },
    });
    expect(onField).toHaveBeenCalledWith("marque", "Renault");

    fireEvent.change(screen.getByPlaceholderText("Ex: 25000"), {
      target: { value: "25000" },
    });
    expect(onField).toHaveBeenCalledWith("prixMax", 25000);

    fireEvent.click(screen.getByRole("button", { name: "Rechercher" }));
    expect(onSearch).toHaveBeenCalledTimes(1);
  });
});
