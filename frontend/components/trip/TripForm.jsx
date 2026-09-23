"use client";

import { useState } from "react";

export default function TripForm({ onSubmit }) {
  const [form, setForm] = useState({
    origin: "",
    destination: "",
    start_date: "",
    end_date: "",
    travelers: 2,
    budget: 60000,
    interests: ["history", "food", "photography"],
  });

  const [error, setError] = useState("");

  function updateField(field, value) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function toggleInterest(interest) {
    setForm((current) => {
      const exists = current.interests.includes(interest);

      return {
        ...current,
        interests: exists
          ? current.interests.filter((item) => item !== interest)
          : [...current.interests, interest],
      };
    });
  }

  function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!form.origin.trim() || !form.destination.trim()) {
      setError("Please enter both your origin and destination.");
      return;
    }

    if (!form.start_date || !form.end_date) {
      setError("Please select your travel dates.");
      return;
    }

    if (new Date(form.end_date) <= new Date(form.start_date)) {
      setError("End date must be after start date.");
      return;
    }

    if (Number(form.travelers) < 1) {
      setError("At least one traveler is required.");
      return;
    }

    if (Number(form.budget) <= 0) {
      setError("Budget must be greater than zero.");
      return;
    }

    onSubmit({
      origin: form.origin.trim(),
      destination: form.destination.trim(),
      start_date: form.start_date,
      end_date: form.end_date,
      travelers: Number(form.travelers),
      budget: {
        total: {
          amount: Number(form.budget),
          currency: "INR",
        },
      },
      profile: {
        travelers: Number(form.travelers),
        interests: form.interests,
      },
    });
  }

  const interests = [
    "history",
    "food",
    "photography",
    "nature",
    "shopping",
    "adventure",
  ];

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10">
      <div className="mx-auto max-w-4xl">
        <div className="mb-10 text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.25em] text-slate-500">
            TripMind
          </p>

          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Plan your next trip
          </h1>

          <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-slate-600">
            Tell TripMind where you're going, when you're travelling, and what
            matters to you. We'll build a verified trip around your constraints.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
        >
          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                From
              </label>

              <input
                value={form.origin}
                onChange={(e) => updateField("origin", e.target.value)}
                placeholder=""
                className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Destination
              </label>

              <input
                value={form.destination}
                onChange={(e) =>
                  updateField("destination", e.target.value)
                }
                placeholder=""
                className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Start date
              </label>

              <input
                type="date"
                value={form.start_date}
                onChange={(e) =>
                  updateField("start_date", e.target.value)
                }
                className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                End date
              </label>

              <input
                type="date"
                value={form.end_date}
                onChange={(e) => updateField("end_date", e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Travelers
              </label>

              <input
                type="number"
                min="1"
                value={form.travelers}
                onChange={(e) =>
                  updateField("travelers", e.target.value)
                }
                className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Total budget (₹)
              </label>

              <input
                type="number"
                min="1"
                value={form.budget}
                onChange={(e) => updateField("budget", e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>
          </div>

          <div className="mt-8">
            <label className="mb-3 block text-sm font-medium text-slate-700">
              What are you interested in?
            </label>

            <div className="flex flex-wrap gap-2">
              {interests.map((interest) => {
                const selected = form.interests.includes(interest);

                return (
                  <button
                    key={interest}
                    type="button"
                    onClick={() => toggleInterest(interest)}
                    className={`rounded-full border px-4 py-2 text-sm font-medium capitalize transition ${
                      selected
                        ? "border-slate-900 bg-slate-900 text-white"
                        : "border-slate-300 bg-white text-slate-700 hover:border-slate-500"
                    }`}
                  >
                    {interest}
                  </button>
                );
              })}
            </div>
          </div>

          {error && (
            <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="mt-8 w-full rounded-xl bg-slate-900 px-6 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            Plan my trip →
          </button>
        </form>
      </div>
    </main>
  );
}