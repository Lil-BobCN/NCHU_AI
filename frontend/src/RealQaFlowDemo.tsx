import { useEffect, useMemo, useRef, useState } from 'react'
import {
  ApartmentOutlined,
  AuditOutlined,
  BranchesOutlined,
  CheckCircleOutlined,
  FormOutlined,
  ReloadOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
  SendOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Bubble, Sender, Think, ThoughtChain, XProvider } from '@ant-design/x'
import type { BubbleItemType, ThoughtChainItemType } from '@ant-design/x'
import { Avatar, Button, Tooltip } from 'antd'
import gsap from 'gsap'
import { useGSAP } from '@gsap/react'
import './RealQaFlowDemo.css'

gsap.registerPlugin(useGSAP)

const questionPlaceholder = '我想了解奖助学金、心理支持或学业预警流程'

const proofItems = ['右侧学生提问', '左侧 AI 回复', 'Ant Design X 推理']

const promptChips = [
  { icon: <FormOutlined />, label: '学生问答' },
  { icon: <ApartmentOutlined />, label: '辅导员协助' },
  { icon: <AuditOutlined />, label: '知识维护' },
]

function AssistantContent({ thinkingDone }: { thinkingDone: boolean }) {
  const thoughtItems: ThoughtChainItemType[] = [
    {
      key: 'intent',
      title: '识别咨询意图',
      description: '奖助学金、心理支持、学业预警',
      status: 'success',
      collapsible: true,
      content: '将问题归入学生事务咨询，并保留心理支持与人工转介边界。',
    },
    {
      key: 'match',
      title: '匹配校内流程',
      description: '从公开政策与服务入口中组织回答',
      status: thinkingDone ? 'success' : 'loading',
      blink: !thinkingDone,
      collapsible: true,
      content: '优先给出学生可以立即执行的入口，再提示需要辅导员确认的事项。',
    },
    {
      key: 'boundary',
      title: '检查人工边界',
      description: '风险、隐私、个案判断不由模型替代',
      status: thinkingDone ? 'success' : 'loading',
      blink: !thinkingDone,
      collapsible: true,
      content: '涉及心理危机、处分、资助资格争议时，建议联系学院辅导员或学校对应部门。',
    },
  ]

  return (
    <div className="qa-assistant-content">
      <Think
        rootClassName="qa-think-block qa-think-stack"
        title={thinkingDone ? '已完成问题匹配' : '正在匹配校内流程'}
        loading={!thinkingDone}
        blink={!thinkingDone}
        defaultExpanded
      >
        <ThoughtChain
          rootClassName="qa-thought-chain"
          line
          defaultExpandedKeys={['intent', 'match']}
          items={thoughtItems}
        />
        <p className="qa-thinking-note">展示的是可解释的匹配过程，不暴露模型内部推理细节。</p>
      </Think>

      <div className="qa-answer" aria-live="polite">
        <p>可以先按下面三个入口判断：</p>
        <ul>
          <li>奖助学金：先查看学生资助通知与申请条件，再准备证明材料。</li>
          <li>心理支持：如果已经影响睡眠、情绪或安全感，优先预约学校心理咨询服务。</li>
          <li>学业预警：先确认课程、绩点与预警节点，再联系辅导员制定补救计划。</li>
        </ul>
        <div className="qa-answer-boundary">
          如果涉及紧急风险或个人隐私细节，系统会建议转人工辅导员处理。
        </div>
      </div>
    </div>
  )
}

function createBubbleRoles() {
  return {
    student: {
      placement: 'end' as const,
      variant: 'filled' as const,
      shape: 'corner' as const,
      avatar: <Avatar size={30} icon={<UserOutlined />} style={{ background: '#122e8a' }} />,
      classNames: {
        content: 'qa-user-bubble-content',
      },
    },
    assistant: {
      placement: 'start' as const,
      variant: 'filled' as const,
      shape: 'corner' as const,
      avatar: <Avatar size={30} icon={<RobotOutlined />} style={{ background: '#f0eee7', color: '#122e8a' }} />,
      classNames: {
        content: 'qa-assistant-bubble-content',
      },
    },
  }
}

