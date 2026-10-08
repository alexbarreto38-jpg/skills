"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { Logo } from "@/components/app-header";
import { Button, Input, Segmented } from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { api, errorMessage, setToken, unwrap } from "@/lib/api";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const res =
        mode === "login"
          ? await unwrap(api.POST("/auth/login", { body: { email, password } }))
          : await unwrap(api.POST("/auth/register", { body: { email, password } }));
      setToken(res.accessToken);
      router.push(params.get("next") ?? "/");
    } catch (err) {
      toast.error("Não foi possível entrar", errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="panel w-full max-w-sm space-y-4 p-6">
      <Logo />
      <Segmented
        value={mode}
        onChange={setMode}
        options={[
          { value: "login", label: "Entrar" },
          { value: "register", label: "Criar conta" },
        ]}
      />
      <Input type="email" required placeholder="email@exemplo.com" value={email} onChange={(e) => setEmail(e.target.value)} />
      <Input type="password" required minLength={8} placeholder="Senha (mín. 8 caracteres)" value={password} onChange={(e) => setPassword(e.target.value)} />
      <Button variant="primary" size="lg" className="w-full" loading={busy} type="submit">
        {mode === "login" ? "Entrar" : "Criar conta"}
      </Button>
      <button
        type="button"
        className="w-full text-center text-xs text-muted hover:text-fg"
        onClick={() => {
          setToken(null);
          toast.info("Sessão encerrada", "Em desenvolvimento o login automático (AUTH_DEV_AUTOLOGIN) continua ativo.");
        }}
      >
        Sair desta conta
      </button>
    </form>
  );
}

export default function LoginPage() {
  return (
    <div className="glow flex min-h-screen items-center justify-center px-4">
      <Suspense>
        <LoginForm />
      </Suspense>
    </div>
  );
}
