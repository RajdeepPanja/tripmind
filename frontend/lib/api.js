const API_BASE_URL = "http://localhost:8001";

export async function createTrip(tripRequest) {
  const response = await fetch(`${API_BASE_URL}/api/trips`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "*/*",
    },
    body: JSON.stringify(tripRequest),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data?.detail?.[0]?.msg ||
        data?.detail ||
        "Trip planning request failed."
    );
  }

  return {
    ...data,
    request: tripRequest,
  };
}