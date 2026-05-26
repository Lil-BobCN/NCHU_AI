import { useMemo, useRef, useState } from 'react'
import { useGSAP } from '@gsap/react'
import gsap from 'gsap'

gsap.registerPlugin(useGSAP)

type TextScrambleProps = {
  phrases: string[]
  className?: string
  cursorClassName?: string
  charDelay?: number
  pause?: number
  repeat?: boolean
}

export function TextScramble({
  phrases,
  className = '',
  cursorClassName = '',
  charDelay = 0.045,
  pause = 1.5,
  repeat = true,
}: TextScrambleProps) {
  const containerRef = useRef<HTMLSpanElement>(null)
  const cursorRef = useRef<HTMLSpanElement>(null)
  const [displayText, setDisplayText] = useState('')
  const promptPhrases = useMemo(() => phrases.filter(Boolean), [phrases])

  useGSAP(
    () => {
      if (promptPhrases.length === 0) {
        setDisplayText('')
        return
      }

      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        setDisplayText(promptPhrases[0])
        gsap.set(cursorRef.current, { autoAlpha: 0 })
        return
      }

      gsap.to(cursorRef.current, {
        autoAlpha: 0.2,
        duration: 0.55,
        ease: 'power1.inOut',
        repeat: -1,
        yoyo: true,
      })

      const timeline = gsap.timeline({ repeat: repeat ? -1 : 0 })

      promptPhrases.forEach((phrase, phraseIndex) => {
        const state = { count: 0 }
        let renderedCount = 0
        const shouldClear = repeat || phraseIndex < promptPhrases.length - 1

        timeline.to(state, {
          count: phrase.length,
          duration: Math.max(phrase.length * charDelay, charDelay),
          ease: 'none',
          onStart: () => {
            renderedCount = 0
            setDisplayText('')
          },
          onUpdate: () => {
            const nextCount = Math.round(state.count)
            if (nextCount !== renderedCount) {
              renderedCount = nextCount
              setDisplayText(phrase.slice(0, nextCount))
            }
          },
        })

        if (shouldClear) {
          timeline.to(state, { count: phrase.length, duration: pause, ease: 'none' })
          timeline.call(() => setDisplayText(''))
          timeline.to(state, { count: 0, duration: 0.2, ease: 'none' })
        }
      })
    },
    {
      dependencies: [charDelay, pause, promptPhrases, repeat],
      scope: containerRef,
      revertOnUpdate: true,
    },
  )

  return (
    <span aria-hidden="true" className={className} ref={containerRef}>
      <span>{displayText}</span>
      <span className={cursorClassName} ref={cursorRef} />
    </span>
  )
}
