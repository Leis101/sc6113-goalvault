"""GoalVault Flask backend. Public blockchain reads only; never signs transactions."""
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from web3 import Web3
from web3._utils.events import get_event_data

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')


def create_app(settings=None):
    app = Flask(__name__)
    app.config.update(settings or {})
    artifact = json.loads((ROOT / 'artifacts/GoalVault.json').read_text())
    abi = json.loads((ROOT / 'abi.json').read_text())
    if abi != artifact['abi']:
        raise ValueError('ABI differs from compiled contract artifact')
    rpc_url = app.config.get('RPC_URL', os.getenv('RPC_URL', 'http://127.0.0.1:8545'))
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 15}))
    deployment_path = Path(app.config.get('DEPLOYMENT_FILE', os.getenv('DEPLOYMENT_FILE', 'deployment.local.json')))
    if not deployment_path.is_absolute():
        deployment_path = ROOT / deployment_path
    config = json.loads(deployment_path.read_text()) if deployment_path.exists() else {}
    for env, field in [('CONTRACT_ADDRESS', 'address'), ('CHAIN_ID', 'chainId'), ('DEPLOYMENT_BLOCK', 'deploymentBlock')]:
        value = app.config.get(env, os.getenv(env))
        if value is not None and str(value).strip():
            config[field] = value

    def checked_contract():
        # Fail closed: the web UI may load before deployment, but no fake balances are returned.
        if not Web3.is_address(config.get('address', '')):
            raise RuntimeError('Contract configuration is incomplete')
        chain_id = int(config.get('chainId', 0))
        block = int(config.get('deploymentBlock', -1))
        if chain_id not in (31337, 11155111) or block < 0:
            raise RuntimeError('Invalid chain configuration')
        address = Web3.to_checksum_address(config['address'])
        if w3.eth.chain_id != chain_id:
            raise RuntimeError('RPC chain does not match deployment')
        if bytes(w3.eth.get_code(address)) != bytes.fromhex(artifact['deployedBytecode'][2:]):
            raise RuntimeError('Deployed bytecode does not match GoalVault')
        return w3.eth.contract(address=address, abi=abi), address, chain_id, block

    def blockchain_unavailable():
        return jsonify(error='Blockchain not ready. Configure the deployed GoalVault address, chain, deployment block and RPC endpoint, then retry.'), 503

    @app.before_request
    def read_only():
        if request.method not in ('GET', 'HEAD'):
            return jsonify(error='Read-only API: method not allowed'), 405

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error='Not found'), 404

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.get('/app.js')
    def javascript():
        return send_from_directory(ROOT / 'static', 'app.js')

    @app.get('/style.css')
    def stylesheet():
        return send_from_directory(ROOT / 'static', 'style.css')

    @app.get('/vendor/ethers.js')
    def ethers_bundle():
        return send_from_directory(ROOT / 'static/vendor', 'ethers.js')

    @app.get('/healthz')
    def healthz():
        # Process liveness for Render. Blockchain readiness is /api/health.
        return jsonify(ok=True, backend='flask')

    @app.get('/api/config')
    def public_config():
        try:
            _, address, chain, block = checked_contract()
            return jsonify(address=address, chainId=chain, deploymentBlock=block, abi=abi,
                           networkName='Local test chain' if chain == 31337 else 'Sepolia',
                           explorer='' if chain == 31337 else 'https://sepolia.etherscan.io', historyWindow=2000)
        except Exception:
            return blockchain_unavailable()

    @app.get('/api/health')
    def blockchain_health():
        try:
            _, _, chain, _ = checked_contract()
            return jsonify(ok=True, chainId=chain, block=w3.eth.block_number, backend='flask')
        except Exception:
            return blockchain_unavailable()

    def integer(value, default, maximum=2**53-1):
        if value is None:
            return default
        if not re.fullmatch(r'[0-9]{1,16}', value) or int(value) > maximum:
            raise ValueError('Invalid range')
        return int(value)

    @app.get('/api/goals/<address>')
    def goals(address):
        if not Web3.is_address(address):
            return jsonify(error='Invalid wallet address'), 400
        try:
            offset = integer(request.args.get('offset'), 0)
        except ValueError:
            return jsonify(error='Invalid offset'), 400
        try:
            c, _, _, _ = checked_contract()
            owner = Web3.to_checksum_address(address)
            latest = w3.eth.get_block('latest')
            block = latest['number']
            count = c.functions.goalCount(owner).call(block_identifier=block)
            items = []
            for index in range(offset, min(count, offset + 20)):
                goal_id = c.functions.goalIdAt(owner, index).call(block_identifier=block)
                g = c.functions.goals(goal_id).call(block_identifier=block)
                items.append(dict(id=str(goal_id), owner=g[0], label=g[1], target=str(g[2]),
                                  balance=str(g[3]), unlockAt=str(g[4]), closed=g[5]))
            return jsonify(count=count, offset=offset, nextOffset=offset + 20 if offset + 20 < count else None,
                           block=block, chainTime=latest['timestamp'], items=items)
        except Exception:
            return blockchain_unavailable()

    event_abis = {bytes(Web3.keccak(text=e['name'] + '(' + ','.join(i['type'] for i in e['inputs']) + ')')): e
                  for e in abi if e['type'] == 'event'}

    @app.get('/api/history/<address>')
    def history(address):
        if not Web3.is_address(address):
            return jsonify(error='Invalid wallet address'), 400
        try:
            c, contract_address, _, first = checked_contract()
            latest = w3.eth.block_number
            try:
                end = integer(request.args.get('to'), latest, latest)
            except ValueError:
                return jsonify(error='Invalid block range'), 400
            if end < first:
                return jsonify(error='Range precedes deployment'), 400
            start = max(first, end - 1999)
            logs = w3.eth.get_logs({'address': contract_address, 'fromBlock': start, 'toBlock': end,
                                   'topics': [['0x' + t.hex() for t in event_abis], None,
                                              '0x' + address[2:].lower().rjust(64, '0')]})
            items = []
            for log in reversed(logs):
                event = get_event_data(w3.codec, event_abis[bytes(log['topics'][0])], log)
                args = event['args']
                items.append(dict(event=event['event'], goalId=str(args['id']),
                                  amount=None if event['event'] == 'GoalCreated' else str(args['amount']),
                                  hash=Web3.to_hex(log['transactionHash']), block=log['blockNumber'], index=log['logIndex'],
                                  confirmations=latest - log['blockNumber'] + 1))
            return jsonify({'from': start, 'to': end, 'nextTo': start - 1 if start > first else None, 'items': items})
        except Exception:
            return blockchain_unavailable()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host=os.getenv('HOST', '127.0.0.1'), port=int(os.getenv('PORT', '3000')), debug=False)
