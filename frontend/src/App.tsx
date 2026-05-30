import { useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import {
  DashboardOutlined,
  LockOutlined,
  LogoutOutlined,
  MessageOutlined,
  RobotOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons'
import {
  App as AntApp,
  Button,
  Card,
  ConfigProvider,
  Divider,
  Layout,
  Menu,
  Segmented,
  Space,
  Statistic,
  Tag,
  Typography,
  theme,
} from 'antd'
import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from 'react-router-dom'
import './App.css'
import ProductionHomePage from './ProductionHomePage'
import StudentChatboxPage from './StudentChatboxPage'

type Role = 'student' | 'counselor' | 'admin'

type DemoUser = {
  id: string
  displayName: string
  role: Role
  demoAccount: boolean
  sessionState: 'authenticated'
}

type TokenResponse = {
  access_token: string
  token_type: string
  provider: string
  issued_at: string
  user: DemoUser
}

type SessionState = {
  token: string
  user: DemoUser
}

type LoginFormValues = {
  username: string
  password: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
const STORAGE_KEY = 'ai-counselor-demo-session'

const roleMeta: Record<
  Role,
  {
    label: string
    icon: ReactNode
    path: string
    color: string
    subtitle: string
    identityLabel: string
    workspaceLabel: string
  }
> = {
  student: {
    label: '学生',
    icon: <UserOutlined />,
    path: '/app/student',
    color: 'blue',
    subtitle: '学生问答、来源卡片、会话历史',
    identityLabel: '学生身份',
    workspaceLabel: '学生工作台',
  },
  counselor: {
    label: '老师',
    icon: <TeamOutlined />,
    path: '/app/counselor',
    color: 'geekblue',
    subtitle: '案例列表、辅助建议、状态更新',
    identityLabel: '老师身份',
    workspaceLabel: '老师工作台',
  },
  admin: {
    label: '运维管理人员',
    icon: <DashboardOutlined />,
    path: '/app/admin',
    color: 'gold',
    subtitle: '知识维护、统计概览、审计查看',
    identityLabel: '运维管理人员身份',
    workspaceLabel: '运维管理台',
  },
}

const demoAccounts: Array<{
  role: Role
  username: string
  password: string
  title: string
  hint: string
}> = [
  {
    role: 'student',
    username: 'student@example.edu',
    password: 'password',
    title: '学生 Demo',
    hint: '进入学生工作区，查看问答与来源卡片',
  },
  {
    role: 'counselor',
    username: 'counselor@example.edu',
    password: 'password',
    title: '老师 Demo',
    hint: '进入老师工作区，查看案例和建议',
  },
  {
    role: 'admin',
    username: 'admin@example.edu',
    password: 'password',
    title: '运维管理人员 Demo',
    hint: '进入运维管理区，查看知识、审计和统计',
  },
]

const navItems = [
  { key: '#meet', label: '认识产品' },
  { key: '#platform', label: '平台能力' },
  { key: '#roles', label: '角色场景' },
  { key: '#governance', label: '治理边界' },
]

function readStoredSession(): SessionState | null {
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as SessionState
  } catch {
    return null
  }
}

async function loginDemo(payload: LoginFormValues): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }))
    throw new Error(error.detail ?? 'Login failed')
  }

  return response.json() as Promise<TokenResponse>
}

