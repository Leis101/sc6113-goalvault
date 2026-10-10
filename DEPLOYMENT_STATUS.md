# Deployment status

The Flask application, standalone ABI, frontend, dependencies and Render configuration are ready.

**Actual Render URL: not available yet.** No service deployment has been performed for this project.

To proceed:

1. Confirm the Render workspace: the connected account lists `SC6113`.
2. Provide a GitHub/GitLab/Bitbucket repository containing this code. You can upload the files through the provider website; no ChatGPT GitHub plugin is required.
3. Deploy GoalVault on Sepolia using MetaMask and provide the public contract address and deployment block. Configure a Sepolia RPC endpoint in Render.

Never send wallet recovery phrases or private keys. A public contract address and transaction hash are sufficient to identify the deployment.

After deployment, record the real Render URL and verify both `/healthz` and `/api/health`. A configured service should show the Sepolia contract, support MetaMask connection and complete a create/deposit/withdraw cycle.
