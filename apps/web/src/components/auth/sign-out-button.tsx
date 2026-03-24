"use client";

import { useState } from "react";
import { supabaseClient } from "@/lib/supabase/client";

export function SignOutButton() {
  const [message, setMessage] = useState("");

  async function onSignOut() {
    const { error } = await supabaseClient.auth.signOut();
    setMessage(error ? error.message : "Signed out");
  }

  return (
    <div>
      <button onClick={onSignOut} type="button">
        Sign out
      </button>
      <p>{message}</p>
    </div>
  );
}
