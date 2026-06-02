import type { HTMLAttributes, ReactNode } from "react"
import { Mermaid, XProvider } from "@ant-design/x"
import { XMarkdown } from "@ant-design/x-markdown"
import type { ComponentProps } from "@ant-design/x-markdown"

type MarkdownTextProps = {
  content: string
  isStreaming?: boolean
  smooth?: boolean
}

const markdownComponents = {
  pre: MarkdownPre,
  code: MarkdownCode,
}

export function MarkdownText({ content, isStreaming = false }: MarkdownTextProps) {
  if (!content.trim()) {
    return null
  }

  return (
    <XProvider>
      <XMarkdown
        className="aui-markdown"
        components={markdownComponents}
        content={content}
        escapeRawHtml
        openLinksInNewTab
        streaming={{
          hasNextChunk: isStreaming,
          enableAnimation: isStreaming,
          tail: isStreaming ? { content: "▋" } : false,
        }}
      />
    </XProvider>
  )
}

function MarkdownPre(props: ComponentProps) {
  const { children, className } = props
  return (
    <div
      {...cleanMarkdownDomProps(props)}
      className={["aui-markdown-codeblock", className].filter(Boolean).join(" ")}
    >
      {children}
    </div>
  )
}

function MarkdownCode(props: ComponentProps) {
  const { block, children, className, lang } = props
  const language = lang?.split(/\s+/)[0]?.toLowerCase()
  if (block && language === "mermaid") {
    return (
      <Mermaid
        actions={{ enableCopy: true, enableDownload: false, enableZoom: true }}
        className="aui-markdown-mermaid"
      >
        {childrenToText(children)}
      </Mermaid>
    )
  }

  return (
    <code
      {...cleanMarkdownDomProps(props)}
      className={[
        block ? "aui-markdown-codeblock-code" : "aui-markdown-code",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </code>
  )
}

function cleanMarkdownDomProps(props: ComponentProps): HTMLAttributes<HTMLElement> {
  const next = { ...props } as Record<string, unknown>
  delete next.block
  delete next.children
  delete next.domNode
  delete next.lang
  delete next.streamStatus
  return next as HTMLAttributes<HTMLElement>
}

function childrenToText(children: ReactNode): string {
  if (typeof children === "string" || typeof children === "number") {
    return String(children)
  }
  if (Array.isArray(children)) {
    return children.map(childrenToText).join("")
  }
  return ""
}
