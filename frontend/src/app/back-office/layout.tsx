import Link from "next/link";

/** En-tête commun aux écrans back-office (connexion, création véhicule). */
export default function BackOfficeLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="min-h-screen bg-[var(--off)]">
      <header className="flex items-center justify-between bg-[var(--navy)] px-6 py-3 text-white shadow-md">
        <Link
          href="/back-office/vehicules/nouveau"
          className="font-[family-name:Syne] text-lg font-bold tracking-wide"
        >
          Back-office — <span className="text-[var(--cyan)]">M-MOTORS</span>
        </Link>
        <nav className="flex gap-5 text-sm">
          <Link href="/" className="opacity-90 hover:opacity-100">
            Catalogue public
          </Link>
          <Link
            href="/back-office/login"
            className="opacity-90 hover:opacity-100"
          >
            Connexion pro
          </Link>
        </nav>
      </header>
      <div className="mx-auto max-w-3xl px-4 py-8">{children}</div>
    </div>
  );
}
