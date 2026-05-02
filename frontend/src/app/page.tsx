import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import CataloguePage from "@/components/CataloguePage";
import { fetchVehicles } from "../lib/fetchVehicles";

export default async function Home() {
  const vehicles = await fetchVehicles();

  return (
    <main>
      <Navbar />
      <Hero vehicleCount={vehicles.length} />
      <CataloguePage vehicles={vehicles} />
    </main>
  );
}
