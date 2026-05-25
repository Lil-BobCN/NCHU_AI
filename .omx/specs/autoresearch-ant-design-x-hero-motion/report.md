# Autoresearch Report: Ant Design X Hero Motion Inspection

Date: 2026-05-23
Status: ready for review
Scope: live-page inspection only, no app code changes

## 1. 结论

你是对的：只看截图会误判。Ant Design X 首页右侧机器人确实有动效，而且动效不是简单静态图。

这次通过真实浏览器访问 `https://x.ant.design/index-cn` 后，结论需要修正为：

**Ant Design X 右侧机器人属于 Lottie 动画资产，使用 SVG renderer 渲染到页面中，并引用多张 PNG 图层资源。**

它不是：

- 不是普通 `<video>` 视频播放；
- 不是 WebGL / Three.js / Spline 的真实 3D 场景；
- 不是纯 CSS 手写动画；
- 也不是单张静态图片加一点 CSS 浮动。

更准确的类型是：

> Lottie / Bodymovin 动效资产 + SVG 渲染 + PNG 图层 + 前端播放器驱动

中文可以叫：

> 设计师制作的 Lottie 分层动效主视觉。

## 2. 证据

### 2.1 浏览器 DOM 证据

Playwright 实时检查首屏后得到：

```json
{
  "media": {
    "video": 0,
    "canvas": 0,
    "img": 22,
    "svg": 12
  }
}
```

这说明首屏没有使用 `<video>`，也没有使用 `<canvas>` / WebGL。

右侧机器人所在节点是：

```text
div.acss-g2p3pr > svg
```

该 SVG 中出现了大量 Lottie 生成标记：

```json
{
  "hasLottieIds": true,
  "lottieIds": [
    "__lottie_element_4",
    "__lottie_element_6",
    "__lottie_element_25",
    "__lottie_element_34",
    "__lottie_element_38"
  ],
  "imageCount": 19,
  "svgChildCount": 75
}
```

这基本可以确认它是 Lottie 渲染后的 SVG 结构。

证据文件：

- `output/ant-design-x-motion/robot-dom-excerpt.json`
- `output/ant-design-x-motion/lottie-svg-evidence.json`

### 2.2 网络资源证据

页面请求了 Lottie JSON 资源：

```text
GET https://mdn.alipayobjects.com/huamei_lkxviz/afts/file/n25_R7prS_0AAAAAQPAAAAgADtFMAQFr
content-type: application/json
```

响应体开头是典型 Lottie JSON：

```json
{
  "v": "5.11.0",
  "fr": 25,
  "ip": 26,
  "op": 155,
  "w": 900,
  "h": 900,
  "ddd": 0,
  "assets": [...]
}
```

其中 `assets` 里引用了多张 PNG 图层：

```json
{
  "id": "g_0",
  "w": 266,
  "h": 82,
  "p": "https://mdn.alipayobjects.com/.../original",
  "e": 1
}
```

证据文件：

- `output/ant-design-x-motion/request-52-body.txt`
- `output/ant-design-x-motion/network-requests.txt`

### 2.3 动态变化证据

真实浏览器连续采样显示，机器人内部 SVG `<g>` 元素的 `transform` 和 `opacity` 随时间变化。

例子：

```json
{
  "i": 417,
  "tag": "g",
  "opacity": "0.841877",
  "transform": "matrix(0.473646, 0, 0, 0.473646, 876.277, 520.759)"
}
```

一秒后：

```json
{
  "i": 417,
  "tag": "g",
  "opacity": "0.745101",
  "transform": "matrix(0.457517, 0, 0, 0.457517, 881.954, 522.211)"
}
```

再一秒后：

```json
{
  "i": 417,
  "tag": "g",
  "opacity": "0.965324",
  "transform": "matrix(0.494221, 0, 0, 0.494221, 869.034, 518.907)"
}
```

证据文件：

- `output/ant-design-x-motion/focused-transform-samples.json`
- `output/ant-design-x-motion/visible-bg-samples.txt`

### 2.4 视频采样证据

已录制 5 秒真实浏览器视频：

- `output/ant-design-x-motion/antx-hero-motion.webm`

截图采样：

- `output/ant-design-x-motion/antx-hero-t0.png`
- `output/ant-design-x-motion/antx-hero-t2.png`
- `output/ant-design-x-motion/antx-hero-t4.png`

截图之间能看到机器人和背景氛围的状态变化，但关键证据仍然是 DOM / Lottie JSON / transform 采样。

