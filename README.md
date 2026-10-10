# GoalVault — SC6113 Financial DApp

Solidity + standalone ABI + Python Flask + HTML/CSS/JavaScript + MetaMask.
The production backend is now Python Flask; Node.js is only needed to compile the contract and run local-chain tests.

## Submission file map

| Required item | File |
|---|---|
| Solidity | `contracts/GoalVault.sol` |
| ABI JSON array | `abi.json` |
| Python Flask | `app.py`, `requirements.txt` |
| HTML | `templates/index.html` |
| CSS | `static/style.css` |
| JavaScript | `static/app.js` |
| Render configuration | `render.yaml` |
| Report | `report/SC6113_GoalVault_Report.pdf` |
| Render URL | Pending actual deployment; see `DEPLOYMENT_STATUS.md` |

## Environment

Python 3.12 and Node.js 22+ are recommended. Install the official MetaMask extension in Chrome or another supported desktop browser. No private key is stored or handled by Flask. The browser uses a locally vendored ethers 6.15.0 bundle, with its MIT license in `static/vendor/`.

Ganache 7.9.2 is pinned for local coursework tests and is archived upstream. A uWS native-module warning under Node.js 24 falls back to JavaScript and does not prevent the included tests. The lockfile marks the bundled macOS-only fsevents watcher as optional for Linux compatibility.

## Local setup

From the project root:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci
npm run compile
```

Windows PowerShell activation is `.venv\Scripts\Activate.ps1`. Browser test orchestration defaults to `python3`; on Windows set `PYTHON` to your virtual environment's Python executable.

Terminal 1, keep it running:

```sh
npm run chain
```

Terminal 2, from the same project folder:

```sh
source .venv/bin/activate
npm run deploy:local
python app.py
```

Visit http://localhost:3000. The chain script prints throwaway local test accounts. Import one into a separate test-only MetaMask profile. These are publicly known development keys; never use them for real funds. Add the local network with RPC `http://127.0.0.1:8545`, chain ID `31337`, currency `ETH`. Select that network and account, then click **Connect MetaMask**.

Create a `Learning fund` goal with target `0.05` ETH and a release time 5–10 minutes ahead. Acknowledge the lock, approve the create transaction, deposit `0.02` ETH and approve again. Wait until release, refresh and withdraw. The target is informational: maturity permits full withdrawal even if the target is not met.

Stopping the local chain discards state. Restart it, rerun `npm run deploy:local`, and restart Flask. If MetaMask cached old local-network nonces, reset only that test network's activity as appropriate.

## Verify the implementation

Activate the Python virtual environment before running:

```sh
npm test
npx playwright install chromium
npm run test:ui
```

- 18 contract tests run on an isolated real local EVM.
- 9 Python Flask integration tests query a real local EVM fixture.
- 13 browser checks exercise the actual Flask/Gunicorn service and local EVM through an explicitly injected EIP-1193 test adapter. They are not actual MetaMask extension tests.

`PYTHON=/absolute/path/to/python` selects a Python executable for subprocesses. `CHROMIUM_PATH` can select a compatible existing Chromium. Report generation is optional and separate from running the DApp; `report/build_report.py` needs reportlab, Pillow and the specified fonts.

## Deploy the contract on Sepolia

1. Use a test-only MetaMask wallet on Sepolia and obtain faucet test ETH.
2. Open https://remix.ethereum.org, copy `contracts/GoalVault.sol` into a file named exactly `GoalVault.sol`.
3. Compile with Solidity **0.8.30**, optimizer **200 runs**, EVM **Shanghai**. Keep the filename and source content unchanged so compiled runtime metadata matches the bundled artifact.
4. Select the injected MetaMask provider in Remix; verify chain ID **11155111**. Deploy GoalVault (no constructor arguments), approve and wait for the receipt.
5. Retain the actual contract address, deployment block and transaction hash. Do not reuse local test hashes as Sepolia evidence.

Configure Flask with these actual values, using `.env` locally or Render's Environment settings:

