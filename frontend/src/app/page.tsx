import Navbar from '@/components/Navbar'
import Hero from '@/components/Hero'
import CataloguePage from '@/components/CataloguePage'
import { VEHICLES } from '@/data/vehicles'

export default function Home() {
  return (
    <main>
      <Navbar />
      <Hero vehicleCount={VEHICLES.length} />
      <CataloguePage />
    </main>
  )
}
