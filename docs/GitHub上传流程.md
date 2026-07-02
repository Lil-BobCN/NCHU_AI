# GitHub 上传流程

目标仓库：

```text
https://github.com/Lil-BobCN/NCHU_AI
```

默认上传分支：

```text
rag_java_dev
```

## 1. 准备条件

只需要做一次：

1. GitHub 账号已接受 `Lil-BobCN/NCHU_AI` 仓库协作者邀请。
2. 本机 Git 已登录 GitHub，或 Windows Git Credential Manager 中已有可写凭据。
3. 仓库权限至少能 push 分支。

不要使用 GitHub 登录密码推送代码。GitHub 推送需要浏览器授权、Git Credential Manager，或 Personal Access Token。

## 2. 开代理

打开本机代理软件，确认 GitHub 可访问。

本次验证可用代理：

```text
http://127.0.0.1:9910
```

测试命令：

```powershell
curl.exe -I -x http://127.0.0.1:9910 https://github.com/
```

看到 `HTTP/1.1 200 OK` 或 `HTTP/2 200` 就可以继续。

## 3. 一键上传

在项目根目录执行：

```powershell
.\deploy\upload_to_github.ps1
```

脚本会自动：

1. 克隆或复用本地临时上传目录。
2. 创建或切换到 `rag_java_dev` 分支。
3. 同步当前项目代码。
4. 排除 `.env`、虚拟环境、缓存、`.pyc`、临时上传包。
5. 提交并推送到 GitHub。

上传完成后查看：

```text
https://github.com/Lil-BobCN/NCHU_AI/tree/rag_java_dev
```

## 4. 代理端口变更

如果代理端口不是 `9910`，例如是 `7890`：

```powershell
.\deploy\upload_to_github.ps1 -Proxy http://127.0.0.1:7890
```

## 5. 自定义提交信息

```powershell
.\deploy\upload_to_github.ps1 -CommitMessage "Update deployment docs"
```

## 6. 注意事项

- 不要上传 `.env`。
- 不要上传 `.venv`、`.cache`、`__pycache__`、`logs`、`uploads`。
- 默认只更新 `rag_java_dev` 分支，不会修改 `main`。
- 如果 Git 弹出登录窗口，用已接受协作者邀请的 GitHub 账号登录授权。
