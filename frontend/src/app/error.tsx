"use client";

/**
 * Affiche une erreur lorsque le catalogue (ou une autre partie de la page) échoue côté serveur ou client.
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto flex min-h-[40vh] max-w-lg flex-col items-center justify-center gap-4 px-4 text-center">
      <h1 className="text-xl font-semibold">Catalogue indisponible</h1>
      <p className="text-neutral-600">{error.message}</p>
      <button
        type="button"
        className="rounded bg-neutral-900 px-4 py-2 text-sm text-white hover:bg-neutral-800"
        onClick={reset}
      >
        Réessayer
      </button>
    </main>
  );
}
