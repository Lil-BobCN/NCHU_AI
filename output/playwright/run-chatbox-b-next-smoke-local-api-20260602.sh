#!/usr/bin/env bash
set -euo pipefail

PWCLI="/mnt/c/Users/liuqi/.codex/skills/playwright/scripts/playwright_cli.sh"
SESSION="bnext-local-api"
BASE_URL="http://127.0.0.1:5300"
DESKTOP_SHOT="C:/Users/liuqi/Desktop/agentproject/output/playwright/chatbox-b-next-401-recovery-sources-desktop-20260602.png"
MOBILE_SHOT="C:/Users/liuqi/Desktop/agentproject/output/playwright/chatbox-b-next-401-recovery-sources-mobile-20260602.png"

"$PWCLI" --session "$SESSION" close >/dev/null 2>&1 || true
"$PWCLI" --session "$SESSION" delete-data >/dev/null 2>&1 || true
"$PWCLI" --session "$SESSION" open "$BASE_URL/login" >/dev/null

"$PWCLI" --session "$SESSION" run-code "async (page) => { await page.getByRole('button', { name: /学生 Demo 登录/ }).click(); await page.waitForURL('**/app/student'); return page.url(); }" >/dev/null
"$PWCLI" --session "$SESSION" goto "$BASE_URL/app/student/chatbox" >/dev/null
"$PWCLI" --session "$SESSION" run-code "async (page) => { await page.locator('[aria-label=\"输入咨询内容\"]').fill('请联网检索 Kimi 当前公开入口并给出来源'); await page.getByRole('button', { name: '发送' }).click(); await page.waitForURL('**/login'); return page.url(); }" >/dev/null
"$PWCLI" --session "$SESSION" run-code "async (page) => { await page.getByRole('button', { name: /学生 Demo 登录/ }).click(); await page.waitForURL('**/app/student/chatbox'); await page.getByRole('button', { name: '重新发送' }).waitFor({ timeout: 10000 }); await page.getByRole('button', { name: '重新发送' }).click(); await page.getByText('公网来源').waitFor({ timeout: 10000 }); await page.getByText('另有 1 个公开来源已折叠').waitFor({ timeout: 10000 }); await page.getByText('Moonshot platform docs').waitFor({ timeout: 10000 }); return page.url(); }" >/dev/null
"$PWCLI" --session "$SESSION" run-code "async (page) => { await page.setViewportSize({ width: 1440, height: 960 }); await page.screenshot({ path: '$DESKTOP_SHOT', fullPage: true }); await page.setViewportSize({ width: 390, height: 844 }); await page.screenshot({ path: '$MOBILE_SHOT', fullPage: true }); return { desktopShot: '$DESKTOP_SHOT', mobileShot: '$MOBILE_SHOT' }; }" >/dev/null
"$PWCLI" --session "$SESSION" run-code "async (page) => ({ finalUrl: page.url(), hasFoldNote: await page.getByText('另有 1 个公开来源已折叠').count(), hasCitationSource: await page.getByText('Moonshot platform docs').count(), hasPublicSources: await page.getByText('公网来源').count() })"
"$PWCLI" --session "$SESSION" console