## 3. Lottie 资料对照

Lottie 官方文档说明，Lottie JSON 是一种描述图形和随时间变化运动的 JSON 动画格式，支持图片资源和 After Effects 表达式。

官方说明链接：

- https://docs.lottiefiles.com/en/format/lottie-json
- https://lottie.github.io/lottie-spec/dev/specs/assets/

这与 Ant Design X 的实际证据吻合：

- `v / fr / ip / op / w / h`：Lottie 动画基本字段；
- `assets`：资源列表；
- `layers`：动画图层；
- `p`：图片资源路径；
- `ks`：transform / opacity / scale / rotation 等关键帧数据；
- DOM 中出现 `__lottie_element_*`：Lottie SVG renderer 常见输出。

## 4. 这对我们项目意味着什么

之前我把 Ant Design X 右侧机器人归类为“分层图片 + CSS/JS 动效”，这个判断不够准确。更准确的生产路径应该是：

```text
设计师/动效师制作动效
    -> 导出 Lottie JSON + 图片资产
    -> 前端用 Lottie 播放器渲染
    -> 页面负责布局、加载、降级、适配
```

对我们的校徽飞翼动画，有三种可选生产路线：

### 路线 A：Lottie 路线

最接近 Ant Design X。

做法：

1. 设计师用 After Effects / Figma 插件 / Lottie 工具制作飞翼动效。
2. 导出 Lottie JSON。
3. 前端用 Lottie player 或 `lottie-web` 接入。

优点：

- 最像 Ant Design X 的生产方式；
- 适合复杂入场、缩放、发光、呼吸、透明度、图层运动；
- 比视频更轻，更适合网页；
- 可以保持透明背景；
- 可循环、可暂停、可响应 reduced-motion。

风险：

- 需要比较专业的 Lottie 动效资产；
- 如果我只靠代码生成 Lottie，质量仍然不一定高；
- 图片图层、遮罩、渐变、滤镜要经过兼容性测试；
- 需要新增播放器依赖，按我们流程要走审批。

### 路线 B：SVG + GSAP 路线

工程可控路线。

做法：

1. 把校徽飞翼拆成干净 SVG 图层。
2. 用 GSAP timeline 控制飞入、组合、整体浮动。

优点：

- 我能直接实现和调试；
- 对最终校徽几何形状控制更强；
- 不依赖外部动效设计工具；
- 更适合我们现在迭代验证。

风险：

- 要达到 Ant Design X 那种细腻质感，需要大量打磨；
- 复杂光效和细节不如专业 Lottie 动效资产自然。

### 路线 C：视频路线

最高保真路线。

做法：

1. 你提供完整飞翼动画视频。
2. 前端把视频接入首页 hero。

优点：

- 如果视频本身好，最终效果最稳定；
- 我不会误解动画细节；
- 开发成本低。

风险：

- 不易交互；
- 透明背景和移动端适配要额外处理；
- 修改需要重新导出视频。

## 5. 我的修正建议

如果你的目标是“像 Ant Design X 这种右侧机器人动效”，那我们的优先方案应该调整为：

```text
首选：Lottie 动效资产路线
备选：SVG + GSAP 工程复刻路线
兜底：视频高保真接入路线
```

更具体地说：

1. 如果你能找人或自己提供 Lottie / AE / Rive / 视频级素材，优先走 Lottie 或视频。
2. 如果没有专业动效素材，我可以先用 SVG + GSAP 做可交互原型，但不应该承诺能自然达到 Ant Design X 的动效细腻度。
3. 如果我们要正式采用 Lottie，需要新增一个 SDAR/审批包，确认：
   - 是否引入 `lottie-web` 或 `@lottiefiles/dotlottie-react`；
   - 动效资产来源；
   - 是否本地托管 JSON 和图片资产；
   - 中国大陆网络环境下是否禁用外链；
   - 首页加载性能和 fallback。

## 6. 推荐下一步

我建议下一步做一个很小的审批/对齐节点：

```text
SDAR: Homepage Wing Motion Asset Strategy
```

只决策一件事：

> 校徽飞翼主视觉到底走 Lottie、SVG+GSAP，还是视频。

我的当前推荐：

- 如果你能提供或制作专业动效资产：选 **Lottie**。
- 如果我们必须完全由我在代码里完成：选 **SVG + GSAP**，但预期要低于 Ant Design X 的细腻度。
- 如果你已经有完整满意的视频：选 **视频接入**。

