# 阿里云 ECS 部署选型与操作研究

日期：2026-05-16  
范围：NCHU AI Counselor Phase 1 后端测试部署，不按生产高可用设计。

## 结论

最适合当前项目体量的性价比选择是：

- 首选：`ecs.e-c1m4.xlarge`，4 vCPU / 16 GiB，ESSD Entry 或 ESSD PL0，系统盘 40-60 GiB，数据盘 80-100 GiB。
- 更稳但更贵：`ecs.u1-c1m4.xlarge` 或 `ecs.u2i-c1m4.xlarge`，4 vCPU / 16 GiB。
- 只做 API 学习、暂时不跑 Milvus：可以降到 2 vCPU / 4-8 GiB。
- 不建议全栈测试用 2 vCPU / 4 GiB 或 2 vCPU / 8 GiB，因为 Milvus Standalone 官方要求至少 8 GiB 内存、推荐 16 GiB，且我们的 Compose 还会同时跑 PostgreSQL、Redis、MinIO、FastAPI、Milvus 依赖。

购买策略：先按量付费试 1-3 天，确认 Docker Compose 全栈、镜像拉取、健康检查、smoke test 都稳定后，再考虑包年包月或活动价。阿里云价格和活动变化很快，最终金额以 ECS 价格计算器/购买页为准。

## 依据

本项目当前 `backend/docker-compose.phase1.yml` 一次启动这些服务：

- `api`：FastAPI
- `postgres`：PostgreSQL + pgvector image
- `redis`
- `minio`
- `milvus-etcd`
- `milvus-minio`
- `milvus`

Milvus 是资源下限的决定因素。Milvus 官方 Standalone 要求：CPU 至少满足 SIMD 扩展，推荐 4 core+；RAM 要求 8 GiB，推荐 16 GiB；硬盘推荐 SSD/NVMe。我们的栈在 Milvus 之外还要留内存给 PostgreSQL、MinIO、Redis 和 API，所以 4c16G 是合理起点。

阿里云官方文档说明，经济型 e 是共享型实例，成本更低，但非绑定 CPU 调度会导致高负载时计算性能波动；适用场景包括中小型网站、开发测试和经典轻量级应用。`ecs.e-c1m4.xlarge` 对应 4 vCPU / 16 GiB，符合本项目测试部署的成本优先目标。

如果后续要做更接近真实演示的长期环境，`u1/u2i` 比经济型 e 更适合数据库、缓存、搜索类组合负载。阿里云 u1 文档列出的场景包含中小型数据库系统、缓存、搜索集群；`ecs.u1-c1m4.xlarge` 也是 4 vCPU / 16 GiB。`u2i-c1m4.xlarge` 的网络和云盘指标更强，适合更稳的测试环境。

## 推荐配置

### 方案 A：最低可跑全栈

- ECS：`ecs.e-c1m2.xlarge`，4 vCPU / 8 GiB
- 磁盘：ESSD Entry/PL0，80 GiB 起
- 适用：短时间 smoke test、学习 Docker Compose、验证 API 是否能跑
- 风险：Milvus + PostgreSQL + MinIO 同机运行时内存余量很小，可能 OOM 或启动慢

### 方案 B：推荐性价比

- ECS：`ecs.e-c1m4.xlarge`，4 vCPU / 16 GiB
- 磁盘：系统盘 40-60 GiB，数据盘 80-100 GiB，ESSD Entry 或 ESSD PL0
- 带宽：按使用流量，3-5 Mbps 起步即可
- 适用：当前 Phase 1 全栈部署、学习服务器、跑 health/readiness/smoke test
- 风险：共享型 CPU 高负载下性能波动，不适合正式生产

### 方案 C：更稳定测试环境

- ECS：`ecs.u1-c1m4.xlarge` 或 `ecs.u2i-c1m4.xlarge`，4 vCPU / 16 GiB
- 磁盘：ESSD PL0/ESSD Entry，100 GiB 起
- 适用：长期测试、演示、多人访问、真实知识库导入
- 风险：成本高于经济型 e

## 你需要准备的东西

