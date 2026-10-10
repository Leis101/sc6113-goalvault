# SC6113 Flask 版本使用说明

## 本次已补齐

| 要求 | 文件 |
|---|---|
| Solidity | `contracts/GoalVault.sol` |
| 单独 ABI | `abi.json` |
| Python Flask | `app.py`、`requirements.txt` |
| HTML | `templates/index.html` |
| CSS | `static/style.css` |
| JavaScript | `static/app.js` |
| Render 部署配置 | `render.yaml` |

后端已经换成 Flask。Node.js 只用于合约编译、本地链和自动化测试，不再作为网站后端。Render 上按 Python 服务运行即可。

## Mac 本地启动

在 VS Code 打开解压后的 `goalvault` 文件夹，执行：

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci
npm run compile
```

终端一执行 `npm run chain` 并保持运行。

终端二进入同一文件夹后执行：

```sh
source .venv/bin/activate
npm run deploy:local
python app.py
```

浏览器打开 `http://localhost:3000`。

MetaMask 添加本地网络：RPC `http://127.0.0.1:8545`、链 ID `31337`、币种 ETH。将终端一显示的开发测试账号导入独立测试钱包。这些开发账号绝不能用于真钱。

连接钱包，创建目标：目标金额 `0.05` ETH，解锁时间选择 5–10 分钟后。批准创建交易，再存入 `0.02` ETH 并批准。到期后刷新并提款。目标未达成不影响到期提款。

## Render 在线链接仍需的条件

Render 需要从 GitHub／GitLab／Bitbucket 拉取代码。目前尚未提供项目仓库，尚未产生真实 Render URL。已连接的 Render 账号列出一个名为 SC6113 的工作区，还需要你确认使用它。

在线网页不能连接你 Mac 上的 `127.0.0.1:8545`。实际在线交易应使用 Sepolia 上已部署的合约，并在 Render 配置以下值：

- `RPC_URL`：可访问的 Sepolia RPC 地址；有密钥时只在 Render 环境变量中设置。
- `CHAIN_ID`：`11155111`。
- `CONTRACT_ADDRESS`：实际部署的合约地址。
- `DEPLOYMENT_BLOCK`：实际部署区块号。

合约通过 Remix 和 MetaMask 部署，详细步骤见 README。无需把钱包私钥或助记词发给任何人。

## Render 服务配置

- 类型：Web Service，Python 3，Free。
- Build：`pip install -r requirements.txt`。
- Start：`gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`。
- Health check：`/healthz`。

`/healthz` 成功表示 Flask 网站在运行；`/api/health` 成功才表示合约连接也正常。不能仅凭网页可打开就认为链上功能已完成。

## 测试和提交

激活虚拟环境后运行 `npm test`；浏览器测试先运行 `npx playwright install chromium`，再运行 `npm run test:ui`。

源码包包含真实本地链测试、Flask 接口测试及浏览器截图。自动化钱包接口不是实际 MetaMask 插件，仍需在自己的浏览器补充真实批准截图。报告已更新为 Flask 版本并如实说明验证范围。

最终提交 PDF、源码和真正部署成功后取得的 Render URL。当前 URL 状态见 `DEPLOYMENT_STATUS.md`。

## 不安装 GitHub 插件的上传方法

1. 在 GitHub 网页创建一个新的空仓库，例如 `sc6113-goalvault`。
2. 解压源码包，进入 `goalvault` 文件夹，把里面的文件和文件夹上传到仓库根目录。不要只上传 ZIP；根目录应该直接看到 `app.py`、`requirements.txt`、`render.yaml`。
3. 使用 GitHub 网页的文件上传功能提交这些文件。不要上传虚拟环境、node_modules、私钥或带密钥的环境配置。
4. 将仓库的网址发给我，并确认使用 Render 的 SC6113 工作区，我即可继续配置 Render。若是私有仓库，还需要你在 Render 网页授权读取该仓库。

这种方式无需在本应用安装 GitHub 插件。
