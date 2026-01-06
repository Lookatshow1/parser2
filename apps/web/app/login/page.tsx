"use client";

import { useState } from "react";
import { loginUser, registerUser } from "../../lib/api";
import { setToken } from "../../lib/session";

export default function LoginPage() {
  const [email, setEmail] = useState("user@example.com");
  const [password, setPassword] = useState("secret123");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const handleRegister = async () => {
    setError(null);
    setNotice(null);
    try {
      await registerUser({ email, password });
      setNotice("User registered. Now log in.");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleLogin = async () => {
    setError(null);
    setNotice(null);
    try {
      const token = await loginUser({ email, password });
      setToken(token.access_token);
      setNotice("Logged in. Go to Orgs to select an organization.");
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="card space-y-4 max-w-md">
      <h1 className="text-xl font-semibold">Login</h1>
      {error && <div className="text-red-400">{error}</div>}
      {notice && <div className="text-green-400">{notice}</div>}
      <label className="text-sm text-slate-400">Email</label>
      <input value={email} onChange={(event) => setEmail(event.target.value)} />
      <label className="text-sm text-slate-400">Password</label>
      <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
      <div className="flex gap-2">
        <button onClick={handleLogin}>Login</button>
        <button onClick={handleRegister} className="bg-slate-700 hover:bg-slate-600">
          Register
        </button>
      </div>
    </div>
  );
}
