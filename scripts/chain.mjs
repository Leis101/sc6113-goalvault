import ganache from 'ganache';
const server=ganache.server({chain:{chainId:31337,hardfork:'shanghai'},wallet:{deterministic:true},logging:{quiet:true}});
await server.listen(8545,'127.0.0.1');
console.log('LOCAL TEST CHAIN ONLY: http://127.0.0.1:8545 / chain 31337');
console.log('Ephemeral chain: restarting deletes all state. Redeploy after restarting.');
// These are throwaway local-test keys, never use them on public networks.
for(const [address,a] of Object.entries(server.provider.getInitialAccounts()).slice(0,2)) console.log(address,a.secretKey);
