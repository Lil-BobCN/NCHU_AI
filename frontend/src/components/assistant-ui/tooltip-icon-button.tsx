import type { ComponentProps, ReactNode } from "react"

import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

type TooltipIconButtonProps = ComponentProps<typeof Button> & {
  tooltip: ReactNode
}

export function TooltipIconButton({
  children,
  className,
  tooltip,
  ...props
}: TooltipIconButtonProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          className={cn("chat-icon-button", className)}
          size="icon-sm"
          variant="ghost"
          {...props}
        >
          {children}
        </Button>
      </TooltipTrigger>
      <TooltipContent sideOffset={8}>{tooltip}</TooltipContent>
    </Tooltip>
  )
}
