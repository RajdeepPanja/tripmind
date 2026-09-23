import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <div>
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.3em] text-muted-foreground">
          AI Travel Operating System
        </p>

        <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
          TripMind
        </h1>

        <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">
          Tell TripMind where you want to go, your budget and preferences.
          It researches live travel data, finds flights, hotels and places,
          builds an optimized itinerary, and verifies your trip.
        </p>
      </div>

      <Link
        href="/plan"
        className="rounded-xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-700"
      >
        Plan my trip →
      </Link>

      <p className="text-xs text-muted-foreground">
        Live data · Constraint-aware planning · Verified itineraries
      </p>
    </main>
  );
}