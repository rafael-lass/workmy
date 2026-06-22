import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ApiError } from '../lib/http'

export function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) return <Navigate to="/dashboard" replace />

  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? '/dashboard'

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Falha ao autenticar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center relative overflow-hidden bg-[#0b0d14] text-white antialiased">
      {/* Atmosphere blobs */}
      <div className="fixed -top-[20%] -right-[10%] w-[600px] h-[600px] rounded-full pointer-events-none bg-primary/20 blur-[120px]" />
      <div className="fixed -bottom-[20%] -left-[10%] w-[500px] h-[500px] rounded-full pointer-events-none bg-tertiary/15 blur-[110px]" />

      {/* Logo header */}
      <header className="w-full flex justify-center pt-12 px-6 relative z-10">
        <span className="font-display-lg text-2xl font-bold tracking-tight text-white">WorkMy</span>
      </header>

      {/* Main form */}
      <main className="flex-1 flex items-center justify-center p-6 relative z-10 w-full">
        <form className="w-[min(440px,96vw)] flex flex-col gap-6" onSubmit={onSubmit}>
          {/* Welcome headline */}
          <div className="text-center flex flex-col gap-2">
            <h1 className="m-0 font-display-lg text-3xl font-bold tracking-tight text-white">
              Bem-vindo de volta
            </h1>
            <p className="m-0 text-[15px] text-white/45">
              Insira suas credenciais para acessar o painel.
            </p>
          </div>

          {/* Fields */}
          <div className="flex flex-col gap-5">
            {/* Username */}
            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-white/85" htmlFor="login-username">
                Usuário
              </label>
              <input
                id="login-username"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-[15px] text-white placeholder:text-white/30 transition-all focus:outline-none focus:bg-white/[0.07] focus:border-primary focus:ring-2 focus:ring-primary/40"
                placeholder="usuario"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
            </div>

            {/* Password */}
            <div className="flex flex-col gap-2">
              <div className="flex justify-between items-center">
                <label className="text-xs font-semibold uppercase tracking-wide text-white/85" htmlFor="login-password">
                  Senha
                </label>
                <a href="#" className="text-xs font-medium text-inverse-primary hover:text-white no-underline" tabIndex={-1}>
                  Esqueceu a senha?
                </a>
              </div>
              <div className="relative">
                <input
                  id="login-password"
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-4 pr-12 py-3.5 text-[15px] text-white placeholder:text-white/30 transition-all focus:outline-none focus:bg-white/[0.07] focus:border-primary focus:ring-2 focus:ring-primary/40"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/80 transition-colors flex items-center p-1"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                >
                  {showPassword ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" />
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Error message */}
          {error && <p className="text-[#f87171] m-0 text-sm font-medium">{error}</p>}

          {/* CTA */}
          <button
            className="w-full bg-primary hover:bg-primary-fixed-dim/90 text-white font-semibold text-[15px] rounded-xl py-4 transition-all shadow-[0_8px_24px_-6px_rgba(67,56,202,0.5)] hover:-translate-y-0.5 active:scale-[0.98] disabled:opacity-45 disabled:cursor-not-allowed disabled:shadow-none disabled:translate-y-0"
            type="submit"
            disabled={loading}
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>

          {/* Sign up link */}
          <div className="text-center pt-3">
            <p className="m-0 text-sm text-white/40">
              Não tem conta?
              <Link to="/register" className="text-white font-semibold no-underline ml-1 hover:text-inverse-primary">
                Criar conta
              </Link>
            </p>
          </div>
        </form>
      </main>

      {/* Footer */}
      <footer className="w-full flex justify-center p-6 relative z-10">
        <p className="m-0 text-xs text-white/25">© 2025 WorkMy. Todos os direitos reservados.</p>
      </footer>
    </div>
  )
}
