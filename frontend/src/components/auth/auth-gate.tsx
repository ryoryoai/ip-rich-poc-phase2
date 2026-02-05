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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

type AuthMode = "sign-in" | "sign-up";

type AuthGateProps = {
  children: React.ReactNode;
};

export default function AuthGate({ children }: AuthGateProps) {
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<"loading" | "authed" | "unauth">(
    "loading"
  );
  const [mode, setMode] = useState<AuthMode>("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

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
    setInfo(null);
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
    setInfo(null);
    try {
      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
      });
      if (signUpError) {
        setError(signUpError.message);
      } else if (!data.session) {
        setInfo(
          "確認メールを送信しました。メール内のリンクから登録を完了してください。"
        );
      }
    } catch {
      setError("新規登録に失敗しました。");
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

  if (status === "authed" && session) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Phase2 にログイン</CardTitle>
          <CardDescription>Supabase Auth で認証します。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Tabs
            value={mode}
            onValueChange={(value) => {
              setMode(value as AuthMode);
              setError(null);
              setInfo(null);
            }}
          >
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="sign-in">ログイン</TabsTrigger>
              <TabsTrigger value="sign-up">新規登録</TabsTrigger>
            </TabsList>
            <TabsContent value="sign-in" className="space-y-4">
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
                onClick={handleSignIn}
              >
                {submitting ? "ログイン中..." : "ログイン"}
              </Button>
            </TabsContent>
            <TabsContent value="sign-up" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="auth-email-signup">メールアドレス</Label>
                <Input
                  id="auth-email-signup"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="auth-password-signup">パスワード</Label>
                <Input
                  id="auth-password-signup"
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              </div>
              <Button
                type="button"
                className="w-full"
                disabled={!canSubmit}
                onClick={handleSignUp}
              >
                {submitting ? "登録中..." : "新規登録"}
              </Button>
              <p className="text-xs text-muted-foreground">
                登録後、メールの確認リンクをクリックして利用を開始してください。
              </p>
            </TabsContent>
          </Tabs>

          {error && (
            <Alert variant="destructive">
              <AlertTitle>認証エラー</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {info && (
            <Alert>
              <AlertTitle>お知らせ</AlertTitle>
              <AlertDescription>{info}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
