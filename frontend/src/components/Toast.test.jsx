import { render, screen } from "@testing-library/react";
import Toast from "./Toast";

describe("Toast", () => {
  it("affiche le message", () => {
    render(<Toast message="Bonjour" visible />);
    expect(screen.getByText("Bonjour")).toBeInTheDocument();
  });
});