```text
RPC_URL=https://YOUR_SEPOLIA_RPC_ENDPOINT
CHAIN_ID=11155111
CONTRACT_ADDRESS=0xYOUR_ACTUAL_CONTRACT_ADDRESS
DEPLOYMENT_BLOCK=ACTUAL_BLOCK_NUMBER
```

Flask checks chain ID and the exact deployed runtime bytecode before returning contract data. A wrong chain, missing configuration or mismatched artifact returns 503; it never returns invented balances. Use the exact compiler settings and source path if metadata differs. Never disable validation to bypass a mismatch.

## Deploy Flask on Render

A GitHub/GitLab/Bitbucket repository accessible to Render is required. Put this project's contents at the repository root. Do not upload `node_modules`, `.venv`, `.env`, private keys or local deployment JSON.

Create a **Web Service**, choose the source repository, and set:

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Plan | Free |
| Region | Singapore |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120` |
| Health check | `/healthz` |

Set the four Sepolia environment variables above. `render.yaml` contains the equivalent Blueprint configuration. `RPC_URL` must be reachable from Render; `127.0.0.1:8545` points to Render itself, not your Mac. Keep RPC tokens private.

The frontend and ethers bundle are included, so Render's Python build does **not** require npm or a Node server. `/healthz` verifies that Flask is alive; `/api/health` additionally verifies the blockchain connection and bytecode. An HTTP 200 homepage by itself does not prove contract readiness. When the deployment becomes Live, record the actual `https://...onrender.com` service URL in `DEPLOYMENT_STATUS.md` and test create/deposit/withdraw through MetaMask on Sepolia.

No Render URL is claimed until a real deployment has completed. See https://render.com/docs/deploy-flask for the official deployment flow.

## API

All application APIs are read-only:

| Route | Result |
|---|---|
| `/healthz` | Flask process liveness |
| `/api/health` | Contract and chain readiness |
| `/api/config` | Public address, ABI, chain and explorer; no RPC credentials |
| `/api/goals/:address?offset=0` | Up to 20 goals at a consistent block snapshot |
| `/api/history/:address?to=N` | Owner-filtered events over up to 2,000 blocks, with older-range cursor |

Invalid inputs return 400, writes 405, unknown paths 404, unavailable blockchain 503. Flask serves HTML, CSS and JS with security headers and self-only CSP. The browser signs through MetaMask; Flask never signs or submits transactions on a user's behalf.

## Contract and security model

A goal requires a public 1–64 byte UTF-8 label, positive target and release 60 seconds to 365 days ahead. Only its owner can deposit before release or withdraw at maturity. Deposits must be positive. Targets do not cap deposits or prevent below-target withdrawal. Withdrawal transfers the full recorded balance and permanently closes the goal. There is no yield, admin withdrawal, upgrade, fee or emergency unlock.

Checks-effects-interactions and a shared reentrancy guard protect withdrawal. Rejected ETH transfers revert accounting atomically. Liabilities equal summed goal balances; actual contract assets must cover them. Forced ETH can create surplus, so equality with actual assets is not assumed. An owner contract that permanently rejects ETH cannot receive a withdrawal.

Use test ETH only. Labels, addresses and amounts are public. This is not an audited financial product. There is no key recovery, insurance, fiat-value guarantee, ERC-20 support, persistent pending transaction index, reorganization-aware database, production load test or mobile wallet deep linking. One mined confirmation is not irreversible settlement. An unavailable RPC/backend can prevent UI use even though custody is on chain.

## Evidence and remaining acceptance

`evidence/` contains actual tests, local receipts, gas observations and screenshots. The browser harness uses real local EVM transactions through a test provider. Manually capture real MetaMask approval screens and, if deploying publicly, Sepolia receipts and the actual Render URL. Do not label the automated adapter as MetaMask or local chain history as Sepolia history.

The supplied report is seven pages and reflects the Flask implementation and actual validation scope. No video is needed. Add your name/student ID if required by the submission portal.