- 阿里云账号，并完成实名认证。
- 账户余额、代金券或支付方式；按量付费创建 ECS 时购买页可能要求账户余额和代金券合计不低于 100 元。
- 一台 ECS：建议先按量付费。
- 一个 SSH 密钥对，下载并保存 `.pem` 私钥。
- 本机 SSH 客户端：Windows PowerShell 自带 `ssh` 通常够用；也可以用阿里云 Workbench。
- 项目代码获取方式：Git 仓库地址，或由本机 `scp` 上传。
- 如需域名访问：中国内地服务器 + 域名通常需要 ICP 备案；只用公网 IP 做早期测试可以先不处理域名。
- 后续真实 AI/RAG：还要准备模型/Embedding API 账号，例如阿里云百炼/通义千问等；当前 smoke test 不依赖模型 API。
- 后续真实 SSO：需要学校 IT 提供测试账号、回调地址、签名/票据校验规则或接口文档。

## 具体操作流程

### 1. 购买 ECS

在阿里云 ECS 控制台选择“自定义购买”：

1. 地域：优先选择离你和目标用户近的中国内地域，例如华东/华南；只做学习可选库存和价格合适的地域。
2. 付费：先选按量付费。
3. VPC/交换机：没有就新建默认 VPC 和交换机。
4. 实例规格：推荐 `ecs.e-c1m4.xlarge`。
5. 镜像：Alibaba Cloud Linux 3 64 位，或 Ubuntu LTS。为了跟阿里云文档更一致，推荐 Alibaba Cloud Linux 3。
6. 存储：系统盘 40-60 GiB；建议加 80-100 GiB 数据盘存 Docker 数据。
7. 公网 IP：分配公网 IP，带宽按使用流量，3-5 Mbps 起步。
8. 安全组：先只开放 SSH 22 到你的当前公网 IP；临时测试可开放 8000 到你的 IP。不要开放 PostgreSQL 5432、Redis 6379、MinIO 9000/9001、Milvus 19530 到公网。
9. 登录凭证：使用密钥对，保存 `.pem`。

### 2. 登录服务器

优先用阿里云 Workbench。也可以在本机 PowerShell：

```powershell
ssh -i C:\path\to\your.pem ecs-user@<ECS公网IP>
```

如果镜像默认用户不是 `ecs-user`，按购买页提示使用 `root` 或实际用户名。

### 3. 初始化数据盘

如果买了数据盘，登录后先查看盘名：

```bash
lsblk
```

假设新盘是 `/dev/vdb`，初始化并挂载到 `/data`：

```bash
sudo mkfs.ext4 /dev/vdb
sudo mkdir -p /data
sudo mount /dev/vdb /data
sudo blkid /dev/vdb
```

把 `UUID=... /data ext4 defaults,nofail 0 2` 写入 `/etc/fstab`，再验证：

```bash
sudo mount -a
df -h
```

### 4. 安装 Docker 和 Compose

Alibaba Cloud Linux 3 按官方文档安装 Docker 和 Compose plugin。关键验证命令：

```bash
sudo systemctl enable --now docker
docker --version
docker compose version
```

如果用数据盘，建议把 Docker 数据目录放到 `/data/docker`：

```bash
sudo systemctl stop docker
sudo mkdir -p /data/docker
sudo tee /etc/docker/daemon.json >/dev/null <<'EOF'
{
  "data-root": "/data/docker",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  }
}
EOF
sudo systemctl start docker
docker info | grep "Docker Root Dir"
```

### 5. 上传或拉取项目

如果项目在 Git：

```bash
sudo dnf install -y git
git clone <your-repo-url>
cd agentproject/backend
```

如果不想配置 Git，可从本机上传 `backend/`：

```powershell
scp -i C:\path\to\your.pem -r C:\Users\liuqi\Desktop\agentproject\backend ecs-user@<ECS公网IP>:~/agentproject/
```

### 6. 配置环境变量

```bash
cd ~/agentproject/backend
cp .env.example .env
```

必须改：

- `POSTGRES_PASSWORD`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `API_BIND_HOST=0.0.0.0`，仅用于临时公网 API 测试
- `CORS_ORIGINS=http://<ECS公网IP>:8000`

保持这些内部组件不要公网暴露：

- `POSTGRES_BIND_HOST=127.0.0.1`
- `REDIS_BIND_HOST=127.0.0.1`
- `MINIO_BIND_HOST=127.0.0.1`
- `MILVUS_BIND_HOST=127.0.0.1`

### 7. 启动服务

