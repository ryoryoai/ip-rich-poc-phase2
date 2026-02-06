"use client";

import { useEffect, useMemo, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase, isSupabaseConfigured } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

type AuthGateProps = {
  children: React.ReactNode;
};

export default function AuthGate({ children }: AuthGateProps) {
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<"loading" | "authed" | "unauth">(
    "loading"
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<"sign-in" | "sign-up">("sign-in");

  useEffect(() => {
    if (!supabase) {
      setStatus("unauth");
      return;
    }

    let active = true;

    supabase.auth
      .getSession()
      .then(({ data, error: sessionError }) => {
        if (!active) return;
        if (sessionError) {
          setError("認証状態の確認に失敗しました。");
        }
        setSession(data.session);
        setStatus(data.session ? "authed" : "unauth");
      })
      .catch(() => {
        if (!active) return;
        setError("認証状態の確認に失敗しました。");
        setStatus("unauth");
      });

    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setStatus(nextSession ? "authed" : "unauth");
    });

    return () => {
      active = false;
      data.subscription.unsubscribe();
    };
  }, []);

  const isApproved = useMemo(() => {
    if (!session) return false;
    const appMetadata = session.user?.app_metadata ?? {};
    return appMetadata.role === "admin" || appMetadata.approved === true;
  }, [session]);

  const canSubmit = useMemo(() => {
    return email.trim().length > 0 && password.length > 0 && !submitting;
  }, [email, password, submitting]);

  const handleSignIn = async () => {
    if (!supabase) return;
    if (!email.trim() || !password) {
      setError("メールアドレスとパスワードを入力してください。");
      return;
    }
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const { error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (signInError) {
        setError(signInError.message);
      }
    } catch {
      setError("ログインに失敗しました。");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSignUp = async () => {
    if (!supabase) return;
    if (!email.trim() || !password) {
      setError("メールアドレスとパスワードを入力してください。");
      return;
    }
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const { error: signUpError } = await supabase.auth.signUp({
        email,
        password,
      });
      if (signUpError) {
        setError(signUpError.message);
      } else {
        setNotice("申請を受け付けました。管理者の承認をお待ちください。");
      }
    } catch {
      setError("新規登録に失敗しました。");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRefresh = async () => {
    if (!supabase) return;
    setSubmitting(true);
    setError(null);
    try {
      const { data, error: refreshError } = await supabase.auth.refreshSession();
      if (refreshError) {
        setError("セッションの更新に失敗しました。");
        return;
      }
      if (data.session) {
        setSession(data.session);
        setStatus("authed");
      }
    } catch {
      setError("セッションの更新に失敗しました。");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSignOut = async () => {
    if (!supabase) return;
    setSubmitting(true);
    setError(null);
    try {
      await supabase.auth.signOut();
      setStatus("unauth");
      setSession(null);
    } catch {
      setError("ログアウトに失敗しました。");
    } finally {
      setSubmitting(false);
    }
  };

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-sm text-muted-foreground">認証状態を確認中...</div>
      </div>
    );
  }

  if (!isSupabaseConfigured) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle>Supabase 設定が必要です</CardTitle>
            <CardDescription>
              環境変数に Supabase の URL と匿名キーを設定してください。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <div>
              <div className="font-semibold text-foreground">必要な環境変数</div>
              <div className="mt-2 space-y-1 font-mono text-xs">
                <div>NEXT_PUBLIC_SUPABASE_URL</div>
                <div>NEXT_PUBLIC_SUPABASE_ANON_KEY</div>
              </div>
            </div>
            <div>
              `frontend/.env.local` に設定後、再起動してください。
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (status === "authed" && session && isApproved) {
    return <>{children}</>;
  }

  if (status === "authed" && session && !isApproved) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle>承認待ち</CardTitle>
            <CardDescription>
              アカウント申請は受け付けました。管理者の承認後に利用できます。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-sm text-muted-foreground">
              申請中のメール: {session.user.email ?? "不明"}
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
              <Button
                type="button"
                className="w-full"
                disabled={submitting}
                onClick={handleRefresh}
              >
                {submitting ? "更新中..." : "承認状態を更新"}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="w-full"
                disabled={submitting}
                onClick={handleSignOut}
              >
                ログアウト
              </Button>
            </div>
            {error && (
              <Alert variant="destructive">
                <AlertTitle>認証エラー</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>
            {authMode === "sign-in" ? "Phase2 にログイン" : "新規登録（申請）"}
          </CardTitle>
          <CardDescription>
            {authMode === "sign-in"
              ? "Supabase Auth で認証します。"
              : "登録後に管理者の承認が必要です。"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="auth-email">メールアドレス</Label>
            <Input
              id="auth-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="auth-password">パスワード</Label>
            <Input
              id="auth-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          <Button
            type="button"
            className="w-full"
            disabled={!canSubmit}
            onClick={authMode === "sign-in" ? handleSignIn : handleSignUp}
          >
            {submitting
              ? authMode === "sign-in"
                ? "ログイン中..."
                : "申請中..."
              : authMode === "sign-in"
                ? "ログイン"
                : "申請する"}
          </Button>
          <Button
            type="button"
            variant="ghost"
            className="w-full text-xs"
            onClick={() => {
              setAuthMode(authMode === "sign-in" ? "sign-up" : "sign-in");
              setError(null);
              setNotice(null);
            }}
          >
            {authMode === "sign-in"
              ? "新規登録（申請）に切り替える"
              : "ログインに切り替える"}
          </Button>

          <p className="text-xs text-muted-foreground">
            新規登録は承認制です。承認後にログインできます。
          </p>

          {notice && (
            <Alert>
              <AlertTitle>受付完了</AlertTitle>
              <AlertDescription>{notice}</AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertTitle>認証エラー</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