function AppShell() {
  const navigate = useNavigate()
  const location = useLocation()
  const [session, setSession] = useState<SessionState | null>(() => readStoredSession())
  const [loadingRole, setLoadingRole] = useState<Role | null>(null)

  useEffect(() => {
    if (session) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
    } else {
      window.localStorage.removeItem(STORAGE_KEY)
    }
  }, [session])

  const currentRole = session?.user.role ?? null
  const isChatboxRoute = location.pathname === '/app/student/chatbox'

  const loginByAccount = async (account: (typeof demoAccounts)[number]) => {
    setLoadingRole(account.role)
    try {
      const result = await loginDemo({
        username: account.username,
        password: account.password,
      })
      setSession({ token: result.access_token, user: result.user })
      navigate(roleMeta[result.user.role].path)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed'
      window.alert(message)
    } finally {
      setLoadingRole(null)
    }
  }

  const logout = () => {
    setSession(null)
    navigate('/')
  }

  const handleSessionExpired = useCallback(() => {
    setSession(null)
    navigate('/login', { replace: true })
  }, [navigate])

  const handleTopnavClick = ({ key }: { key: string }) => {
    if (!key.startsWith('#')) {
      navigate(key)
      return
    }

    if (location.pathname !== '/') {
      navigate('/')
      window.setTimeout(() => {
        document.querySelector(key)?.scrollIntoView({ behavior: 'smooth' })
      }, 0)
      return
    }

    document.querySelector(key)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#2f6dff',
          colorInfo: '#2f6dff',
          borderRadius: 8,
          fontFamily:
            "'Inter', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif",
        },
      }}
    >
      <AntApp>
        <Layout
          className={`app-shell ${location.pathname === '/' ? 'home-shell' : ''} ${
            isChatboxRoute ? 'chatbox-shell' : ''
          }`}
        >
          {location.pathname === '/' || isChatboxRoute ? null : (
            <Layout.Header className="topbar">
              <div className="brand" onClick={() => navigate('/')} role="button" tabIndex={0}>
                <div className="brand-mark" aria-hidden="true">
                  <RobotOutlined />
                </div>
                <div>
                  <div className="brand-title">NCHU AI</div>
                  <div className="brand-subtitle">AI Counselor Demo</div>
                </div>
              </div>
              <Menu
                mode="horizontal"
                items={navItems}
                selectedKeys={[]}
                className="topnav"
                onClick={handleTopnavClick}
              />
              <Space size={12} className="topbar-actions">
                {session ? (
                  <>
                    <Tag className="identity-tag" color={roleMeta[currentRole ?? 'student'].color}>
                      {roleMeta[currentRole ?? 'student'].identityLabel}
                    </Tag>
                    <Button
                      type="primary"
                      shape="round"
                      onClick={() => navigate(roleMeta[currentRole ?? 'student'].path)}
                    >
                      {roleMeta[currentRole ?? 'student'].workspaceLabel}
                    </Button>
                    <Button type="text" className="nav-text-button" icon={<LogoutOutlined />} onClick={logout}>
                      退出
                    </Button>
                  </>
                ) : (
                  <>
                    <Button type="text" className="nav-text-button" onClick={() => navigate('/login')}>
                      登录
                    </Button>
                    <Button type="primary" shape="round" onClick={() => navigate('/login')}>
                      开始体验
                    </Button>
                  </>
                )}
              </Space>
            </Layout.Header>
          )}

          <Layout.Content className="app-content">
            <RouterOutlet
              session={session}
              onLogin={loginByAccount}
              onSessionExpired={handleSessionExpired}
              loadingRole={loadingRole}
            />
          </Layout.Content>
        </Layout>
      </AntApp>
    </ConfigProvider>
  )
}

