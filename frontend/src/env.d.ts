// Vite 类型声明：让 TypeScript 识别 import.meta.env 等构建时变量。

/// <reference types="vite/client" />

declare module '*.png' {
  const src: string
  export default src
}
