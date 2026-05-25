import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import gsap from 'gsap'
import { useGSAP } from '@gsap/react'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import {
  ArrowRightOutlined,
  AuditOutlined,
  CloudServerOutlined,
  DashboardOutlined,
  LockOutlined,
  LogoutOutlined,
  MessageOutlined,
  SafetyCertificateOutlined,
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
import StudentChatboxPage from './StudentChatboxPage'

gsap.registerPlugin(useGSAP, ScrollTrigger)

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
  { key: '#hero', label: '首页' },
  { key: '#capabilities', label: '产品能力' },
  { key: '#workflow', label: '使用流程' },
  { key: '#trust', label: '可信边界' },
]

const trustSignals = [
  { value: '3', label: '角色工作台' },
  { value: 'Demo', label: '模拟数据边界' },
  { value: 'FastAPI', label: '后端业务边界' },
]

const narrativeChapters = [
  {
    id: 'capabilities',
    eyebrow: '01 / Student consultation',
    title: '学生咨询从问题进入，以来源与边界结束。',
    copy:
      '学生端展示清晰的提问入口、回答状态、来源卡片和不支持问题的回退提示。Demo 阶段不冒充真实 RAG，也不使用真实学生记录。',
    metric: 'Source-backed',
    icon: <UserOutlined />,
    visualTitle: '学生问答流',
    visualItems: ['问题识别', '确定性来源匹配', '回答与来源卡片', 'Unsupported fallback'],
  },
  {
    id: 'workflow',
    eyebrow: '02 / Counselor workspace',
    title: '老师看到的是案例工作流，而不是一个泛用聊天框。',
    copy:
      '老师工作台以模拟案例、状态变化、辅助建议和后续动作组织信息，让 AI 成为工作流里的辅助层，而不是替代专业判断。',
    metric: 'Case-aware',
    icon: <TeamOutlined />,
    visualTitle: '辅导员协作',
    visualItems: ['模拟案例列表', '风险与状态', '辅助建议', '人工确认动作'],
  },
  {
    id: 'operations',
    eyebrow: '03 / Knowledge operations',
    title: '知识运维和审计被放在独立管理面，不混入学生入口。',
    copy:
      '运维管理人员维护 Demo 知识资源、查看统计活动、执行重置动作。后续真实 schema、RAG、向量库和模型接入都要走审批门控。',
    metric: 'Auditable',
    icon: <AuditOutlined />,
    visualTitle: '知识与审计',
    visualItems: ['知识资源', 'Demo seed/reset', '统计快照', '审计事件'],
  },
  {
    id: 'trust',
    eyebrow: '04 / Trusted demo boundary',
    title: '把“能演示什么”和“还没有上线什么”讲清楚。',
    copy:
      '当前版本保持 Demo 数据、非生产 SSO、非真实学生数据和可回滚实现。用户体验追求正式产品感，但技术边界不会被视觉包装掩盖。',
    metric: 'Demo-safe',
    icon: <SafetyCertificateOutlined />,
    visualTitle: '边界声明',
    visualItems: ['模拟数据', '非生产 SSO', '无真实学生记录', '可替换动效资产'],
  },
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
        <Layout className={`app-shell ${location.pathname === '/' ? 'home-shell' : ''}`}>
          <Layout.Header className="topbar" data-home-nav={location.pathname === '/'}>
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

          <Layout.Content className="app-content">
            <RouterOutlet
              session={session}
              onLogin={loginByAccount}
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
  loadingRole,
}: {
  session: SessionState | null
  onLogin: (account: (typeof demoAccounts)[number]) => Promise<void>
  loadingRole: Role | null
}) {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route
        path="/login"
        element={<LoginPage session={session} onLogin={onLogin} loadingRole={loadingRole} />}
      />
      <Route path="/app" element={<WorkspaceLayout session={session} />}>
        <Route index element={<Navigate to="/login" replace />} />
        <Route path="student" element={<WorkspacePage role="student" session={session} />} />
        <Route
          path="student/chatbox"
          element={<StudentChatboxPage apiBase={API_BASE} session={session} />}
        />
        <Route path="counselor" element={<WorkspacePage role="counselor" session={session} />} />
        <Route path="admin" element={<WorkspacePage role="admin" session={session} />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function LandingPage() {
  const navigate = useNavigate()
  const pageRef = useRef<HTMLElement | null>(null)

  useGSAP(
    () => {
      const mm = gsap.matchMedia()

      mm.add(
        {
          reduceMotion: '(prefers-reduced-motion: reduce)',
          desktop: '(min-width: 900px)',
        },
        (context) => {
          const { reduceMotion, desktop } = context.conditions as {
            reduceMotion: boolean
            desktop: boolean
          }
          const homeTopbar = document.querySelector<HTMLElement>('.home-shell .topbar')
          const introTargets = [
            homeTopbar,
            ...gsap.utils.toArray<HTMLElement>(
              '.hero-kicker, .hero-title-line, .hero-text, .hero-actions, .trust-item, .scroll-cue, .cinema-stage',
            ),
          ].filter(Boolean) as HTMLElement[]

          gsap.set(introTargets, { autoAlpha: 1 })

          if (reduceMotion) {
            gsap.set('.chapter-card', { autoAlpha: 1, y: 0, scale: 1 })
            gsap.set('.motion-orbit, .motion-node, .scan-line', { clearProps: 'all' })
            return
          }

          const intro = gsap.timeline({ defaults: { ease: 'power3.out' } })
          intro
            .from('.cinema-stage', { autoAlpha: 0, scale: 1.08, duration: 1.35 })
          if (homeTopbar) {
            intro.from(homeTopbar, { y: -28, autoAlpha: 0, duration: 0.8 }, '<0.2')
          }
          intro
            .from('.hero-kicker', { y: 24, autoAlpha: 0, filter: 'blur(12px)', duration: 0.8 }, '<0.16')
            .from(
              '.hero-title-line',
              {
                yPercent: 110,
                autoAlpha: 0,
                filter: 'blur(16px)',
                stagger: 0.13,
                duration: 0.92,
              },
              '<0.08',
            )
            .from('.hero-text', { y: 28, autoAlpha: 0, filter: 'blur(10px)', duration: 0.8 }, '-=0.28')
            .from('.hero-actions', { y: 22, autoAlpha: 0, duration: 0.7 }, '-=0.34')
            .from('.trust-item', { y: 18, autoAlpha: 0, stagger: 0.08, duration: 0.54 }, '-=0.2')
            .from('.scroll-cue', { y: -8, autoAlpha: 0, duration: 0.54 }, '-=0.1')

          gsap.to('.motion-orbit', {
            rotation: 360,
            transformOrigin: '50% 50%',
            duration: 22,
            ease: 'none',
            repeat: -1,
            stagger: { each: 3, from: 'center' },
          })

          gsap.to('.motion-node', {
            y: (index) => (index % 2 === 0 ? -16 : 16),
            x: (index) => (index % 3 === 0 ? 12 : -8),
            duration: 3.6,
            ease: 'sine.inOut',
            repeat: -1,
            yoyo: true,
            stagger: 0.22,
          })

          gsap.to('.scan-line', {
            xPercent: 170,
            duration: 4.2,
            ease: 'power1.inOut',
            repeat: -1,
            repeatDelay: 0.8,
          })

          gsap.utils.toArray<HTMLElement>('.chapter-card').forEach((chapter, index) => {
            gsap.from(chapter, {
              autoAlpha: 0,
              y: desktop ? 96 : 42,
              scale: desktop ? 0.96 : 1,
              duration: 0.9,
              ease: 'power3.out',
              scrollTrigger: {
                trigger: chapter,
                start: desktop ? 'top 72%' : 'top 84%',
                toggleActions: 'play none none reverse',
              },
            })

            const visualItems = chapter.querySelectorAll('.chapter-visual-item')
            gsap.from(visualItems, {
              autoAlpha: 0,
              x: index % 2 === 0 ? -26 : 26,
              duration: 0.54,
              ease: 'power2.out',
              stagger: 0.09,
              scrollTrigger: {
                trigger: chapter,
                start: desktop ? 'top 64%' : 'top 80%',
                toggleActions: 'play none none reverse',
              },
            })
          })

          if (desktop) {
            gsap.to('.hero-motion-field', {
              yPercent: 12,
              scale: 0.96,
              ease: 'none',
              scrollTrigger: {
                trigger: '.hero-section',
                start: 'top top',
                end: 'bottom top',
                scrub: 1,
              },
            })
          }
        },
      )

      return () => mm.revert()
    },
    { scope: pageRef },
  )

  const scrollToChapters = () => {
    document.getElementById('capabilities')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <main className="home-page" ref={pageRef}>
      <section id="hero" className="hero-section" aria-labelledby="home-hero-title">
        <div className="cinema-stage" aria-hidden="true">
          <div className="cinema-vignette" />
          <div className="hero-motion-field">
            <svg className="motion-map" viewBox="0 0 1000 720" role="img" aria-label="">
              <defs>
                <linearGradient id="routeGlow" x1="0%" y1="100%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#42d4ff" stopOpacity="0" />
                  <stop offset="42%" stopColor="#6aa8ff" stopOpacity="0.72" />
                  <stop offset="100%" stopColor="#ffffff" stopOpacity="0.08" />
                </linearGradient>
                <radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#ffffff" stopOpacity="0.9" />
                  <stop offset="48%" stopColor="#51d6ff" stopOpacity="0.45" />
                  <stop offset="100%" stopColor="#2f6dff" stopOpacity="0" />
                </radialGradient>
              </defs>
              <path
                className="motion-route route-one"
                d="M 76 612 C 212 510, 318 470, 452 362 S 710 166, 932 86"
              />
              <path
                className="motion-route route-two"
                d="M 84 516 C 244 478, 390 396, 512 290 S 738 118, 956 154"
              />
              <path
                className="motion-route route-three"
                d="M 160 650 C 320 575, 472 480, 570 380 S 720 240, 892 222"
              />
              <g className="motion-orbit orbit-one">
                <ellipse cx="628" cy="268" rx="256" ry="116" />
              </g>
              <g className="motion-orbit orbit-two">
                <ellipse cx="628" cy="268" rx="346" ry="164" />
              </g>
              <circle className="motion-node node-one" cx="266" cy="494" r="56" />
              <circle className="motion-node node-two" cx="466" cy="366" r="72" />
              <circle className="motion-node node-three" cx="692" cy="214" r="96" />
              <circle className="motion-node node-four" cx="850" cy="128" r="46" />
            </svg>
            <div className="scan-line" />
            <div className="video-slot">
              <div className="video-slot-label">Future motion asset slot</div>
              <div className="video-slot-title">NCHU emblem animation / product video</div>
              <div className="video-slot-copy">当前使用本地 GSAP + SVG 抽象航空 AI 动效占位，后续可替换为正式视频、Lottie 或校徽动效资产。</div>
            </div>
          </div>
        </div>

        <div className="hero-content">
          <div className="hero-kicker">
            <CloudServerOutlined />
            <span>AI-powered campus consultation</span>
          </div>
          <Typography.Title id="home-hero-title" level={1} className="hero-title">
            <span className="hero-title-mask">
              <span className="hero-title-line">NCHU AI</span>
            </span>
            <span className="hero-title-mask">
              <span className="hero-title-line">让校园咨询服务拥有</span>
            </span>
            <span className="hero-title-mask">
              <span className="hero-title-line">清晰、可信、可演示的 AI 工作台。</span>
            </span>
          </Typography.Title>
          <Typography.Paragraph className="hero-text">
            独立主站承载产品定位与能力叙事，登录后根据账号自动识别学生、老师、运维管理人员身份。
            当前版本坚持 Demo 边界：模拟数据、非生产 SSO、非真实学生记录，并为后续真实知识库和 RAG 编排保留接口。
          </Typography.Paragraph>
          <div className="hero-actions">
            <Button
              type="primary"
              size="large"
              shape="round"
              icon={<ArrowRightOutlined />}
              onClick={() => navigate('/login')}
            >
              进入登录
            </Button>
            <Button size="large" shape="round" onClick={scrollToChapters}>
              查看产品叙事
            </Button>
          </div>
          <div className="trust-row" aria-label="Demo status">
            {trustSignals.map((item) => (
              <div className="trust-item" key={item.label}>
                <strong>{item.value}</strong>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        <button className="scroll-cue" onClick={scrollToChapters} aria-label="向下查看产品能力">
          <span>Scroll</span>
          <i aria-hidden="true" />
        </button>
      </section>

      <section className="narrative-stack" aria-label="产品能力章节">
        {narrativeChapters.map((chapter, index) => (
          <article className="chapter-card" id={chapter.id} key={chapter.id}>
            <div className="chapter-copy">
              <div className="chapter-eyebrow">
                {chapter.icon}
                <span>{chapter.eyebrow}</span>
              </div>
              <Typography.Title level={2} className="chapter-title">
                {chapter.title}
              </Typography.Title>
              <Typography.Paragraph className="chapter-text">{chapter.copy}</Typography.Paragraph>
              <div className="chapter-meta">
                <strong>{chapter.metric}</strong>
                <span>{index === 0 ? 'Phase 3 ready' : 'Planned node'}</span>
              </div>
            </div>
            <div className="chapter-visual">
              <div className="chapter-visual-header">
                <span>{chapter.visualTitle}</span>
                <Tag color={index === 3 ? 'gold' : 'blue'}>{index === 3 ? 'Boundary' : 'Demo'}</Tag>
              </div>
              <div className="chapter-visual-grid">
                {chapter.visualItems.map((item, itemIndex) => (
                  <div className="chapter-visual-item" key={item}>
                    <span>{String(itemIndex + 1).padStart(2, '0')}</span>
                    <strong>{item}</strong>
                  </div>
                ))}
              </div>
            </div>
          </article>
        ))}
      </section>
    </main>
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