```bash
docker compose -f docker-compose.phase1.yml up -d --build
docker compose -f docker-compose.phase1.yml ps
```

Milvus 第一次启动可能要等 1-3 分钟。看日志：

```bash
docker compose -f docker-compose.phase1.yml logs -f milvus
docker compose -f docker-compose.phase1.yml logs -f api
```

### 8. 服务器本机验证

```bash
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8000/api/v1/readiness
```

期望：

- health 能返回 API 存活。
- readiness 能连通 PostgreSQL、Redis、MinIO、Milvus。

### 9. 浏览器访问

临时测试时，安全组开放 `8000` 给你的 IP，然后浏览器打开：

```text
http://<ECS公网IP>:8000/api/v1/health
```

长期演示不建议直接暴露 8000。更合理做法是后续加 Nginx + HTTPS，只开放 80/443。

### 10. 跑项目 smoke test

在服务器上跑：

```bash
cd ~/agentproject/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python scripts/smoke_phase1.py
```

通过标准：health/readiness 正常，smoke 脚本能完成写入、读取、搜索和清理。

## 主要困难与处理策略

- Milvus 吃内存：8 GiB 是最低线，推荐 16 GiB。若 OOM，先升级规格到 4c16G，不要在 2c4G 上浪费时间。
- 镜像拉取失败：当前 compose 已对 Milvus 使用 DaoCloud 镜像，但 MinIO 仍来自 `quay.io`，中国内地网络可能不稳定。后续可通过 `.env` 的镜像变量替换为可访问镜像源。
- 安全组配置：服务打不开时先查安全组，再查 Docker 端口绑定，再查容器日志。安全组不要把数据库/Redis/Milvus/MinIO 开到公网。
- 域名和备案：中国内地 ECS 绑定域名提供网站服务时需要 ICP 备案；早期测试用公网 IP 可先绕开域名流程。
- 数据持久化：Docker volume 在服务器本地，删除 volume 会丢数据；后续需要快照/备份策略。
- 当前业务层仍是内存实现：即使 PostgreSQL/Milvus 能跑，业务 Phase 1 的用户、问答、知识维护等还不是最终持久化合同，重启后业务内存数据会丢。
- 代码部署风险：`backend/` 目前没有 `.dockerignore`，Docker build 会把 `.env`、缓存目录等一起送入构建上下文。正式上服务器前建议先补 `.dockerignore`。

## 后续开发建议

1. 先补 `.dockerignore`，避免 `.env` 和缓存进入镜像构建上下文。
2. 写一份 `docs/ALIYUN_DEPLOYMENT.md`，把上面流程变成项目内正式手册。
3. 增加服务器部署专用 `.env.aliyun.example`。
4. 增加 `make phase1-up` / `make phase1-smoke` 或 PowerShell 脚本，减少手工命令错误。
5. 后续再做 Nginx + HTTPS + 域名/备案路线。
6. 再进入 PostgreSQL 持久化、真实知识导入、模型 API、SSO 对接。

## 参考资料

- 阿里云 ECS 控制台自定义购买 Linux 实例：<https://help.aliyun.com/zh/ecs/getting-started/create-and-manage-an-ecs-instance-by-using-the-ecs-console>
- 阿里云 ECS 自定义购买实例：<https://help.aliyun.com/zh/ecs/user-guide/create-an-instance-by-using-the-wizard/>
- 阿里云共享型/经济型 e 实例规格：<https://help.aliyun.com/zh/ecs/user-guide/shared-instance-families>
- 阿里云通用算力型 U 实例规格：<https://help.aliyun.com/zh/ecs/user-guide/general-work-force>
- 阿里云安全组使用：<https://help.aliyun.com/zh/ecs/user-guide/start-using-security-groups>
- 阿里云安装 Docker 和 Docker Compose：<https://help.aliyun.com/zh/ecs/use-cases/install-and-use-docker>
- 阿里云初始化 Linux 数据盘：<https://help.aliyun.com/zh/ecs/user-guide/initialize-a-data-disk-whose-size-does-not-exceed-2-tib-on-a-linux-instance/>
- 阿里云 ICP 备案说明：<https://help.aliyun.com/zh/icp-filing/product-overview/what-is-an-icp-filing>
- Milvus Standalone Docker Compose 安装要求：<https://milvus.io/docs/prerequisite-docker.md>
