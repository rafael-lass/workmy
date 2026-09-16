import { Navigate, Route, Routes } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { PageSkeleton } from './shared/ui/Skeleton'
import { AppLayout } from './components/AppLayout.tsx'
import { DashboardPage } from './pages/DashboardPage.tsx'
import { LoginPage } from './pages/LoginPage.tsx'
import { RegisterPage } from './pages/RegisterPage.tsx'
import { ProtectedRoute } from './components/ProtectedRoute.tsx'
import { ClientesPage } from './pages/ClientesPage.tsx'
import { ClienteDetailPage } from './pages/ClienteDetailPage.tsx'
import { ProjetosPage } from './pages/ProjetosPage.tsx'
import { FinanceiroPage } from './pages/FinanceiroPage.tsx'

const ServicosPage = lazy(() => import('./pages/ServicosPage').then((module) => ({ default: module.ServicosPage })))

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="projetos" element={<ProjetosPage />} />
        <Route path="clientes" element={<ClientesPage />} />

        <Route path="clientes/:id" element={<ClienteDetailPage />} />
        <Route path="servicos" element={<Suspense fallback={<PageSkeleton />}><ServicosPage /></Suspense>} />
        <Route path="servicos/:id" element={<Navigate to="/servicos" replace />} />
        <Route path="financeiro" element={<FinanceiroPage />} />
        <Route path="pagamentos" element={<Navigate to="/financeiro" replace />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}


export default App
