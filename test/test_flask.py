"""Integration tests against the local EVM fixture started by test-flask.mjs."""
import json
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app

class FlaskIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({'TESTING': True})
        cls.client = cls.app.test_client()
        cls.owner = os.environ['TEST_OWNER']
        cls.other = os.environ['TEST_OTHER']

    def test_health_and_public_configuration(self):
        self.assertTrue(self.client.get('/healthz').json['ok'])
        self.assertEqual(self.client.get('/api/health').json['backend'], 'flask')
        cfg = self.client.get('/api/config').json
        self.assertEqual(cfg['chainId'], 31337)
        self.assertNotIn('RPC_URL', cfg)
        self.assertNotIn('privateKey', cfg)

    def test_goal_snapshot_and_decimal_wei(self):
        r = self.client.get('/api/goals/' + self.owner).json
        self.assertEqual(r['items'][0]['balance'], '25')
        self.assertEqual(r['items'][0]['label'], '<script>alert(1)</script>')
        self.assertGreater(r['chainTime'], 0)
        self.assertIsNone(r['nextOffset'])

    def test_owner_filtered_event_history(self):
        r = self.client.get('/api/history/' + self.owner).json
        self.assertEqual(len(r['items']), 2)
        self.assertEqual(r['items'][0]['event'], 'Deposited')
        self.assertEqual(r['items'][0]['amount'], '25')
        self.assertTrue(r['items'][0]['hash'].startswith('0x'))
        self.assertEqual(self.client.get('/api/history/' + self.other).json['items'], [])

    def test_invalid_inputs(self):
        for route in ['/api/goals/not-address','/api/goals/'+self.owner+'?offset=-1',
                      '/api/history/'+self.owner+'?to=999999', '/api/history/'+self.owner+'?to=0']:
            self.assertEqual(self.client.get(route).status_code, 400, route)

    def test_read_only_and_not_found(self):
        self.assertEqual(self.client.post('/api/config').status_code, 405)
        self.assertEqual(self.client.get('/secret').status_code, 404)

    def test_assets_and_security_headers(self):
        r = self.client.get('/')
        self.assertIn(b'Create a savings goal', r.data)
        self.assertIn("frame-ancestors 'none'", r.headers['Content-Security-Policy'])
        for route in ['/app.js','/style.css','/vendor/ethers.js']:
            with self.client.get(route) as response:
                self.assertEqual(response.status_code, 200)
        self.assertEqual(r.headers['X-Content-Type-Options'], 'nosniff')

    def test_wrong_chain_fails_closed(self):
        c = create_app({'CHAIN_ID':11155111}).test_client()
        self.assertEqual(c.get('/api/config').status_code, 503)
        self.assertEqual(c.get('/api/goals/'+self.owner).status_code, 503)

    def test_unconfigured_server_is_live_but_not_blockchain_ready(self):
        c = create_app({'DEPLOYMENT_FILE':'artifacts/does-not-exist.json'}).test_client()
        self.assertEqual(c.get('/').status_code, 200)
        self.assertEqual(c.get('/healthz').status_code, 200)
        self.assertEqual(c.get('/api/config').status_code, 503)
        self.assertEqual(c.get('/api/health').status_code, 503)

    def test_wrong_contract_bytecode_fails_closed(self):
        c = create_app({'CONTRACT_ADDRESS':self.other}).test_client()
        self.assertEqual(c.get('/api/config').status_code, 503)

if __name__ == '__main__':
    unittest.main(verbosity=2)
