import "./globals.css";

export const metadata = {
  title: "TripMind — AI Travel Operating System",
  description:
    "Plan real, verifiable trips with live travel data and multi-agent reasoning.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}