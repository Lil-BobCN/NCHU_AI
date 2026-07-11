// 本地 ID 工具：为上传队列等前端临时对象生成稳定标识。

export function createLocalId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}
