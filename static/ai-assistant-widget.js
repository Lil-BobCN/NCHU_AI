/**
 * AI智能问答助手 HTML插件
 * 独立的纯JavaScript实现，可嵌入任何HTML页面
 * 
 * @author AI Team
 * @version 1.0.2
 * 
 * 使用方式:
 * 1. 引入CSS: <link rel="stylesheet" href="ai-assistant-widget.css">
 * 2. 引入JS: <script src="ai-assistant-widget.js"></script>
 * 3. 初始化: await AIAssistant.init({ title: '智能助理' });
 * 
 * Markdown渲染优先级:
 * 1. 如果已加载官方marked.js，使用官方库（最佳效果）
 * 2. 否则自动从 CDN 加载 marked.js
 * 3. CDN加载失败或超时，回退到内置简化版本
 * 
 * 注意:
 * - init() 方法是 async 的，需要使用 await 或 .then()
 * - 插件会自动管理 marked.js 的加载，无需手动引入
 */

(function (global) {
  'use strict';

  // ========== 动态加载并检查marked.js ==========
  let marked;
  let markedReady = false;
  const markedCallbacks = [];

  // 检查marked是否就绪的Promise
  const ensureMarked = new Promise((resolve) => {
    // 1. 检测是否已经加载了官方marked库
    if (typeof window.marked !== 'undefined') {
      marked = window.marked;
      markedReady = true;
      resolve(marked);
      return;
    }

    // 2. 尝试动态加载CDN版本
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/marked/lib/marked.umd.js';
    script.async = true;

    script.onload = () => {
      if (typeof window.marked !== 'undefined') {
        marked = window.marked;
        
        // 配置marked选项：链接在新窗口打开
        if (marked.setOptions) {
          const renderer = new marked.Renderer();
          // 重写链接渲染函数 - 兼容不同版本的marked
          renderer.link = function(token) {
            // marked v9+ 传入的是token对象
            const href = typeof token === 'object' ? token.href : arguments[0];
            const title = typeof token === 'object' ? token.title : arguments[1];
            const text = typeof token === 'object' ? token.text : arguments[2];
            const titleAttr = title ? ` title="${title}"` : '';
            return `<a href="${href}" target="_blank" rel="noopener noreferrer nofollow"${titleAttr}>${text}</a>`;
          };
          marked.setOptions({ renderer: renderer });
        }
        
        markedReady = true;
        resolve(marked);
      } else {
        console.warn('⚠️ CDN 加载失败，使用内置简化版本');
        initBuiltInMarked();
        resolve(marked);
      }
    };

    script.onerror = () => {
      console.warn('⚠️ CDN 加载失败，使用内置简化版本');
      initBuiltInMarked();
      resolve(marked);
    };

    // 设置超时（5秒）
    setTimeout(() => {
      if (!markedReady) {
        console.warn('⚠️ CDN 加载超时，使用内置简化版本');
        script.onload = null;
        script.onerror = null;
        initBuiltInMarked();
        resolve(marked);
      }
    }, 5000);

    document.head.appendChild(script);
  });

  // 初始化内置的简化版marked
  function initBuiltInMarked() {
    marked = (function () {
      const marked = function (src) {
        return marked.parse(src);
      };

      marked.parse = function (src) {
        const tokens = marked.lexer(src);
        return marked.parser(tokens);
      };

      marked.lexer = function (src) {
        src = src.replace(/\r\n|\r/g, '\n').replace(/\t/g, '    ');
        return marked.blockTokens(src);
      };

      marked.blockTokens = function (src) {
        const tokens = [];
        let token;

        while (src) {
          // 表格（更强健的匹配）
          const tableRegex = /^(\|.+\|\s*\n)(\|\s*:?-+:?\s*\|.+\n)((?:\|.+\|\s*\n?)+)/;
          if (token = tableRegex.exec(src)) {
            src = src.substring(token[0].length);

            // 表头 - 保留所有单元格（包括空的）
            const headerParts = token[1].split('|');
            const header = [];
            for (let i = 1; i < headerParts.length - 1; i++) {
              header.push(headerParts[i].trim());
            }

            // 对齐方式 - 保持与表头一致
            const alignParts = token[2].split('|');
            const align = [];
            for (let i = 1; i < alignParts.length - 1; i++) {
              const c = alignParts[i].trim();
              if (/^:?-+:$/.test(c)) align.push('center');
              else if (/-+:$/.test(c)) align.push('right');
              else if (/^:-+/.test(c)) align.push('left');
              else align.push(null);
            }

            // 表体 - 保证每行列数一致
            const cells = [];
            const rows = token[3].trim().split('\n').filter(row => row.trim());
            rows.forEach(row => {
              const rowParts = row.split('|');
              const rowCells = [];
              for (let i = 1; i < rowParts.length - 1; i++) {
                rowCells.push(rowParts[i].trim());
              }
              // 补齐到表头长度
              while (rowCells.length < header.length) {
                rowCells.push('');
              }
              cells.push(rowCells);
            });

            tokens.push({ type: 'table', header, align, cells });
            continue;
          }

          // 代码块
          if (token = /^```([^\n]*)\n([\s\S]*?)```/.exec(src)) {
            src = src.substring(token[0].length);
            tokens.push({ type: 'code', lang: token[1], text: token[2] });
            continue;
          }

          // 标题
          if (token = /^(#{1,6}) +([^\n]+)/.exec(src)) {
            src = src.substring(token[0].length);
            tokens.push({ type: 'heading', depth: token[1].length, text: token[2] });
            continue;
          }

          // 列表（改进版 - 支持空格可选，兼容不同 AI 输出格式）
          if (token = /^( *)([-*+]|\d+\.) *([^\n]+)/.exec(src)) {
            const indent = token[1].length;
            const ordered = token[2].length > 1;
            const items = [];
            let currentItem = token[3];

            src = src.substring(token[0].length);

            // 持续收集列表项
            while (src) {
              // 检查是否是下一个列表项（紧邻的）
              const nextItemPattern = indent === 0
                ? /^\n([-*+]|\d+\.) *([^\n]+)/
                : new RegExp(`^\\n {${indent}}([-*+]|\\d+\\.) *([^\\n]+)`);
              const nextItem = nextItemPattern.exec(src);
              if (nextItem) {
                items.push(currentItem.trim());
                currentItem = nextItem[2];
                src = src.substring(nextItem[0].length);
                continue;
              }

              // 检查是否是继续行（缩进的内容）
              const continuationPattern = new RegExp(`^\\n {${indent + 2},}([^\\n]+)`);
              const continuation = continuationPattern.exec(src);
              if (continuation) {
                currentItem += '\n' + continuation[1];
                src = src.substring(continuation[0].length);
                continue;
              }

              // 空行后的继续项（修复：支持多个空行）
              const blankContinuationPattern = indent === 0
                ? /^\n+\s*([-*+]|\d+\.) *([^\n]+)/
                : new RegExp(`^\\n+\\s* {${indent}}([-*+]|\\d+\\.) *([^\\n]+)`);
              const blankContinuation = blankContinuationPattern.exec(src);
              if (blankContinuation) {
                items.push(currentItem.trim());
                currentItem = blankContinuation[2];
                src = src.substring(blankContinuation[0].length);
                continue;
              }

              break;
            }

            items.push(currentItem.trim());
            tokens.push({ type: 'list', ordered, items });
            continue;
          }

          // 段落
          const paragraphRegex = new RegExp('^([^\\n]+(?:\\n(?!\\n)[^\\n]+)*)');
          if (token = paragraphRegex.exec(src)) {
            src = src.substring(token[0].length);
            tokens.push({ type: 'paragraph', text: token[1] });
            continue;
          }

          // 空行
          if (token = /^\n+/.exec(src)) {
            src = src.substring(token[0].length);
            continue;
          }

          src = src.substring(1);
        }

        return tokens;
      };

      marked.parser = function (tokens) {
        let html = '';

        for (const token of tokens) {
          switch (token.type) {
            case 'heading':
              html += `<h${token.depth}>${marked.parseInline(token.text)}</h${token.depth}>`;
              break;
            case 'paragraph':
              html += `<p>${marked.parseInline(token.text)}</p>`;
              break;
            case 'code':
              html += `<pre><code class="language-${token.lang}">${marked.escape(token.text)}</code></pre>`;
              break;
            case 'list':
              const tag = token.ordered ? 'ol' : 'ul';
              html += `<${tag}>`;
              token.items.forEach(item => {
                html += `<li>${marked.parseInline(item)}</li>`;
              });
              html += `</${tag}>`;
              break;
            case 'table':
              html += '<table class="markdown-table"><thead><tr>';
              token.header.forEach((cell, i) => {
                const align = token.align[i] ? ` style="text-align:${token.align[i]}"` : '';
                html += `<th${align}>${marked.parseInline(cell || '')}</th>`;
              });
              html += '</tr></thead><tbody>';
              token.cells.forEach(row => {
                html += '<tr>';
                // 确保每行都有和表头一致的列数
                for (let i = 0; i < token.header.length; i++) {
                  const cell = row[i] !== undefined ? row[i] : '';
                  const align = token.align[i] ? ` style="text-align:${token.align[i]}"` : '';
                  html += `<td${align}>${marked.parseInline(cell || '-')}</td>`;
                }
                html += '</tr>';
              });
              html += '</tbody></table>';
              break;
          }
        }

        return html;
      };

      marked.parseInline = function (text) {
        if (!text) return '';

        // 1. 先保护代码块内容（避免代码中的特殊符号被处理）
        const codeBlocks = [];
        text = text.replace(/`([^`]+)`/g, function (match, code) {
          const index = codeBlocks.length;
          codeBlocks.push(code);
          return `__CODE_BLOCK_${index}__`;
        });

        // 2. 转义HTML特殊字符（但保留代码块占位符）
        text = text
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;');

        // 3. 处理Markdown格式（按优先级顺序）
        // 粗体（必须在斜体之前处理）
        text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/__(.+?)__/g, '<strong>$1</strong>');

        // 斜体
        text = text.replace(/\*([^*]+?)\*/g, '<em>$1</em>');
        text = text.replace(/_([^_]+?)_/g, '<em>$1</em>');

        // 删除线
        text = text.replace(/~~(.+?)~~/g, '<del>$1</del>');

        // 下划线
        text = text.replace(/<u>(.+?)<\/u>/g, '<u>$1</u>');

        // 高亮（使用mark标签）
        text = text.replace(/==(.+?)==/g, '<mark>$1</mark>');

        // 上标
        text = text.replace(/\^(.+?)\^/g, '<sup>$1</sup>');

        // 下标
        text = text.replace(/~(.+?)~/g, '<sub>$1</sub>');

        // 链接（Markdown格式：[文本](URL)）
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer nofollow">$1</a>');

        // 自动链接化：纯文本 URL（http://... 或 https://...）
        // 避免替换已存在的 <a> 标签内的 URL
        text = text.replace(/(?<!["'>])(https?:\/\/[^\s<>"']+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer nofollow">$1</a>');

        // 图片（Markdown格式）
        text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width: 100%; height: auto; border-radius: 8px; margin: 8px 0;" />');

        // 4. 恢复代码块并转义其中的HTML
        text = text.replace(/__CODE_BLOCK_(\d+)__/g, function (match, index) {
          const code = codeBlocks[parseInt(index)];
          const escapedCode = code
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
          return `<code>${escapedCode}</code>`;
        });

        // 5. 处理特殊HTML实体（常见的特殊符号）
        // 注意：不在inline中处理换行，由块级元素自动处理
        text = text
          .replace(/&amp;copy;/g, '&copy;')    // ©
          .replace(/&amp;reg;/g, '&reg;')      // ®
          .replace(/&amp;trade;/g, '&trade;')  // ™
          .replace(/&amp;nbsp;/g, '&nbsp;')    // 空格
          .replace(/&amp;mdash;/g, '&mdash;')  // —
          .replace(/&amp;ndash;/g, '&ndash;')  // –
          .replace(/&amp;hellip;/g, '&hellip;')// …
          .replace(/&amp;larr;/g, '&larr;')    // ←
          .replace(/&amp;rarr;/g, '&rarr;')    // →
          .replace(/&amp;uarr;/g, '&uarr;')    // ↑
          .replace(/&amp;darr;/g, '&darr;');   // ↓

        return text;
      };

      marked.escape = function (html) {
        if (!html) return '';
        return html
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#39;');
      };

      return marked;
    })();
  }

  // ========== fetch-event-source 内联实现 ==========
  const fetchEventSource = (function () {
    function fetchEventSource(url, options) {
      const { signal, onopen, onmessage, onerror, onclose, ...fetchOptions } = options;

      return fetch(url, {
        ...fetchOptions,
        credentials: fetchOptions.credentials || 'include',
        headers: {
          ...fetchOptions.headers,
          'Accept': 'text/event-stream'
        },
        signal
      }).then(async response => {
        if (!response.ok) {
          if (onopen) {
            await onopen(response);
          }
          throw new Error(`HTTP Error: ${response.status}`);
        }

        if (onopen) {
          await onopen(response);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        async function processStream() {
          try {
            while (true) {
              const { done, value } = await reader.read();

              if (done) {
                // 在关闭前，处理缓冲区中剩余的数据
                if (buffer.trim()) {
                  const remainingLines = buffer.split('\n');
                  for (const line of remainingLines) {
                    if (line.trim() === '' || line.startsWith(':')) continue;
                    if (line.startsWith('data:')) {
                      const data = line.startsWith('data: ') ? line.slice(6) : line.slice(5);
                      if (onmessage) {
                        onmessage({ data });
                      }
                    }
                  }
                  buffer = '';
                }
                if (onclose) onclose();
                break;
              }

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n');
              buffer = lines.pop() || '';

              for (const line of lines) {
                if (line.trim() === '' || line.startsWith(':')) continue;

                // 支持 "data:" 和 "data: " 两种格式
                if (line.startsWith('data:')) {
                  const data = line.startsWith('data: ') ? line.slice(6) : line.slice(5);
                  if (onmessage) {
                    onmessage({ data });
                  }
                }
              }
            }
          } catch (err) {
            // 忽略主动中止导致的错误
            if (err.name === 'AbortError') {
              if (onclose) onclose();
              return;
            }
            if (onerror) {
              onerror(err);
            }
            throw err;
          }
        }

        return processStream();
      }).catch(err => {
        // 忽略主动中止导致的错误
        if (err.name === 'AbortError') {
          return;
        }
        if (onerror) {
          onerror(err);
        }
        throw err;
      });
    }

    return fetchEventSource;
  })();

  // ========== 配置 ==========
  const defaultConfig = {
    // API配置（必须从外部传入，插件不包含任何默认API信息）
    apiKey: '',  // 必须传入：API密钥
    apiBaseUrl: '',  // 必须传入：API服务器地址
    chatId: '',  // 必须传入：对话ID

    // 界面配置
    title: 'AI智能助理',

    // 悬浮球位置配置(支持top/bottom和left/right组合)
    position: {
      bottom: '20px',  // 距离底部距离,可选top或bottom
      right: '20px'    // 距离右侧距离,可选left或right
    },

    // 悬浮球图标配置(支持图片URL或SVG代码)
    floatingIcon: {
      type: 'image',  // 'image' 或 'svg'
      value: 'AI_ASSISTANT_IMAGE.svg'  // 图片URL或SVG代码
    },

    // 悬浮球尺寸配置(单位:px)
    floatingBallSize: {
      width: 80,  // 悬浮球宽度,默认80px
      height: 80  // 悬浮球高度,默认80px
    },

    // 悬浮球消息气泡文字配置
    tooltipText: '您好！我是一个AI聊天助手！请问有什么需要帮助的吗？',

    // AI响应状态文字配置（显示在typing indicator中）
    thinkingText: '正在联网搜索，请稍候...',

    // 错误消息附加文本配置（显示在错误消息最后一行）
    errorAdditionalText: '',

    // 预设问题配置（可从外部传入，默认为空数组）
    presetTabs: [],

    // 文件上传配置
    maxFileSize: 10 * 1024 * 1024, // 10MB
    allowedFileTypes: ['txt', 'md', 'csv', 'pdf', 'doc', 'docx', 'xls', 'xlsx'],

    // 回调函数
    onInit: null,
    onOpen: null,
    onClose: null,
    onMessage: null,

    // 输入框配置
    maxInputLength: 500  // 最大输入500字
  };

  // ========== 状态管理 ==========
  let state = {
    showChatWindow: false,
    isFullscreen: false,
    isMobile: false,
    messages: [],
    isSending: false,
    isReceiving: false,
    activePresetTab: 0,
    hasHistoryMessages: false,
    historyMessageCount: 0,
    showDeleteConfirm: false,
    deleteConfirmData: {
      messageType: '',
      contentPreview: '',
      index: -1
    },
    showClearAllConfirm: false,
    clearAllConfirmData: {
      messageCount: 0
    },
    currentAbortController: null,
    currentTimeoutId: null, // 添加超时定时器ID
    showCloseConfirm: false,
    sliderAnimationId: null, // 滑块动画ID
    autoScrollEnabled: true,  // 自动滚动开关
    // 对话窗口拖动相关状态
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0,
    windowLeft: null,  // 对话窗口的left位置（非全屏时）
    windowTop: null,   // 对话窗口的top位置（非全屏时）
    windowWidth: 625,  // 对话窗口的宽度（非全屏时）
    windowHeight: 750, // 对话窗口的高度（非全屏时）
    // 悬浮球拖动相关状态
    isBallDragging: false,
    ballDragStartX: 0,
    ballDragStartY: 0,
    ballLeft: null,
    ballBottom: null,
    // 调整大小相关状态
    isResizing: false,
    resizeDirection: null,  // 调整方向：'n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw'
    resizeStartX: 0,
    resizeStartY: 0,
    resizeStartWidth: 625,
    resizeStartHeight: 750,
    resizeStartLeft: 0,
    resizeStartTop: 0,
    isWindowResizing: false,  // 标识窗口是否正在调整大小（包括全屏切换）
    savedScrollPercentageBeforeResize: null,  // 窗口调整大小前保存的滚动百分比
    savedScrollContainerInfo: null,  // 窗口调整大小前保存的容器尺寸信息
    hasSavedScrollForResize: false,  // 标识当前窗口调整操作是否已经保存过滚动位置
    ignoreNextScrollEvent: false,  // 标识是否忽略下一个滚动事件
    isRestoringScrollPosition: false,  // 标识是否正在恢复滚动位置
    hasShownWelcome: false,  // 标识是否已显示欢迎消息
    userCollege: null,  // 用户学院信息
    // 认证状态
    isLoggedIn: false,
    currentUser: null,  // { username, email, student_id }
    // 模型功能控制开关
    searchResults: [],  // 存储搜索结果URL
    citationUrls: {},   // 引用编号到URL的映射
    // Phase 6: 消息反馈状态
    feedback: {},       // { messageIndex: 'like' | 'dislike' }
  };

  let config = {};
  let container = null;

  // CRITICAL FIX: 文档级事件监听器只绑定一次，防止 render() 重复累积
  let _documentListenersBound = false;

  // ========== 工具函数 ==========
  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // ========== SVG图标 ==========
  const ICONS = {
    fullscreen: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg>',
    exitFullscreen: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path></svg>',
    close: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>',
    copy: '<svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>',
    copied: '<svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
    delete: '<svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>',
    resend: '<svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>',
    arrow: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>',
    warning: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="warning-icon"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
    stop: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg" class="stop-icon"><rect x="1" y="1" width="12" height="12" rx="2" stroke="white" stroke-width="2" fill="#ef4444"/></svg>',
    attachment: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>',
    clearAll: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><path d="M10 11 L10 17 M14 11 L14 17"></path><path d="M9 3 L15 3" stroke-linecap="round"></path></svg>',
    chevronLeft: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>',
    chevronRight: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>',
    sendArrow: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>',
    chevronDown: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>',
    sparkles: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path><path d="M5 3v4"></path><path d="M19 17v4"></path><path d="M3 5h4"></path><path d="M17 19h4"></path></svg>',
    regenerate: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"></path><path d="M16 16h5v5"></path></svg>',
    share: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path><polyline points="16 6 12 2 8 6"></polyline><line x1="12" y1="2" x2="12" y2="15"></line></svg>',
    thumbsUp: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 10v12"></path><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"></path></svg>',
    thumbsDown: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 14V2"></path><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"></path></svg>',
  };

  // ========== 工具函数 ==========
  function checkMobile() {
    const userAgent = navigator.userAgent.toLowerCase();
    const mobileKeywords = ['android', 'iphone', 'ipad', 'ipod', 'mobile', 'phone'];
    state.isMobile = mobileKeywords.some(keyword => userAgent.includes(keyword)) ||
      window.innerWidth <= 768;
  }

  function saveMessagesToSession() {
    try {
      const messagesToSave = state.messages.map(msg => ({
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp,
        citationUrls: msg.citationUrls,
        searchResults: msg.searchResults
      }));
      sessionStorage.setItem('ai_chatMessages', JSON.stringify(messagesToSave));
    } catch (error) {
      console.error('保存历史消息失败:', error);
    }
  }

  // 保存窗口状态到sessionStorage
  function saveWindowState() {
    try {
      const windowState = {
        isFullscreen: state.isFullscreen
      };
      sessionStorage.setItem('ai_windowState', JSON.stringify(windowState));
    } catch (error) {
      console.error('保存窗口状态失败:', error);
    }
  }

  // 保存滚动位置到sessionStorage
  function saveScrollPosition() {
    try {
      const messagesContainer = container.querySelector('.chat-messages');
      if (messagesContainer) {
        // 计算滚动百分比：当前滚动位置相对于可滚动范围的比例
        // 可滚动范围 = 总内容高度 - 可见区域高度
        const scrollableHeight = Math.max(0, messagesContainer.scrollHeight - messagesContainer.clientHeight);
        const scrollPercentage = scrollableHeight > 0 ? messagesContainer.scrollTop / scrollableHeight : 0;

        const scrollPosition = {
          scrollPercentage: scrollPercentage,
          clientHeight: messagesContainer.clientHeight,
          scrollHeight: messagesContainer.scrollHeight,
          scrollTop: messagesContainer.scrollTop,  // 同时保存绝对滚动位置
          timestamp: Date.now()
        };
        sessionStorage.setItem('ai_scrollPosition', JSON.stringify(scrollPosition));
      }
    } catch (error) {
      console.error('保存滚动位置失败:', error);
    }
  }

  // 保存输入状态到sessionStorage
  function saveInputState() {
    try {
      const input = container.querySelector('#ai-input');
      const inputState = {
        text: input ? input.value : ''
      };
      sessionStorage.setItem('ai_inputState', JSON.stringify(inputState));
    } catch (error) {
      console.error('保存输入状态失败:', error);
    }
  }

  // 从 sessionStorage 加载窗口状态
  function loadWindowState() {
    try {
      const savedState = sessionStorage.getItem('ai_windowState');
      if (savedState) {
        const parsedState = JSON.parse(savedState);
        if (parsedState && typeof parsedState.isFullscreen === 'boolean') {
          state.isFullscreen = parsedState.isFullscreen;
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('加载窗口状态失败:', error);
      return false;
    }
  }

  // 从 sessionStorage 加载滚动位置
  function loadScrollPosition() {
    try {
      // 如果窗口正在调整大小，则不执行滚动位置恢复
      if (state.isWindowResizing) {
        return false;
      }

      // 优先使用窗口调整大小前保存的百分比
      if (state.savedScrollPercentageBeforeResize !== null) {
        // 使用 requestAnimationFrame 确保 DOM 已渲染
        requestAnimationFrame(() => {
          const messagesContainer = container.querySelector('.chat-messages');
          if (messagesContainer) {
            const currentScrollableHeight = Math.max(0, messagesContainer.scrollHeight - messagesContainer.clientHeight);
            const targetScrollTop = Math.max(0, Math.min(
              currentScrollableHeight * state.savedScrollPercentageBeforeResize,
              currentScrollableHeight
            ));

            messagesContainer.scrollTop = targetScrollTop;

            // 重置保存的百分比
            state.savedScrollPercentageBeforeResize = null;
          }
        });
        return true;
      }

      // 如果没有保存的百分比，则从 sessionStorage 加载
      const savedPosition = sessionStorage.getItem('ai_scrollPosition');
      if (savedPosition) {
        const parsedPosition = JSON.parse(savedPosition);
        if (parsedPosition && typeof parsedPosition.scrollPercentage === 'number') {
          // 使用 requestAnimationFrame 确保 DOM 已渲染
          requestAnimationFrame(() => {
            const messagesContainer = container.querySelector('.chat-messages');
            if (messagesContainer) {
              // 使用保存的百分比乘以当前可滚动范围计算目标滚动位置
              const currentScrollableHeight = Math.max(0, messagesContainer.scrollHeight - messagesContainer.clientHeight);
              const targetScrollTop = Math.max(0, Math.min(
                currentScrollableHeight * parsedPosition.scrollPercentage,
                currentScrollableHeight
              ));

              messagesContainer.scrollTop = targetScrollTop;
            }
          });
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('加载滚动位置失败:', error);
      return false;
    }
  }

  // 从 sessionStorage 加载输入状态
  function loadInputState() {
    try {
      const savedInputState = sessionStorage.getItem('ai_inputState');
      if (savedInputState) {
        const parsedState = JSON.parse(savedInputState);
        if (parsedState) {
          // 恢复文本内容
          if (parsedState.text) {
            requestAnimationFrame(() => {
              const input = container.querySelector('#ai-input');
              if (input) {
                input.value = parsedState.text;
                adjustTextareaHeight.call(input);
                updateSendButtonState(); // 更新发送按钮状态

                // 确保输入框的滚动条位置正确
                setTimeout(() => {
                  input.scrollTop = input.scrollHeight;
                }, 0);
              }
            });
          }

          // 恢复附件信息（仅显示，实际文件需要重新选择）
          if (parsedState.file) {
            // 注意：出于安全原因，浏览器不允许通过JavaScript设置file input的值
            // 所以我们只能保存文件信息用于显示，但用户需要重新选择文件才能真正上传
            // 这里我们可以显示一个提示
          }

          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('加载输入状态失败:', error);
      return false;
    }
  }

  function loadMessagesFromSession() {
    try {
      const savedMessages = sessionStorage.getItem('ai_chatMessages');
      if (savedMessages) {
        const parsedMessages = JSON.parse(savedMessages);
        if (parsedMessages && parsedMessages.length > 0) {
          state.messages = parsedMessages.map(msg => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
            citationUrls: msg.citationUrls || {},
            searchResults: msg.searchResults || []
          }));
          state.hasHistoryMessages = true;
          state.historyMessageCount = parsedMessages.length;
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('加载历史消息失败:', error);
      return false;
    }
  }

  function scrollToBottom() {
    if (!state.autoScrollEnabled) return; // 如果自动滚动被禁用，则不执行

    setTimeout(() => {
      const messagesContainer = container.querySelector('.chat-messages');
      if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    }, 10);
  }

  // 检查是否已滚动到底部（允许10px的误差）
  function isScrolledToBottom(container) {
    if (!container) return true;
    const threshold = 10;
    return container.scrollHeight - container.scrollTop - container.clientHeight <= threshold;
  }

  // 监听消息容器的滚动事件
  let scrollSaveTimer = null;
  function handleMessagesScroll(e) {
    const messagesContainer = e.target;

    // 如果需要忽略滚动事件，则直接返回
    if (state.ignoreNextScrollEvent) {
      state.ignoreNextScrollEvent = false; // 重置标志
      return;
    }

    // 如果窗口正在调整大小，也忽略滚动事件
    if (state.isWindowResizing) {
      return;
    }

    // 如果正在恢复滚动位置，也忽略滚动事件
    if (state.isRestoringScrollPosition) {
      return;
    }

    if (isScrolledToBottom(messagesContainer)) {
      // 用户滚动到底部，重新启用自动滚动
      if (!state.autoScrollEnabled) {
        state.autoScrollEnabled = true;
      }
    } else {
      // 用户手动向上滚动，禁用自动滚动
      if (state.autoScrollEnabled) {
        state.autoScrollEnabled = false;
      }
    }

    // 防抖保存滚动位置（500ms后保存）
    // 仅在窗口未调整大小时保存
    if (!state.isWindowResizing) {
      // 重置窗口调整期间的保存标志
      state.hasSavedScrollForResize = false;

      if (scrollSaveTimer) {
        clearTimeout(scrollSaveTimer);
      }
      scrollSaveTimer = setTimeout(() => {
        saveScrollPosition();
      }, 500);
    }
  }

  // ========== 工具函数 ==========
  /**
   * 根据位置配置生成CSS样式字符串
   * @param {Object} position - 位置配置对象
   * @returns {string} CSS样式字符串
   */
  function getPositionStyle(position) {
    if (!position) {
      return 'bottom: 20px; right: 20px;';
    }

    const styles = [];

    // 处理垂直方向(top/bottom)
    if (position.top !== undefined) {
      styles.push(`top: ${position.top}`);
    } else if (position.bottom !== undefined) {
      styles.push(`bottom: ${position.bottom}`);
    } else {
      styles.push('bottom: 20px');
    }

    // 处理水平方向(left/right)
    if (position.left !== undefined) {
      styles.push(`left: ${position.left}`);
    } else if (position.right !== undefined) {
      styles.push(`right: ${position.right}`);
    } else {
      styles.push('right: 20px');
    }

    return styles.join('; ') + ';';
  }

  // ========== 渲染函数 ==========
  function renderFloatingBall() {
    // 根据配置类型生成悬浮球图标
    let iconHTML = '';
    if (config.floatingIcon.type === 'svg') {
      // 直接使用SVG代码
      iconHTML = config.floatingIcon.value;
    } else {
      // 使用图片URL
      iconHTML = `<img src="${config.floatingIcon.value}" alt="AI助手" class="floating-ball-img">`;
    }

    // 获取悬浮球尺寸配置
    const ballWidth = config.floatingBallSize?.width || 80;
    const ballHeight = config.floatingBallSize?.height || 80;

    // 获取悬浮球位置配置
    const positionStyle = getPositionStyle(config.position);

    return `
      <div class="floating-ball-wrapper" style="${positionStyle}">
        <button class="floating-ball" id="ai-floating-ball" style="width: ${ballWidth}px; height: ${ballHeight}px;">
          ${iconHTML}
        </button>
        <div class="floating-ball-tooltip">
          ${config.tooltipText}
        </div>
        <button class="floating-ball-close" id="ai-floating-ball-close" title="关闭AI助手">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      ${renderCloseConfirm()}
    `;
  }

  function renderCloseConfirm() {
    if (!state.showCloseConfirm) return '';

    return `
      <div class="close-confirm-overlay" id="ai-close-confirm-overlay">
        <div class="close-confirm-dialog">
          <div class="close-confirm-header">
            <svg class="info-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2196F3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
            <h3>关闭AI助手</h3>
          </div>
          <div class="close-confirm-body">
            <p>确定要关闭AI智能问答助手吗？</p>
            <p class="hint-text">关闭后您可以刷新页面来重新显示AI助手。</p>
          </div>
          <div class="close-confirm-footer">
            <button class="btn-cancel" id="ai-cancel-close">取消</button>
            <button class="btn-confirm-close" id="ai-confirm-close">确定关闭</button>
          </div>
        </div>
      </div>
    `;
  }

  function renderPresetPanel() {
    const tabs = config.presetTabs.map((tab, index) => `
      <button class="preset-tab ${state.activePresetTab === index ? 'active' : ''}" 
              data-tab-index="${index}">
        ${tab.title}
      </button>
    `).join('');

    const questions = config.presetTabs[state.activePresetTab].questions.map((q, index) => `
      <div class="preset-question-item" data-question="${q}">
        <span>${q}</span>
        ${ICONS.arrow}
      </div>
    `).join('');

    return `
      <div class="preset-panel">
        <div class="tabs-nav-container">
          <button class="tab-nav-btn tab-nav-left" id="ai-tab-nav-left" title="向左滚动">
            ${ICONS.chevronLeft}
          </button>
          <div class="preset-tabs">
            <div class="preset-tabs-slider" id="ai-tabs-slider"></div>
            <div class="preset-tabs-underline" id="ai-tabs-underline"></div>
            ${tabs}
          </div>
          <button class="tab-nav-btn tab-nav-right" id="ai-tab-nav-right" title="向右滚动">
            ${ICONS.chevronRight}
          </button>
        </div>
        <div class="preset-questions">${questions}</div>
      </div>
    `;
  }

  // 将纯文本 URL 转换为 Markdown 链接（自动链接化）
  function linkifyText(text) {
    // 先将已经是 Markdown 格式的链接保护起来，避免二次转换
    const protectedParts = [];
    let processedText = text.replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      function(match) {
        protectedParts.push(match);
        return `__LINK_${protectedParts.length - 1}__`;
      }
    );
    
    // 转换纯文本 URL 为 Markdown 链接
    // 支持：域名、IP地址、localhost、端口号
    processedText = processedText.replace(
      /(?<!["'\(])((?:https?:\/\/)(?:[a-zA-Z0-9][-a-zA-Z0-9]*|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|localhost)(?::\d+)?(?:[-a-zA-Z0-9._~:/?#[\]@!$&'()*+,;=%]*)?)/g,
      '[$1]($1)'
    );
    
    // 恢复被保护的 Markdown 链接
    protectedParts.forEach((part, index) => {
      processedText = processedText.replace(`__LINK_${index}__`, part);
    });
    
    return processedText;
  }

  // ========== 引用链接转换 ==========
  // 从 AI 回答内容中提取 Markdown 脚注格式的引用-URL映射
  // 支持格式：[^数字]: URL - 标题（Markdown脚注标准格式）
  function extractCitationUrlsFromContent(content) {
    if (!content) return {};
    
    const citationUrls = {};
    
    // Markdown 脚注格式：[^数字]: URL - 标题
    // 示例：[^1]: https://jwc.nchu.edu.cn/xxx.html - 教务处通知
    // 改进：支持更多URL格式，包括带参数、带括号的URL
    const footnoteRegex = /\[\^(\d+)\]:\s*(https?:\/\/[^\s\n]+?)(?:\s*-\s*([^\n]+))?$/gm;
    let match;
    while ((match = footnoteRegex.exec(content)) !== null) {
      const num = match[1];
      let url = match[2].trim();
      const title = match[3]?.trim();
      
      // 清理URL末尾的标点符号
      url = url.replace(/[.,;!?]+$/, '');
      
      if (num && url) {
        citationUrls[num] = { url, title };
      }
    }
    
    // 备选：也尝试匹配没有^的格式 [数字]: URL
    const altFootnoteRegex = /\[(\d+)\]:\s*(https?:\/\/[^\s\n]+?)(?:\s*-\s*([^\n]+))?$/gm;
    while ((match = altFootnoteRegex.exec(content)) !== null) {
      const num = match[1];
      let url = match[2].trim();
      const title = match[3]?.trim();
      
      url = url.replace(/[.,;!?]+$/, '');
      
      // 只有当这个编号还没有被提取过时才添加
      if (num && url && !citationUrls[num]) {
        citationUrls[num] = { url, title };
      }
    }
    
    return citationUrls;
  }
  
  // 将 [数字] 转换为可点击的引用链接（Phase 4: Kimi 风格 citation pill）
  function convertCitationsToLinks(htmlContent, citationUrls) {
    if (!htmlContent) return htmlContent;

    // 优先级1：传入的 citationUrls（从文末信息来源解析的）
    // 优先级2：state.citationUrls（来自搜索结果，兼容旧格式）
    const allCitationUrls = {};

    // 合并 state.citationUrls（可能是字符串URL）
    Object.entries(state.citationUrls).forEach(([num, val]) => {
      if (typeof val === 'string') {
        allCitationUrls[num] = { url: val, title: null };
      } else if (val && val.url) {
        allCitationUrls[num] = val;
      }
    });

    // 合并传入的 citationUrls（优先）
    Object.entries(citationUrls).forEach(([num, val]) => {
      if (typeof val === 'string') {
        allCitationUrls[num] = { url: val, title: null };
      } else if (val && val.url) {
        allCitationUrls[num] = val;
      }
    });

    // 按引用编号从大到小替换，避免[10]被[1]先匹配
    const sortedKeys = Object.keys(allCitationUrls).sort((a, b) => parseInt(b) - parseInt(a));

    let result = htmlContent;
    for (const num of sortedKeys) {
      const { url, title } = allCitationUrls[num];
      const safeTitle = escapeHtml(title || '查看详情');
      const safeNum = escapeHtml(num);
      const safeUrl = escapeHtml(url);

      // HIGH FIX: 替换时跳过 <code> 和 <pre> 块内的内容
      // 使用负向前瞻确保不在 <code>/<pre> 标签内
      const replacement = `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" ` +
        `class="citation-link" data-citation-num="${safeNum}" ` +
        `data-citation-title="${safeTitle}" data-citation-url="${safeUrl}">${num}</a>`;

      // 替换 [^数字] 格式
      const regex1 = new RegExp(`\\[\\^${num}\\](?!</a>)(?![^<]*</code>)(?![^<]*</pre>)`, 'g');
      result = result.replace(regex1, replacement);

      // 替换 [数字] 格式
      const regex2 = new RegExp(`\\[${num}\\](?!</a>)(?!:\\s*https?://)(?![^<]*</code>)(?![^<]*</pre>)`, 'g');
      result = result.replace(regex2, replacement);
    }

    return result;
  }

  // 处理信息来源部分，将其转换为链接列表
  function processSourceSection(htmlContent, citationUrls) {
    if (!htmlContent) return htmlContent;
    
    
    // 检测信息来源/参考资料区块 - 改进正则，更灵活匹配
    const sourceSectionRegex = /(<h[1-6][^>]*>\s*(?:信息来源|参考资料|参考链接|相关链接|引用来源|参考)[：:\s]*<\/h[1-6]>|<p>\s*<strong>\s*(?:信息来源|参考资料|参考链接|相关链接|引用来源|参考)[：:\s]*<\/strong>\s*<\/p>|<p>\s*(?:信息来源|参考资料|参考链接|相关链接|引用来源|参考)[：:\s]*<\/p>|<h[1-6][^>]*>\s*##\s*(?:信息来源|参考资料|参考链接|相关链接|引用来源|参考)[：:\s]*<\/h[1-6]>)([\s\S]*?)(?=<(?:h[1-6]|p><strong|div)|<\/div>|<div class="|$)/i;
    
    // 如果没有匹配到标准区块，尝试匹配 ## 参考链接 格式
    const altSourceRegex = /##\s*(?:参考链接|参考资料|信息来源)([\s\S]*?)(?=\n##|\n\n\n|$)/i;
    
    let hasMatch = false;
    
    // 先尝试标准匹配
    let result = htmlContent.replace(sourceSectionRegex, (match, header, content) => {
      hasMatch = true;
      return generateSourceSection(content, citationUrls);
    });
    
    // 如果没匹配到，尝试备选匹配
    if (!hasMatch) {
      result = result.replace(altSourceRegex, (match, content) => {
        return generateSourceSection(content, citationUrls);
      });
    }
    
    return result;
  }
  
  // 辅助函数：生成来源区块HTML
  function generateSourceSection(content, citationUrls) {
    // 从 citationUrls 构建链接列表
    const links = [];
    
    Object.entries(citationUrls).forEach(([num, val]) => {
      const url = typeof val === 'string' ? val : val?.url;
      let title = typeof val === 'string' ? null : val?.title;
      
      if (!url) return;
      
      // 跳过模拟链接
      if (url.includes('example')) return;
      
      // 如果没有标题，使用域名
      if (!title) {
        try {
          const urlObj = new URL(url);
          title = urlObj.hostname.replace(/^www\./, '');
        } catch (e) {
          title = '相关链接';
        }
      }
      
      // 去重
      if (!links.find(l => l.url === url)) {
        links.push({ url, title, num });
      }
    });
    
    // 同时处理 Markdown 脚注格式 [^数字]: URL - 标题
    // 从原始内容中提取脚注定义
    const footnoteMatches = content.matchAll(/\[\^(\d+)\]:\s*(https?:\/\/[^\s\n]+?)(?:\s*-\s*([^<\n]+))?/g);
    for (const match of footnoteMatches) {
      const num = match[1];
      let url = match[2].trim();
      const title = match[3]?.trim();
      
      // 清理URL
      url = url.replace(/[.,;!?]+$/, '');
      
      if (url && !links.find(l => l.url === url)) {
        links.push({ url, title: title || `参考链接[^${num}]`, num });
      }
    }
    
    
    // 如果没有有效链接，返回空字符串（不显示该部分）
    if (links.length === 0) {
      return '';
    }
    
    // 按编号排序
    links.sort((a, b) => parseInt(a.num) - parseInt(b.num));
    
    // 生成链接列表 HTML - 使用标题作为链接文本
    const linksHtml = links.map(link =>
      `<li><a href="${escapeHtml(link.url)}" target="_blank" rel="noopener noreferrer" class="source-link">${escapeHtml(link.title)}</a></li>`
    ).join('');
    
    return `
      <div class="source-section">
        <p class="source-title"><strong>📚 相关链接</strong></p>
        <ul class="source-list">${linksHtml}</ul>
      </div>
    `;
  }

  function renderMessage(message, index) {
    // ========== Phase 3: 思考卡片渲染 ==========
    if (message.type === 'ai' && message.isThinking) {
      const thinkingText = message.thinkingStatus === 'searching' ? '正在搜索' : '正在思考';
      return `
        <div class="message ai" data-layout="three-part">
          <div class="thinking-card">
            <div class="thinking-dots">
              <span></span><span></span><span></span>
            </div>
            <span class="thinking-label">${thinkingText}</span>
          </div>
          <div class="message-actions"></div>
        </div>
      `;
    }

    // 对 AI 消息预处理：自动链接化纯文本 URL
    let processedContent = message.type === 'ai' ? linkifyText(message.content) : message.content;
    
    // 如果是AI消息，从内容中提取文末的引用-URL映射
    if (message.type === 'ai' && !message.citationUrls) {
      message.citationUrls = extractCitationUrlsFromContent(message.content);
    }
    
    let content = message.type === 'ai'
      ? (marked.parse ? marked.parse(processedContent) : marked(processedContent))
      : escapeHtml(processedContent).replace(/\n/g, '<br>');
    
    // 转换引用链接 [数字] 为可点击链接
    if (message.type === 'ai' && content) {
      content = convertCitationsToLinks(content, message.citationUrls || {});
    }
    
    // 处理信息来源部分，将其转换为链接列表
    if (message.type === 'ai' && content) {
      content = processSourceSection(content, message.citationUrls || {});
    }

    // 如果是错误消息，且配置了附加文本，则添加到内容末尾
    if (message.type === 'error' && config.errorAdditionalText && config.errorAdditionalText.trim() !== '') {
      const additionalText = config.errorAdditionalText.replace(/\n/g, '<br>');
      content += `<span class="error-additional-text">${additionalText}</span>`;
    }

    // 判断当前是否正在发送或接收消息
    const isProcessing = state.isSending || state.isReceiving;

    // 判断是否是最后一条AI消息且正在输出
    const isLastAIMessage = message.type === 'ai' && index === state.messages.length - 1;
    const isTypingThisMessage = isLastAIMessage && message.isTyping;

    // 重新发送按钮（只有用户消息才有）
    const resendBtn = message.type === 'user' ? `
      <button class="action-btn resend-btn${isProcessing ? ' disabled' : ''}" 
              data-index="${index}" 
              title="重新发送"
              ${isProcessing ? 'disabled' : ''}>
        <svg xmlns="http://www.w3.org/2000/svg" width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="23 4 23 10 17 10"></polyline>
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
        </svg>
      </button>
    ` : '';

    // Phase 6: AI 消息新增操作按钮
    const aiExtraBtns = message.type === 'ai' ? `
      <button class="action-btn regenerate-btn" data-index="${index}" title="重新生成" ${isProcessing ? 'disabled' : ''}>
        ${ICONS.regenerate}
      </button>
      <button class="action-btn share-btn" data-index="${index}" title="分享消息">
        ${ICONS.share}
      </button>
      <button class="action-btn feedback-btn feedback-like${message.feedback === 'like' ? ' active' : ''}" data-index="${index}" data-feedback="like" title="点赞">
        ${ICONS.thumbsUp}
      </button>
      <button class="action-btn feedback-btn feedback-dislike${message.feedback === 'dislike' ? ' active' : ''}" data-index="${index}" data-feedback="dislike" title="点踩">
        ${ICONS.thumbsDown}
      </button>
    ` : '';

    // 复制按钮：允许复制AI正在输出的消息
    const copyBtn = `
      <button class="action-btn copy-btn"
              data-index="${index}"
              title="复制消息">
        ${message.copied ? ICONS.copied : ICONS.copy}
      </button>
    `;

    // 删除按钮：处理期间禁用
    const deleteBtn = `
      <button class="action-btn delete-btn${isProcessing ? ' disabled' : ''}"
              data-index="${index}"
              title="删除消息"
              ${isProcessing ? 'disabled' : ''}>
        ${ICONS.delete}
      </button>
    `;

    // 始终显示按钮
    const actions = `
      <div class="message-actions">
        ${aiExtraBtns}
        ${copyBtn}
        ${resendBtn}
        ${deleteBtn}
      </div>
    `;


    // 【第二部分】联网搜索结果区 - 独立窗口
    let searchHTML = '';
    if (message.type === 'ai' && message.searchResults && message.searchResults.length > 0) {
      const searchItems = message.searchResults.map((result, i) => {
        const safeUrl = escapeHtml(result.url || '');
        const safeTitle = escapeHtml(result.title || '搜索结果');
        return `
        <div class="search-result-item" data-url="${safeUrl}">
          <span class="search-result-bullet">📄</span>
          <div class="search-result-content">
            <div class="search-result-title">${safeTitle}</div>
            <div class="search-result-url">${safeUrl}</div>
          </div>
        </div>`;
      }).join('');

      searchHTML = `
        <div class="search-panel" data-part="search">
          <div class="search-header">
            <span class="search-icon">🔍</span>
            <span class="search-label">联网搜索结果</span>
            <span class="search-count">共 ${message.searchResults.length} 条</span>
          </div>
          <div class="search-results">
            ${searchItems}
          </div>
        </div>
      `;
    }

    // ========== Phase 3: 搜索关键词条（Kimi 风格）==========
    let searchKeywordsBarHTML = '';
    if (message.type === 'ai' && message.searchKeywords && message.searchKeywords.length > 0) {
      const keywordTags = message.searchKeywords.map(kw => `<span class="keyword-tag">${escapeHtml(kw)}</span>`).join('');
      searchKeywordsBarHTML = `
        <div class="search-keywords-bar">
          <span class="search-icon-label">🔍 搜索</span>
          ${keywordTags}
          ${message.searchResultCount ? `<span class="result-count">${escapeHtml(String(message.searchResultCount))} 个结果</span>` : ''}
        </div>
      `;
    }

    // ========== Phase 5: 底部来源卡片 ==========
    let sourceCardsHTML = '';
    if (message.type === 'ai' && message.citationUrls && Object.keys(message.citationUrls).length > 0) {
      const sourceEntries = Object.entries(message.citationUrls)
        .map(([num, val]) => {
          const url = typeof val === 'string' ? val : val?.url;
          const title = typeof val === 'string' ? null : val?.title;
          if (!url || url.includes('example')) return null;
          const domain = (() => {
            try { return new URL(url).hostname.replace('www.', ''); } catch { return url; }
          })();
          const safeTitle = escapeHtml(title || domain);
          const safeDomain = escapeHtml(domain);
          const faviconUrl = `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=32`;
          return { url, safeTitle, safeDomain, faviconUrl };
        })
        .filter(Boolean);

      if (sourceEntries.length > 0) {
        const sourceCount = sourceEntries.length;
        const cardsHTML = sourceEntries.map(entry => `
          <div class="source-card" data-url="${escapeHtml(entry.url)}">
            <img class="source-favicon" src="${entry.faviconUrl}" onerror="this.style.display='none'" alt="" referrerpolicy="no-referrer" />
            <div class="source-info">
              <div class="source-title">${entry.safeTitle}</div>
              <div class="source-domain">${entry.safeDomain}</div>
            </div>
            <div class="source-expand-icon">›</div>
          </div>`).join('');
        sourceCardsHTML = `
          <div class="source-cards-container" data-source-cards>
            <div class="source-cards-header" data-action="toggle-sources">
              <span class="source-cards-label">${sourceCount} 个来源</span>
              <span class="source-cards-toggle">▼</span>
            </div>
            <div class="source-cards-list collapsed">
              ${cardsHTML}
            </div>
          </div>`;
      }
    }

    const historyDivider = state.hasHistoryMessages && index === state.historyMessageCount - 1 ? `
      <div class="history-divider">
        <span>———— 以上是历史消息 ————</span>
      </div>
    ` : '';

    // 【第三部分】最终结果区
    return `
      <div class="message ${message.type}" data-layout="three-part">
        ${searchKeywordsBarHTML}
        ${searchHTML}
        <div class="message-content" data-part="answer">${content}</div>
        ${sourceCardsHTML}
        ${actions}
        ${historyDivider}
      </div>
    `;
  }
  
  // 获取状态文本
  function getStatusText(status) {
    const statusMap = {
      'processing': '进行中',
      'completed': '已完成',
      'failed': '失败',
      'searching': '搜索中',
      
      'analyzing': '分析中'
    };
    return statusMap[status] || '已完成';
  }

  function renderTypingIndicator() {
    // 简化typing indicator，只显示闪烁光标
    return `
      <div class="typing-indicator">
        <span class="streaming-cursor"></span>
      </div>
    `;
  }

  function renderDeleteConfirm() {
    if (!state.showDeleteConfirm) return '';

    return `
      <div class="confirm-overlay" id="ai-confirm-overlay">
        <div class="confirm-dialog">
          <div class="confirm-header">
            ${ICONS.warning}
            <h3>确认删除</h3>
          </div>
          <div class="confirm-body">
            <p class="message-type">${state.deleteConfirmData.messageType}</p>
            <div class="content-preview">
              <p>${state.deleteConfirmData.contentPreview}</p>
            </div>
            <p class="warning-text">此操作不可撤销，确定要删除吗？</p>
          </div>
          <div class="confirm-footer">
            <button class="btn-cancel" id="ai-cancel-delete">取消</button>
            <button class="btn-confirm" id="ai-confirm-delete">确定删除</button>
          </div>
        </div>
      </div>
    `;
  }

  function renderChatWindow() {
    const fullscreenBtn = !state.isMobile ? `
      <button class="fullscreen-btn" id="ai-fullscreen-btn" title="${state.isFullscreen ? '退出全屏' : '全屏'}">
        ${state.isFullscreen ? ICONS.exitFullscreen : ICONS.fullscreen}
      </button>
    ` : '';

    const messages = state.messages.map((msg, index) => renderMessage(msg, index)).join('');
    const typingIndicator = state.isReceiving && !isLastMessageAI() ? renderTypingIndicator() : '';

    return `
      <div class="ai-assistant ${state.isFullscreen ? 'fullscreen' : ''}">
        <div class="chat-header">
          <span class="chat-header-title">${config.title}</span>
          ${state.isLoggedIn && state.currentUser ? `
          <div class="header-user-info">
            <span class="header-username" title="${escapeHtml(state.currentUser.username)}">${escapeHtml(state.currentUser.username)}</span>
            <button class="header-logout-btn" id="ai-logout-btn" title="退出登录">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
            </button>
          </div>
          ` : `
          <button class="header-login-btn" id="ai-login-btn" title="登录/注册">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path><polyline points="10 17 15 12 10 7"></polyline><line x1="15" y1="12" x2="3" y2="12"></line></svg>
            <span>登录</span>
          </button>
          `}
          <div class="header-buttons">
            ${fullscreenBtn}
            <button class="close-btn" id="ai-close-btn">${ICONS.close}</button>
          </div>
        </div>
        
        <div class="chat-messages" id="ai-messages">
          ${renderPresetPanel()}
          ${messages}
          ${typingIndicator}
        </div>
        
        <div class="chat-input">
          <textarea 
            id="ai-input"
            placeholder="${'输入消息...（最多' + config.maxInputLength + '字）'}"
            rows="1"
            ${state.isSending ? 'disabled' : ''}
          ></textarea>
          <div class="input-controls">
            <button class="clear-all-btn ${state.isSending ? 'disabled' : ''}" id="ai-clear-all-btn" title="清除所有消息" ${state.isSending ? 'disabled' : ''}>
              ${ICONS.clearAll}
            </button>
            ${!state.isSending ? `
            <button 
              class="send-btn" 
              id="ai-send-btn"
              title="发送消息"
            >
              <span class="send-btn-text">发送</span>
              <span class="send-btn-icon">${ICONS.sendArrow}</span>
            </button>
            ` : `
            <button 
              class="stop-btn" 
              id="ai-stop-btn"
              title="中止AI输出"
            >
              ${ICONS.stop}
            </button>
            `}
          </div>
        </div>
        
        <!-- 按钮已移除，深度思考和联网搜索功能默认开启 -->
        
        ${!state.isFullscreen ? renderResizeHandles() : ''}
      </div>
      ${renderDeleteConfirm()}
    `;
  }

  // 渲染调整大小的控制点
  function renderResizeHandles() {
    return `
      <div class="resize-handle resize-n" data-direction="n"></div>
      <div class="resize-handle resize-s" data-direction="s"></div>
      <div class="resize-handle resize-e" data-direction="e"></div>
      <div class="resize-handle resize-w" data-direction="w"></div>
      <div class="resize-handle resize-ne" data-direction="ne"></div>
      <div class="resize-handle resize-nw" data-direction="nw"></div>
      <div class="resize-handle resize-se" data-direction="se"></div>
      <div class="resize-handle resize-sw" data-direction="sw"></div>
    `;
  }

  function render(skipScroll = false) {
    if (!container) return;

    // 如果需要保持滚动位置，先保存当前位置
    let savedScrollTop = 0;
    let savedTabsScrollLeft = 0; // 保存标签栏滚动位置
    let shouldRestoreScroll = false;
    let shouldRestoreTabsScroll = false;
    let shouldScrollToBottom = false;

    if (state.showChatWindow && skipScroll) {
      const messagesContainer = container.querySelector('.chat-messages');
      if (messagesContainer) {
        savedScrollTop = messagesContainer.scrollTop;
        shouldRestoreScroll = true;
      }

      // 保存标签栏滚动位置
      const tabsContainer = container.querySelector('.preset-tabs');
      if (tabsContainer) {
        savedTabsScrollLeft = tabsContainer.scrollLeft;
        shouldRestoreTabsScroll = true;
      }
    } else if (state.showChatWindow && !skipScroll) {
      // 需要滚动到底部
      shouldScrollToBottom = true;
    }

    if (state.showChatWindow) {
      // CRITICAL FIX: DOM 替换前清理孤立的 tooltip
      const orphanTooltip = document.body.querySelector('.citation-preview-tooltip');
      if (orphanTooltip) orphanTooltip.remove();

      container.innerHTML = renderChatWindow() + renderFloatingBall();

      // DOM重建后立即恢复标签栏滚动位置，不使用requestAnimationFrame
      if (shouldRestoreTabsScroll) {
        const tabsContainer = container.querySelector('.preset-tabs');
        if (tabsContainer) {
          tabsContainer.scrollLeft = savedTabsScrollLeft;
        }
      }
    } else {
      container.innerHTML = renderFloatingBall();
    }

    bindEvents();

    // Phase 6: 为渲染后的表格添加操作按钮
    requestAnimationFrame(() => {
      const tables = container.querySelectorAll('table:not([data-table-actions-added])');
      tables.forEach(addTableActions);
    });

    // 恢复窗口的位置和尺寸（必须在bindEvents之后）
    if (state.showChatWindow) {
      const assistant = container.querySelector('.ai-assistant');
      if (assistant) {
        // 临时禁用transition，避免尺寸恢复时的动画
        const originalTransition = assistant.style.transition;
        assistant.style.transition = 'none';

        if (state.isFullscreen) {
          // 全屏模式
          assistant.style.top = '20px';
          assistant.style.left = '20px';
          assistant.style.bottom = '20px';
          assistant.style.right = '20px';
          assistant.style.width = 'calc(100vw - 40px)';
          assistant.style.height = 'calc(100vh - 40px)';
        } else {
          // 非全屏模式，应用保存的位置和尺寸
          if (state.windowLeft !== null && state.windowTop !== null) {
            assistant.style.left = state.windowLeft + 'px';
            assistant.style.top = state.windowTop + 'px';
          }
          // 始终应用保存的尺寸
          assistant.style.width = state.windowWidth + 'px';
          assistant.style.height = state.windowHeight + 'px';
          assistant.style.right = 'auto';
          assistant.style.bottom = 'auto';
        }

        // 强制重绘后恢复transition
        requestAnimationFrame(() => {
          assistant.style.transition = originalTransition;
        });
      }
    }

    // 恢复悬浮球的位置（如果被拖动过）
    if (!state.showChatWindow && state.ballLeft !== null && state.ballBottom !== null) {
      const ballWrapper = container.querySelector('.floating-ball-wrapper');
      if (ballWrapper) {
        ballWrapper.style.left = state.ballLeft + 'px';
        ballWrapper.style.bottom = state.ballBottom + 'px';
        ballWrapper.style.right = 'auto';
        ballWrapper.style.top = 'auto';

        // 恢复 tooltip 的禁用状态
        if (tooltipDisabled) {
          ballWrapper.classList.add('tooltip-disabled');
          const tooltip = container.querySelector('.floating-ball-tooltip');
          if (tooltip) {
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'hidden';
          }
        }
      }
    }

    // 恢复滚动位置或滚动到底部（必须在bindEvents之后）
    // 使用 requestAnimationFrame 确保omd已完全渲染，避免闪烁
    if (shouldRestoreScroll) {
      requestAnimationFrame(() => {
        const messagesContainer = container.querySelector('.chat-messages');
        if (messagesContainer) {
          messagesContainer.scrollTop = savedScrollTop;
        }
      });
    } else if (shouldScrollToBottom) {
      // 立即滚动到底部，不等待，避免看到从顶部滚动的过程
      requestAnimationFrame(() => {
        const messagesContainer = container.querySelector('.chat-messages');
        if (messagesContainer && state.autoScrollEnabled) {
          messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
      });
    }

    // 渲染后更新标签滑块位置（仅当未恢复滚动位置时）
    if (state.showChatWindow && !shouldRestoreTabsScroll) {
      // 只有在没有恢复滚动位置的情况下才需要更新滑块
      requestAnimationFrame(() => {
        updateTabSlider(true); // skipTransition = true
        updateScrollButtons(); // 更新滚动按钮状态
      });
    } else if (state.showChatWindow && shouldRestoreTabsScroll) {
      // 如果恢复了滚动位置，只需要更新按钮状态，不更新滑块位置
      requestAnimationFrame(() => {
        updateScrollButtons(); // 更新滚动按钮状态
      });
    }
  }

  // ========== 欢迎消息 ==========
  function showWelcomeMessage() {
    const welcomeContent = `同学你好！我是南昌航空大学智能学术顾问 🎓

为了给你提供更精准的学院定制服务，请告诉我你属于哪个学院？

**可选学院：**
- 经济管理学院
- 材料科学与工程学院  
- 航空制造工程学院
- 信息工程学院
- 飞行器工程学院
- 环境与化学工程学院
- 软件学院
- 其他学院（请说明）

请直接回复学院名称即可～`;
    
    state.messages.push({
      type: 'ai',
      content: welcomeContent,
      timestamp: Date.now()
    });
    render();
    scrollToBottom();
  }

  // ========== 事件处理 ==========
  function isLastMessageAI() {
    if (state.messages.length === 0) return false;
    return state.messages[state.messages.length - 1].type === 'ai';
  }

  // 深度思考和联网搜索功能已默认开启，移除切换函数

  function toggleChatWindow() {
    // 检查是否刚刚拖动过悬浮球
    const floatingBall = container.querySelector('.floating-ball');
    if (floatingBall && floatingBall.getAttribute('data-just-dragged') === 'true') {
      return; // 如果刚拖动过，不打开窗口
    }

    const wasOpen = state.showChatWindow;
    state.showChatWindow = !state.showChatWindow;
    if (state.showChatWindow) {
      // 移动端强制全屏（不受窗口状态记忆影响）
      if (state.isMobile) {
        state.isFullscreen = true;
      }
      // 如果不是移动端，使用保存的窗口状态（已在 loadWindowState 中加载）

      // 加载输入状态
      loadInputState();

      if (config.onOpen) config.onOpen();

      // 首次打开时添加动画
      if (!wasOpen) {
        // 先渲染并立即添加opening类，避免闪烁
        render();
        // 恢复滚动位置
        loadScrollPosition();

        // 首次打开时显示欢迎消息
        if (!state.hasShownWelcome && state.messages.length === 0) {
          state.hasShownWelcome = true;
          setTimeout(() => {
            showWelcomeMessage();
          }, 300);
        }

        // 如果是全屏模式，应用全屏样式
        const assistant = container.querySelector('.ai-assistant');
        if (assistant && state.isFullscreen) {
          assistant.style.top = '20px';
          assistant.style.left = '20px';
          assistant.style.bottom = '20px';
          assistant.style.right = '20px';
          assistant.style.width = 'calc(100vw - 40px)';
          assistant.style.height = 'calc(100vh - 40px)';
        } else if (assistant && state.windowLeft !== null && state.windowTop !== null) {
          // 如果不是全屏且有保存的位置，应用保存的位置和尺寸
          assistant.style.left = state.windowLeft + 'px';
          assistant.style.top = state.windowTop + 'px';
          assistant.style.width = state.windowWidth + 'px';
          assistant.style.height = state.windowHeight + 'px';
          assistant.style.right = 'auto';
          assistant.style.bottom = 'auto';
        }

        // 使用requestAnimationFrame确保DOM已渲染
        requestAnimationFrame(() => {
          if (assistant) {
            assistant.classList.add('opening');
            // 动画完成后移除类
            setTimeout(() => {
              assistant.classList.remove('opening');
            }, 400);
          }
        });
      } else {
        render();
        // 恢复滚动位置
        loadScrollPosition();

        // 如果是全屏模式，应用全屏样式
        const assistant = container.querySelector('.ai-assistant');
        if (assistant && state.isFullscreen) {
          assistant.style.top = '20px';
          assistant.style.left = '20px';
          assistant.style.bottom = '20px';
          assistant.style.right = '20px';
          assistant.style.width = 'calc(100vw - 40px)';
          assistant.style.height = 'calc(100vh - 40px)';
        } else if (assistant && state.windowLeft !== null && state.windowTop !== null) {
          // 如果不是全屏且有保存的位置，应用保存的位置和尺寸
          assistant.style.left = state.windowLeft + 'px';
          assistant.style.top = state.windowTop + 'px';
          assistant.style.width = state.windowWidth + 'px';
          assistant.style.height = state.windowHeight + 'px';
          assistant.style.right = 'auto';
          assistant.style.bottom = 'auto';
        }
      }
    } else {
      if (config.onClose) config.onClose();
      render();
    }
  }

  function toggleFullscreen() {
    if (state.isMobile && state.isFullscreen) return;

    const assistant = container.querySelector('.ai-assistant');
    if (!assistant) return;

    // 切换前保存当前位置
    if (!state.isFullscreen) {
      // 保存当前小窗口的位置，用于退出全屏时恢复
      const rect = assistant.getBoundingClientRect();
      state.windowLeft = rect.left;
      state.windowTop = rect.top;
    }

    // 在动画开始前保存滚动百分比，用于动画结束后恢复
    const messagesContainer = container.querySelector('.chat-messages');
    if (messagesContainer) {
      const scrollableHeight = Math.max(0, messagesContainer.scrollHeight - messagesContainer.clientHeight);
      state.savedScrollPercentageBeforeResize = scrollableHeight > 0 ? messagesContainer.scrollTop / scrollableHeight : 0;
      // 同时保存当前的容器尺寸信息，以便在恢复时参考
      state.savedScrollContainerInfo = {
        clientHeight: messagesContainer.clientHeight,
        scrollHeight: messagesContainer.scrollHeight
      };
    }

    // 设置窗口正在调整大小标志
    state.isWindowResizing = true;

    state.isFullscreen = !state.isFullscreen;

    // 保存窗口状态
    saveWindowState();

    // 触发过渡动画，不要立即渲染，让CSS过渡生效
    if (assistant) {
      if (state.isFullscreen) {
        // 进入全屏：固定使用20px边距，铺满整个浏览器窗口
        assistant.classList.add('fullscreen');

        assistant.style.top = '20px';
        assistant.style.left = '20px';
        assistant.style.bottom = '20px';
        assistant.style.right = '20px';
        assistant.style.width = 'calc(100vw - 40px)';
        assistant.style.height = 'calc(100vh - 40px)';

        // 移除调整大小控制点
        const resizeHandles = assistant.querySelectorAll('.resize-handle');
        resizeHandles.forEach(handle => handle.remove());
      } else {
        assistant.classList.remove('fullscreen');
        // 退出全屏时，恢复到之前的拖动位置和调整后的尺寸
        if (state.windowLeft !== null && state.windowTop !== null) {
          // 有保存的位置，恢复到之前的位置
          assistant.style.left = state.windowLeft + 'px';
          assistant.style.top = state.windowTop + 'px';
          assistant.style.width = state.windowWidth + 'px';
          assistant.style.height = state.windowHeight + 'px';
          assistant.style.right = 'auto';
          assistant.style.bottom = 'auto';
        } else {
          // 没有保存的位置，使用CSS默认位置（右下角）
          const defaultRight = 20;
          const defaultBottom = 20;
          const defaultLeft = window.innerWidth - state.windowWidth - defaultRight;
          const defaultTop = window.innerHeight - state.windowHeight - defaultBottom;

          assistant.style.left = defaultLeft + 'px';
          assistant.style.top = defaultTop + 'px';
          assistant.style.width = state.windowWidth + 'px';
          assistant.style.height = state.windowHeight + 'px';
          assistant.style.right = 'auto';
          assistant.style.bottom = 'auto';

          // 保存这个默认位置
          state.windowLeft = defaultLeft;
          state.windowTop = defaultTop;
        }

        // 添加调整大小控制点
        const resizeHandlesHTML = renderResizeHandles();
        assistant.insertAdjacentHTML('beforeend', resizeHandlesHTML);
      }
    }

    // 动态更新全屏按钮图标和提示
    const fullscreenBtn = container.querySelector('#ai-fullscreen-btn');
    if (fullscreenBtn) {
      fullscreenBtn.innerHTML = state.isFullscreen ? ICONS.exitFullscreen : ICONS.fullscreen;
      fullscreenBtn.title = state.isFullscreen ? '退出全屏' : '全屏';
    }

    // 窗口大小改变后，需要重新计算滑块位置
    // 使用 requestAnimationFrame 等待 CSS 过渡完成后再更新
    requestAnimationFrame(() => {
      // 再等一帧，确保样式已应用
      requestAnimationFrame(() => {
        updateTabSlider(true); // skipTransition = true，瞬间调整位置
        updateScrollButtons(); // 更新滚动按钮状态

        // 重新调整输入框高度以适应新的窗口状态
        const input = container.querySelector('#ai-input');
        if (input) {
          // 短暂延时以确保DOM完全更新后再调整高度
          setTimeout(() => {
            // 强制重新计算textarea的滚动条
            adjustTextareaHeight.call(input);
            // 再次延时确保第一次计算完成后再重新计算一次
            setTimeout(() => {
              adjustTextareaHeight.call(input);
              // 第三次确保滚动条状态完全正确
              setTimeout(() => {
                adjustTextareaHeight.call(input);
              }, 100);
            }, 50);
          }, 0);
        } else {
          // 如果输入框不存在，稍后再次尝试
          setTimeout(() => {
            const input = container.querySelector('#ai-input');
            if (input) {
              adjustTextareaHeight.call(input);
            }
          }, 100);
        }

        // 重置窗口调整大小标志
        state.isWindowResizing = false;
        state.hasSavedScrollForResize = false;  // 重置保存标志

        // 使用setTimeout延迟恢复滚动位置，确保所有布局变化都已完成
        setTimeout(() => {
          // 在布局稳定后，使用保存的百分比恢复滚动位置
          if (state.savedScrollPercentageBeforeResize !== null) {
            const messagesContainer = container.querySelector('.chat-messages');
            if (messagesContainer) {
              // 设置标志表示正在恢复滚动位置
              state.isRestoringScrollPosition = true;

              const currentScrollableHeight = Math.max(0, messagesContainer.scrollHeight - messagesContainer.clientHeight);
              const targetScrollTop = Math.max(0, Math.min(
                currentScrollableHeight * state.savedScrollPercentageBeforeResize,
                currentScrollableHeight
              ));

              messagesContainer.scrollTop = targetScrollTop;

              // 重置保存的百分比
              state.savedScrollPercentageBeforeResize = null;
              state.savedScrollContainerInfo = null; // 清除保存的容器信息

              // 延迟重置恢复标志，确保滚动位置稳定
              setTimeout(() => {
                state.isRestoringScrollPosition = false;
              }, 300); // 额外的300ms确保滚动位置稳定
            }
          }

          // 确保重置忽略标志，以便后续用户滚动正常工作
          state.ignoreNextScrollEvent = false;
        }, 200); // 200ms 等待布局完全稳定
      });
    });
  }

  // Phase 5: 来源卡片折叠/展开（事件委托）
  function toggleSourceCards(headerEl) {
    const listEl = headerEl.nextElementSibling;
    const toggleIcon = headerEl.querySelector('.source-cards-toggle');
    if (!listEl || !toggleIcon) return;

    const isCollapsed = listEl.classList.contains('collapsed');
    if (isCollapsed) {
      listEl.classList.remove('collapsed');
      listEl.classList.add('expanded');
      toggleIcon.textContent = '▲';
    } else {
      listEl.classList.add('collapsed');
      listEl.classList.remove('expanded');
      toggleIcon.textContent = '▼';
    }
  }

  function closeChatWindow() {
    // 关闭窗口时保存当前的窗口状态和滚动位置
    saveWindowState();
    saveScrollPosition();

    // 添加关闭动画
    const assistant = container.querySelector('.ai-assistant');
    if (assistant) {
      assistant.classList.add('closing');
      // 等待动画完成后再关闭
      setTimeout(() => {
        state.showChatWindow = false;
        // 注意：不再重置 isFullscreen，保持用户的选择
        if (config.onClose) config.onClose();
        render();
      }, 350); // 与动画时间一致
    } else {
      state.showChatWindow = false;
      // 注意：不再重置 isFullscreen，保持用户的选择
      if (config.onClose) config.onClose();
      render();
    }
  }

  function selectPresetQuestion(question) {
    const input = container.querySelector('#ai-input');
    if (input) {
      input.value = question;
      sendMessage();
    }
  }

  function switchPresetTab(tabIndex) {
    if (state.activePresetTab === tabIndex) return; // 已经是当前标签页，不再切换

    const questionsContainer = container.querySelector('.preset-questions');
    const targetTab = container.querySelector(`.preset-tab[data-tab-index="${tabIndex}"]`);

    if (!questionsContainer || !targetTab) {
      // 如果没有找到容器，直接渲染
      state.activePresetTab = tabIndex;
      render(true);
      return;
    }

    // 立即开始滑动到目标位置（带动画，550ms）
    // 这会自动处理滚动位置
    updateTabSliderToTarget(targetTab);

    // 添加淡出动画
    questionsContainer.classList.add('fade-out');

    // 等待淡出动画完成后再切换内容
    setTimeout(() => {
      // **不要取消滑块动画**，让它继续运行到完成
      // 这样用户能看到完整的滑块动画（550ms）

      // 保存当前滚动位置
      const tabsContainer = container.querySelector('.preset-tabs');
      const scrollLeftBeforeRender = tabsContainer ? tabsContainer.scrollLeft : 0;

      // 等待滚动完全结束（移动端的smooth滚动可能需要更长时间）
      setTimeout(() => {
        // 再次读取最终的滚动位置
        const finalScrollLeft = tabsContainer ? tabsContainer.scrollLeft : scrollLeftBeforeRender;

        // 保存输入框的当前值
        const input = container.querySelector('#ai-input');
        const inputValue = input ? input.value : '';

        state.activePresetTab = tabIndex;
        render(true); // 不滚动到底部

        // 恢复输入框的值
        const restoredInput = container.querySelector('#ai-input');
        if (restoredInput) {
          restoredInput.value = inputValue;

          // 重新调整输入框高度和滚动条状态
          adjustTextareaHeight.call(restoredInput);

          // 确保输入框的滚动条位置正确
          if (inputValue) {
            // 如果有内容，确保滚动到最底部
            setTimeout(() => {
              restoredInput.scrollTop = restoredInput.scrollHeight;
            }, 0);
          }

          // 在恢复输入框值后，更新发送按钮状态
          updateSendButtonState();
        }

        // 渲染后立即恢复滚动位置，防止浏览器自动滚动
        const tabsContainerAfterRender = container.querySelector('.preset-tabs');
        if (tabsContainerAfterRender) {
          // 立即直接赋值恢复，不使用requestAnimationFrame
          tabsContainerAfterRender.scrollLeft = finalScrollLeft;
        }

        // DOM重建后，直接设置滑块到目标位置（不需要动画）
        // 因为用户已经看过了完整的滑块动画（550ms）
        const newTargetTab = container.querySelector(`.preset-tab[data-tab-index="${tabIndex}"]`);
        if (newTargetTab) {
          const slider = container.querySelector('#ai-tabs-slider');
          const underline = container.querySelector('#ai-tabs-underline');

          if (slider && tabsContainerAfterRender) {
            // 计算目标位置
            const containerRect = tabsContainerAfterRender.getBoundingClientRect();
            const tabRect = newTargetTab.getBoundingClientRect();
            const targetX = tabRect.left - containerRect.left + tabsContainerAfterRender.scrollLeft;
            const targetWidth = tabRect.width;

            // 立即设置到目标位置，不显示过渡动画
            slider.style.transition = 'none';
            slider.style.transform = `translateX(${targetX}px)`;
            slider.style.width = `${targetWidth}px`;

            if (underline) {
              underline.style.transition = 'none';
              underline.style.transform = `translateX(${targetX}px)`;
              underline.style.width = `${targetWidth}px`;
            }

            // 强制重绘后恢复过渡
            requestAnimationFrame(() => {
              slider.style.transition = '';
              if (underline) {
                underline.style.transition = '';
              }
            });
          }
        }

        const newQuestionsContainer = container.querySelector('.preset-questions');
        if (newQuestionsContainer) {
          newQuestionsContainer.classList.add('fade-in');
          // 动画完成后移除类
          setTimeout(() => {
            newQuestionsContainer.classList.remove('fade-in');
          }, 300);
        }
      }, 100); // 等待滚动完成
    }, 250); // 与 fade-out 动画时间一致
  }

  // 更新滑块到目标标签位置（精确同步550ms，自然缓动）
  function updateTabSliderToTarget(targetTab) {
    const slider = container.querySelector('#ai-tabs-slider');
    const underline = container.querySelector('#ai-tabs-underline');
    if (!slider || !targetTab) return;

    const tabsContainer = container.querySelector('.preset-tabs');
    if (!tabsContainer) return;

    // 智能滚动：让目标标签在可视区域居中显示
    const containerRect = tabsContainer.getBoundingClientRect();
    const tabRect = targetTab.getBoundingClientRect();

    // 计算目标标签相对于容器的位置
    const tabRelativeLeft = tabRect.left - containerRect.left;
    const tabRelativeRight = tabRect.right - containerRect.left;

    // 判断标签是否完全可见
    const isFullyVisible = tabRelativeLeft >= 0 && tabRelativeRight <= containerRect.width;

    if (!isFullyVisible) {
      // 标签不完全可见，需要滚动
      // 计算让标签居中的滚动位置
      const targetScrollLeft = tabsContainer.scrollLeft + tabRelativeLeft - (containerRect.width - tabRect.width) / 2;

      // 平滑滚动到目标位置
      tabsContainer.scrollTo({
        left: Math.max(0, targetScrollLeft), // 不能小于0
        behavior: 'smooth'
      });

      // 等待滚动完成后再开始滑块动画
      setTimeout(() => {
        startSliderAnimation();
      }, 300); // 滚动动画大约300ms
    } else {
      // 标签已经可见，直接开始滑块动画
      startSliderAnimation();
    }

    // 滑块动画函数
    function startSliderAnimation() {
      // 获取当前滑块的位置和宽度（起点）
      const currentTransform = slider.style.transform || 'translateX(0px)';
      const currentX = parseFloat(currentTransform.match(/translateX\(([^)]+)px\)/)?.[1] || 0);
      const currentWidth = parseFloat(slider.style.width || 0);

      // 重新获取位置（因为可能已经滚动）
      const containerRectNow = tabsContainer.getBoundingClientRect();
      const tabRectNow = targetTab.getBoundingClientRect();
      const targetX = tabRectNow.left - containerRectNow.left + tabsContainer.scrollLeft;
      const targetWidth = tabRectNow.width;

      // 计算移动的增量（保留方向）
      const deltaX = targetX - currentX;
      const deltaWidth = targetWidth - currentWidth;

      // 固定总时长：250ms淡出 + 300ms淡入 = 550ms
      const TOTAL_DURATION = 550;
      const startTime = performance.now();

      // 使用三次方缓动函数：easeInOutCubic
      function easeInOutCubic(t) {
        return t < 0.5
          ? 4 * t * t * t
          : 1 - Math.pow(-2 * t + 2, 3) / 2;
      }

      // 取消之前的动画
      if (state.sliderAnimationId) {
        cancelAnimationFrame(state.sliderAnimationId);
      }

      // 动画主循环
      function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / TOTAL_DURATION, 1);
        const eased = easeInOutCubic(progress);

        const newX = currentX + deltaX * eased;
        const newWidth = currentWidth + deltaWidth * eased;

        slider.style.transform = `translateX(${newX}px)`;
        slider.style.width = `${newWidth}px`;

        if (underline) {
          underline.style.transform = `translateX(${newX}px)`;
          underline.style.width = `${newWidth}px`;
        }

        if (progress < 1) {
          state.sliderAnimationId = requestAnimationFrame(animate);
        } else {
          // 动画完成
          slider.style.transform = `translateX(${targetX}px)`;
          slider.style.width = `${targetWidth}px`;

          if (underline) {
            underline.style.transform = `translateX(${targetX}px)`;
            underline.style.width = `${targetWidth}px`;
          }

          state.sliderAnimationId = null;
        }
      }

      // 启动动画
      state.sliderAnimationId = requestAnimationFrame(animate);
    }
  }

  // 更新标签滑块位置（到当前激活标签）
  function updateTabSlider(skipTransition = false) {
    const slider = container.querySelector('#ai-tabs-slider');
    const underline = container.querySelector('#ai-tabs-underline');
    const activeTab = container.querySelector('.preset-tab.active');

    if (!slider || !activeTab) return;

    const tabsContainer = container.querySelector('.preset-tabs');
    if (!tabsContainer) return;

    // 获取激活标签的位置和宽度
    const containerRect = tabsContainer.getBoundingClientRect();
    const tabRect = activeTab.getBoundingClientRect();

    const offsetLeft = tabRect.left - containerRect.left + tabsContainer.scrollLeft;
    const width = tabRect.width;

    // 如果需要跳过过渡动画（用于初始化或渲染后的位置校准）
    if (skipTransition) {
      // 暂时禁用过渡
      slider.style.transition = 'none';
      slider.style.transform = `translateX(${offsetLeft}px)`;
      slider.style.width = `${width}px`;

      if (underline) {
        underline.style.transition = 'none';
        underline.style.transform = `translateX(${offsetLeft}px)`;
        underline.style.width = `${width}px`;
      }

      // 强制重绘后恢复过渡
      requestAnimationFrame(() => {
        slider.style.transition = '';
        if (underline) {
          underline.style.transition = '';
        }
      });
    } else {
      // 正常设置位置（带过渡动画）
      slider.style.transform = `translateX(${offsetLeft}px)`;
      slider.style.width = `${width}px`;

      if (underline) {
        underline.style.transform = `translateX(${offsetLeft}px)`;
        underline.style.width = `${width}px`;
      }
    }
  }

  // 标签栏左滚动
  function scrollTabsLeft() {
    const tabsContainer = container.querySelector('.preset-tabs');
    if (!tabsContainer) return;

    const scrollAmount = 200; // 每次滚动200px
    tabsContainer.scrollBy({
      left: -scrollAmount,
      behavior: 'smooth'
    });
  }

  // 标签栏右滚动
  function scrollTabsRight() {
    const tabsContainer = container.querySelector('.preset-tabs');
    if (!tabsContainer) return;

    const scrollAmount = 200; // 每次滚动200px
    tabsContainer.scrollBy({
      left: scrollAmount,
      behavior: 'smooth'
    });
  }

  // 更新滚动按钮状态
  function updateScrollButtons() {
    const tabsContainer = container.querySelector('.preset-tabs');
    const leftBtn = container.querySelector('#ai-tab-nav-left');
    const rightBtn = container.querySelector('#ai-tab-nav-right');

    if (!tabsContainer || !leftBtn || !rightBtn) return;

    // 检查内容是否溢出（使用容差值避免浮点数精度问题）
    const scrollWidth = tabsContainer.scrollWidth;
    const clientWidth = tabsContainer.clientWidth;
    const scrollLeft = tabsContainer.scrollLeft;
    const tolerance = 5; // 容差值，避免浮点数精度问题

    // 内容是否真的溢出
    const hasOverflow = scrollWidth > clientWidth + tolerance;

    // 检查是否可以向左滚动
    const canScrollLeft = hasOverflow && scrollLeft > tolerance;
    // 检查是否可以向右滚动
    const canScrollRight = hasOverflow && scrollLeft < (scrollWidth - clientWidth - tolerance);

    // 更新按钮可见性
    if (canScrollLeft) {
      leftBtn.classList.add('visible');
    } else {
      leftBtn.classList.remove('visible');
    }

    if (canScrollRight) {
      rightBtn.classList.add('visible');
    } else {
      rightBtn.classList.remove('visible');
    }
  }

  function copyMessage(content, index) {
    // 直接使用兼容性最好的 execCommand 方案
    const textArea = document.createElement('textarea');
    textArea.value = content;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '0';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);

      if (successful) {
        state.messages[index].copied = true;

        // 只更新按钮图标，不重新渲染整个页面
        const copyBtn = container.querySelector(`.copy-btn[data-index="${index}"]`);
        if (copyBtn) {
          copyBtn.innerHTML = ICONS.copied;
        }

        setTimeout(() => {
          state.messages[index].copied = false;
          const copyBtn = container.querySelector(`.copy-btn[data-index="${index}"]`);
          if (copyBtn) {
            copyBtn.innerHTML = ICONS.copy;
          }
        }, 2000);
      } else {
        console.error('复制失败');
        alert('复制失败，请手动选择复制。');
      }
    } catch (err) {
      if (textArea.parentNode) {
        document.body.removeChild(textArea);
      }
      console.error('复制失败:', err);
      alert('复制失败，请手动选择复制。');
    }
  }

  // Phase 6: 重新生成消息
  function regenerateMessage(index) {
    if (state.isSending || state.isReceiving) return;

    // 检查是否有后续消息，如果有则提示用户
    const msgsAfterRegen = state.messages.length - index;
    if (msgsAfterRegen > 1) {
      if (!confirm('重新生成将删除此消息之后的所有内容，确定继续？')) {
        return;
      }
    }

    // 找到该消息之前最近的一条用户消息
    let userIndex = index;
    while (userIndex >= 0 && state.messages[userIndex].type !== 'user') {
      userIndex--;
    }
    if (userIndex < 0) return;

    const userMessage = state.messages[userIndex];

    // 删除从该 AI 消息之后的所有消息
    state.messages.splice(index, state.messages.length - index);

    // 重新发送用户消息
    state.messages.push({ type: 'user', content: userMessage.content, timestamp: new Date() });
    state.messages.push({
      type: 'ai',
      content: '',
      timestamp: new Date(),
      isTyping: true,
      searchKeywords: null,
      searchResultCount: 0,
      searchResults: [],
      citationUrls: {},
      feedback: null
    });
    sendMessageToAPI();
    render();
  }

  // Phase 6: 表格操作（复制/下载 CSV）
  function addTableActions(table) {
    if (table.dataset.tableActionsAdded) return;
    table.dataset.tableActionsAdded = 'true';

    // 创建操作按钮容器
    const wrapper = document.createElement('div');
    wrapper.className = 'table-actions-wrapper';
    wrapper.style.cssText = 'position:relative;';

    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);

    const btnContainer = document.createElement('div');
    btnContainer.className = 'table-action-buttons';
    btnContainer.innerHTML = `
      <button class="table-action-btn" title="复制表格" data-action="copy-table">
        ${ICONS.copy}
      </button>
      <button class="table-action-btn" title="下载 CSV" data-action="download-csv">
        ${ICONS.share}
      </button>`;
    btnContainer.style.cssText = 'position:absolute;top:4px;right:4px;display:flex;gap:4px;z-index:10;';
    wrapper.appendChild(btnContainer);

    btnContainer.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-action]');
      if (!btn) return;
      const action = btn.getAttribute('data-action');
      if (action === 'copy-table') {
        const csv = tableToCSV(table);
        navigator.clipboard.writeText(csv).then(() => {
          btn.textContent = '✓';
          setTimeout(() => { btn.innerHTML = ICONS.copy; }, 1500);
        }).catch(() => {
          // Fallback
          const ta = document.createElement('textarea');
          ta.value = csv;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
        });
      } else if (action === 'download-csv') {
        const csv = tableToCSV(table);
        const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'table_' + Date.now() + '.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    });
  }

  // 表格转 CSV
  function tableToCSV(table) {
    const rows = table.querySelectorAll('tr');
    return Array.from(rows).map(row => {
      const cells = row.querySelectorAll('th, td');
      return Array.from(cells).map(cell => {
        let text = cell.textContent.trim();
        // 如果包含逗号、引号或换行，用双引号包裹
        if (text.includes(',') || text.includes('"') || text.includes('\n') || text.includes('\r')) {
          text = '"' + text.replace(/"/g, '""') + '"';
        }
        return text;
      }).join(',');
    }).join('\n');
  }

  // Phase 6: 分享消息（复制为文本）
  function shareMessage(index) {
    const message = state.messages[index];
    if (!message || message.type !== 'ai') return;

    const shareText = message.content;
    const textArea = document.createElement('textarea');
    textArea.value = shareText;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      document.body.removeChild(textArea);
      // 短暂显示"已复制"反馈
      const shareBtn = container.querySelector(`.share-btn[data-index="${index}"]`);
      if (shareBtn) {
        const original = shareBtn.innerHTML;
        shareBtn.innerHTML = ICONS.copied;
        shareBtn.classList.add('copied');
        setTimeout(() => {
          shareBtn.innerHTML = original;
          shareBtn.classList.remove('copied');
        }, 1500);
      }
    } catch (err) {
      document.body.removeChild(textArea);
      console.error('分享失败:', err);
    }
  }

  // Phase 6: 设置反馈
  function setFeedback(index, type) {
    if (!state.feedback) state.feedback = {};
    const isActive = state.feedback[index] === type;
    // 切换：已选中则取消，否则选中
    if (isActive) {
      delete state.feedback[index];
    } else {
      state.feedback[index] = type;
    }
    // 同步到消息对象
    if (state.messages[index]) {
      state.messages[index].feedback = state.feedback[index] || null;
    }
    // 只更新反馈按钮状态
    const likeBtn = container.querySelector(`.feedback-like[data-index="${index}"]`);
    const dislikeBtn = container.querySelector(`.feedback-dislike[data-index="${index}"]`);

    if (likeBtn) {
      likeBtn.classList.toggle('active', state.feedback[index] === 'like');
    }
    if (dislikeBtn) {
      dislikeBtn.classList.toggle('active', state.feedback[index] === 'dislike');
    }
  }

  function confirmDeleteMessage(index) {
    const message = state.messages[index];
    const messageType = message.type === 'user' ? '用户消息' : message.type === 'ai' ? 'AI回复' : '消息';
    const contentPreview = escapeHtml(message.content.length > 50
      ? message.content.substring(0, 50) + '...'
      : message.content);

    state.deleteConfirmData = {
      messageType: messageType,
      contentPreview: contentPreview,
      index: index
    };
    state.showDeleteConfirm = true;

    // 不重新渲染整个页面，只插入弹窗
    showDeleteConfirmDialog();
  }

  function cancelDelete() {
    state.showDeleteConfirm = false;
    state.deleteConfirmData = {
      messageType: '',
      contentPreview: '',
      index: -1
    };

    // 不重新渲染整个页面，只移除弹窗
    hideDeleteConfirmDialog();
  }

  function executeDelete() {
    const index = state.deleteConfirmData.index;
    if (index !== -1) {
      state.messages.splice(index, 1);

      if (state.hasHistoryMessages && index < state.historyMessageCount) {
        state.historyMessageCount--;
        if (state.historyMessageCount === 0) {
          state.hasHistoryMessages = false;
        }
      }

      saveMessagesToSession();
    }

    // 先隐藏弹窗
    state.showDeleteConfirm = false;
    state.deleteConfirmData = {
      messageType: '',
      contentPreview: '',
      index: -1
    };
    hideDeleteConfirmDialog();

    // 删除后需要重新渲染消息列表，但保持当前滚动位置
    render(true); // skipScroll = true
  }

  // 确认清除所有消息
  function confirmClearAllMessages() {
    // AI思考或回复时禁止清除
    if (state.isSending) {
      return;
    }

    // 检查是否有消息
    if (state.messages.length === 0) {
      // 没有消息时显示提示弹窗
      showNoMessagesDialog();
      return;
    }

    state.clearAllConfirmData = {
      messageCount: state.messages.length
    };
    state.showClearAllConfirm = true;

    // 不重新渲染整个页面，只插入弹窗
    showClearAllConfirmDialog();
  }

  // 取消清除所有消息
  function cancelClearAll() {
    state.showClearAllConfirm = false;
    state.clearAllConfirmData = {
      messageCount: 0
    };

    // 不重新渲染整个页面，只移除弹窗
    hideClearAllConfirmDialog();
  }

  // 执行清除所有消息
  function executeClearAll() {
    // 清除所有消息
    state.messages = [];
    state.hasHistoryMessages = false;
    state.historyMessageCount = 0;

    // 保存到sessionStorage
    saveMessagesToSession();

    // 先隐藏弹窗
    state.showClearAllConfirm = false;
    state.clearAllConfirmData = {
      messageCount: 0
    };
    hideClearAllConfirmDialog();

    // 清除后重新渲染，显示预设问题面板
    render();

    // 清空输入框并更新按钮状态
    const input = container.querySelector('#ai-input');
    if (input) {
      input.value = '';
      updateSendButtonState();
    }
  }

  // 显示清除所有消息确认弹窗
  function showClearAllConfirmDialog() {
    // 移除已存在的弹窗
    hideClearAllConfirmDialog();

    // 创建弹窗HTML
    const dialogHtml = `
      <div class="confirm-overlay" id="ai-clear-all-overlay">
        <div class="confirm-dialog">
          <div class="confirm-header">
            ${ICONS.warning}
            <h3>确认清除</h3>
          </div>
          <div class="confirm-body">
            <p class="message-type">清除所有消息</p>
            <div class="content-preview">
              <p>将清除所有 <strong>${state.clearAllConfirmData.messageCount}</strong> 条消息（包括用户消息和AI回复）</p>
            </div>
            <p class="warning-text">此操作不可撤销，确定要清除所有消息吗？</p>
          </div>
          <div class="confirm-footer">
            <button class="btn-cancel" id="ai-cancel-clear-all">取消</button>
            <button class="btn-confirm" id="ai-confirm-clear-all">确定清除</button>
          </div>
        </div>
      </div>
    `;

    // 插入弹窗到容器
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = dialogHtml;
    const overlay = tempDiv.firstElementChild;
    container.appendChild(overlay);

    // 绑定弹窗事件
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) cancelClearAll();
    });

    const cancelBtn = overlay.querySelector('#ai-cancel-clear-all');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', cancelClearAll);
    }

    const confirmBtn = overlay.querySelector('#ai-confirm-clear-all');
    if (confirmBtn) {
      confirmBtn.addEventListener('click', executeClearAll);
    }
  }

  // 隐藏清除所有消息确认弹窗
  function hideClearAllConfirmDialog() {
    const overlay = container.querySelector('#ai-clear-all-overlay');
    if (overlay) {
      overlay.remove();
    }
  }

  // 显示"没有消息"提示弹窗
  function showNoMessagesDialog() {
    // 移除已存在的弹窗
    hideNoMessagesDialog();

    // 创建弹窗HTML
    const dialogHtml = `
      <div class="confirm-overlay" id="ai-no-messages-overlay">
        <div class="confirm-dialog">
          <div class="confirm-header" style="border-bottom: 2px solid #90CAF9;">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2196F3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="info-icon">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
            <h3 style="color: #2196F3;">提示</h3>
          </div>
          <div class="confirm-body">
            <p class="message-type" style="color: #2196F3;">当前没有消息</p>
            <div class="content-preview" style="background: #E3F2FD; border-left-color: #2196F3;">
              <p style="color: #1976D2;">对话列表为空，没有需要清除的消息。</p>
            </div>
          </div>
          <div class="confirm-footer">
            <button class="btn-confirm" id="ai-no-messages-ok" style="background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); width: 100%;">知道了</button>
          </div>
        </div>
      </div>
    `;

    // 插入弹窗到容器
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = dialogHtml;
    const overlay = tempDiv.firstElementChild;
    container.appendChild(overlay);

    // 绑定弹窗事件
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) hideNoMessagesDialog();
    });

    const okBtn = overlay.querySelector('#ai-no-messages-ok');
    if (okBtn) {
      okBtn.addEventListener('click', hideNoMessagesDialog);
    }
  }

  // 隐藏"没有消息"提示弹窗
  function hideNoMessagesDialog() {
    const overlay = container.querySelector('#ai-no-messages-overlay');
    if (overlay) {
      overlay.remove();
    }
  }

  // 显示删除确认弹窗（不重新渲染整个页面）
  function showDeleteConfirmDialog() {
    // 移除已存在的弹窗
    hideDeleteConfirmDialog();

    // 创建弹窗HTML
    const dialogHtml = `
      <div class="confirm-overlay" id="ai-confirm-overlay">
        <div class="confirm-dialog">
          <div class="confirm-header">
            ${ICONS.warning}
            <h3>确认删除</h3>
          </div>
          <div class="confirm-body">
            <p class="message-type">${state.deleteConfirmData.messageType}</p>
            <div class="content-preview">
              <p>${state.deleteConfirmData.contentPreview}</p>
            </div>
            <p class="warning-text">此操作不可撤销，确定要删除吗？</p>
          </div>
          <div class="confirm-footer">
            <button class="btn-cancel" id="ai-cancel-delete">取消</button>
            <button class="btn-confirm" id="ai-confirm-delete">确定删除</button>
          </div>
        </div>
      </div>
    `;

    // 插入弹窗到容器
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = dialogHtml;
    const overlay = tempDiv.firstElementChild;
    container.appendChild(overlay);

    // 绑定弹窗事件
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) cancelDelete();
    });

    const cancelBtn = overlay.querySelector('#ai-cancel-delete');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', cancelDelete);
    }

    const confirmBtn = overlay.querySelector('#ai-confirm-delete');
    if (confirmBtn) {
      confirmBtn.addEventListener('click', executeDelete);
    }
  }

  // 隐藏删除确认弹窗
  function hideDeleteConfirmDialog() {
    const overlay = container.querySelector('#ai-confirm-overlay');
    if (overlay) {
      overlay.remove();
    }
  }

  // 显示关闭AI助手确认弹窗
  function showCloseConfirm() {
    state.showCloseConfirm = true;
    render();
  }

  // 取消关闭AI助手
  function cancelCloseConfirm() {
    state.showCloseConfirm = false;
    render();
  }

  // 执行关闭AI助手
  function executeCloseWidget() {
    // 移除插件DOM
    if (container && container.parentNode) {
      container.parentNode.removeChild(container);
    }
    // 清空container引用
    container = null;
  }

  // 中止AI输出
  function stopAIOutput() {
    // 清除超时定时器
    if (state.currentTimeoutId) {
      clearTimeout(state.currentTimeoutId);
      state.currentTimeoutId = null;
    }

    if (state.currentAbortController) {
      state.currentAbortController.abort();
      state.currentAbortController = null;
    }

    // 重置状态
    state.isSending = false;
    state.isReceiving = false;

    // 如果有未完成的AI消息，添加中断标记
    if (state.messages.length > 0) {
      const lastMessage = state.messages[state.messages.length - 1];
      if (lastMessage.type === 'ai') {
        // 停止打字动画
        if (lastMessage.isTyping) {
          lastMessage.isTyping = false;
          // 将待处理内容添加到主内容
          if (lastMessage.pendingContent) {
            lastMessage.content += lastMessage.pendingContent;
            lastMessage.pendingContent = '';
          }
        }
        // 添加中断提示
        if (!lastMessage.content.includes('[用户中止]')) {
          lastMessage.content += '\n\n🚫 **<span style = "color: red; font-size: 20px">用户中止输出</span>**';
        }
      }
    }

    // 保存消息
    saveMessagesToSession();
    render();

    // 中止后自动将对话窗口滚动到底部
    setTimeout(() => {
      const messagesContainer = container.querySelector('.chat-messages');
      if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    }, 0);
  }

  // 重新发送消息
  async function resendMessage(index) {
    // 未登录拦截
    if (!state.isLoggedIn) {
      state.messages.push({
        type: 'error',
        content: '请先登录后再使用 AI 助手。',
        timestamp: new Date()
      });
      render();
      return;
    }

    const message = state.messages[index];
    if (message.type !== 'user' || state.isSending) return;

    // 获取消息内容，移除附件提示
    let content = message.content;
    // 移除 "（附带文件：...）" 部分
    content = content.replace(/（附带文件：[^）]+）$/, '').trim();

    // 删除当前消息及之后的所有消息
    state.messages.splice(index);

    // 更新历史消息计数
    if (state.hasHistoryMessages && index < state.historyMessageCount) {
      state.historyMessageCount = index;
      if (state.historyMessageCount === 0) {
        state.hasHistoryMessages = false;
      }
    }

    // 添加用户消息
    const userMessage = {
      type: 'user',
      content: content,
      timestamp: new Date()
    };
    state.messages.push(userMessage);
    saveMessagesToSession();

    // 重新发送消息时，重新启用自动滚动
    state.autoScrollEnabled = true;

    // 只渲染一次，render内部已处理滚动
    state.isSending = true;
    state.isReceiving = true;
    render();

    // 发送消息
    try {
      await callRagflowAPI(content);
    } catch (error) {
      // 忽略主动中止导致的错误
      if (error.name !== 'AbortError') {
        console.error('重新发送失败:', error);
      }
    } finally {
      state.isSending = false;
      state.isReceiving = false;
      saveMessagesToSession();

      // 如果自动滚动被禁用，保持当前滚动位置
      if (!state.autoScrollEnabled) {
        render(true); // skipScroll = true
      } else {
        render();
        scrollToBottom();
      }
    }
  }

  function adjustTextareaHeight() {
    const textarea = container.querySelector('#ai-input');
    if (textarea) {
      // 保存当前滚动位置
      const currentScrollTop = textarea.scrollTop;

      // 重置高度以获取正确的scrollHeight
      textarea.style.height = 'auto';
      const scrollHeight = textarea.scrollHeight;

      // 根据实际内容高度和窗口状态调整高度
      const maxHeight = state.isFullscreen ? 200 : 150;
      const newHeight = Math.min(Math.max(scrollHeight, 40), maxHeight);
      textarea.style.height = newHeight + 'px';

      // 精确检测溢出：创建一个镜像元素来真实模拟文本渲染
      const computedStyle = window.getComputedStyle(textarea);
      const mirror = document.createElement('div');

      // 设置镜像元素样式，精确复制textarea
      Object.assign(mirror.style, {
        position: 'absolute',
        top: '-9999px',
        left: '-9999px',
        width: computedStyle.width,
        height: newHeight + 'px',
        padding: computedStyle.padding,
        margin: computedStyle.margin,
        border: computedStyle.border,
        fontSize: computedStyle.fontSize,
        fontFamily: computedStyle.fontFamily,
        lineHeight: computedStyle.lineHeight,
        whiteSpace: computedStyle.whiteSpace,
        wordWrap: computedStyle.wordWrap,
        wordBreak: computedStyle.wordBreak,
        overflow: 'hidden',
        boxSizing: 'border-box',
        visibility: 'hidden'
      });

      // 复制内容并添加到DOM进行测量
      mirror.textContent = textarea.value || ' ';
      document.body.appendChild(mirror);

      // 检测是否溢出：内容高度是否超过容器高度
      const contentHeight = mirror.scrollHeight;
      const containerHeight = mirror.clientHeight;
      const needsScrollbar = contentHeight > containerHeight;

      // 清理镜像元素
      document.body.removeChild(mirror);

      // 设置滚动条
      textarea.style.setProperty('overflow-y', needsScrollbar ? 'auto' : 'hidden', 'important');

      // 恢复之前的滚动位置
      textarea.scrollTop = currentScrollTop;

      // 确保滚动条状态正确应用
      if (needsScrollbar) {
        // 强制浏览器重新计算滚动条
        textarea.scrollTop = currentScrollTop;
      }
    }
  }

  // ========== 实时流式显示（无延迟） ==========
  function typeText(messageIndex, textToAdd) {
    const message = state.messages[messageIndex];
    if (!message) {
      console.error('[找不到消息]', messageIndex, state.messages.length);
      return;
    }

    // 直接追加内容，立即显示，无动画延迟
    message.content += textToAdd;
    
    // 直接更新DOM
    updateMessageDisplay(messageIndex);
    scrollToBottom();
  }

  // 更新指定消息的显示（流式过程中实时渲染引用链接）
  // isFinal: true 时执行完整来源区块处理（仅流结束后调用一次）
  function updateMessageDisplay(messageIndex, isFinal = false) {

    const messagesContainer = container.querySelector('#ai-messages');
    if (!messagesContainer) {

      return;
    }

    const allMessages = messagesContainer.querySelectorAll('.message');
    let actualIndex = 0;

    for (let i = 0; i < allMessages.length; i++) {
      const msgEl = allMessages[i];
      if (msgEl.classList.contains('ai') || msgEl.classList.contains('user') || msgEl.classList.contains('error')) {
        if (actualIndex === messageIndex) {
          const contentEl = msgEl.querySelector('.message-content');
          if (contentEl) {
            const message = state.messages[messageIndex];
            if (!message) return;

            // 获取完整内容（包括pendingContent）
            const fullContent = message.content + (message.pendingContent || '');

            // AI 消息：引用提取（流式期间节流，最终渲染立即执行）
            if (message.type === 'ai') {
              if (isFinal || !message._lastCitationExtract || Date.now() - message._lastCitationExtract > 300) {
                const contentCitations = extractCitationUrlsFromContent(fullContent);
                // 仅添加新发现的、有有效 URL 的引用，不覆盖已有的完整条目
                for (const [key, val] of Object.entries(contentCitations)) {
                  const existingVal = (message.citationUrls || {})[key];
                  const valUrl = typeof val === 'string' ? val : val?.url;
                  if (!valUrl) continue; // 跳过无效条目
                  if (existingVal) {
                    const existingUrl = typeof existingVal === 'string' ? existingVal : existingVal?.url;
                    if (existingUrl) continue; // 已有完整条目，不覆盖
                  }
                  if (!message.citationUrls) message.citationUrls = {};
                  message.citationUrls[key] = val;
                }
                message._lastCitationExtract = Date.now();
              }
            }

            // 对 AI 消息预处理：自动链接化纯文本 URL
            const processedContent = message.type === 'ai' ? linkifyText(fullContent) : fullContent;

            // 使用兼容模式：支持marked.parse()和marked()
            let htmlContent;
            try {
              htmlContent = message.type === 'ai'
                ? (marked.parse ? marked.parse(processedContent) : marked(processedContent))
                : processedContent.replace(/\n/g, '<br>');
            } catch (e) {
              // marked解析失败时显示纯文本
              htmlContent = processedContent.replace(/\n/g, '<br>');
            }

            // AI 消息：实时转换引用链接（流式期间就渲染可点击链接）
            if (message.type === 'ai' && htmlContent) {
              htmlContent = convertCitationsToLinks(htmlContent, message.citationUrls || {});

              // 来源区块格式化：流式期间节流（每300ms），最终渲染时立即执行
              if (isFinal || !message._lastSourceUpdate || Date.now() - message._lastSourceUpdate > 300) {
                htmlContent = processSourceSection(htmlContent, message.citationUrls || {});
                message._lastSourceUpdate = Date.now();
              }
            }

            // 最终渲染时清理节流标记
            if (isFinal) {
              delete message._lastCitationExtract;
              delete message._lastSourceUpdate;
            }

            // 直接更新DOM
            contentEl.innerHTML = htmlContent;
          }
          break;
        }
        actualIndex++;
      }
    }
  }

  // 将内容分段渲染，添加动画类
  function renderSegmentedContent(htmlContent) {
    // 按段落分割（h1-h4标题、段落、列表等）
    const segments = htmlContent.split(/(<h[1-4][^>]*>.*?<\/h[1-4]>|<p[^>]*>.*?<\/p>|<ul[^>]*>.*?<\/ul>|<ol[^>]*>.*?<\/ol>|<pre[^>]*>.*?<\/pre>|<blockquote[^>]*>.*?<\/blockquote>|<table[^>]*>.*?<\/table>)/s);
    
    let result = '';
    let segmentIndex = 0;
    
    segments.forEach((segment) => {
      if (segment.trim()) {
        // 检查是否是块级元素
        if (segment.match(/^<(h[1-4]|p|ul|ol|pre|blockquote|table)/)) {
          result += `<div class="message-segment" style="animation-delay: ${segmentIndex * 0.1}s">${segment}</div>`;
          segmentIndex++;
        } else {
          result += segment;
        }
      }
    });
    
    return result || htmlContent;
  }

  // 渲染搜索窗口 (三段式布局 - 第二部分)
  function renderSearchPanel(messageIndex, searchResults) {
    const messagesContainer = container.querySelector('#ai-messages');
    if (!messagesContainer) return;

    const allMessages = messagesContainer.querySelectorAll('.message');
    let actualIndex = 0;

    for (let i = 0; i < allMessages.length; i++) {
      const msgEl = allMessages[i];
      if (msgEl.classList.contains('ai')) {
        if (actualIndex === messageIndex) {
          // 检查是否已存在搜索窗口
          let searchPanel = msgEl.querySelector('.search-panel');
          
          if (!searchPanel && searchResults && searchResults.length > 0) {
            // 创建新的搜索窗口
            searchPanel = document.createElement('div');
            searchPanel.className = 'search-panel';
            
            const resultsHtml = searchResults.map((result, idx) => `
              <div class="search-result-item">
                <span class="search-result-bullet">•</span>
                <div class="search-result-content">
                  <div class="search-result-title">${result.title || '搜索结果 ' + (idx + 1)}</div>
                  ${result.url ? `<div class="search-result-url">${result.url}</div>` : ''}
                </div>
              </div>
            `).join('');
            
            searchPanel.innerHTML = `
              <div class="search-header">
                <span class="search-icon">🔍</span>
                <span class="search-label">Search</span>
                <span class="search-query">${searchResults[0]?.query || ''}</span>
                <span class="search-count">${searchResults.length} results</span>
              </div>
              <div class="search-results">
                ${resultsHtml}
              </div>
            `;
            
            // 插入到消息内容之前
            const messageContent = msgEl.querySelector('.message-content');
            if (messageContent) {
              msgEl.insertBefore(searchPanel, messageContent);
            } else {
              msgEl.appendChild(searchPanel);
            }
          }
          
          break;
        }
        actualIndex++;
      }
    }
  }

  // ========== Dashscope API请求构建 ==========
  function buildDashscopeRequest(messageHistory) {
    // 提取用户问题（最后一条用户消息）
    const userQuery = messageHistory.filter(m => m.role === 'user').pop()?.content || '';
    
    // 检测学院信息
    const detectedCollege = detectCollegeFromHistory(messageHistory);
    
    // 系统提示词（精简版，提高响应速度）
    const instructions = `# 角色
你是南昌航空大学智能学术顾问"航宝智辅"。

## 任务
基于联网搜索回答学校相关问题，必须准确标注信息来源。

## 回答规则
- 仅基于搜索结果回答，禁止编造
- 每个事实后标注引用编号 [数字]
- 引用编号从1开始递增，与文末来源编号一一对应
- 在回答末尾列出所有引用来源，格式为：
  信息来源：
  - [1](https://完整链接) - 链接标题
  - [2](https://完整链接) - 链接标题
- 确保每个链接都是真实可访问的URL，禁止提供模拟链接
- 优先使用学校官网链接
- 回答简明扼要，控制在500字内

## 风格
简洁、结构化、专业可信`; 

    // 构建请求体
    const payload = {
      model: 'qwen3.5-plus',
      input: messageHistory.map(m => ({
        role: m.role,
        content: m.content
      })),
      instructions: instructions,
      tools: state.webSearchEnabled !== false ? [{ type: 'web_search' }] : [],
      stream: true,
      enable_thinking: false,  // 禁用深度思考，提升响应速度
      max_tokens: 1200,  // 限制回答长度，提高响应速度
      temperature: 0.7   // 降低随机性，提高确定性
    };
    
    return payload;
  }
  
  // 从对话历史中检测学院
  function detectCollegeFromHistory(messages) {
    const colleges = [
      '经济管理学院', '材料科学与工程学院', '航空制造与机械工程学院',
      '信息工程学院', '飞行器工程学院', '环境与化学工程学院',
      '软件学院', '外国语学院', '数学与信息科学学院',
      '土木建筑学院', '体育学院', '马克思主义学院',
      '艺术学院', '航空服务与音乐学院', '创新创业学院',
      '继续教育学院', '国际教育学院', '研究生院'
    ];
    
    for (const msg of messages) {
      if (msg.role === 'user' || msg.role === 'assistant') {
        for (const college of colleges) {
          if (msg.content.includes(college)) {
            return college;
          }
        }
      }
    }
    return null;
  }

  // ========== API调用 ==========
  async function callRagflowAPI(question) {
    const messageHistory = [];

    // 构建完整对话历史，供后端判断对话状态（学院识别、是否首次对话等）
    // 后端会在调用 AI 模型前智能截断，避免干扰联网搜索
    for (let i = 0; i < state.messages.length; i++) {
      const msg = state.messages[i];
      if (msg.type === 'user') {
        // 跳过当前正在发送的消息（最后一条）
        if (i === state.messages.length - 1) continue;
        const nextMsg = state.messages[i + 1];
        // 只添加有对应AI回复的用户消息（成对添加）
        if (nextMsg && nextMsg.type === 'ai') {
          messageHistory.push({ role: 'user', content: msg.content });
          messageHistory.push({ role: 'assistant', content: nextMsg.content });
        }
      }
    }
    // 添加当前问题
    messageHistory.push({ role: 'user', content: question });

    let aiMessageIndex = -1;
    let timeoutId;
    let hasResolved = false;
    let streamFinished = false;
    let fullReceivedContent = '';
    let abortController = new AbortController();
    
    // 初始化推理过程数据
    let currentReasoning = [];
    let reasoningStepId = 0;
    state.currentReasoningId = null;

    // 保存到状态
    state.currentAbortController = abortController;
    
    // 重置搜索结果和引用映射
    state.searchResults = [];
    state.citationUrls = {};

    return new Promise((resolve, reject) => {
      timeoutId = setTimeout(() => {
        console.error('API请求超时');
        if (!hasResolved) {
          hasResolved = true;
          streamFinished = true;
          abortController.abort();

          if (aiMessageIndex === -1) {
            state.messages.push({
              type: 'error',
              content: '响应超时，请稍后重试或尝试重新提问。',
              timestamp: new Date()
            });
          } else {
            state.messages[aiMessageIndex].content += '\n\n[响应超时，内容可能不完整]';
            state.messages[aiMessageIndex].type = 'error';
          }

          // 保持当前滚动位置，不自动滚动
          render(true);
          reject(new Error('请求超时'));
        }
      }, 60000);  // 60秒超时

      // 保存超时定时器ID
      state.currentTimeoutId = timeoutId;

      // 通过 Flask 后端代理调用（后端持有 API Key，强制登录鉴权）
      const apiUrl = config.server.baseUrl + '/api/chat';
      const headers = {
        'Content-Type': 'application/json'
      };
      
      // 立即显示思考卡片（Kimi 风格 - 感知速度优化）
      const loadingMessageIndex = state.messages.length;
      state.messages.push({
        type: 'ai',
        content: '',
        timestamp: new Date(),
        isTyping: false,
        isThinking: true,
        thinkingStatus: 'searching'  // searching -> thinking -> done
      });
      render(true);
      
      // 构建请求体（Flask 后端格式：messages + chat_id）
      const dashscopeRequest = buildDashscopeRequest(messageHistory);
      const requestBody = {
        messages: messageHistory,
        chat_id: 'chat_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
        // 透传 Dashscope 特有参数供后端使用
        model: dashscopeRequest.model,
        instructions: dashscopeRequest.instructions,
        tools: dashscopeRequest.tools,
        temperature: dashscopeRequest.temperature
      };

      fetchEventSource(apiUrl, {
        method: 'POST',
        headers: headers,
        credentials: 'include',
        body: JSON.stringify(requestBody),
        signal: abortController.signal,

        onopen(response) {
          if (!response.ok) {
            clearTimeout(timeoutId);
            state.currentTimeoutId = null;
            // 401 未登录，跳转到登录页
            if (response.status === 401) {
              window.location.href = getLoginUrl();
              return;
            }
            if (!hasResolved) {
              hasResolved = true;
              streamFinished = true;

              state.messages.push({
                type: 'error',
                content: `❌ 请求失败 (HTTP ${response.status})，请检查网络连接或稍后重试。`,
                timestamp: new Date()
              });

              render(true);
            }
            // 不 throw，让 fetchEventSource 正常处理错误回调
          }
        },

        onmessage(event) {
          if (streamFinished) return;

          clearTimeout(timeoutId);
          state.currentTimeoutId = null; // 清除状态中的定时器ID

          if (event.data === '[DONE]') {
            streamFinished = true;

            // 最终渲染：只做一次精确的 DOM 更新，不重建整个容器
            if (aiMessageIndex !== -1) {
              const message = state.messages[aiMessageIndex];
              if (message && message.type === 'ai') {
                // 确保引用完整
                if (!message.citationUrls || Object.keys(message.citationUrls).length === 0) {
                  message.citationUrls = extractCitationUrlsFromContent(message.content);
                }
                if (state.citationUrls && Object.keys(state.citationUrls).length > 0) {
                  message.citationUrls = { ...state.citationUrls, ...message.citationUrls };
                }
                // isFinal=true 确保来源区块立即处理（不受节流限制）
                updateMessageDisplay(aiMessageIndex, true);
              }
            }

            if (!hasResolved) {
              hasResolved = true;
              resolve(aiMessageIndex !== -1 ? state.messages[aiMessageIndex].content : '');
            }
            // 关闭连接（[DONE] 是最后一个事件，无需等待 onclose）
            abortController.abort();
            return;
          }

          try {
            const parsed = JSON.parse(event.data);

            // 处理Dashscope Responses API错误
            if (parsed.error) {
              console.error('[SSE Error] API返回错误:', parsed.error);
              clearTimeout(timeoutId);
              state.currentTimeoutId = null;
              streamFinished = true;

              if (!hasResolved) {
                hasResolved = true;
                
                // 移除loading消息
                if (loadingMessageIndex !== -1 && state.messages[loadingMessageIndex] &&
                    state.messages[loadingMessageIndex].isThinking) {
                  state.messages.splice(loadingMessageIndex, 1);
                }

                state.messages.push({
                  type: 'error',
                  content: '⚠️ AI服务错误，请稍后重试。',
                  timestamp: new Date()
                });

                render();
                scrollToBottom();
                reject(new Error(parsed.error));
              }
              return;
            }

            // Dashscope Responses API格式解析
            // 支持多种事件类型：output_text.delta, reasoning.delta, web_search_call, search_keywords, thinking_start, thinking_end 等
            let content = null;

            // ========== 处理后端返回的引用数据（方案A核心）==========
            if (parsed.citations) {
              // 后端返回的引用映射（优先使用）
              if (aiMessageIndex !== -1) {
                const message = state.messages[aiMessageIndex];
                if (message) {
                  message.citationUrls = { ...message.citationUrls, ...parsed.citations };
                  // 立即重新渲染，使新引用链接可见（不等下一个 content chunk）
                  updateMessageDisplay(aiMessageIndex);
                }
              }
            }

            // ========== Phase 3: 处理 search_keywords 事件 ==========
            if (parsed.type === 'search_keywords') {
              const keywords = parsed.keywords || [];
              const count = parsed.count || 0;
              if (aiMessageIndex !== -1) {
                const message = state.messages[aiMessageIndex];
                if (message) {
                  message.searchKeywords = keywords;
                  message.searchResultCount = count;
                  message.isThinking = false;
                  message.thinkingStatus = 'thinking';
                  updateMessageDisplay(aiMessageIndex);
                }
              }
              return;
            }

            // ========== Phase 3: 处理 thinking_start 事件 ==========
            if (parsed.type === 'thinking_start') {
              if (aiMessageIndex !== -1) {
                const message = state.messages[aiMessageIndex];
                if (message) {
                  message.thinkingStatus = 'thinking';
                  updateMessageDisplay(aiMessageIndex);
                }
              }
              return;
            }

            // ========== Phase 3: 处理 thinking_end 事件 ==========
            if (parsed.type === 'thinking_end') {
              if (aiMessageIndex !== -1) {
                const message = state.messages[aiMessageIndex];
                if (message) {
                  message.isThinking = false;
                  message.thinkingStatus = 'done';
                  updateMessageDisplay(aiMessageIndex);
                }
              }
              return;
            }

            // 捕获搜索结果（原有逻辑，保持兼容）
            if (parsed.type === 'response.web_search_call' && parsed.web_search_call) {
              const searchCall = parsed.web_search_call;
              if (searchCall.search_results && Array.isArray(searchCall.search_results)) {
                searchCall.search_results.forEach((result, idx) => {
                  if (result.url) {
                    state.searchResults.push({
                      title: result.title || '',
                      url: result.url,
                      snippet: result.snippet || ''
                    });
                    // 建立引用编号到URL的映射
                    state.citationUrls[idx + 1] = result.url;
                  }
                });
              }
            }
            
            if (parsed.type === 'response.output_text.delta' && parsed.delta) {
              // 标准文本输出
              content = parsed.delta;
            } else if (parsed.type === 'response.reasoning.delta' && parsed.delta) {
              // 推理内容（可忽略或用于显示思考过程）
              content = null; // 不显示推理内容
            } else if (parsed.choices?.[0]?.delta?.content) {
              // 兼容OpenAI格式（如果API返回此格式）
              content = parsed.choices[0].delta.content;
            }

            // 处理正常内容流
            if (content !== undefined && content !== null && content !== '') {
              // 首次收到内容时，替换loading消息或创建新消息
              if (aiMessageIndex === -1) {
                // 如果之前有思考卡片消息，替换它
                if (loadingMessageIndex !== -1 && state.messages[loadingMessageIndex]?.isThinking) {
                  state.messages[loadingMessageIndex] = {
                    type: 'ai',
                    content: content,
                    timestamp: new Date(),
                    isTyping: false,
                    pendingContent: '',
                    searchKeywords: state.messages[loadingMessageIndex].searchKeywords || [],
                    searchResultCount: state.messages[loadingMessageIndex].searchResultCount || 0
                  };
                  aiMessageIndex = loadingMessageIndex;
                } else {
                  // 创建新消息
                  state.messages.push({
                    type: 'ai',
                    content: content,
                    timestamp: new Date(),
                    isTyping: false,
                    pendingContent: ''
                  });
                  aiMessageIndex = state.messages.length - 1;
                }
                render();
              } else {
                // 追加内容
                typeText(aiMessageIndex, content);
              }
            }
          } catch (e) {
            console.error('解析流数据失败:', e, event.data);
          }
        },

        onerror(err) {
          // 忽略主动中止导致的错误
          if (err.name === 'AbortError' || streamFinished) {
            return;
          }

          console.error('SSE连接错误:', err);
          clearTimeout(timeoutId);
          state.currentTimeoutId = null; // 清除状态中的定时器ID
          streamFinished = true;

          if (!hasResolved) {
            hasResolved = true;

            if (aiMessageIndex === -1) {
              state.messages.push({
                type: 'error',
                content: '❌ 连接失败，请检查网络连接或稍后重试。',
                timestamp: new Date()
              });
            } else {
              state.messages[aiMessageIndex].content += '\n\n❌ [连接中断，内容可能不完整]';
              state.messages[aiMessageIndex].type = 'error';
            }

            // 保持当前滚动位置，不自动滚动
            render(true);
            reject(err);
          }
        },

        onclose() {
          if (!hasResolved && !streamFinished) {
            streamFinished = true;

            // ========== 流式响应完成后，做最终渲染（兜底） ==========
            if (aiMessageIndex !== -1) {
              const message = state.messages[aiMessageIndex];
              if (message && message.type === 'ai') {
                // 重新提取引用映射（此时内容已完整）
                const contentCitations = extractCitationUrlsFromContent(message.content);
                message.citationUrls = { ...contentCitations, ...(message.citationUrls || {}) };

                if (state.citationUrls && Object.keys(state.citationUrls).length > 0) {
                  message.citationUrls = { ...state.citationUrls, ...message.citationUrls };
                }

                // 只做精确的 DOM 更新，不重建整个容器
                updateMessageDisplay(aiMessageIndex, true);
              }
            }

            hasResolved = true;
            const finalContent = aiMessageIndex !== -1 ? state.messages[aiMessageIndex].content : '';
            resolve(finalContent);
          }
        }
      });
    });

    function waitForTypingComplete() {
      return new Promise(resolve => {
        const checkTyping = () => {
          const message = aiMessageIndex !== -1 ? state.messages[aiMessageIndex] : null;
          if (message && message.isTyping) {
            setTimeout(checkTyping, 50);
          } else {
            resolve();
          }
        };
        checkTyping();
      });
    }

    function formatReferenceInfo(reference) {
      if (!reference || !Array.isArray(reference) || reference.length === 0) {
        return '';
      }

      let referenceText = '\n\n参考资料：\n';
      reference.forEach((ref, index) => {
        referenceText += `\n${index + 1}. ${ref.name || '未知文件'} - ${ref.content || ''}`;
      });

      return referenceText;
    }
  }

  // 更新发送按钮状态
  function updateSendButtonState() {
    const input = container.querySelector('#ai-input');
    const sendBtn = container.querySelector('#ai-send-btn');

    if (!sendBtn || !input) return;

    const inputValue = input.value.trim();
    const hasContent = inputValue.length > 0;

    // 临时禁用过渡动画以防止闪烁
    const originalTransition = sendBtn.style.transition;
    sendBtn.style.transition = 'none';

    if (hasContent) {
      sendBtn.classList.remove('disabled-empty');
      sendBtn.removeAttribute('disabled');
    } else {
      sendBtn.classList.add('disabled-empty');
      sendBtn.setAttribute('disabled', 'true');
    }

    // 恢复过渡动画
    requestAnimationFrame(() => {
      sendBtn.style.transition = originalTransition || '';
    });
  }

  async function sendMessage() {
    const input = container.querySelector('#ai-input');
    const inputValue = input ? input.value.trim() : '';

    // 截断超出最大长度的输入
    let processedInputValue = inputValue;
    if (processedInputValue.length > config.maxInputLength) {
      processedInputValue = processedInputValue.substring(0, config.maxInputLength);
      if (input) {
        input.value = processedInputValue; // 更新输入框内容
      }
    }

    if (!processedInputValue || state.isSending) return;

    // 未登录拦截
    if (!state.isLoggedIn) {
      state.messages.push({
        type: 'error',
        content: '请先登录后再使用 AI 助手。',
        timestamp: new Date()
      });
      render();
      return;
    }

    const userMessage = {
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };
    state.messages.push(userMessage);

    saveMessagesToSession();

    // 发送新消息时，重新启用自动滚动
    state.autoScrollEnabled = true;

    const userQuestion = inputValue;
    if (input) {
      input.value = '';
      updateSendButtonState(); // 更新发送按钮状态
    }

    // 清除保存的输入状态
    sessionStorage.removeItem('ai_inputState');

    // 渲染并自动滚动到底部（render内部已处理滚动）
    render();

    try {
      state.isSending = true;
      state.isReceiving = true;
      // 初始化流式输出状态
      state.streamingPhase = 'idle';
      render();

      await callRagflowAPI(userQuestion);
    } catch (error) {
      // 忽略主动中止导致的错误
      if (error.name !== 'AbortError') {
        console.error('发送消息失败:', error);
      }
    } finally {
      state.isSending = false;
      state.isReceiving = false;
      saveMessagesToSession();

      // 如果自动滚动被禁用，保持当前滚动位置
      if (!state.autoScrollEnabled) {
        render(true); // skipScroll = true
      } else {
        render();
        scrollToBottom();
      }

      if (config.onMessage) {
        config.onMessage(state.messages);
      }
    }
  }

  // ========== 事件绑定 ==========
  function bindEvents() {
    // 悬浮球点击
    const floatingBall = container.querySelector('#ai-floating-ball');
    if (floatingBall) {
      floatingBall.addEventListener('click', toggleChatWindow);
    }

    // 悬浮球鼠标移入/移出事件，用于恢复消息气泡
    const ballWrapper = container.querySelector('.floating-ball-wrapper');
    if (ballWrapper) {
      // 鼠标离开悬浮球
      ballWrapper.addEventListener('mouseleave', () => {
        // 如果消息气泡被禁用，标记为已经离开
        if (tooltipDisabled) {
          hasLeftAfterDrag = true;
        }
      });

      // 鼠标进入悬浮球
      ballWrapper.addEventListener('mouseenter', () => {
        // 只有在拖动后离开过，再重新进入时才恢复
        if (tooltipDisabled && hasLeftAfterDrag) {
          tooltipDisabled = false;
          hasLeftAfterDrag = false;
          // 移除禁用CSS类，恢复hover效果
          ballWrapper.classList.remove('tooltip-disabled');

          const tooltip = container.querySelector('.floating-ball-tooltip');
          if (tooltip) {
            // 移除auto-hide类
            tooltip.classList.remove('auto-hide');

            // 先设置初始状态（缩小到中心）
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'visible';
            tooltip.style.transform = 'scale(0)';

            // 使用requestAnimationFrame确保过渡动画正常运行
            requestAnimationFrame(() => {
              // 清除内联样式，让CSS的hover效果生效，产生过渡动画
              tooltip.style.opacity = '';
              tooltip.style.visibility = '';
              tooltip.style.transform = '';
            });
          }
        }
      });
    }

    // 悬浮球关闭按钮
    const floatingBallClose = container.querySelector('#ai-floating-ball-close');
    if (floatingBallClose) {
      floatingBallClose.addEventListener('click', (e) => {
        e.stopPropagation(); // 防止触发悬浮球点击
        showCloseConfirm();
      });
    }

    // 关闭AI助手确认弹窗
    const closeConfirmOverlay = container.querySelector('#ai-close-confirm-overlay');
    if (closeConfirmOverlay) {
      closeConfirmOverlay.addEventListener('click', (e) => {
        if (e.target === closeConfirmOverlay) cancelCloseConfirm();
      });
    }

    const cancelCloseBtn = container.querySelector('#ai-cancel-close');
    if (cancelCloseBtn) {
      cancelCloseBtn.addEventListener('click', cancelCloseConfirm);
    }

    const confirmCloseBtn = container.querySelector('#ai-confirm-close');
    if (confirmCloseBtn) {
      confirmCloseBtn.addEventListener('click', executeCloseWidget);
    }

    // 关闭按钮
    const closeBtn = container.querySelector('#ai-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', closeChatWindow);
    }

    // 全屏按钮
    const fullscreenBtn = container.querySelector('#ai-fullscreen-btn');
    if (fullscreenBtn) {
      fullscreenBtn.addEventListener('click', toggleFullscreen);
    }

    // 登出按钮
    const logoutBtn = container.querySelector('#ai-logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        handleLogout();
      });
    }

    // 登录按钮
    const loginBtn = container.querySelector('#ai-login-btn');
    if (loginBtn) {
      loginBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        window.location.href = getLoginUrl();
      });
    }

    // 发送按钮
    const sendBtn = container.querySelector('#ai-send-btn');
    if (sendBtn) {
      sendBtn.addEventListener('click', sendMessage);
    }

    // 中止按钮
    const stopBtn = container.querySelector('#ai-stop-btn');
    if (stopBtn) {
      stopBtn.addEventListener('click', stopAIOutput);
    }

    // 清除所有消息按钮
    const clearAllBtn = container.querySelector('#ai-clear-all-btn');
    if (clearAllBtn) {
      clearAllBtn.addEventListener('click', confirmClearAllMessages);
    }

    // 输入框回车发送
    const input = container.querySelector('#ai-input');
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });
      input.addEventListener('input', function () {
        // 限制最大输入字符数
        if (this.value.length > config.maxInputLength) {
          this.value = this.value.substring(0, config.maxInputLength);

          // 显示字数限制提醒弹窗
          showWordLimitModal();
        }

        adjustTextareaHeight.call(this);
        saveInputState(); // 保存输入状态
        updateSendButtonState(); // 更新发送按钮状态
      });
      // 初始化时检查发送按钮状态
      updateSendButtonState();
    }

    // 预设问题标签页
    const presetTabs = container.querySelectorAll('.preset-tab');
    presetTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const index = parseInt(tab.getAttribute('data-tab-index'));
        switchPresetTab(index);
      });
    });

    // 标签栏滚动按钮
    const tabNavLeft = container.querySelector('#ai-tab-nav-left');
    const tabNavRight = container.querySelector('#ai-tab-nav-right');
    if (tabNavLeft) {
      tabNavLeft.addEventListener('click', scrollTabsLeft);
    }
    if (tabNavRight) {
      tabNavRight.addEventListener('click', scrollTabsRight);
    }

    // 监听标签栏滚动，更新按钮状态
    const tabsContainer = container.querySelector('.preset-tabs');
    if (tabsContainer) {
      tabsContainer.addEventListener('scroll', updateScrollButtons);
    }

    // 监听消息容器滚动，控制自动滚动行为
    const messagesContainer = container.querySelector('.chat-messages');
    if (messagesContainer) {
      messagesContainer.addEventListener('scroll', handleMessagesScroll);

      // 事件委托处理链接点击，确保所有链接在新窗口打开
      messagesContainer.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (link && link.href) {
          e.preventDefault();
          e.stopPropagation();
          window.open(link.href, '_blank', 'noopener,noreferrer');
        }
      });

      // Phase 4: 悬浮引用预览（事件委托）
      let citationTooltip = null;
      let citationHideTimeout = null;

      function hideCitationTooltip() {
        if (citationTooltip) {
          citationTooltip.classList.remove('visible');
          setTimeout(() => {
            if (citationTooltip && citationTooltip.parentNode) {
              document.body.removeChild(citationTooltip);
            }
            citationTooltip = null;
          }, 200);
        }
      }

      messagesContainer.addEventListener('mouseover', (e) => {
        const pill = e.target.closest('a.citation-link');
        if (!pill) return;

        clearTimeout(citationHideTimeout);

        // 销毁旧 tooltip
        if (citationTooltip) {
          document.body.removeChild(citationTooltip);
          citationTooltip = null;
        }

        const num = pill.getAttribute('data-citation-num');
        const title = pill.getAttribute('data-citation-title');
        const url = pill.getAttribute('data-citation-url');

        if (!num || !url) return;

        // 创建悬浮预览卡片
        citationTooltip = document.createElement('div');
        citationTooltip.className = 'citation-preview-tooltip';
        citationTooltip.innerHTML = `
          <div class="citation-source-name">[${num}] ${escapeHtml(title)}</div>
          <div class="citation-url-preview">${escapeHtml(url)}</div>
          <div class="citation-arrow"></div>
        `;

        document.body.appendChild(citationTooltip);

        // 鼠标移入 tooltip 时不关闭
        citationTooltip.addEventListener('mouseleave', () => {
          if (citationHideTimeout) clearTimeout(citationHideTimeout);
          citationHideTimeout = setTimeout(() => {
            hideCitationTooltip();
          }, 100);
        });

        // 计算位置：在 pill 正上方居中
        const pillRect = pill.getBoundingClientRect();
        const tooltipRect = citationTooltip.getBoundingClientRect();
        const left = pillRect.left + pillRect.width / 2 - tooltipRect.width / 2;
        const top = pillRect.top - tooltipRect.height - 8;

        // 防止超出左边界
        const adjustedLeft = Math.max(8, left);
        // 防止超出右边界
        const finalLeft = adjustedLeft + tooltipRect.width > window.innerWidth
          ? window.innerWidth - tooltipRect.width - 8
          : adjustedLeft;
        // 如果上方空间不足，显示在下方
        let showBelow = top < 8;
        // 下方也不够时，强制显示在上方并裁剪
        if (showBelow && pillRect.bottom + tooltipRect.height > window.innerHeight - 8) {
          showBelow = false;
        }
        const finalTop = showBelow ? pillRect.bottom + 8 : top;

        citationTooltip.style.left = finalLeft + 'px';
        citationTooltip.style.top = finalTop + 'px';

        // 翻转到下方时箭头方向也要改变
        const arrow = citationTooltip.querySelector('.citation-arrow');
        if (showBelow) {
          arrow.style.bottom = 'auto';
          arrow.style.top = '-6px';
          arrow.style.transform = 'translateX(-50%) rotate(-135deg)';
        }

        // 短暂延迟后显示动画
        requestAnimationFrame(() => {
          citationTooltip.classList.add('visible');
        });
      });

      messagesContainer.addEventListener('mouseout', (e) => {
        const pill = e.target.closest('a.citation-link');
        if (!pill) return;

        // 检查是否移动到了 tooltip 上
        const relatedTarget = e.relatedTarget;
        if (relatedTarget && relatedTarget.closest && relatedTarget.closest('.citation-preview-tooltip')) {
          return;
        }

        citationHideTimeout = setTimeout(() => {
          hideCitationTooltip();
        }, 100);
      });

      // Phase 5: 来源卡片事件委托（点击打开链接 + 折叠/展开）
    messagesContainer.addEventListener('click', (e) => {
      // 搜索结果点击 - 打开链接
      const searchItem = e.target.closest('.search-result-item');
      if (searchItem) {
        const url = searchItem.getAttribute('data-url');
        if (url) window.open(url, '_blank', 'noopener,noreferrer');
        return;
      }

      // 来源卡片点击 - 打开链接
      const card = e.target.closest('.source-card');
      if (card) {
        const url = card.getAttribute('data-url');
        if (url) window.open(url, '_blank', 'noopener,noreferrer');
        return;
      }

      // 来源卡片头部点击 - 折叠/展开
      const header = e.target.closest('[data-action="toggle-sources"]');
      if (header) {
        toggleSourceCards(header);
        return;
      }
    });

    // 预设问题项
    const presetItems = container.querySelectorAll('.preset-question-item');
    presetItems.forEach(item => {
      item.addEventListener('click', () => {
        const question = item.getAttribute('data-question');
        selectPresetQuestion(question);
      });
    });

    // HIGH FIX: 使用事件委托处理所有操作按钮，防止 updateMessageDisplay 后事件丢失
    messagesContainer.addEventListener('click', (e) => {
      // 复制按钮
      const copyBtn = e.target.closest('.copy-btn');
      if (copyBtn) {
        const index = parseInt(copyBtn.getAttribute('data-index'));
        copyMessage(state.messages[index].content, index);
        return;
      }

      // 重新发送按钮
      const resendBtn = e.target.closest('.resend-btn');
      if (resendBtn) {
        const index = parseInt(resendBtn.getAttribute('data-index'));
        resendMessage(index);
        return;
      }

      // 删除按钮
      const deleteBtn = e.target.closest('.delete-btn');
      if (deleteBtn) {
        const index = parseInt(deleteBtn.getAttribute('data-index'));
        confirmDeleteMessage(index);
        return;
      }

      // 重新生成按钮
      const regenBtn = e.target.closest('.regenerate-btn');
      if (regenBtn) {
        const index = parseInt(regenBtn.getAttribute('data-index'));
        regenerateMessage(index);
        return;
      }

      // 分享按钮
      const shareBtn = e.target.closest('.share-btn');
      if (shareBtn) {
        const index = parseInt(shareBtn.getAttribute('data-index'));
        shareMessage(index);
        return;
      }

      // 点赞/点踩按钮
      const feedbackBtn = e.target.closest('.feedback-btn');
      if (feedbackBtn) {
        const index = parseInt(feedbackBtn.getAttribute('data-index'));
        const type = feedbackBtn.getAttribute('data-feedback');
        setFeedback(index, type);
        return;
      }
    });

    // 深度思考和联网搜索按钮已移除，功能默认开启

    // 删除确认弹窗
    const confirmOverlay = container.querySelector('#ai-confirm-overlay');
    if (confirmOverlay) {
      confirmOverlay.addEventListener('click', (e) => {
        if (e.target === confirmOverlay) cancelDelete();
      });
    }

    const cancelDeleteBtn = container.querySelector('#ai-cancel-delete');
    if (cancelDeleteBtn) {
      cancelDeleteBtn.addEventListener('click', cancelDelete);
    }

    const confirmDeleteBtn = container.querySelector('#ai-confirm-delete');
    if (confirmDeleteBtn) {
      confirmDeleteBtn.addEventListener('click', executeDelete);
    }
  }

    // ========== 拖动功能 ==========
    const chatHeader = container.querySelector('.chat-header');
    const assistant = container.querySelector('.ai-assistant');

    if (chatHeader && assistant) {
      chatHeader.addEventListener('mousedown', handleDragStart);
      chatHeader.addEventListener('touchstart', handleDragStart, { passive: false });
    }

    // CRITICAL FIX: 文档级事件监听器只绑定一次
    if (!_documentListenersBound) {
      _documentListenersBound = true;
      // 窗口拖动
      document.addEventListener('mousemove', handleDragMove);
      document.addEventListener('mouseup', handleDragEnd);
      document.addEventListener('touchmove', handleDragMove, { passive: false });
      document.addEventListener('touchend', handleDragEnd);

      // 窗口调整大小
      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeEnd);
      document.addEventListener('touchmove', handleResizeMove, { passive: false });
      document.addEventListener('touchend', handleResizeEnd);

      // 悬浮球拖动
      document.addEventListener('mousemove', handleBallDragMove);
      document.addEventListener('mouseup', handleBallDragEnd);
      document.addEventListener('touchmove', handleBallDragMove, { passive: false });
      document.addEventListener('touchend', handleBallDragEnd);
    }

    // 调整大小功能：事件委托
    container.addEventListener('mousedown', (e) => {
      const resizeHandle = e.target.closest('.resize-handle');
      if (resizeHandle) {
        handleResizeStart(e);
      }
    });

    container.addEventListener('touchstart', (e) => {
      const resizeHandle = e.target.closest('.resize-handle');
      if (resizeHandle) {
        handleResizeStart(e);
      }
    }, { passive: false });

    // 悬浮球拖动功能
    const floatingBallForDrag = container.querySelector('.floating-ball');
    if (floatingBallForDrag) {
      floatingBallForDrag.addEventListener('mousedown', handleBallDragStart);
      floatingBallForDrag.addEventListener('touchstart', handleBallDragStart, { passive: false });
    }
  }

  // ========== 拖动功能处理 ==========
  function handleDragStart(e) {
    const assistant = container.querySelector('.ai-assistant');
    if (!assistant || state.isFullscreen) return; // 全屏时不允许拖动

    // 防止点击头部按钮时触发拖动
    if (e.target.closest('.fullscreen-btn') || e.target.closest('.close-btn')) {
      return;
    }

    // 防止点击调整大小控制点时触发拖动
    if (e.target.closest('.resize-handle')) {
      return;
    }

    state.isDragging = true;

    // 获取鼠标/触摸位置
    const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
    const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;

    state.dragStartX = clientX;
    state.dragStartY = clientY;

    // 获取当前窗口位置
    const rect = assistant.getBoundingClientRect();
    if (state.windowLeft === null) {
      state.windowLeft = rect.left;
    }
    if (state.windowTop === null) {
      state.windowTop = rect.top;
    }

    // 添加拖动样式
    assistant.classList.add('dragging');

    // 阻止默认行为
    e.preventDefault();
  }

  function handleDragMove(e) {
    if (!state.isDragging || state.isFullscreen || state.isResizing) return;

    const assistant = container.querySelector('.ai-assistant');
    if (!assistant) return;

    // 获取鼠标/触摸位置
    const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
    const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;

    // 计算移动距离
    const deltaX = clientX - state.dragStartX;
    const deltaY = clientY - state.dragStartY;

    // 计算新位置
    let newLeft = state.windowLeft + deltaX;
    let newTop = state.windowTop + deltaY;

    // 边界检查，防止拖出视口
    const rect = assistant.getBoundingClientRect();
    const maxLeft = window.innerWidth - rect.width;
    const maxTop = window.innerHeight - rect.height;

    newLeft = Math.max(0, Math.min(newLeft, maxLeft));
    newTop = Math.max(0, Math.min(newTop, maxTop));

    // 应用新位置
    assistant.style.left = newLeft + 'px';
    assistant.style.top = newTop + 'px';
    assistant.style.right = 'auto';
    assistant.style.bottom = 'auto';

    e.preventDefault();
  }

  function handleDragEnd(e) {
    if (!state.isDragging) return;

    const assistant = container.querySelector('.ai-assistant');
    if (assistant) {
      // 移除拖动样式
      assistant.classList.remove('dragging');

      // 保存当前位置
      const rect = assistant.getBoundingClientRect();
      state.windowLeft = rect.left;
      state.windowTop = rect.top;
    }

    state.isDragging = false;
  }

  // ========== 调整大小功能处理 ==========
  function handleResizeStart(e) {
    if (state.isFullscreen) return; // 全屏时不允许调整大小

    const handle = e.target.closest('.resize-handle');
    if (!handle) return;

    e.preventDefault();
    e.stopPropagation();

    state.isResizing = true;
    state.resizeDirection = handle.dataset.direction;

    // 在调整大小开始前保存滚动百分比，用于调整结束后恢复
    const messagesContainer = container.querySelector('.chat-messages');
    if (messagesContainer) {
      const scrollableHeight = Math.max(0, messagesContainer.scrollHeight - messagesContainer.clientHeight);
      state.savedScrollPercentageBeforeResize = scrollableHeight > 0 ? messagesContainer.scrollTop / scrollableHeight : 0;
      // 同时保存当前的容器尺寸信息，以便在恢复时参考
      state.savedScrollContainerInfo = {
        clientHeight: messagesContainer.clientHeight,
        scrollHeight: messagesContainer.scrollHeight
      };
    }

    // 设置窗口正在调整大小标志
    state.isWindowResizing = true;

    const assistant = container.querySelector('.ai-assistant');
    if (!assistant) return;

    // 获取鼠标/触摸位置
    const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
    const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;

    state.resizeStartX = clientX;
    state.resizeStartY = clientY;

    // 保存当前尺寸和位置
    const rect = assistant.getBoundingClientRect();
    state.resizeStartWidth = rect.width;
    state.resizeStartHeight = rect.height;
    state.resizeStartLeft = rect.left;
    state.resizeStartTop = rect.top;

    // 添加调整大小样式
    assistant.classList.add('resizing');
  }

  function handleResizeMove(e) {
    if (!state.isResizing || state.isDragging) return;

    const assistant = container.querySelector('.ai-assistant');
    if (!assistant) return;

    e.preventDefault();

    // 获取鼠标/触摸位置
    const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
    const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;

    // 计算移动距离
    const deltaX = clientX - state.resizeStartX;
    const deltaY = clientY - state.resizeStartY;

    let newWidth = state.resizeStartWidth;
    let newHeight = state.resizeStartHeight;
    let newLeft = state.resizeStartLeft;
    let newTop = state.resizeStartTop;

    // 最小尺寸
    const minWidth = 400;
    const minHeight = 500;
    // 最大尺寸（全屏尺寸 - 40px）
    const maxWidth = window.innerWidth - 40;
    const maxHeight = window.innerHeight - 40;

    // 根据调整方向计算新尺寸
    if (state.resizeDirection.includes('e')) {
      newWidth = state.resizeStartWidth + deltaX;
    }
    if (state.resizeDirection.includes('w')) {
      newWidth = state.resizeStartWidth - deltaX;
      newLeft = state.resizeStartLeft + deltaX;
    }
    if (state.resizeDirection.includes('s')) {
      newHeight = state.resizeStartHeight + deltaY;
    }
    if (state.resizeDirection.includes('n')) {
      newHeight = state.resizeStartHeight - deltaY;
      newTop = state.resizeStartTop + deltaY;
    }

    // 限制尺寸范围
    newWidth = Math.max(minWidth, Math.min(newWidth, maxWidth));
    newHeight = Math.max(minHeight, Math.min(newHeight, maxHeight));

    // 如果达到最小宽度，调整left位置
    if (state.resizeDirection.includes('w') && newWidth === minWidth) {
      newLeft = state.resizeStartLeft + (state.resizeStartWidth - minWidth);
    }
    // 如果达到最小高度，调整top位置
    if (state.resizeDirection.includes('n') && newHeight === minHeight) {
      newTop = state.resizeStartTop + (state.resizeStartHeight - minHeight);
    }

    // 限制位置不超出视口
    newLeft = Math.max(0, Math.min(newLeft, window.innerWidth - newWidth));
    newTop = Math.max(0, Math.min(newTop, window.innerHeight - newHeight));

    // 应用新尺寸和位置
    assistant.style.width = newWidth + 'px';
    assistant.style.height = newHeight + 'px';
    assistant.style.left = newLeft + 'px';
    assistant.style.top = newTop + 'px';
    assistant.style.right = 'auto';
    assistant.style.bottom = 'auto';
  }

  function handleResizeEnd(e) {
    if (!state.isResizing) return;

    const assistant = container.querySelector('.ai-assistant');
    if (assistant) {
      // 移除调整大小样式
      assistant.classList.remove('resizing');

      // 保存当前位置和尺寸
      const rect = assistant.getBoundingClientRect();
      state.windowLeft = rect.left;
      state.windowTop = rect.top;
      state.windowWidth = rect.width;  // 保存宽度
      state.windowHeight = rect.height; // 保存高度
      state.resizeStartWidth = rect.width;
      state.resizeStartHeight = rect.height;
    }

    state.isResizing = false;
    state.resizeDirection = null;

    // 重置窗口调整大小标志
    state.isWindowResizing = false;
    state.hasSavedScrollForResize = false;  // 重置保存标志

    // 使用setTimeout延迟恢复滚动位置，确保所有布局变化都已完成
    setTimeout(() => {
      // 在布局稳定后，使用保存的百分比恢复滚动位置
      if (state.savedScrollPercentageBeforeResize !== null) {
        const messagesContainer = container.querySelector('.chat-messages');
        if (messagesContainer) {
          // 设置标志表示正在恢复滚动位置
          state.isRestoringScrollPosition = true;

          const currentScrollableHeight = Math.max(0, messagesContainer.scrollHeight - messagesContainer.clientHeight);
          const targetScrollTop = Math.max(0, Math.min(
            currentScrollableHeight * state.savedScrollPercentageBeforeResize,
            currentScrollableHeight
          ));

          messagesContainer.scrollTop = targetScrollTop;

          // 重置保存的百分比
          state.savedScrollPercentageBeforeResize = null;
          state.savedScrollContainerInfo = null; // 清除保存的容器信息

          // 延迟重置恢复标志，确保滚动位置稳定
          setTimeout(() => {
            state.isRestoringScrollPosition = false;
          }, 300); // 额外的300ms确保滚动位置稳定
        }
      }

      // 确保重置忽略标志，以便后续用户滚动正常工作
      state.ignoreNextScrollEvent = false;
    }, 200); // 200ms 等待布局完全稳定
  }

  // ========== 悬浮球拖动功能处理 ==========
  let ballHasMoved = false; // 标记是否真正拖动了
  let tooltipDisabled = false; // 标记消息气泡是否被禁用
  let hasLeftAfterDrag = false; // 标记拖动后是否离开过

  function handleBallDragStart(e) {
    // 防止点击关闭按钮时触发拖动
    if (e.target.closest('.floating-ball-close')) {
      return;
    }

    state.isBallDragging = true;
    ballHasMoved = false; // 重置拖动标记

    // 立即隐藏消息气泡（拖动开始时）
    const tooltip = container.querySelector('.floating-ball-tooltip');
    if (tooltip) {
      tooltip.classList.remove('auto-show');
      tooltip.classList.add('auto-hide');
      // 强制隐藏，立即生效
      tooltip.style.opacity = '0';
      tooltip.style.visibility = 'hidden';
    }

    // 获取鼠标/触摸位置
    const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
    const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;

    state.ballDragStartX = clientX;
    state.ballDragStartY = clientY;

    // 获取当前悬浮球位置（始终使用实时位置）
    const ballWrapper = container.querySelector('.floating-ball-wrapper');
    if (ballWrapper) {
      const rect = ballWrapper.getBoundingClientRect();
      // 每次拖动开始时都重新获取当前位置
      state.ballLeft = rect.left;
      state.ballBottom = window.innerHeight - rect.bottom;

      // 添加拖动样式
      ballWrapper.classList.add('dragging');
    }

    // 只有鼠标事件才立即preventDefault，触摸事件等待移动后再判断
    if (e.type === 'mousedown') {
      e.preventDefault();
    }
  }

  function handleBallDragMove(e) {
    if (!state.isBallDragging) return;

    const ballWrapper = container.querySelector('.floating-ball-wrapper');
    if (!ballWrapper) return;

    // 获取鼠标/触摸位置
    const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
    const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;

    // 计算移动距离
    const deltaX = clientX - state.ballDragStartX;
    const deltaY = clientY - state.ballDragStartY;

    // 如果移动距离超过5px，认为是拖动而不是点击
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    if (distance > 5) {
      ballHasMoved = true;
      // 确认是拖动后，才阻止默认行为
      e.preventDefault();
    } else {
      // 移动距离小于5px，不认为是拖动，不阻止默认行为
      return;
    }

    // 计算新位置
    let newLeft = state.ballLeft + deltaX;
    let newBottom = state.ballBottom - deltaY;

    // 边界检查，防止拖出视口
    const rect = ballWrapper.getBoundingClientRect();
    const maxLeft = window.innerWidth - rect.width;
    const maxBottom = window.innerHeight - rect.height;

    newLeft = Math.max(0, Math.min(newLeft, maxLeft));
    newBottom = Math.max(0, Math.min(newBottom, maxBottom));

    // 应用新位置
    ballWrapper.style.left = newLeft + 'px';
    ballWrapper.style.bottom = newBottom + 'px';
    ballWrapper.style.right = 'auto';
    ballWrapper.style.top = 'auto';
  }

  function handleBallDragEnd(e) {
    if (!state.isBallDragging) return;

    const ballWrapper = container.querySelector('.floating-ball-wrapper');
    if (ballWrapper) {
      // 移除拖动样式
      ballWrapper.classList.remove('dragging');
      // 添加no-animation类，永久禁用弹跳动画
      ballWrapper.classList.add('no-animation');

      // 保存当前位置
      const rect = ballWrapper.getBoundingClientRect();
      state.ballLeft = rect.left;
      state.ballBottom = window.innerHeight - rect.bottom;
    }

    state.isBallDragging = false;

    // 如果发生了拖动，阻止点击事件
    if (ballHasMoved) {
      e.preventDefault();
      e.stopPropagation();

      // 禁用消息气泡
      tooltipDisabled = true;
      hasLeftAfterDrag = false; // 重置离开标记

      // 添加CSS类禁用hover效果
      const ballWrapper = container.querySelector('.floating-ball-wrapper');
      if (ballWrapper) {
        ballWrapper.classList.add('tooltip-disabled');
      }

      // 隐藏消息气泡（如果正在显示）
      const tooltip = container.querySelector('.floating-ball-tooltip');
      if (tooltip) {
        tooltip.classList.remove('auto-show');
        tooltip.classList.add('auto-hide');
      }

      // 设置一个短暂的标记，防止后续的click事件触发
      const floatingBall = container.querySelector('.floating-ball');
      if (floatingBall) {
        floatingBall.setAttribute('data-just-dragged', 'true');
        setTimeout(() => {
          floatingBall.removeAttribute('data-just-dragged');
        }, 100);
      }
    }
  }

  // ========== 首次自动显示消息气泡 ==========
  function showTooltipOnFirstLoad() {
    // 移除sessionStorage限制，每次页面加载时都显示

    // 等待DOM渲染完成
    setTimeout(() => {
      const tooltip = container.querySelector('.floating-ball-tooltip');
      if (!tooltip) return;

      // 添加自动显示类
      tooltip.classList.add('auto-show');

      // 2.5秒后自动隐藏
      setTimeout(() => {
        // 先添加auto-hide类，再移除auto-show类，确保动画连贯
        tooltip.classList.add('auto-hide');
        tooltip.classList.remove('auto-show');

        // 动画结束后移除auto-hide类，恢复默认隐藏状态
        setTimeout(() => {
          tooltip.classList.remove('auto-hide');
        }, 400); // 等待淡出动画完成（0.4秒）
      }, 2500); // 2.5秒后开始淡出
    }, 500); // 等待页面渲染完成
  }

  // 显示字数限制提醒弹窗
  function showWordLimitModal() {
    // 检查是否已存在弹窗
    const existingModal = container.querySelector('.word-limit-modal');
    if (existingModal) {
      // 如果弹窗已存在且已显示，不重复显示
      if (existingModal.classList.contains('show')) {
        return;
      }
      // 如果弹窗存在但未显示，直接显示
      existingModal.classList.add('show');
      return;
    }

    // 创建弹窗HTML
    const modalHTML = `
      <div class="word-limit-modal">
        <div class="word-limit-content">
          <div class="word-limit-title">字数限制提醒</div>
          <div class="word-limit-message">已达到最大字数限制（${config.maxInputLength}字），无法继续输入。</div>
          <button class="word-limit-close-btn">确定</button>
        </div>
      </div>
    `;

    // 添加到容器中
    container.insertAdjacentHTML('beforeend', modalHTML);

    // 获取弹窗元素
    const modal = container.querySelector('.word-limit-modal');
    const closeBtn = container.querySelector('.word-limit-close-btn');

    // 显示弹窗
    setTimeout(() => {
      modal.classList.add('show');
    }, 0);

    // 绑定关闭事件
    const closeModal = () => {
      modal.classList.remove('show');
      setTimeout(() => {
        if (modal.parentNode) {
          modal.parentNode.removeChild(modal);
        }
      }, 300); // 等待动画完成
    };

    closeBtn.addEventListener('click', closeModal);

    // 点击遮罩层关闭
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal();
      }
    });
  }

  // ========== 认证状态检查 ==========
  // ========== 认证相关工具函数 ==========
  function getLoginUrl() {
    // file:// 协议下需要跳转到 http://localhost 下的登录页，确保 cookie 可共享
    if (window.location.protocol === 'file:' && config.server && config.server.baseUrl) {
      const base = config.server.baseUrl;
      const redirect = encodeURIComponent(base + '/');
      return base + '/static/login.html?redirect=' + redirect;
    }
    return '/login';
  }

  async function checkAuthState() {
    try {
      const meUrl = config.server.baseUrl + config.server.endpoints.auth.me;
      const res = await fetch(meUrl, {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });

      if (res.ok) {
        const user = await res.json();
        state.isLoggedIn = true;
        state.currentUser = user;
      } else if (res.status === 401) {
        state.isLoggedIn = false;
        state.currentUser = null;
      }
      // 其他状态码：保持默认未登录状态，不做改变
    } catch (err) {
      // 网络错误：保持默认未登录状态
      state.isLoggedIn = false;
      state.currentUser = null;
    }
  }

  async function handleLogout() {
    try {
      const logoutUrl = config.server.baseUrl + config.server.endpoints.auth.logout;
      await fetch(logoutUrl, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (err) {
      console.error('[Auth] 登出请求失败:', err);
    }

    state.isLoggedIn = false;
    state.currentUser = null;

    // 重新渲染
    render();
  }

  // ========== 公开API ==========
  const AIAssistant = {
    /**
     * 初始化AI助手插件
     * @param {Object} options - 配置选项
     */
    init: async function (options = {}) {
      // 等待marked加载完成
      await ensureMarked;

      config = { ...defaultConfig, ...options };

      // 创建容器
      container = document.createElement('div');
      container.className = 'ai-widget';
      container.id = 'ai-assistant-widget';
      document.body.appendChild(container);

      // 检测设备类型
      checkMobile();
      window.addEventListener('resize', () => {
        checkMobile();
        // 窗口大小改变时更新滑块位置（不显示过渡动画）
        if (state.showChatWindow) {
          updateTabSlider(true); // skipTransition = true
          updateScrollButtons(); // 更新滚动按钮状态

          // 重新计算textarea高度和滚动条状态
          const input = container.querySelector('#ai-input');
          if (input) {
            adjustTextareaHeight.call(input);
          }
        }
      });

      // 加载历史消息
      loadMessagesFromSession();

      // 加载窗口状态
      loadWindowState();

      // 加载输入状态
      loadInputState();

      // 页面销毁前，中止正在进行的 AI 连接
      window.addEventListener('beforeunload', () => {
        if (state.isSending || state.isReceiving) {
          stopAIOutput();
        }
      });

      // 初始渲染
      render();

      // 检查认证状态
      checkAuthState().then(() => {
        render();
      });

      // 首次自动显示消息气泡
      showTooltipOnFirstLoad();

      // 回调
      if (config.onInit) {
        config.onInit();
      }


      return this;
    },

    /**
     * 显示悬浮球
     */
    show: function () {
      if (container) {
        container.style.display = 'block';
      }
      return this;
    },

    /**
     * 隐藏悬浮球
     */
    hide: function () {
      if (container) {
        container.style.display = 'none';
      }
      return this;
    },

    /**
     * 打开聊天窗口
     */
    open: function () {
      if (!state.showChatWindow) {
        toggleChatWindow();
      }
      return this;
    },

    /**
     * 关闭聊天窗口
     */
    close: function () {
      if (state.showChatWindow) {
        closeChatWindow();
      }
      return this;
    },

    /**
     * 发送消息
     * @param {string} message - 消息内容
     */
    sendMessage: function (message) {
      if (!state.showChatWindow) {
        toggleChatWindow();
      }

      setTimeout(() => {
        const input = container.querySelector('#ai-input');
        if (input) {
          input.value = message;
          sendMessage();
        }
      }, 100);

      return this;
    },

    /**
     * 清除历史消息
     */
    clearHistory: function () {
      try {
        sessionStorage.removeItem('ai_chatMessages');
        state.messages = [];
        state.hasHistoryMessages = false;
        state.historyMessageCount = 0;
        render();
      } catch (error) {
        console.error('清除历史消息失败:', error);
      }
      return this;
    },

    /**
     * 获取消息历史
     * @returns {Array} 消息数组
     */
    getMessages: function () {
      return [...state.messages];
    },

    /**
     * 更新配置
     * @param {Object} options - 新配置选项
     */
    setConfig: function (options) {
      config = { ...config, ...options };
      render();
      return this;
    },

    /**
     * 销毁插件
     */
    destroy: function () {
      // CRITICAL FIX: 清理孤立的 tooltip
      const orphanTooltip = document.body.querySelector('.citation-preview-tooltip');
      if (orphanTooltip) orphanTooltip.remove();

      if (container) {
        container.remove();
        container = null;
      }
      window.removeEventListener('resize', checkMobile);
      return this;
    }
  };

  // 导出到全局
  global.AIAssistant = AIAssistant;

})(typeof window !== 'undefined' ? window : this);
