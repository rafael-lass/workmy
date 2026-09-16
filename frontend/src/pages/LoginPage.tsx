import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ApiError } from '../lib/http'
import { Alert } from '../shared/ui/Alert'
import { Button } from '../shared/ui/Button'
import { Field, fieldA11y } from '../shared/ui/Field'
import { Icon } from '../shared/ui/Icon'

export function LoginPage() {
  const { login, isAuthenticated, loading: sessionLoading } = useAuth(); const navigate = useNavigate(); const location = useLocation(); const [identifier, setIdentifier] = useState(''); const [password, setPassword] = useState(''); const [showPassword, setShowPassword] = useState(false); const [errors, setErrors] = useState<Record<string, string>>({}); const [apiError, setApiError] = useState(''); const [busy, setBusy] = useState(false)
  if (sessionLoading) return <div className="auth-shell"><div className="ui-button__spinner h-8 w-8 text-indigo-300" aria-label="Validando sessão" /></div>
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? '/dashboard'
  const submit = async (event: FormEvent) => { event.preventDefault(); const next: Record<string, string> = {}; if (!identifier.trim()) next.identifier = 'Informe seu usuário ou e-mail.'; if (!password) next.password = 'Informe sua senha.'; if (Object.keys(next).length) { setErrors(next); return } setBusy(true); setApiError(''); try { await login(identifier.trim(), password); navigate(from, { replace: true }) } catch (error) { setApiError(error instanceof ApiError ? error.message : 'Não foi possível entrar.') } finally { setBusy(false) } }
  return <main className="auth-shell"><div className="auth-brand"><span className="auth-brand__mark">W</span>WorkMy</div><section className="auth-card"><p className="page-header__eyebrow !text-indigo-300">Sua operação, organizada</p><h1>Bem-vindo de volta</h1><p className="auth-card__intro">Entre para acompanhar projetos, clientes e recebimentos.</p><form onSubmit={submit} noValidate>{apiError && <Alert tone="error">{apiError}</Alert>}<Field id="login-identifier" label="Usuário ou e-mail" error={errors.identifier}><input id="login-identifier" autoFocus autoComplete="username" placeholder="seu usuário ou email@empresa.com" value={identifier} onChange={(event) => { setIdentifier(event.target.value); setErrors((current) => ({ ...current, identifier: '' })) }} {...fieldA11y('login-identifier', errors.identifier)} /></Field><Field id="login-password" label="Senha" error={errors.password}><div className="password-field"><input id="login-password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" placeholder="Sua senha" value={password} onChange={(event) => { setPassword(event.target.value); setErrors((current) => ({ ...current, password: '' })) }} {...fieldA11y('login-password', errors.password)} /><button type="button" className="ui-icon-button" aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'} onClick={() => setShowPassword((current) => !current)}><Icon name="eye"/></button></div></Field><Button className="mt-2 w-full" type="submit" loading={busy}>Entrar</Button><p className="auth-card__footer">Ainda não tem conta? <Link to="/register">Criar conta</Link></p></form></section></main>
}
