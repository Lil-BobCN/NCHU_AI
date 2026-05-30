import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown"

export function MarkdownText({ smooth }: { smooth?: boolean }) {
  return (
    <MarkdownTextPrimitive
      className="aui-markdown"
      smooth={smooth}
      components={{
        a: ({ children, ...props }) => (
          <a {...props} target="_blank" rel="noreferrer">
            {children}
          </a>
        ),
        pre: ({ children, ...props }) => (
          <pre {...props} className="aui-markdown-codeblock">
            {children}
          </pre>
        ),
        code: ({ children, ...props }) => (
          <code {...props} className="aui-markdown-code">
            {children}
          </code>
        ),
      }}
    />
  )
}
