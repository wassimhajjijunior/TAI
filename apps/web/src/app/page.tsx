"use client";

import { useEffect, useState } from "react";
import { fetchApiHealth } from "@/lib/api/client";

export default function HomePage() {
  const [apiStatus, setApiStatus] = useState("unknown");

  useEffect(() => {
    fetchApiHealth()
      .then((result) => {
        setApiStatus(result.status);
      })
      .catch(() => {
        setApiStatus("unreachable");
      });
  }, []);

  return (
    <main>
      <h1>P2M-TAI</h1>
      <p>Foundation scaffold ready for Track A and Track B.</p>
      <p>API health: {apiStatus}</p>
    </main>
  );
}
