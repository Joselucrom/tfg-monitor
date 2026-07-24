import { NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import {
  LayoutDashboard, Server, Globe, Bell,
  ShieldAlert, List, LogOut, Settings
} from 'lucide-react'
import ModalPerfil from './ModalPerfil'

const navItems = [
  { to: '/',          label: 'Dashboard',     icon: LayoutDashboard, end: true },
  { to: '/sistemas',  label: 'Sistemas',      icon: Server },
  { to: '/servicios', label: 'Servicios web', icon: Globe },
  { to: '/eventos',   label: 'Eventos',       icon: List },
  { to: '/alertas',   label: 'Alertas',       icon: Bell },
  { to: '/reglas',    label: 'Reglas',        icon: ShieldAlert },
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const [modalPerfil, setModalPerfil] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isAdmin = user?.rol === 'admin'

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">

      {/* Sidebar */}
      <aside className="w-48 bg-gray-100 border-r border-gray-200 flex flex-col py-4 px-3 shrink-0">

        {/* Logo */}
        <div className="flex items-center gap-2 px-2 mb-6">
          <div className="w-6 h-6 rounded-md bg-blue-50 flex items-center justify-center">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="7" cy="7" r="2.5" fill="#3B82F6"/>
              <path d="M7 1v1.5M7 11.5V13M1 7h1.5M11.5 7H13"
                stroke="#3B82F6" strokeWidth="1.2" strokeLinecap="round"/>
            </svg>
          </div>
          <span className="text-sm font-medium text-gray-800">TFG Monitor</span>
        </div>

        {/* Nav principal */}
        <nav className="flex flex-col gap-1 flex-1">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors
                 ${isActive
                   ? 'bg-white text-gray-900 font-medium shadow-sm'
                   : 'text-gray-500 hover:bg-white hover:text-gray-800'
                 }`
              }
            >
              <Icon size={15} />
              {label}
            </NavLink>
          ))}

          {/* Sección admin — solo visible para admins */}
          {isAdmin && (
            <>
              <div className="h-px bg-gray-200 my-2" />
              <p className="text-xs text-gray-400 px-3 pb-1 uppercase tracking-wide">
                Admin
              </p>
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors
                   ${isActive
                     ? 'bg-white text-gray-900 font-medium shadow-sm'
                     : 'text-gray-500 hover:bg-white hover:text-gray-800'
                   }`
                }
              >
                <Settings size={15} />
                Panel admin
              </NavLink>
            </>
          )}
        </nav>

        {/* Usuario - clickable */}
        <div className="border-t border-gray-200 pt-3 mt-3">
          <button
            onClick={() => setModalPerfil(true)}
            className="flex items-center gap-2 px-2 mb-2 w-full hover:bg-white
                       rounded-lg py-1.5 transition-colors group"
          >
            <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center
                            text-xs font-medium text-blue-700 shrink-0">
              {user?.nombre?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="min-w-0 text-left">
              <p className="text-xs font-medium text-gray-800 truncate">{user?.nombre}</p>
              <p className="text-xs text-gray-400 truncate">{user?.rol}</p>
            </div>
          </button>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-3 py-2 w-full rounded-lg text-sm
                       text-gray-500 hover:bg-white hover:text-gray-800 transition-colors"
          >
            <LogOut size={14} />
            Cerrar sesión
          </button>
        </div>

        {/* Modal de perfil */}
        {modalPerfil && (
          <ModalPerfil
            usuario={user}
            onClose={() => setModalPerfil(false)}
          />
        )}
      </aside>

      {/* Contenido principal */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}