export type StudentChatAttachmentPayload = {
  id: string
  name: string
  mimeType?: string
  size: number
  content?: string
  encoding: "text" | "base64"
  error?: string
}
