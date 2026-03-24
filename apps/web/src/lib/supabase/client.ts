import { createClient } from "@supabase/supabase-js";

function getRequiredEnv(name: "NEXT_PUBLIC_SUPABASE_URL" | "NEXT_PUBLIC_SUPABASE_ANON_KEY"): string {
  const value = process.env[name];
  if (!value) {
    if (name === "NEXT_PUBLIC_SUPABASE_URL") {
      return "http://127.0.0.1:54321";
    }
    return "replace-with-local-anon-key";
  }
  return value;
}

const supabaseUrl = getRequiredEnv("NEXT_PUBLIC_SUPABASE_URL");
const supabaseAnonKey = getRequiredEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY");

export const supabaseClient = createClient(supabaseUrl, supabaseAnonKey);
