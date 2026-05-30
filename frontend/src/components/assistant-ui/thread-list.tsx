import { ThreadListItemPrimitive, ThreadListPrimitive } from "@assistant-ui/react"

import { Button } from "@/components/ui/button"
import { Plus } from "@/components/assistant-ui/chat-icons"
import { SheetClose } from "@/components/ui/sheet"
import { cn } from "@/lib/utils"

export type AssistantConversationMeta = {
  id: string
  title: string
  messageCount: number
  updatedAt?: string
}

type StudentThreadListProps = {
  conversations: AssistantConversationMeta[]
  className?: string
  closeOnSelect?: boolean
}

export function StudentThreadList({
  conversations,
  className,
  closeOnSelect = false,
}: StudentThreadListProps) {
  return (
    <ThreadListPrimitive.Root
      className={cn("aui-thread-list-root", className)}
      aria-label="会话记录"
    >
      <ThreadListPrimitive.New asChild>
        <Button className="aui-new-thread-button" type="button" variant="ghost">
          <Plus data-icon="inline-start" />
          新会话
        </Button>
      </ThreadListPrimitive.New>

      <div className="aui-thread-list-scroll">
        {conversations.length === 0 ? (
          <div className="aui-thread-list-empty">
            还没有会话记录。发送第一条消息后，会自动出现在这里。
          </div>
        ) : (
          <ThreadListPrimitive.Items>
            {({ threadListItem }) => {
              const conversation = conversations.find((item) => item.id === threadListItem.id)
              const item = <StudentThreadListItem conversation={conversation} />

              return closeOnSelect ? <SheetClose asChild>{item}</SheetClose> : item
            }}
          </ThreadListPrimitive.Items>
        )}
      </div>
    </ThreadListPrimitive.Root>
  )
}

function StudentThreadListItem({
  conversation,
}: {
  conversation?: AssistantConversationMeta
}) {
  return (
    <ThreadListItemPrimitive.Root className="aui-thread-list-item">
      <ThreadListItemPrimitive.Trigger className="aui-thread-list-trigger">
        <span className="aui-thread-list-title">
          <ThreadListItemPrimitive.Title fallback={conversation?.title || "未命名会话"} />
        </span>
        <span className="aui-thread-list-meta">
          {conversation ? `${conversation.messageCount} 条消息` : "继续会话"}
        </span>
      </ThreadListItemPrimitive.Trigger>
    </ThreadListItemPrimitive.Root>
  )
}
