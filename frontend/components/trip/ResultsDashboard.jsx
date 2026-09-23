"use client";

function money(value) {
  if (value === null || value === undefined) return "—";

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(date) {
  if (!date) return "";

  return new Date(`${date}T00:00:00`).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
  });
}

function Stat({ label, value, sub }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
        {label}
      </p>

      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>

      {sub && (
        <p className="mt-1 text-sm text-slate-500">
          {sub}
        </p>
      )}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-5 text-lg font-bold text-slate-900">{title}</h2>

      {children}
    </section>
  );
}

export default function ResultsDashboard({ trip, onBack }) {
  const request = trip.request || {};

  const budget = trip.budget || {};
  const totalBudget = budget.total_budget?.amount || 0;
  const spent = budget.spent?.amount || 0;
  const remaining = budget.remaining?.amount || 0;

  const verification = trip.verification || {};
  const itinerary = trip.itinerary?.days || [];

  const selectedFlight = trip.selected_flight;
  const selectedHotel = trip.selected_hotel;

  const flightItems =
    budget.line_items?.find((item) => item.category === "flights")
      ?.amount?.amount || 0;

  const hotelItems =
    budget.line_items?.find((item) => item.category === "hotels")
      ?.amount?.amount || 0;

  const foodItems =
    budget.line_items?.find((item) => item.category === "food")
      ?.amount?.amount || 0;

  const activityItems =
    budget.line_items?.find((item) => item.category === "activities")
      ?.amount?.amount || 0;

  const transportItems =
    budget.line_items?.find((item) => item.category === "transport")
      ?.amount?.amount || 0;

  const totalPlaces = itinerary.reduce(
    (count, day) => count + (day.activities?.length || 0),
    0
  );

  const totalDistance = trip.route_plan?.total_distance_km || 0;

  const isVerified = verification.passed === true;

  // false means the selected flight + hotel is a fallback because
  // no available combination satisfied the requested budget.
  const budgetFeasible = trip.budget_feasible !== false;

  const isOverBudget = remaining < 0;
  const hasNoFlight = !selectedFlight;
  const hasBudgetFallback = !budgetFeasible && !hasNoFlight;

  const destination = request.destination || "Destination";

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      {/* Header */}

      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-950 text-white">
                ✦
              </div>

              <span className="text-lg font-bold">TripMind</span>
            </div>

            <p className="mt-2 text-sm text-slate-500">
              AI Travel Operating System
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div
              className={`rounded-full px-4 py-2 text-sm font-semibold ${
                isOverBudget
                  ? "bg-red-50 text-red-700"
                  : isVerified
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-amber-50 text-amber-700"
              }`}
            >
              {isOverBudget
                ? "⚠ Over budget"
                : isVerified
                  ? "✓ Trip verified"
                  : "⚠ Needs attention"}
            </div>

            <button
              onClick={onBack}
              className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-50"
            >
              New trip
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl space-y-8 px-6 py-8">
        {/* Hero */}

        <div>
          <p className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Your trip
          </p>

          <h1 className="mt-2 text-4xl font-bold tracking-tight">
            {request.origin} → {request.destination}
          </h1>

          <p className="mt-2 text-slate-500">
            {formatDate(request.start_date)} –{" "}
            {formatDate(request.end_date)} · {request.travelers} travelers ·{" "}
            {money(totalBudget)} budget
          </p>
        </div>

        {/* Budget feasibility warning */}

        {hasBudgetFallback && (
          <div className="rounded-3xl border border-red-200 bg-red-50 p-6">
            <div className="flex gap-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-red-100 text-xl">
                ⚠️
              </div>

              <div>
                <h2 className="text-lg font-bold text-red-900">
                  No available flight + hotel combination fits your budget
                </h2>

                <p className="mt-2 text-sm leading-6 text-red-800">
                  TripMind could not find a transport and hotel combination
                  within your requested budget after reserving money for food,
                  activities, local transport, and the safety buffer.
                </p>

                {trip.selection_reasons?.budget && (
                  <p className="mt-3 text-sm font-medium text-red-700">
                    {trip.selection_reasons.budget}
                  </p>
                )}

                <p className="mt-3 text-xs text-red-600">
                  The transport and hotel shown below are the cheapest
                  available fallback, not a budget-feasible selection.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Stats */}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat
            label="Trip cost"
            value={money(spent)}
            sub={
              remaining >= 0
                ? `${money(remaining)} remaining`
                : `${money(Math.abs(remaining))} over budget`
            }
          />

          <Stat
            label="Activities planned"
            value={totalPlaces}
            sub={`${itinerary.length} days`}
          />

          <Stat
            label="Local route"
            value={`${totalDistance.toFixed(1)} km`}
            sub={`${destination} sightseeing route`}
          />

          <Stat
            label="Data searched"
            value={
              (trip.sources?.flights_considered || 0) +
              (trip.sources?.hotels_considered || 0) +
              (trip.sources?.places_considered || 0)
            }
            sub="live results considered"
          />
        </div>

        {/* Verification / general warning */}

        {!isVerified && verification.violations?.length > 0 && (
          <div className="rounded-3xl border border-amber-200 bg-amber-50 p-6">
            <div className="flex gap-4">
              <div className="text-xl">⚠️</div>

              <div>
                <h2 className="font-bold text-amber-900">
                  Trip needs optimization
                </h2>

                <div className="mt-2 space-y-1">
                  {verification.violations.map((violation, index) => (
                    <p key={index} className="text-sm text-amber-800">
                      {violation.message}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Flight + Hotel */}

        <div className="grid gap-6 lg:grid-cols-2">
          <Section title="Selected flight">
  {selectedFlight ? (
    <div>
      {hasBudgetFallback && (
        <div className="mb-4 rounded-xl bg-red-50 px-4 py-3 text-xs font-semibold text-red-700">
          Fallback selection — no flight + hotel combination was available
          within the requested budget.
        </div>
      )}

      <div className="flex items-start justify-between">
        <div>
          <p className="text-xl font-bold">
            {selectedFlight.airline}
          </p>

          <p className="mt-1 text-sm text-slate-500">
            {selectedFlight.flight_number}
          </p>
        </div>

        <p className="text-xl font-bold">
          {money(selectedFlight.price?.amount)}
        </p>
      </div>

      <div className="mt-6 flex items-center justify-between">
        <div>
          <p className="text-2xl font-bold">
            {new Date(
              selectedFlight.departure_time
            ).toLocaleTimeString("en-IN", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>

          <p className="text-sm text-slate-500">
            {selectedFlight.origin_airport}
          </p>
        </div>

        <div className="flex-1 px-6 text-center">
          <p className="text-xs text-slate-400">
            {Math.floor(selectedFlight.duration_minutes / 60)}h{" "}
            {selectedFlight.duration_minutes % 60}m
          </p>

          <div className="my-2 h-px bg-slate-200" />

          <p className="text-xs font-medium text-emerald-600">
            {selectedFlight.stops === 0
              ? "Non-stop"
              : `${selectedFlight.stops} stop`}
          </p>
        </div>

        <div className="text-right">
          <p className="text-2xl font-bold">
            {new Date(
              selectedFlight.arrival_time
            ).toLocaleTimeString("en-IN", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>

          <p className="text-sm text-slate-500">
            {selectedFlight.destination_airport}
          </p>
        </div>
      </div>

      {/* Alternative transport advisory */}
      {hasBudgetFallback && (
        <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4">
          <p className="font-semibold text-amber-900">
            💡 Consider alternative transport
          </p>

          <p className="mt-1 text-sm leading-6 text-amber-800">
            This flight is not budget-feasible. You may want to check
            trains, buses, or other ground transport options for a
            lower-cost journey.
          </p>
        </div>
      )}
    </div>
  ) : (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
      <p className="font-semibold text-amber-900">
        ⚠️ No suitable flight found
      </p>

      <p className="mt-1 text-sm leading-6 text-amber-800">
        TripMind could not find a suitable flight for this trip.
        Consider checking trains, buses, or other ground transport
        options instead.
      </p>
    </div>
  )}
</Section>
          <Section title="Selected hotel">
            {selectedHotel ? (
              <div>
                {hasBudgetFallback && (
                  <div className="mb-4 rounded-xl bg-red-50 px-4 py-3 text-xs font-semibold text-red-700">
                    Fallback selection — cheapest available hotel.
                  </div>
                )}

                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xl font-bold">{selectedHotel.name}</p>

                    <p className="mt-1 text-sm text-slate-500">
                      ★ {selectedHotel.rating} ·{" "}
                      {selectedHotel.review_count} reviews
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="text-xl font-bold">
                      {money(selectedHotel.total_price?.amount)}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      total stay
                    </p>
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-2 gap-4">
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs text-slate-400">Per night</p>

                    <p className="mt-1 font-semibold">
                      {money(selectedHotel.price_per_night?.amount)}
                    </p>
                  </div>

                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs text-slate-400">Stay</p>

                    <p className="mt-1 font-semibold">
                      {selectedHotel.nights} nights
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-slate-500">No hotel selected.</p>
            )}
          </Section>
        </div>

        {/* Budget */}

        <Section title="Budget breakdown">
          <div className="space-y-4">
            {[
              ["Flights", flightItems],
              ["Hotels", hotelItems],
              ["Food", foodItems],
              ["Activities", activityItems],
              ["Transport", transportItems],
            ].map(([label, value]) => {
              const percentage =
                totalBudget > 0
                  ? Math.min((value / totalBudget) * 100, 100)
                  : 0;

              return (
                <div key={label}>
                  <div className="mb-2 flex justify-between text-sm">
                    <span className="font-medium">{label}</span>

                    <span className="font-semibold">{money(value)}</span>
                  </div>

                  <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-slate-900"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <p className="mt-5 text-xs text-slate-400">
            Food, activities, local transport, and the safety buffer are
            planning estimates rather than live booking prices.
          </p>

          <div className="mt-6 grid gap-4 border-t border-slate-100 pt-6 sm:grid-cols-3">
            <div>
              <p className="text-xs text-slate-400">Budget</p>

              <p className="mt-1 text-lg font-bold">{money(totalBudget)}</p>
            </div>

            <div>
              <p className="text-xs text-slate-400">Estimated spend</p>

              <p className="mt-1 text-lg font-bold">{money(spent)}</p>
            </div>

            <div>
              <p className="text-xs text-slate-400">Remaining</p>

              <p
                className={`mt-1 text-lg font-bold ${
                  remaining < 0 ? "text-red-600" : "text-emerald-600"
                }`}
              >
                {money(remaining)}
              </p>
            </div>
          </div>
        </Section>

        {/* Itinerary */}

        <Section title="Your itinerary">
          <div className="space-y-8">
            {itinerary.map((day) => (
              <div key={day.day_number}>
                <div className="mb-4 flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-950 text-sm font-bold text-white">
                    {day.day_number}
                  </div>

                  <div>
                    <p className="font-bold">Day {day.day_number}</p>

                    <p className="text-xs text-slate-400">
                      {formatDate(day.date)}
                    </p>
                  </div>
                </div>

                <div className="ml-4 border-l-2 border-slate-100 pl-6">
                  <div className="space-y-4">
                    {day.activities?.map((activity, index) => (
                      <div
                        key={`${day.day_number}-${index}`}
                        className="relative"
                      >
                        <div className="absolute -left-[31px] top-1.5 h-3 w-3 rounded-full border-2 border-white bg-slate-400 ring-1 ring-slate-200" />

                        <div className="rounded-2xl bg-slate-50 p-4">
                          <div className="flex items-start gap-4">
                            <span className="w-12 shrink-0 text-sm font-semibold text-slate-400">
                              {activity.time}
                            </span>

                            <div className="flex-1">
                              <p className="font-semibold">
                                {activity.title}
                              </p>

                              {activity.notes && (
                                <p className="mt-1 text-sm text-slate-500">
                                  {activity.notes}
                                </p>
                              )}

                              <p className="mt-2 text-xs text-slate-400">
                                {activity.duration_minutes} min
                                {activity.travel_to_next
                                  ? ` · ${activity.travel_to_next.duration_minutes} min travel`
                                  : ""}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* Verification */}

        <Section title="Trip verification">
          <div className="flex items-start gap-4">
            <div
              className={`flex h-11 w-11 items-center justify-center rounded-full ${
                isOverBudget
                  ? "bg-red-100 text-red-700"
                  : isVerified
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-amber-100 text-amber-700"
              }`}
            >
              {isOverBudget ? "!" : isVerified ? "✓" : "!"}
            </div>

            <div>
              <p className="font-bold">
                {isOverBudget
                  ? "Budget constraint could not be satisfied"
                  : isVerified
                    ? "All verification checks passed"
                    : "Verification found issues"}
              </p>

              <p className="mt-1 text-sm text-slate-500">
                Revision count: {trip.revision_count || 0}
              </p>

              {verification.violations?.map((violation, index) => (
                <p key={index} className="mt-2 text-sm text-amber-700">
                  • {violation.message}
                </p>
              ))}
            </div>
          </div>
        </Section>

        {/* Data sources */}

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <p className="text-xs uppercase tracking-wider text-slate-400">
              Flights
            </p>

            <p className="mt-2 text-2xl font-bold">
              {trip.sources?.flights_considered || 0}
            </p>

            <p className="text-sm text-slate-500">options considered</p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <p className="text-xs uppercase tracking-wider text-slate-400">
              Hotels
            </p>

            <p className="mt-2 text-2xl font-bold">
              {trip.sources?.hotels_considered || 0}
            </p>

            <p className="text-sm text-slate-500">options considered</p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <p className="text-xs uppercase tracking-wider text-slate-400">
              Places
            </p>

            <p className="mt-2 text-2xl font-bold">
              {trip.sources?.places_considered || 0}
            </p>

            <p className="text-sm text-slate-500">places researched</p>
          </div>
        </div>

        {/* Future controls */}


      </div>
    </main>
  );
}