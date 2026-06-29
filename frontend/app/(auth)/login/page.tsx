"use client";

import { motion } from "framer-motion";
import { TriangleAlert } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import { SocialAuth } from "@/components/auth/SocialAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { useAuth } from "@/lib/store";

export default function LoginPage() {
  const router = useRouter();
  const { login, loading } = useAuth();
  const goDashboard = useCallback(() => router.push("/dashboard"), [router]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xatolik");
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle className="font-display text-2xl">Kirish</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="siz@maktab.uz"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Parol</Label>
            <Input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && (
            <p className="flex items-center gap-2 rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <TriangleAlert size={15} /> {error}
            </p>
          )}
          <Button type="submit" size="lg" className="w-full" disabled={loading}>
            {loading && <Spinner size={16} />}
            {loading ? "Kutib turing…" : "Kirish"}
          </Button>
        </form>
        <SocialAuth onSuccess={goDashboard} />
        <p className="mt-4 text-center text-sm text-muted-foreground">
          Akkauntingiz yo'qmi?{" "}
          <Link href="/register" className="font-medium text-primary underline">
            Ro'yxatdan o'ting
          </Link>
        </p>
      </CardContent>
    </Card>
    </motion.div>
  );
}
