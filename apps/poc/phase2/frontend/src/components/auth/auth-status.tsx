"use client";

import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase, isSupabaseConfigured } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";

export default function AuthStatus() {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!supabase) {
      setReady(true);
      return;
    }

    let active = true;

    supabase.auth
      .getSession()
      .then(({ data }) => {
        if (!active) return;
        setSession(data.session);
        setReady(true);
      })
      .catch(() => {
        if (!active) return;
        setReady(true);
      });

    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });

    return () => {
      active = false;
      data.subscription.unsubscribe();
    };
  }, []);

  if (!isSupabaseConfigured || !ready || !session) {
    return null;
  }

  const email = session.user.email ?? "ログイン中";

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground">{email}</span>
      <Button
        variant="outline"
        size="sm"
        onClick={() => supabase?.auth.signOut()}
      >
        ログアウト
      </Button>
    </div>
  );
}