function RouterOutlet({
  session,
  onLogin,
  onSessionExpired,
  loadingRole,
}: {
  session: SessionState | null
  onLogin: (account: (typeof demoAccounts)[number]) => Promise<void>
  onSessionExpired: () => void
  loadingRole: Role | null
}) {
  return (
    <Routes>
      <Route path="/" element={<ProductionHomePage />} />
      <Route
        path="/login"
        element={<LoginPage session={session} onLogin={onLogin} loadingRole={loadingRole} />}
      />
      <Route path="/app" element={<WorkspaceLayout session={session} />}>
        <Route index element={<Navigate to="/login" replace />} />
        <Route path="student" element={<WorkspacePage role="student" session={session} />} />
        <Route
          path="student/chatbox"
          element={
            <StudentChatboxPage
              apiBase={API_BASE}
              onSessionExpired={onSessionExpired}
              session={session}
            />
          }
        />
        <Route path="counselor" element={<WorkspacePage role="counselor" session={session} />} />
        <Route path="admin" element={<WorkspacePage role="admin" session={session} />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function LoginPage({
  session,
  onLogin,
  loadingRole,
}: {
  session: SessionState | null
  onLogin: (account: (typeof demoAccounts)[number]) => Promise<void>
  loadingRole: Role | null
}) {
  const [selectedRole, setSelectedRole] = useState<Role>('student')
  const selectedAccount = demoAccounts.find((item) => item.role === selectedRole) ?? demoAccounts[0]
  const navigate = useNavigate()

  useEffect(() => {
    if (session) {
      navigate(roleMeta[session.user.role].path, { replace: true })
    }
  }, [navigate, session])

  return (
    <main className="page login-page">
      <Card className="login-hero" variant="borderless">
        <div className="login-hero-copy">
          <Space size={8} wrap>
            <Tag color={roleMeta.student.color}>学生</Tag>
            <Tag color={roleMeta.counselor.color}>老师</Tag>
            <Tag color={roleMeta.admin.color}>运维管理人员</Tag>
          </Space>
          <Typography.Title level={2} className="section-title">
            登录后自动识别身份，并进入对应工作台
          </Typography.Title>
          <Typography.Paragraph className="section-copy">
            登录页承担读取 Demo 账号、身份判断和跳转。学生、老师、运维管理人员使用不同账号登录，系统根据后端返回的角色进入对应工作区。
          </Typography.Paragraph>
        </div>

        <Card className="login-panel" variant="outlined">
          <Segmented
            block
            value={selectedRole}
            onChange={(value) => setSelectedRole(value as Role)}
            options={Object.entries(roleMeta).map(([key, value]) => ({
              label: value.label,
              value: key,
            }))}
          />
          <Divider />
          <div className="role-card">
            <div className="role-card-header">
              <span className="role-icon">{roleMeta[selectedAccount.role].icon}</span>
              <div>
                <div className="role-card-title">{selectedAccount.title}</div>
                <div className="role-card-subtitle">{selectedAccount.hint}</div>
              </div>
            </div>
            <div className="login-summary">
              <div>
                <span className="summary-label">账号</span>
                <span className="summary-value">{selectedAccount.username}</span>
              </div>
              <div>
                <span className="summary-label">密码</span>
                <span className="summary-value">password</span>
              </div>
            </div>
            <Button
              type="primary"
              size="large"
              block
              loading={loadingRole === selectedAccount.role}
              icon={<LockOutlined />}
              onClick={() => onLogin(selectedAccount)}
            >
              以 {selectedAccount.title} 登录
            </Button>
            <Typography.Text type="secondary" className="login-footnote">
              该入口仅用于 Demo。登录成功后进入对应角色工作台。
            </Typography.Text>
          </div>
        </Card>
      </Card>

      <section className="account-row">
        {demoAccounts.map((account) => (
          <Card
            key={account.role}
            className={`account-card ${selectedRole === account.role ? 'active' : ''}`}
            onClick={() => setSelectedRole(account.role)}
          >
            <div className="account-card-top">
              <Tag color={roleMeta[account.role].color}>{roleMeta[account.role].label}</Tag>
              {selectedRole === account.role ? <Tag color="green">selected</Tag> : null}
            </div>
            <div className="account-card-title">{account.title}</div>
            <div className="account-card-copy">{account.hint}</div>
          </Card>
        ))}
      </section>
    </main>
  )
}

function WorkspaceLayout({ session }: { session: SessionState | null }) {
  if (!session) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

function WorkspacePage({
  role,
  session,
}: {
  role: Role
  session: SessionState | null
}) {
  const navigate = useNavigate()

  if (!session) {
    return <Navigate to="/login" replace />
  }

  if (session.user.role !== role) {
    return <Navigate to={roleMeta[session.user.role].path} replace />
  }

  const meta = roleMeta[role]

  return (
    <main className="page workspace-page">
      <section className="workspace-header">
        <div>
          <Space size={8} wrap>
            <Tag color={meta.color}>{meta.workspaceLabel}</Tag>
            <Tag>Demo</Tag>
          </Space>
          <Typography.Title level={2} className="section-title">
            {session.user.displayName}
          </Typography.Title>
          <Typography.Paragraph className="section-copy">
            {meta.subtitle}。当前只使用已批准的 Demo 契约，不包含真实学生数据或生产 SSO。
          </Typography.Paragraph>
        </div>
        {role === 'student' ? (
          <Button
            type="primary"
            icon={<MessageOutlined />}
            onClick={() => navigate('/app/student/chatbox')}
          >
            打开 Chatbox
          </Button>
        ) : (
          <Button onClick={() => navigate('/login')}>返回登录</Button>
        )}
      </section>

      <section className="metric-grid">
        <Card className="metric-card">
          <Statistic title="会话状态" value={session.user.sessionState} />
        </Card>
        <Card className="metric-card">
          <Statistic title="Demo 账号" value={session.user.demoAccount ? 'true' : 'false'} />
        </Card>
        <Card className="metric-card">
          <Statistic title="当前角色" value={meta.label} />
        </Card>
      </section>

      <section className="workspace-grid">
        <Card className="workspace-card" title="交互结构">
          <ul className="bullet-list">
            <li>登录成功后进入角色专属工作台。</li>
            <li>学生、老师、运维管理人员各自只显示自己的主入口。</li>
            <li>未授权角色会被重定向回可访问路径。</li>
          </ul>
        </Card>
        <Card className="workspace-card" title="下一阶段接口">
          <ul className="bullet-list">
            <li>学生 Chatbox 独立页。</li>
            <li>老师案例与建议。</li>
            <li>运维管理人员知识、审计和统计。</li>
          </ul>
        </Card>
      </section>
    </main>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}
