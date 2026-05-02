import { render, screen } from "@testing-library/react";
import Navbar from "./Navbar";

describe("Navbar", () => {
  it("affiche la marque et le lien catalogue", () => {
    render(<Navbar />);
    expect(screen.getByText(/M-/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Catalogue" })).toHaveAttribute(
      "href",
      "/",
    );
  });
});
