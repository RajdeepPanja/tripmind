export const mockTripData = {
  trip_id: "trip_demo_jaipur_001",
  status: "COMPLETED",

  request: {
    origin: "Kolkata",
    destination: "Jaipur",
    travelers: 2,
    budget: 60000,
    interests: ["history", "food", "photography"],
  },

  selected_flight: {
    airline: "IndiGo",
    flight_number: "6E 342",
    origin: "CCU",
    destination: "JAI",
    departure: "08:15",
    arrival: "10:55",
    duration: "2h 40m",
    stops: 0,
    price: 12400,
  },

  selected_hotel: {
    name: "Jaipur Heritage Stay",
    rating: 5.0,
    location: "Jaipur",
    price_per_night: 4200,
    nights: 4,
    total_price: 16800,
  },

  budget: {
    total: 60000,
    flight: 12400,
    hotel: 16800,
    food: 7200,
    activities: 4200,
    transport: 4460,
    remaining: 4940,
  },

  route_plan: {
    distance_km: 51,
    travel_time_minutes: 128,
  },

  verification: {
    passed: true,
    checks: 8,
    warnings: [],
  },

  places: [
    {
      id: "amber-fort",
      name: "Amber Fort",
      category: "History",
      rating: 4.6,
      area: "Amer",
    },
    {
      id: "city-palace",
      name: "City Palace",
      category: "History",
      rating: 4.5,
      area: "Old City",
    },
    {
      id: "hawa-mahal",
      name: "Hawa Mahal",
      category: "Photography",
      rating: 4.5,
      area: "Old City",
    },
    {
      id: "jantar-mantar",
      name: "Jantar Mantar",
      category: "History",
      rating: 4.4,
      area: "Old City",
    },
    {
      id: "nahargarh",
      name: "Nahargarh Fort",
      category: "Photography",
      rating: 4.5,
      area: "Aravalli Hills",
    },
    {
      id: "jal-mahal",
      name: "Jal Mahal",
      category: "Photography",
      rating: 4.4,
      area: "Amer Road",
    },
  ],

  itinerary: [
    {
      day: 1,
      title: "Arrival & Old Jaipur",
      activities: [
        {
          time: "11:30",
          name: "Hotel check-in & freshen up",
          type: "Stay",
        },
        {
          time: "13:00",
          name: "Lunch in the Old City",
          type: "Food",
        },
        {
          time: "15:00",
          name: "City Palace",
          type: "History",
        },
        {
          time: "17:00",
          name: "Hawa Mahal",
          type: "Photography",
        },
        {
          time: "19:30",
          name: "Traditional Rajasthani dinner",
          type: "Food",
        },
      ],
    },

    {
      day: 2,
      title: "Forts & Heritage",
      activities: [
        {
          time: "08:30",
          name: "Breakfast",
          type: "Food",
        },
        {
          time: "09:30",
          name: "Amber Fort",
          type: "History",
        },
        {
          time: "13:00",
          name: "Lunch near Amer",
          type: "Food",
        },
        {
          time: "15:00",
          name: "Jal Mahal",
          type: "Photography",
        },
        {
          time: "18:00",
          name: "Local market walk",
          type: "Shopping",
        },
      ],
    },

    {
      day: 3,
      title: "Science, Culture & Food",
      activities: [
        {
          time: "09:00",
          name: "Breakfast",
          type: "Food",
        },
        {
          time: "10:00",
          name: "Jantar Mantar",
          type: "History",
        },
        {
          time: "12:30",
          name: "Local lunch experience",
          type: "Food",
        },
        {
          time: "15:00",
          name: "Photography walk",
          type: "Photography",
        },
        {
          time: "19:00",
          name: "Rajasthani dinner",
          type: "Food",
        },
      ],
    },

    {
      day: 4,
      title: "Hills & Sunset",
      activities: [
        {
          time: "09:00",
          name: "Breakfast",
          type: "Food",
        },
        {
          time: "10:00",
          name: "Nahargarh Fort",
          type: "History",
        },
        {
          time: "13:30",
          name: "Lunch",
          type: "Food",
        },
        {
          time: "16:30",
          name: "Jaipur photography spots",
          type: "Photography",
        },
        {
          time: "18:00",
          name: "Sunset viewpoint",
          type: "Photography",
        },
      ],
    },
  ],
};