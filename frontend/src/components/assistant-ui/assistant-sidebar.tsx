import { type ReactNode } from "react"

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Menu } from "@/components/assistant-ui/chat-icons"
import {
  type AssistantConversationMeta,
  StudentThreadList,
} from "@/components/assistant-ui/thread-list"
import { TooltipIconButton } from "@/components/assistant-ui/tooltip-icon-button"
import { cn } from "@/lib/utils"

type AssistantSidebarProps = {
  conversations: AssistantConversationMeta[]
  header: ReactNode
  utility: ReactNode
  className?: string
  theme?: "light" | "dark"
}

export function AssistantSidebar({
  conversations,
  header,
  utility,
  className,
}: AssistantSidebarProps) {
  return (
    <aside className={cn("aui-sidebar", className)} aria-label="会话侧边栏">
      {header}
      {utility}
      <StudentThreadList conversations={conversations} />
    </aside>
  )
}

export function AssistantMobileSidebar({
  conversations,
  header,
  theme = "light",
  utility,
}: AssistantSidebarProps) {
  return (
    <TooltipProvider>
      <Sheet>
        <SheetTrigger asChild>
          <TooltipIconButton
            aria-label="打开会话记录"
            className="aui-mobile-sidebar-trigger"
            tooltip="会话记录"
            type="button"
          >
            <Menu />
          </TooltipIconButton>
        </SheetTrigger>
        <SheetContent
          className="aui-mobile-sidebar-sheet"
          data-chat-theme={theme}
          side="left"
          showCloseButton
        >
          <SheetHeader className="aui-mobile-sidebar-header">
            <SheetTitle className="aui-mobile-sidebar-title">会话记录</SheetTitle>
            <SheetDescription className="sr-only">
              查看会话记录、切换主题或开始新的学生咨询会话。
            </SheetDescription>
          </SheetHeader>
          {header}
          {utility}
          <StudentThreadList conversations={conversations} closeOnSelect />
        </SheetContent>
      </Sheet>
    </TooltipProvider>
  )
}
