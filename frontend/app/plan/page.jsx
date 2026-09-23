"use client";

import { useState } from "react";
import TripForm from "@/components/trip/TripForm";
import PlanningScreen from "@/components/trip/PlanningScreen";
import ResultsDashboard from "@/components/trip/ResultsDashboard";
import { createTrip } from "@/lib/api";

export default function PlanPage() {
  const [screen, setScreen] = useState("form");
  const [trip, setTrip] = useState(null);
  const [error, setError] = useState("");

  async function handleSubmit(formData) {
    setError("");
    setTrip(null);
    setScreen("planning");

    try {
      const result = await createTrip(formData);

      console.log("LIVE TRIP RESPONSE:", result);

      setTrip(result);
    } catch (err) {
      console.error("TripMind API error:", err);

      setError(
        err?.message || "Something went wrong while planning your trip."
      );
    }
  }

  function handlePlanningComplete() {
    if (trip) {
      setScreen("results");
    }
  }

  function handleBack() {
    setError("");
    setTrip(null);
    setScreen("form");
  }

  if (screen === "planning") {
    return (
      <PlanningScreen
        onComplete={handlePlanningComplete}
        error={error}
        completed={Boolean(trip)}
      />
    );
  }

  if (screen === "results" && trip) {
    return (
      <ResultsDashboard
        trip={trip}
        onBack={handleBack}
      />
    );
  }

  return <TripForm onSubmit={handleSubmit} />;
}