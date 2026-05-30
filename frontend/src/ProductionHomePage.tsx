import { useEffect, useMemo, useRef, useState } from 'react'
import gsap from 'gsap'
import { useGSAP } from '@gsap/react'
import { useNavigate } from 'react-router-dom'
import './ProductionHomePage.css'

gsap.registerPlugin(useGSAP)

type HomeTheme = 'light' | 'dark'
type HomeLanguage = 'zh' | 'en'

type Translation = {
  nav: {
    homeLabel: string
    primaryLabel: string
    meet: string
    platform: string
    roles: string
    governance: string
    resources: string
    login: string
    contact: string
    enter: string
  }
  productBar: {
    title: string
    link: string
  }
  hero: {
    eyebrow: string
    titleA: string
    titleB: string
    copy: string
    placeholder: string
    prompts: string[]
    inputLabel: string
    start: string
    pillsLabel: string
    pillStudent: string
    pillCounselor: string
    pillKnowledge: string
    visualLabel: string
    svgLabel: string
    chipA: { title: string; copy: string }
    chipB: { title: string; copy: string }
    latest: { kicker: string; title: string; link: string }
  }
  platform: {
    title: string
    lead: string
    actionsLabel: string
    rolesLink: string
    governanceLink: string
    listLabel: string
    features: Array<{ title: string; copy: string }>
    networkLabel: string
    networkSvgLabel: string
    orbit1: string
    orbit2: string
    orbit3: string
    orbit4: string
  }
  roles: {
    kicker: string
    cta: string
    title: string
    lead: string
    tabsLabel: string
    tabs: string[]
    cards: Array<{ title: string; copy: string }>
  }
  governance: {
    title: string
    lead: string
    backTop: string
    plan: string
  }
  footer: string
}

const THEME_STORAGE_KEY = 'nchu-ai-production-home-theme'
const LANGUAGE_STORAGE_KEY = 'nchu-ai-production-home-language'

