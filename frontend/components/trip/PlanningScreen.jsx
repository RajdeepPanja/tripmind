"use client";

import { useEffect, useState } from "react";

const stages = [
"Searching flights",
"Searching hotels",
"Finding places",
"Optimizing route",
"Building itinerary",
"Verifying trip",
];

export default function PlanningScreen({
onComplete,
error,
completed,
}) {
const [activeStage, setActiveStage] = useState(0);

useEffect(() => {
const interval = setInterval(() => {
setActiveStage((current) => {
if (current >= stages.length - 1) {
clearInterval(interval);
return current;
}

    return current + 1;
  });
}, 1100);

return () => clearInterval(interval);

}, []);

useEffect(() => {
if (!completed) return;

setActiveStage(stages.length - 1);

const timer = setTimeout(() => {
  onComplete();
}, 700);

return () => clearTimeout(timer);

}, [completed, onComplete]);

useEffect(() => {
if (!error) return;

const timer = setTimeout(() => {
  onComplete();
}, 500);

return () => clearTimeout(timer);

}, [error, onComplete]);

return (
<main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-white">
<div className="w-full max-w-xl">
<div className="mb-12 text-center">
<div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-2xl text-slate-950 shadow-lg">
✦
</div>

      <p className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-400">
        TripMind
      </p>

      <h1 className="mt-4 text-3xl font-bold sm:text-4xl">
        Building your trip
      </h1>

      <p className="mt-3 text-slate-400">
        Searching live travel data and optimizing your journey.
      </p>
    </div>

    <div className="space-y-3">
      {stages.map((stage, index) => {
        const completedStage = index < activeStage;
        const active = index === activeStage;

        return (
          <div
            key={stage}
            className={`flex items-center gap-4 rounded-2xl border px-5 py-4 transition-all duration-500 ${
              active
                ? "border-white/20 bg-white/10"
                : completedStage
                  ? "border-white/10 bg-white/5"
                  : "border-white/5 bg-transparent"
            }`}
          >
            <div
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
                completedStage
                  ? "bg-white text-slate-950"
                  : active
                    ? "bg-white/20 text-white"
                    : "bg-white/5 text-slate-600"
              }`}
            >
              {completedStage ? "✓" : index + 1}
            </div>

            <span
              className={`flex-1 ${
                active || completedStage
                  ? "text-white"
                  : "text-slate-600"
              }`}
            >
              {stage}
            </span>

            {active && !completed && !error && (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white" />
            )}

            {completedStage && (
              <span className="text-xs text-slate-400">Done</span>
            )}
          </div>
        );
      })}
    </div>

    {error ? (
      <div className="mt-8 rounded-2xl border border-red-400/20 bg-red-400/10 p-5 text-sm text-red-200">
        <div className="font-semibold">Trip planning failed</div>
        <div className="mt-1 text-red-300/80">{error}</div>
      </div>
    ) : (
      <p className="mt-8 text-center text-xs text-slate-500">
        TripMind is researching live travel data.
      </p>
    )}
  </div>
</main>

);
}