export default function RealQaFlowDemo() {
  const rootRef = useRef<HTMLElement | null>(null)
  const [playKey, setPlayKey] = useState(0)
  const [thinkingDone, setThinkingDone] = useState(false)
  const bubbleRoles = useMemo(() => createBubbleRoles(), [])

  const bubbleItems: BubbleItemType[] = [
    {
      key: 'student-question',
      role: 'student',
      rootClassName: 'qa-flow-step qa-bubble-user',
      content: '我想了解奖助学金、心理支持或学业预警流程，能不能告诉我从哪里开始？',
    },
    {
      key: 'assistant-answer',
      role: 'assistant',
      rootClassName: 'qa-flow-step qa-bubble-assistant',
      content: <AssistantContent thinkingDone={thinkingDone} />,
    },
  ]

  useEffect(() => {
    const timer = window.setTimeout(() => setThinkingDone(true), 4300)
    return () => window.clearTimeout(timer)
  }, [playKey])

  useGSAP(
    () => {
      const mm = gsap.matchMedia()

      mm.add(
        {
          reduceMotion: '(prefers-reduced-motion: reduce)',
          allowMotion: '(prefers-reduced-motion: no-preference)',
        },
        (context) => {
          const { reduceMotion } = context.conditions as { reduceMotion: boolean }
          const flowPanel = rootRef.current?.querySelector<HTMLElement>('.qa-flow-panel')

          if (!flowPanel) {
            return
          }

          gsap.set('.qa-frame, .qa-status-pill, .qa-compact-sender, .qa-chip, .qa-flow-toolbar, .qa-flow-step, .qa-think-stack, .qa-answer li, .qa-followup-sender', {
            clearProps: 'all',
          })

          if (reduceMotion) {
            gsap.set(flowPanel, { height: 'auto', autoAlpha: 1 })
            gsap.set('.qa-frame, .qa-status-pill, .qa-compact-sender, .qa-chip, .qa-flow-toolbar, .qa-flow-step, .qa-think-stack, .qa-answer li, .qa-followup-sender', {
              autoAlpha: 1,
              y: 0,
              scale: 1,
            })
            return
          }

          gsap.set(flowPanel, { height: 0, autoAlpha: 0 })
          gsap.set('.qa-flow-toolbar, .qa-flow-step, .qa-think-stack, .qa-answer li, .qa-followup-sender', {
            autoAlpha: 0,
            y: 18,
          })

          const timeline = gsap.timeline({
            defaults: { ease: 'power3.out' },
          })

          timeline
            .from('.qa-frame', {
              autoAlpha: 0,
              y: 28,
              scale: 0.985,
              duration: 0.72,
            })
            .from('.qa-status-pill', { autoAlpha: 0, y: 10, duration: 0.34 }, '-=0.34')
            .from('.qa-compact-sender', { autoAlpha: 0, y: 14, duration: 0.46 }, '-=0.16')
            .from('.qa-chip', { autoAlpha: 0, y: 12, stagger: 0.08, duration: 0.34 }, '-=0.14')
            .to('.qa-live-dot', {
              scale: 1.55,
              duration: 0.34,
              yoyo: true,
              repeat: 1,
              ease: 'sine.inOut',
            }, 'submit')
            .to('.qa-prompt-card', { y: -2, duration: 0.24 }, 'submit+=0.18')
            .to(flowPanel, {
              height: 'auto',
              autoAlpha: 1,
              duration: 0.82,
              ease: 'power3.inOut',
            }, 'submit+=0.28')
            .fromTo('.qa-flow-toolbar', { autoAlpha: 0, y: 12 }, { autoAlpha: 1, y: 0, duration: 0.36 }, 'submit+=0.72')
            .to('.qa-flow-step-student, .qa-bubble-user', { autoAlpha: 1, y: 0, duration: 0.42 }, 'submit+=1.02')
            .to('.qa-bubble-assistant', { autoAlpha: 1, y: 0, duration: 0.48 }, 'submit+=1.62')
            .to('.qa-think-stack', { autoAlpha: 1, y: 0, duration: 0.42 }, 'submit+=1.86')
            .to('.qa-answer li', { autoAlpha: 1, y: 0, stagger: 0.11, duration: 0.38 }, 'submit+=2.86')
            .to('.qa-followup-sender', { autoAlpha: 1, y: 0, duration: 0.4 }, 'submit+=3.38')
        },
        rootRef,
      )

      return () => mm.revert()
    },
    { scope: rootRef, dependencies: [playKey], revertOnUpdate: true },
  )

  const restart = () => {
    setThinkingDone(false)
    setPlayKey((current) => current + 1)
  }

  return (
    <XProvider
      theme={{
        token: {
          colorPrimary: '#122e8a',
          borderRadius: 8,
          fontFamily: "'Inter', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif",
        },
      }}
    >
      <main className="real-qa-demo-page" ref={rootRef}>
        <section className="real-qa-demo-layout" aria-labelledby="real-qa-demo-title">
          <div className="real-qa-demo-copy">
            <div className="real-qa-kicker">
              <BranchesOutlined />
              <span>Real QA flow demo</span>
            </div>
            <h1 id="real-qa-demo-title" className="real-qa-title">
              从一个咨询入口展开为真实答疑流程
            </h1>
            <p className="real-qa-copy">
              入口保持主站提示框的窄宽度；页面加载后先出现输入态，再从原位置向下展开为对话流。
            </p>
            <div className="real-qa-proof" aria-label="Demo checkpoints">
              {proofItems.map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          </div>

          <div className="real-qa-stage">
            <Tooltip title="重播动效">
              <Button className="qa-replay" shape="circle" icon={<ReloadOutlined />} onClick={restart} />
            </Tooltip>

            <div className="qa-frame" key={playKey}>
              <div className="qa-prompt-card">
                <div className="qa-prompt-topline">
                  <span className="qa-status-pill">
                    <span className="qa-live-dot" />
                    学生支持入口
                  </span>
                  <span className="qa-prompt-caption">NCHU AI</span>
                </div>

                <Sender
                  rootClassName="qa-compact-sender"
                  value=""
                  readOnly
                  submitType="shiftEnter"
                  autoSize={{ minRows: 1, maxRows: 2 }}
                  placeholder={questionPlaceholder}
                  onChange={() => undefined}
                  onSubmit={() => undefined}
                  suffix={
                    <Button type="primary" className="qa-start-button" icon={<SendOutlined />}>
                      开始咨询
                    </Button>
                  }
                />

                <div className="qa-chip-row">
                  {promptChips.map((item) => (
                    <span className="qa-chip" key={item.label}>
                      {item.icon}
                      {item.label}
                    </span>
                  ))}
                </div>
              </div>

              <div className="qa-flow-panel">
                <div className="qa-flow-inner">
                  <div className="qa-flow-toolbar">
                    <span className="qa-flow-title">学生咨询 · 奖助学金 / 心理支持 / 学业预警</span>
                    <span className="qa-evidence-tag">
                      <SafetyCertificateOutlined />
                      人工边界检查
                    </span>
                  </div>

                  <Bubble.List
                    className="qa-bubble-list"
                    autoScroll
                    role={bubbleRoles}
                    items={bubbleItems}
                  />

                  <Sender
                    rootClassName="qa-followup-sender"
                    value=""
                    readOnly
                    submitType="shiftEnter"
                    autoSize={{ minRows: 1, maxRows: 2 }}
                    placeholder="继续追问，例如：我该先联系哪个办公室？"
                    onChange={() => undefined}
                    onSubmit={() => undefined}
                    suffix={<Button icon={<CheckCircleOutlined />} />}
                  />
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </XProvider>
  )
}