const translations: Record<HomeLanguage, Translation> = {
  zh: {
    nav: {
      homeLabel: 'NCHU AI 首页',
      primaryLabel: '主导航',
      meet: '认识产品',
      platform: '平台能力',
      roles: '角色场景',
      governance: '治理边界',
      resources: '资源',
      login: '登录',
      contact: '联系项目组',
      enter: '进入体验',
    },
    productBar: {
      title: '产品概览',
      link: '查看平台能力',
    },
    hero: {
      eyebrow: 'AI Counselor Demo, Phase 2',
      titleA: '遇见你的',
      titleB: 'AI 辅导员',
      copy: '与NCHU AI同行，让校园信息触手可及',
      placeholder: '我想了解奖助学金、心理支持或学业预警流程',
      prompts: [
        '我想了解奖助学金申请需要准备哪些材料？',
        '我最近学习压力很大，可以从哪里获得心理支持？',
        '如果收到学业预警，我应该先联系谁？',
        '我想知道学校有哪些困难补助和资助渠道？',
        '我和室友沟通不顺，适合先找辅导员聊吗？',
        '我错过课程作业截止时间，应该如何补救？',
        '这个回答有没有来源，能不能给我看依据？',
        '我想把这次咨询记录保存下来，方便下次继续。',
        '什么情况会转给人工辅导员继续处理？',
        '当前 Demo 能回答哪些问题，哪些还需要人工确认？',
      ],
      inputLabel: '示例问题',
      start: '开始咨询',
      pillsLabel: '常用入口',
      pillStudent: '学生问答',
      pillCounselor: '辅导员协助',
      pillKnowledge: '知识维护',
      visualLabel: 'NCHU AI 抽象能力图',
      svgLabel: 'AI 辅导员能力连线',
      chipA: {
        title: '学生请求',
        copy: '问题识别、资源匹配、历史连续性',
      },
      chipB: {
        title: '人工接管',
        copy: '高风险场景交给辅导员处理',
      },
      latest: {
        kicker: 'Latest update',
        title: 'Phase 2 正在打磨登录、角色识别和首页体验。',
        link: '查看 Demo 路线',
      },
    },
    platform: {
      title: '面向学生支持的 AI 工作伙伴',
      lead: '它不是孤立的聊天窗口，而是一个可审计、可维护、可接管的校内服务入口。',
      actionsLabel: '角色入口',
      rolesLink: '查看角色场景',
      governanceLink: '了解治理边界',
      listLabel: '平台能力列表',
      features: [
        {
          title: '确定性 Demo 回答',
          copy: '先用可解释的知识匹配证明完整流程，避免在未审批阶段误称 RAG 能力已经上线。',
        },
        {
          title: '角色化工作台',
          copy: '学生、辅导员和管理员进入不同界面，操作路径和信息密度按真实职责拆开。',
        },
        {
          title: '来源与审计',
          copy: '答案、资源、操作记录和统计面板保留追踪线索，服务学校内部治理要求。',
        },
        {
          title: '人工协同',
          copy: '系统提供建议和上下文，关键判断仍由辅导员完成，边界清楚。',
        },
      ],
      networkLabel: '能力网络图',
      networkSvgLabel: 'NCHU AI 能力网络',
      orbit1: '学生问答',
      orbit2: '知识资源',
      orbit3: '辅导员协助',
      orbit4: '审计统计',
    },
    roles: {
      kicker: 'Built for campus support workflows',
      cta: '把学生服务入口、辅导员处理链路和管理审计放到同一套 Demo 里。',
      title: '如何使用 NCHU AI',
      lead: '登录后由账号角色决定入口，不在首页暴露三个独立工作台按钮。',
      tabsLabel: '使用角色',
      tabs: ['学生', '辅导员', '管理员', '项目演示'],
      cards: [
        {
          title: '学生端',
          copy: '提出问题、查看来源卡片、保存会话，并在需要时转人工支持。',
        },
        {
          title: '辅导员端',
          copy: '查看模拟个案、获得辅助建议、更新状态并保留处理记录。',
        },
        {
          title: '管理端',
          copy: '维护 Demo 知识资源、重置数据、查看统计和审计活动。',
        },
      ],
    },
    governance: {
      title: '清楚展示能力边界',
      lead: '当前阶段以 Demo 可信度为先：模拟数据明确标注，RAG、真实学生数据和公网部署都必须经过审批包。',
      backTop: '回到首页',
      plan: '查看后续计划',
    },
    footer:
      '原型说明：本页面参考 Claude 产品页的布局层级、按钮组合和动效节奏，但使用 NCHU AI 辅导员系统语境与项目审批色彩。',
  },
  en: {
    nav: {
      homeLabel: 'NCHU AI home',
      primaryLabel: 'Primary navigation',
      meet: 'Overview',
      platform: 'Capabilities',
      roles: 'Roles',
      governance: 'Governance',
      resources: 'Resources',
      login: 'Log in',
      contact: 'Contact team',
      enter: 'Enter demo',
    },
    productBar: {
      title: 'Product overview',
      link: 'View capabilities',
    },
    hero: {
      eyebrow: 'AI Counselor Demo, Phase 2',
      titleA: 'Meet your',
      titleB: 'AI counselor',
      copy: 'With NCHU AI, campus information is always within reach.',
      placeholder: 'I want to understand scholarships, mental health support, or academic warning workflows',
      prompts: [
        'What materials do I need for scholarship applications?',
        'I feel overwhelmed by study pressure. Where can I get support?',
        'If I receive an academic warning, who should I contact first?',
        'What emergency aid or financial support channels are available?',
        'I am having roommate conflict. Should I talk with a counselor first?',
        'I missed an assignment deadline. What should I do next?',
        'Can this answer show its source or policy basis?',
        'Can I save this consultation and continue it next time?',
        'When will the system hand me off to a human counselor?',
        'What can this demo answer now, and what still needs human confirmation?',
      ],
      inputLabel: 'Example question',
      start: 'Start consultation',
      pillsLabel: 'Common entry points',
      pillStudent: 'Student Q&A',
      pillCounselor: 'Counselor assist',
      pillKnowledge: 'Knowledge ops',
      visualLabel: 'NCHU AI abstract capability map',
      svgLabel: 'AI counselor capability routes',
      chipA: {
        title: 'Student request',
        copy: 'Intent recognition, resource matching, and session continuity',
      },
      chipB: {
        title: 'Human handoff',
        copy: 'High-risk situations are routed to counselors',
      },
      latest: {
        kicker: 'Latest update',
        title: 'Phase 2 is polishing login, role recognition, and the homepage experience.',
        link: 'View demo path',
      },
    },
    platform: {
      title: 'An AI partner for student support',
      lead: 'It is not an isolated chat box. It is an auditable, maintainable, and handoff-ready campus service entry point.',
      actionsLabel: 'Role entry points',
      rolesLink: 'View role scenarios',
      governanceLink: 'Review governance boundary',
      listLabel: 'Platform capability list',
      features: [
        {
          title: 'Deterministic demo answers',
          copy: 'Prove the full workflow with explainable knowledge matching before claiming approved RAG capabilities are live.',
        },
        {
          title: 'Role-based workspaces',
          copy: 'Students, counselors, and admins enter different interfaces with paths and density tuned to real duties.',
        },
        {
          title: 'Sources and audit',
          copy: 'Answers, resources, actions, and stats keep traceable context for internal governance needs.',
        },
        {
          title: 'Human collaboration',
          copy: 'The system provides suggestions and context, while key judgments stay with counselors.',
        },
      ],
      networkLabel: 'Capability network diagram',
      networkSvgLabel: 'NCHU AI capability network',
      orbit1: 'Student Q&A',
      orbit2: 'Knowledge resources',
      orbit3: 'Counselor assist',
      orbit4: 'Audit stats',
    },
    roles: {
      kicker: 'Built for campus support workflows',
      cta: 'Bring student service entry, counselor handling, and management audit into one demo.',
      title: 'How to use NCHU AI',
      lead: 'After login, the account role decides the entry point. The homepage does not expose three separate workspace buttons.',
      tabsLabel: 'User roles',
      tabs: ['Student', 'Counselor', 'Admin', 'Project demo'],
      cards: [
        {
          title: 'Student portal',
          copy: 'Ask questions, review source cards, save sessions, and transfer to human support when needed.',
        },
        {
          title: 'Counselor portal',
          copy: 'Review simulated cases, receive assistive suggestions, update status, and retain handling records.',
        },
        {
          title: 'Admin portal',
          copy: 'Maintain demo knowledge resources, reset data, and review statistics and audit activity.',
        },
      ],
    },
    governance: {
      title: 'Show capability boundaries clearly',
      lead: 'This phase prioritizes demo credibility: simulated data is labeled, and RAG, real student data, and public deployment require approval packages.',
      backTop: 'Back to top',
      plan: 'View next plan',
    },
    footer:
      'Prototype note: this page references the layout hierarchy, button grouping, and motion rhythm of Claude product pages, while using the NCHU AI counselor context and project approval colors.',
  },
}

function readStoredTheme(): HomeTheme {
  if (typeof window === 'undefined') {
    return 'light'
  }

  const value = window.localStorage.getItem(THEME_STORAGE_KEY)
  return value === 'dark' || value === 'light' ? value : 'light'
}

function readStoredLanguage(): HomeLanguage {
  if (typeof window === 'undefined') {
    return 'zh'
  }

  const value = window.localStorage.getItem(LANGUAGE_STORAGE_KEY)
  return value === 'en' || value === 'zh' ? value : 'zh'
}

function tokenizeMotionText(text: string) {
  return text.match(/\s+|[A-Za-z0-9]+|[\u4e00-\u9fff]|[^\s]/gu) ?? []
}

function MotionText({ text, className, motion }: { text: string; className?: string; motion: string }) {
  const tokens = useMemo(() => tokenizeMotionText(text), [text])

  return (
    <span className={className} data-motion={motion}>
      {tokens.map((token, index) => {
        if (/^\s+$/.test(token)) {
          return token
        }

        return (
          <span className="motion-token" key={`${token}-${index}`}>
            {token}
          </span>
        )
      })}
    </span>
  )
}

export default function ProductionHomePage() {
  const navigate = useNavigate()
  const pageRef = useRef<HTMLDivElement | null>(null)
  const typewriterRef = useRef<HTMLSpanElement | null>(null)
  const cursorRef = useRef<HTMLSpanElement | null>(null)
  const [theme, setTheme] = useState<HomeTheme>(() => readStoredTheme())
  const [language, setLanguage] = useState<HomeLanguage>(() => readStoredLanguage())
  const [promptFocused, setPromptFocused] = useState(false)
  const t = translations[language]

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme)
  }, [theme])

  useEffect(() => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language)
    document.documentElement.lang = language === 'en' ? 'en' : 'zh-CN'
  }, [language])

  useEffect(() => {
    if (!window.location.hash) {
      window.scrollTo({ top: 0, left: 0 })
    }

    const previousScrollRestoration = window.history.scrollRestoration
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual'
    }

    return () => {
      if ('scrollRestoration' in window.history) {
        window.history.scrollRestoration = previousScrollRestoration
      }
    }
  }, [])

  useEffect(() => {
    if (!typewriterRef.current || !cursorRef.current || promptFocused) {
      return
    }

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const typewriter = typewriterRef.current
    const cursor = cursorRef.current
    let timeline: gsap.core.Timeline | null = null
    let cursorTween: gsap.core.Tween | null = null

    if (reduceMotion) {
      typewriter.textContent = t.hero.placeholder
      cursor.style.opacity = '0'
      return
    }

    cursorTween = gsap.to(cursor, {
      autoAlpha: 0.24,
      duration: 0.55,
      ease: 'power1.inOut',
      repeat: -1,
      yoyo: true,
    })
    timeline = gsap.timeline({ repeat: -1, delay: 2.2 })

    t.hero.prompts.forEach((question) => {
      const state = { count: 0 }
      let rendered = 0

      timeline?.to(state, {
        count: question.length,
        duration: Math.max(question.length * 0.09, 1.2),
        ease: 'none',
        onStart: () => {
          rendered = 0
          typewriter.textContent = ''
        },
        onUpdate: () => {
          const next = Math.round(state.count)
          if (next !== rendered) {
            rendered = next
            typewriter.textContent = question.slice(0, next)
          }
        },
      })
      timeline?.to({}, { duration: 2.25 })
      timeline?.call(() => {
        typewriter.textContent = ''
      })
      timeline?.to({}, { duration: 0.35 })
    })

    return () => {
      timeline?.kill()
      cursorTween?.kill()
    }
  }, [language, promptFocused, t.hero.placeholder, t.hero.prompts])

  useGSAP(
    () => {
      const scope = pageRef.current
      if (!scope) {
        return
      }

      const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      const root = scope
      const selectAll = (selector: string) => gsap.utils.toArray<HTMLElement>(selector, root)

      if (reduceMotion) {
        gsap.set(selectAll('.motion-prep, .reveal, .motion-token, .hero-visual'), {
          autoAlpha: 1,
          y: 0,
          clearProps: 'clipPath,transform',
        })
        gsap.set(selectAll('.draw-line'), { strokeDashoffset: 0 })
        root.classList.add('motion-ready')
        return
      }

      let intro: gsap.core.Timeline | null = null
      let ambientTweens: gsap.core.Tween[] = []
      let pageGatedTimeline: gsap.core.Timeline | null = null
      let previousScrollY = window.scrollY
      let scrollDirectionY = 1
      const heroTokens = selectAll('.hero .motion-token')
      const revealItems = selectAll('.reveal')
      const pageGatedScope = scope.querySelector<HTMLElement>('[data-replay-scope="previous-page-gated"]')
      const pageGatedRevealItems = pageGatedScope
        ? revealItems.filter((item) => pageGatedScope.contains(item))
        : []
      const standaloneRevealItems = revealItems.filter(
        (item) => !pageGatedScope || !pageGatedScope.contains(item),
      )
      const childRevealSelector = '.feature-item, .role-card, .download-actions, .tabs'

      const getRevealChildren = (element: HTMLElement) => {
        if (!element.matches(childRevealSelector)) {
          return []
        }

        return element.matches('.download-actions, .tabs')
          ? Array.from(element.children) as HTMLElement[]
          : Array.from(element.querySelectorAll<HTMLElement>('.feature-num, h3, p'))
      }

      const getChildY = (y: number) => (y < 0 ? -12 : 12)

      const startAmbientMotion = () => {
        if (ambientTweens.length) {
          return
        }

        ambientTweens = selectAll('.flight-chip, .latest-card, .network-center').map((element, index) =>
          gsap.to(element, {
            y: index % 2 === 0 ? -8 : 8,
            duration: 3.4 + index * 0.2,
            repeat: -1,
            yoyo: true,
            ease: 'sine.inOut',
          }),
        )
      }

      const resetBrand = () => {
        const animatedText = scope.querySelector<HTMLElement>('[data-brand-animated-text]')
        if (!animatedText) {
          return
        }

        const shinyText = animatedText.querySelector<HTMLElement>('.brand-shiny-text')
        const introText = animatedText.querySelector<HTMLElement>('.brand-intro-text')
        const letters = Array.from(animatedText.querySelectorAll<HTMLElement>('.brand-text-letter'))
        const underline = animatedText.querySelector<HTMLElement>('.brand-text-underline')

        animatedText.classList.remove('brand-effect-ready')
        gsap.killTweensOf([animatedText, shinyText, introText, ...letters, underline].filter(Boolean))
        gsap.set(animatedText, { autoAlpha: 1 })
        gsap.set(letters, { autoAlpha: 0, y: 20 })
        if (shinyText) {
          gsap.set(shinyText, { autoAlpha: 0 })
        }
        if (introText) {
          gsap.set(introText, { autoAlpha: 1 })
        }
        if (underline) {
          gsap.set(underline, {
            autoAlpha: 0,
            width: '0%',
            left: '50%',
            scaleX: 1,
            transformOrigin: 'center center',
          })
        }
      }

      const createBrandTimeline = () => {
        const animatedText = scope.querySelector<HTMLElement>('[data-brand-animated-text]')
        const letters = animatedText
          ? Array.from(animatedText.querySelectorAll<HTMLElement>('.brand-text-letter'))
          : []
        const underline = animatedText?.querySelector<HTMLElement>('.brand-text-underline')
        const shinyText = animatedText?.querySelector<HTMLElement>('.brand-shiny-text')
        const introText = animatedText?.querySelector<HTMLElement>('.brand-intro-text')

        const timeline = gsap.timeline({
          onComplete: () => {
            if (!animatedText) {
              return
            }

            if (shinyText) {
              gsap.set(shinyText, { clearProps: 'opacity,visibility' })
            }
            if (introText) {
              gsap.set(introText, { clearProps: 'opacity,visibility' })
            }
            animatedText.classList.add('brand-effect-ready')
          },
        })

        if (!animatedText || !letters.length) {
          return timeline
        }

        timeline.to(letters, {
          autoAlpha: 1,
          y: 0,
          duration: 0.5,
          ease: 'back.out(1.7)',
          stagger: 0.1,
        })

        if (underline) {
          timeline.to(
            underline,
            {
              autoAlpha: 1,
              width: '100%',
              left: '0%',
              duration: 0.8,
              ease: 'power2.out',
            },
            letters.length * 0.1,
          )
        }

        return timeline
      }

      const playTextScramble = () => {
        const element = scope.querySelector<HTMLElement>('[data-text-scramble]')
        if (!element) {
          return
        }

        const text = element.dataset.textScramble || element.textContent || ''
        const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        const duration = Number(element.dataset.scrambleDuration || 0.8)
        const speed = Number(element.dataset.scrambleSpeed || 0.04)
        const steps = Math.max(1, Math.ceil(duration / Math.max(speed, 0.016)))
        const frameMs = Math.max(16, speed * 1000)
        let step = 0

        const timer = window.setInterval(() => {
          const progress = step / steps
          let scrambled = ''

          for (let index = 0; index < text.length; index += 1) {
            if (text[index] === ' ') {
              scrambled += ' '
            } else if (progress * text.length > index) {
              scrambled += text[index]
            } else {
              scrambled += characters[Math.floor(Math.random() * characters.length)]
            }
          }

          element.textContent = scrambled
          step += 1

          if (step > steps) {
            window.clearInterval(timer)
            element.textContent = text
          }
        }, frameMs)
      }

      const stopAmbientMotion = () => {
        ambientTweens.forEach((tween) => tween.kill())
        ambientTweens = []
        gsap.set(selectAll('.network-center'), { y: 0 })
      }

      const resetIntro = () => {
        intro?.kill()
        stopAmbientMotion()
        root.classList.remove('motion-ready')
        resetBrand()
        gsap.killTweensOf(selectAll('[data-motion], .hero-visual, .hero .draw-line, .motion-token'))
        gsap.set(selectAll('[data-motion="nav"]'), { autoAlpha: 0, y: -26 })
        gsap.set(selectAll('[data-motion="product-bar"]'), { autoAlpha: 0, y: 18 })
        gsap.set(selectAll('[data-motion="hero-eyebrow"], [data-motion="hero-line"], [data-motion="hero-copy"], [data-motion="prompt"]'), {
          autoAlpha: 0,
          y: 28,
        })
        gsap.set(selectAll('.hero-visual'), { autoAlpha: 0, y: 34 })
        gsap.set(selectAll('[data-motion="visual-panel"]'), { autoAlpha: 0, y: 28, scale: 0.985 })
        gsap.set(selectAll('[data-motion="chip"], [data-motion="latest-card"]'), { autoAlpha: 0, y: 24 })
        gsap.set(heroTokens, { autoAlpha: 0, y: 22 })
        gsap.set(selectAll('.hero .draw-line'), { strokeDashoffset: 1 })
      }

      const playIntro = () => {
        resetIntro()
        intro = gsap.timeline({
          defaults: { ease: 'power3.out' },
          delay: 0.06,
          onComplete: () => {
            root.classList.add('motion-ready')
            startAmbientMotion()
          },
        })

        intro
          .addLabel('top', 0)
          .to(selectAll('[data-motion="nav"]'), { autoAlpha: 1, y: 0, duration: 1.05 }, 'top')
          .add(createBrandTimeline(), 'top+=1.05')
          .to(selectAll('[data-motion="product-bar"]'), { autoAlpha: 1, y: 0, duration: 0.96 }, 'top+=0.24')
          .addLabel('hero', 'top+=0.62')
          .to(selectAll('[data-motion="hero-eyebrow"]'), { autoAlpha: 1, y: 0, duration: 0.86 }, 'hero')
          .call(playTextScramble, [], 'hero+=0.04')
          .set(selectAll('[data-motion="hero-line"]'), { autoAlpha: 1, y: 0 }, 'hero+=0.1')
          .to(heroTokens, { autoAlpha: 1, y: 0, duration: 1.18, stagger: { amount: 0.42 } }, 'hero+=0.12')
          .to(selectAll('[data-motion="hero-copy"]'), { autoAlpha: 1, y: 0, duration: 1.02 }, 'hero+=0.76')
          .to(selectAll('[data-motion="prompt"]'), { autoAlpha: 1, y: 0, scale: 1, duration: 0.98 }, 'hero+=1.02')
          .addLabel('visual', 'hero+=1.16')
          .to(selectAll('.hero-visual'), { autoAlpha: 1, y: 0, duration: 1.02 }, 'visual')
          .to(selectAll('[data-motion="visual-panel"]'), { autoAlpha: 1, y: 0, scale: 1, duration: 1.08 }, 'visual+=0.12')
          .to(selectAll('.hero .draw-line'), { strokeDashoffset: 0, duration: 1.38, stagger: 0.09 }, 'visual+=0.34')
          .to(selectAll('[data-motion="chip"]'), { autoAlpha: 1, y: 0, duration: 0.84, stagger: 0.12 }, 'visual+=0.56')
          .to(selectAll('[data-motion="latest-card"]'), { autoAlpha: 1, y: 0, duration: 0.9 }, 'visual+=0.78')
      }

      const resetReveal = (element: HTMLElement, y = 28) => {
        const textTokens = Array.from(element.querySelectorAll<HTMLElement>('.motion-token'))
        const children = getRevealChildren(element)
        gsap.killTweensOf([element, ...textTokens, ...children])
        gsap.set(element, { autoAlpha: 0, y, clipPath: 'inset(12% 0 0 0)' })
        gsap.set(textTokens, { autoAlpha: 0, y: getChildY(y) })
        gsap.set(children, { autoAlpha: 0, y: getChildY(y) })

        if (element.classList.contains('network-card')) {
          gsap.set(Array.from(element.querySelectorAll<HTMLElement>('.draw-line')), { strokeDashoffset: 1 })
          gsap.set(Array.from(element.querySelectorAll<HTMLElement>('.orbit-label')), {
            autoAlpha: 0,
            y: getChildY(y),
          })
        }

        element.dataset.revealActive = 'false'
      }

      const playReveal = (element: HTMLElement, y = 28) => {
        if (element.dataset.revealActive === 'true') {
          return
        }

        element.dataset.revealActive = 'true'
        const textTokens = Array.from(element.querySelectorAll<HTMLElement>('.motion-token'))
        const children = getRevealChildren(element)
        gsap.killTweensOf([element, ...textTokens, ...children])

        if (textTokens.length) {
          gsap.set(element, { autoAlpha: 1, y: 0, clipPath: 'inset(0% 0% 0% 0%)' })
          gsap.fromTo(
            textTokens,
            { autoAlpha: 0, y: getChildY(y) },
            {
              autoAlpha: 1,
              y: 0,
              duration: 0.9,
              stagger: { amount: 0.22 },
              ease: 'power2.out',
              overwrite: 'auto',
            },
          )
        } else {
          gsap.fromTo(
            element,
            { autoAlpha: 0, y, clipPath: 'inset(12% 0 0 0)' },
            {
              autoAlpha: 1,
              y: 0,
              clipPath: 'inset(0% 0% 0% 0%)',
              duration: 0.78,
              ease: 'power2.out',
              overwrite: 'auto',
            },
          )
        }

        if (children.length) {
          gsap.fromTo(
            children,
            { autoAlpha: 0, y: getChildY(y) },
            {
              autoAlpha: 1,
              y: 0,
              duration: 0.58,
              stagger: 0.055,
              ease: 'power2.out',
              delay: 0.08,
              overwrite: 'auto',
            },
          )
        }

        if (element.classList.contains('network-card')) {
          gsap.fromTo(
            Array.from(element.querySelectorAll<HTMLElement>('.draw-line')),
            { strokeDashoffset: 1 },
            { strokeDashoffset: 0, duration: 1.08, stagger: 0.08, ease: 'power3.out', overwrite: 'auto' },
          )
          gsap.fromTo(
            Array.from(element.querySelectorAll<HTMLElement>('.orbit-label')),
            { autoAlpha: 0, y: getChildY(y) },
            {
              autoAlpha: 1,
              y: 0,
              duration: 0.58,
              stagger: 0.08,
              ease: 'power3.out',
              delay: 0.18,
              overwrite: 'auto',
            },
          )
        }
      }

      const isInMotionViewport = (element: HTMLElement) => {
        const rect = element.getBoundingClientRect()
        return rect.bottom > window.innerHeight * 0.08 && rect.top < window.innerHeight * 0.92
      }

      const resetPageGatedReplayIfOnPreviousPage = () => {
        if (!pageGatedScope || !pageGatedRevealItems.length) {
          return
        }

        const rect = pageGatedScope.getBoundingClientRect()
        const isFullyBackOnPreviousPage = rect.top >= window.innerHeight * 0.9

        if (!isFullyBackOnPreviousPage || pageGatedScope.dataset.replayArmed === 'true') {
          return
        }

        pageGatedTimeline?.kill()
        pageGatedTimeline = null
        pageGatedRevealItems.forEach((element) => resetReveal(element, 28))
        pageGatedScope.dataset.replayArmed = 'true'
        pageGatedScope.dataset.replayPlayed = 'false'
      }

      const playPageGatedReplay = (y = 28) => {
        if (!pageGatedScope || pageGatedScope.dataset.replayPlayed === 'true') {
          return
        }

        pageGatedScope.dataset.replayPlayed = 'true'
        pageGatedScope.dataset.replayArmed = 'false'
        pageGatedTimeline = gsap.timeline({ defaults: { ease: 'power2.out' } })
        pageGatedRevealItems.forEach((element, index) => {
          pageGatedTimeline?.call(() => playReveal(element, y), [], index * 0.07)
        })
      }

      const onScroll = () => {
        const currentScrollY = window.scrollY
        scrollDirectionY = currentScrollY < previousScrollY ? -1 : 1
        previousScrollY = currentScrollY
        resetPageGatedReplayIfOnPreviousPage()
      }

      const getRevealY = (entry: IntersectionObserverEntry) => {
        if (entry.isIntersecting) {
          return scrollDirectionY < 0 ? -24 : 28
        }

        const rootTop = entry.rootBounds ? entry.rootBounds.top : 0
        return entry.boundingClientRect.top < rootTop ? -24 : 28
      }

      const revealObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            const element = entry.target as HTMLElement
            const y = getRevealY(entry)

            if (entry.isIntersecting) {
              playReveal(element, y)
            } else {
              resetReveal(element, y)
            }
          })
        },
        { threshold: 0.22, rootMargin: '-4% 0px -12% 0px' },
      )

      const pageGatedObserver = pageGatedScope
        ? new IntersectionObserver(
            (entries) => {
              entries.forEach((entry) => {
                if (
                  entry.isIntersecting &&
                  (scrollDirectionY >= 0 || pageGatedScope.dataset.replayArmed === 'true')
                ) {
                  playPageGatedReplay(28)
                }
              })
            },
            { threshold: 0.18, rootMargin: '-4% 0px -12% 0px' },
          )
        : null

      playIntro()
      revealItems.forEach((element) => resetReveal(element, 28))
      standaloneRevealItems.forEach((element) => revealObserver.observe(element))
      if (pageGatedScope) {
        pageGatedObserver?.observe(pageGatedScope)
      }
      window.addEventListener('scroll', onScroll, { passive: true })
      resetPageGatedReplayIfOnPreviousPage()

      if (pageGatedScope && isInMotionViewport(pageGatedScope)) {
        playPageGatedReplay(28)
      }

      return () => {
        intro?.kill()
        pageGatedTimeline?.kill()
        stopAmbientMotion()
        revealObserver.disconnect()
        pageGatedObserver?.disconnect()
        window.removeEventListener('scroll', onScroll)
      }
    },
    { scope: pageRef, dependencies: [language, theme], revertOnUpdate: true },
  )

  const goLogin = () => navigate('/login')
  const scrollTo = (selector: string) => {
    pageRef.current?.querySelector(selector)?.scrollIntoView({ behavior: 'smooth' })
  }
  const switchTheme = () => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))

  return (
    <div className="production-home" data-theme={theme} data-language={language} ref={pageRef}>
      <div className="site-shell">
        <div className="sticky-header">
          <header className="top-nav motion-prep" data-motion="nav">
            <div className="nav-inner">
              <a className="brand" href="#top" aria-label={t.nav.homeLabel}>
                <span className="brand-mark" aria-hidden="true">
                  <svg viewBox="0 0 32 32" fill="none">
                    <path d="M6 22 18 6l8 4-11 16-9-4Z" fill="currentColor" opacity="0.9" />
                    <path d="M9 22h15l-7 5-8-5Z" fill="currentColor" opacity="0.58" />
                  </svg>
                </span>
                <span className="animated-shiny-text" data-brand-animated-text="NCHU AI" aria-label="NCHU AI">
                  <span className="brand-shiny-text" aria-hidden="true">
                    NCHU AI
                  </span>
                  <span className="brand-intro-text" aria-hidden="true">
                    {'NCHU AI'.split('').map((letter, index) => (
                      <span className="brand-text-letter" key={`${letter}-${index}`}>
                        {letter === ' ' ? '\u00a0' : letter}
                      </span>
                    ))}
                  </span>
                  <span className="brand-text-underline" aria-hidden="true" />
                </span>
              </a>

              <nav className="primary-links" aria-label={t.nav.primaryLabel}>
                <a href="#meet">{t.nav.meet}</a>
                <a href="#platform">{t.nav.platform}</a>
                <a href="#roles">{t.nav.roles}</a>
                <a href="#governance">{t.nav.governance}</a>
                <a href="#resources">{t.nav.resources}</a>
              </nav>

              <div className="nav-actions">
                <button className="nav-link" type="button" onClick={goLogin}>
                  {t.nav.login}
                </button>
                <a className="btn btn-ghost" href="#resources">
                  {t.nav.contact}
                </a>
                <button className="btn btn-primary" type="button" onClick={goLogin}>
                  {t.nav.enter}
                </button>
                <div className="language-switch" aria-label={language === 'zh' ? '语言切换' : 'Language switch'}>
                  <button
                    type="button"
                    aria-pressed={language === 'zh'}
                    onClick={() => setLanguage('zh')}
                  >
                    中
                  </button>
                  <button
                    type="button"
                    aria-pressed={language === 'en'}
                    onClick={() => setLanguage('en')}
                  >
                    EN
                  </button>
                </div>
                <label className="theme-switch" htmlFor="homepage-theme-toggle" aria-label="主题切换">
                  <span className="theme-switch__toggle-wrap">
                    <input
                      id="homepage-theme-toggle"
                      className="theme-switch__toggle"
                      type="checkbox"
                      role="switch"
                      name="theme"
                      value="dark"
                      checked={theme === 'dark'}
                      onChange={switchTheme}
                    />
                    <span className="theme-switch__fill" />
                    <span className="theme-switch__icon" aria-hidden="true">
                      <span className="theme-switch__icon-part" />
                      <span className="theme-switch__icon-part" />
                      <span className="theme-switch__icon-part" />
                      <span className="theme-switch__icon-part" />
                      <span className="theme-switch__icon-part" />
                      <span className="theme-switch__icon-part" />
                      <span className="theme-switch__icon-part" />
                      <span className="theme-switch__icon-part" />
                      <span className="theme-switch__icon-part" />
                      <svg className="theme-switch__moon" viewBox="-2.4 0 24 24" focusable="false">
                        <path
                          fill="currentColor"
                          d="M20.1 14.6a7.6 7.6 0 0 1-10.7-10.7 8.5 8.5 0 1 0 10.7 10.7Z"
                        />
                      </svg>
                    </span>
                  </span>
                </label>
              </div>
            </div>
          </header>

          <div className="product-bar motion-prep" data-motion="product-bar">
            <div className="product-strip">
              <strong>{t.productBar.title}</strong>
              <a href="#platform">
                <span>{t.productBar.link}</span> <span aria-hidden="true">→</span>
              </a>
            </div>
          </div>
        </div>

        <main id="top" className="production-home-main">
          <section className="hero" id="meet" aria-labelledby="hero-title">
            <div className="hero-copy-block">
              <p className="eyebrow motion-prep" data-motion="hero-eyebrow">
                <span
                  className="text-scramble"
                  data-text-scramble={t.hero.eyebrow}
                  data-scramble-duration="0.8"
                  data-scramble-speed="0.04"
                  aria-label={t.hero.eyebrow}
                >
                  {t.hero.eyebrow}
                </span>
              </p>
              <h1 id="hero-title">
                <MotionText text={t.hero.titleA} motion="hero-line" className="motion-prep" />
                <MotionText text={t.hero.titleB} motion="hero-line" className="motion-prep" />
              </h1>
              <p className="hero-copy motion-prep" data-motion="hero-copy">
                {t.hero.copy}
              </p>

              <div className="prompt-box motion-prep" data-motion="prompt">
                <div className="prompt-main">
                  <div className="prompt-input-shell">
                    <input
                      value=""
                      placeholder={promptFocused ? t.hero.placeholder : ''}
                      aria-label={t.hero.inputLabel}
                      onChange={() => undefined}
                      onFocus={() => setPromptFocused(true)}
                      onBlur={() => setPromptFocused(false)}
                    />
                    <span className={`prompt-typewriter ${promptFocused ? 'is-hidden' : ''}`} aria-hidden="true">
                      <span className="prompt-typewriter-text" ref={typewriterRef} />
                      <span className="prompt-typewriter-cursor" ref={cursorRef} />
                    </span>
                  </div>
                  <button className="btn btn-primary" type="button" onClick={goLogin}>
                    {t.hero.start}
                  </button>
                </div>
                <div className="prompt-pills" aria-label={t.hero.pillsLabel}>
                  <button type="button" onClick={goLogin}>
                    {t.hero.pillStudent}
                  </button>
                  <button type="button" onClick={goLogin}>
                    {t.hero.pillCounselor}
                  </button>
                  <button type="button" onClick={goLogin}>
                    {t.hero.pillKnowledge}
                  </button>
                </div>
              </div>
            </div>

            <div className="hero-visual" aria-label={t.hero.visualLabel}>
              <div className="orbital-panel motion-prep" data-motion="visual-panel">
                <svg className="hero-svg" viewBox="0 0 640 560" role="img" aria-label={t.hero.svgLabel}>
                  <defs>
                    <linearGradient id="productionHomeLineGradient" x1="0" x2="1" y1="0" y2="1">
                      <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.28" />
                      <stop offset="100%" stopColor="var(--primary)" stopOpacity="0.9" />
                    </linearGradient>
                  </defs>
                  <path className="hero-line soft draw-line" pathLength="1" d="M83 386 C186 296 243 238 354 244 S515 215 566 103" />
                  <path className="hero-line soft draw-line" pathLength="1" d="M104 456 C192 396 270 374 390 382 S534 324 584 244" />
                  <path className="hero-line draw-line" pathLength="1" d="M122 324 C234 218 334 172 496 142" />
                  <path className="hero-line draw-line" pathLength="1" d="M210 452 C284 330 342 284 508 302" />
                  <g className="wing-symbol ambient-float">
                    <path d="M270 268 404 116l56 28-124 164-66-40Z" fill="var(--primary)" opacity="0.94" />
                    <path d="M278 312h150l-70 52-80-52Z" fill="var(--primary)" opacity="0.55" />
                    <path d="M224 372 360 218l56 30-125 164-67-40Z" fill="var(--primary)" opacity="0.74" />
                  </g>
                  <circle className="node pulse-ring" cx="124" cy="324" r="13" />
                  <circle className="node pulse-ring" cx="210" cy="452" r="10" />
                  <circle className="node pulse-ring" cx="496" cy="142" r="12" />
                  <circle className="node pulse-ring" cx="566" cy="103" r="8" />
                  <circle className="node pulse-ring" cx="584" cy="244" r="10" />
                </svg>
              </div>

              <div className="flight-chip chip-a motion-prep" data-motion="chip">
                <span className="dot" aria-hidden="true" />
                <span>
                  <strong>{t.hero.chipA.title}</strong>
                  <span>{t.hero.chipA.copy}</span>
                </span>
              </div>
              <div className="flight-chip chip-b motion-prep" data-motion="chip">
                <span className="dot" aria-hidden="true" />
                <span>
                  <strong>{t.hero.chipB.title}</strong>
                  <span>{t.hero.chipB.copy}</span>
                </span>
              </div>

              <aside className="latest-card motion-prep" data-motion="latest-card">
                <small>{t.hero.latest.kicker}</small>
                <h3>{t.hero.latest.title}</h3>
                <a href="#roles">
                  <span>{t.hero.latest.link}</span> →
                </a>
              </aside>
            </div>
          </section>

          <section id="platform" aria-labelledby="problem-title" data-replay-scope="previous-page-gated">
            <div className="section-inner section-centered">
              <h2 id="problem-title" className="reveal">
                <MotionText text={t.platform.title} motion="reveal-title" />
              </h2>
              <p className="section-lead reveal">{t.platform.lead}</p>
              <div className="download-actions reveal" aria-label={t.platform.actionsLabel}>
                <a className="btn btn-primary" href="#roles">
                  {t.platform.rolesLink}
                </a>
                <a className="btn btn-ghost" href="#governance">
                  {t.platform.governanceLink}
                </a>
              </div>

              <div className="problem-grid">
                <div className="feature-list" aria-label={t.platform.listLabel}>
                  {t.platform.features.map((feature, index) => (
                    <article className="feature-item reveal" key={feature.title}>
                      <span className="feature-num">{String(index + 1).padStart(2, '0')}</span>
                      <div>
                        <h3>{feature.title}</h3>
                        <p>{feature.copy}</p>
                      </div>
                    </article>
                  ))}
                </div>

                <div className="network-card reveal" aria-label={t.platform.networkLabel}>
                  <svg className="network-svg" viewBox="0 0 700 560" role="img" aria-label={t.platform.networkSvgLabel}>
                    <circle className="hero-line soft pulse-ring" cx="350" cy="280" r="178" />
                    <circle className="hero-line soft pulse-ring" cx="350" cy="280" r="238" />
                    <path className="hero-line draw-line" pathLength="1" d="M350 280 188 132" />
                    <path className="hero-line draw-line" pathLength="1" d="M350 280 536 126" />
                    <path className="hero-line draw-line" pathLength="1" d="M350 280 560 406" />
                    <path className="hero-line draw-line" pathLength="1" d="M350 280 158 420" />
                    <circle className="node" cx="188" cy="132" r="11" />
                    <circle className="node" cx="536" cy="126" r="11" />
                    <circle className="node" cx="560" cy="406" r="11" />
                    <circle className="node" cx="158" cy="420" r="11" />
                  </svg>
                  <div className="network-center" aria-hidden="true">
                    <span>NCHU AI</span>
                  </div>
                  <span className="orbit-label label-1">{t.platform.orbit1}</span>
                  <span className="orbit-label label-2">{t.platform.orbit2}</span>
                  <span className="orbit-label label-3">{t.platform.orbit3}</span>
                  <span className="orbit-label label-4">{t.platform.orbit4}</span>
                </div>
              </div>
            </div>
          </section>

          <section className="use-section" id="roles" aria-labelledby="use-title">
            <div className="cta-band reveal">
              <small>{t.roles.kicker}</small>
              <div className="cta-title">
                <MotionText text={t.roles.cta} motion="reveal-title" />
              </div>
            </div>

            <div className="section-inner">
              <div className="use-heading">
                <div className="use-icon reveal" aria-hidden="true">
                  <svg width="30" height="30" viewBox="0 0 32 32" fill="none">
                    <path d="M7 22 18 7l7 4-11 14-7-3Z" fill="currentColor" />
                    <path d="M10 23h13l-6 4-7-4Z" fill="currentColor" opacity="0.55" />
                  </svg>
                </div>
                <h2 id="use-title" className="reveal">
                  <MotionText text={t.roles.title} motion="reveal-title" />
                </h2>
                <p className="section-lead reveal">{t.roles.lead}</p>
              </div>

              <div className="tabs reveal" aria-label={t.roles.tabsLabel}>
                {t.roles.tabs.map((tab, index) => (
                  <span className={`tab ${index === 0 ? 'is-active' : ''}`} key={tab}>
                    {tab}
                  </span>
                ))}
              </div>

              <div className="role-preview">
                {t.roles.cards.map((card) => (
                  <article className="role-card reveal" key={card.title}>
                    <h3>{card.title}</h3>
                    <p>{card.copy}</p>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section id="governance" aria-labelledby="govern-title">
            <div className="section-inner section-centered">
              <h2 id="govern-title" className="reveal">
                <MotionText text={t.governance.title} motion="reveal-title" />
              </h2>
              <p className="section-lead reveal">{t.governance.lead}</p>
              <div className="download-actions reveal">
                <button className="btn btn-primary" type="button" onClick={() => scrollTo('#top')}>
                  {t.governance.backTop}
                </button>
                <a className="btn btn-ghost" href="#resources">
                  {t.governance.plan}
                </a>
              </div>
            </div>
          </section>
        </main>

        <footer className="review-note" id="resources">
          {t.footer}
        </footer>
      </div>
    </div>
  )
}
