from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("ReportSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("ReportSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily("ReportSans",normal="ReportSans",bold="ReportSans-Bold",italic="ReportSans",boldItalic="ReportSans-Bold")
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from PIL import Image as PILImage
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'report/SC6113_GoalVault_Report.pdf'
gas=json.loads((ROOT/'evidence/gas-results.json').read_text())
ui=json.loads((ROOT/'evidence/browser-results.json').read_text())
history=json.loads((ROOT/'evidence/ui-chain-history.json').read_text())
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyX',fontName='ReportSans',fontSize=9.6,leading=14,spaceAfter=9,textColor=colors.HexColor('#23302b')))
styles.add(ParagraphStyle(name='TitleX',fontName='ReportSans-Bold',fontSize=26,leading=30,spaceAfter=14,textColor=colors.black))
styles.add(ParagraphStyle(name='H1X',fontName='ReportSans-Bold',fontSize=16,leading=20,spaceBefore=9,spaceAfter=10,textColor=colors.black))
styles.add(ParagraphStyle(name='H2X',fontName='ReportSans-Bold',fontSize=11.5,leading=15,spaceBefore=8,spaceAfter=7,textColor=colors.black))
styles.add(ParagraphStyle(name='SmallX',fontName='ReportSans',fontSize=8.3,leading=11.5,spaceAfter=7,textColor=colors.HexColor('#506158')))
styles.add(ParagraphStyle(name='CellX',fontName='ReportSans',fontSize=8.2,leading=11.5,spaceAfter=0))
styles.add(ParagraphStyle(name='RefX',fontName='ReportSans',fontSize=8.2,leading=11,spaceAfter=6,wordWrap='CJK'))
W=A4[0]-100
story=[]
def p(t,style='BodyX'): story.append(Paragraph(t,styles[style]))
def h(t):p(t,'H1X')
def sub(t):p(t,'H2X')
def page():story.append(PageBreak())
def table(headers,rows,widths):
 data=[[Paragraph('<b>'+escape(str(x))+'</b>',styles['CellX']) for x in headers]]+[[Paragraph(escape(str(x)),styles['CellX']) for x in row] for row in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eee8')),('GRID',(0,0),(-1,-1),.45,colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
 story.extend([t,Spacer(1,10)])
def screenshot(name,box,outname,width=W):
 im=PILImage.open(ROOT/'evidence'/name);im=im.crop(box);out=ROOT/'report'/outname;im.save(out);story.append(Image(str(out),width=width,height=width*im.height/im.width));story.append(Spacer(1,6))
def footer(c,d):
 c.setFont('ReportSans',8);c.setFillColor(colors.HexColor('#607568'));c.drawString(50,30,'SC6113  |  GoalVault Financial DApp');c.drawRightString(A4[0]-50,30,f'{d.page} / 7')

p('GoalVault Financial DApp','TitleX')
p('Time locked savings with owner controlled withdrawals','H2X')
p('SC6113 Individual Assignment  |  Implementation and evaluation  |  10 October 2026','SmallX')
h('1 Introduction')
p('GoalVault is a financial decentralized application that turns a savings intention into an enforceable release schedule. A user connects an Ethereum wallet, creates a goal, deposits test ETH and withdraws the recorded balance after a chosen time. The application combines a Solidity contract, a Python Flask backend and a responsive browser interface. It demonstrates programmable custody and verifiable transaction records without an administrator who can spend user deposits.')
p('The implemented lifecycle has been executed on a local Ethereum-compatible chain. The evidence consists of 27 passing contract/backend tests, 13 passing browser checks, transaction receipts and screenshots. The browser automation uses an EIP-1193 test adapter; actual MetaMask extension interaction and Sepolia deployment remain separate manual acceptance steps. This distinction limits the claims made about deployment and usability.')
h('2 Problem Statement')
p('A student saving for a course or equipment purchase may want money reserved until a known date. A spreadsheet can track progress but cannot enforce the reservation. A custodial application can enforce restrictions, but its operator controls the ledger and may hold the funds. GoalVault explores a narrower alternative: a publicly inspectable contract enforces a rule agreed by the depositor, while only that depositor can request a release.')
p('The design deliberately separates the target amount from the release condition. A user who saves 0.02 ETH toward a 0.05 ETH target can still recover the full 0.02 ETH after maturity. Requiring the target to be met could trap an underfunded goal indefinitely. Conversely, early withdrawal is unavailable: this makes the commitment meaningful but unsuitable for emergency reserves. No interest, purchasing-power protection or investment return is promised.')
h('3 Objectives')
table(['Objective','Acceptance criterion'],[
('Owner control','A different wallet cannot deposit into or withdraw from a goal.'),
('Enforced savings rule','Positive deposits are accepted before release; withdrawals are blocked until maturity.'),
('Usable full-stack workflow','Connect a wallet, create a goal, deposit, withdraw and view confirmed history.'),
('Verifiable implementation','Provide executable tests, real local-chain evidence and reproducible setup instructions.')],[135,W-135])
p('Scope: native test ETH, one contract per configured network and independent goals per wallet. The original contribution is the integrated coursework implementation and explicit time-versus-target behavior, rather than a claim to invent a new DeFi primitive.','SmallX')
page()

h('4 System Architecture')
p('The contract is the authoritative record of ownership, balances and release times. The backend reads that record; it never signs transactions or receives private keys. The wallet authorizes each write independently. A blockchain transaction can therefore remain valid even if the read service later becomes unavailable, although the supplied interface depends on that service for configuration and display.')
d=Drawing(W,180)
def box(x,y,w,h,label,small):
 d.add(Rect(x,y,w,h,strokeColor=colors.HexColor('#c9d6cc'),fillColor=colors.HexColor('#f1f5f1'),radius=5));d.add(String(x+w/2,y+h-22,label,textAnchor='middle',fontName='ReportSans-Bold',fontSize=10));d.add(String(x+w/2,y+16,small,textAnchor='middle',fontName='ReportSans',fontSize=8))
def arrow(x1,y1,x2,y2):
 d.add(Line(x1,y1,x2,y2,strokeColor=colors.HexColor('#537761'),strokeWidth=1));
 if y1==y2:d.add(Polygon([x2,y2,x2-6,y2+3,x2-6,y2-3],fillColor=colors.HexColor('#537761'),strokeColor=None))
 else:d.add(Polygon([x2,y2,x2-3,y2+6,x2+3,y2+6],fillColor=colors.HexColor('#537761'),strokeColor=None))
box(0,108,160,62,'Browser interface','Forms, status and event history');box(W-160,108,160,62,'Python Flask backend','Read-only API and static assets');box(0,4,160,62,'Wallet provider','Account approval and signing');box(W-160,4,160,62,'Ethereum contract','Balances, rules and event logs')
arrow(160,140,W-160,140);d.add(String(W/2,150,'HTTP reads',textAnchor='middle',fontSize=8));arrow(80,108,80,66);d.add(String(90,83,'EIP-1193',fontSize=8));arrow(W-80,108,W-80,66);d.add(String(W-69,84,'RPC reads',fontSize=8));arrow(160,36,W-160,36);d.add(String(W/2,46,'Signed writes',textAnchor='middle',fontSize=8));story.append(d)
p('Figure 1. Read and write paths have different trust responsibilities. The wallet signs; the backend only reads.','SmallX')
p('For a deposit, the browser parses an ETH decimal into integer wei, asks the wallet to send deposit(id) with value, and shows the transaction hash while waiting for a receipt. After a successful mined receipt it reloads goals and event history through the backend. Public-chain deployments additionally link transaction hashes to the configured Sepolia explorer. A mined receipt is not represented as irreversible finality.')
h('5 Technologies Used')
table(['Component','Implementation and purpose'],[
('Smart contract','Solidity 0.8.30; optimizer 200 runs; Shanghai EVM target; standalone source.'),
('Web and backend','Python 3.12, Flask 3.1.2, web3.py 7.14.0 and Gunicorn 23.0.0; HTML/CSS/JS and ethers 6.15.0.'),
('Wallet protocol','Injected EIP-1193 provider; account requests, chain checks and change events [2].'),
('Local verification','Ganache 7.9.2, Node test runner and Playwright 1.56.1; local chain ID 31337.'),
('Public test option','Sepolia, chain ID 11155111; manual Remix/MetaMask instructions supplied [4].')],[130,W-130])
p('Render uses Gunicorn to serve Flask [6]. The included render.yaml specifies a free Python web service; a live URL has not yet been created.','SmallX')
p('No database is required: contract storage and event logs supply persistent records for a running chain. The local test chain is intentionally ephemeral. Ganache is pinned for reproducibility, but its repository is archived; migration to maintained tooling is a future maintenance task [5].')
page()

h('6 Smart Contract Design')
p('Each Goal stores owner, label, target, balance, unlockAt and closed. A global ID identifies each goal; an owner-to-ID array enables bounded reads without scanning every user. totalLiabilities records the sum of all withdrawable goal balances. Owner checks use msg.sender, so backend requests cannot confer spending authority.')
table(['Function','Checks and state transition'],[
('createGoal','Label is 1–64 UTF-8 bytes; target > 0; release is 60 seconds to 365 days ahead. Store a new goal and emit GoalCreated.'),
('deposit','Require owner, open goal, time before release and value > 0. Increase goal balance and total liabilities; emit Deposited.'),
('withdraw','Require owner, open goal and maturity. Set balance to zero, close goal, reduce liabilities, emit Withdrawn and transfer the prior balance.')],[105,W-105])
p('An open goal accepts deposits until its release timestamp. At maturity it becomes withdrawable without a separate state-changing transaction. After withdrawal it is permanently closed. An empty mature goal can also close. Targets are advisory, so overfunding is accepted and underfunding never blocks a mature withdrawal. There is no administrator, fee recipient, upgrade mechanism or early-release override.')
sub('Accounting and external calls')
p('The tested invariant is that the sum of goal balances equals totalLiabilities, and contract ETH assets are at least that liability. Equality with actual ETH is not assumed because ETH can be forced into a contract independently of the deposit function. Ordinary unsolicited transfers revert. Forced surplus has no withdrawal path in this minimal design.')
p('Withdrawal follows checks-effects-interactions: the contract validates authority and time, clears the balance and liability, then calls the owner. A shared reentrancy guard covers every state-changing entry point. If the recipient rejects ETH, TransferFailed reverts the complete transaction, including balance changes and events. The owner can retry if the receiving behavior is repaired. This implements the external-call precautions described in the Solidity guidance [1].')
sub('Validation and gas considerations')
p('Custom errors identify invalid labels, targets, release times, owners, closed goals, zero deposits and failed transfers. Solidity checked arithmetic and integer wei avoid floating-point accounting. Release time uses block.timestamp, not the browser clock; the interface adds a time margin because transaction inclusion is not instantaneous.')
p('All three write functions operate on a single goal without looping over all users. Short labels limit storage growth, and uint64 unlockAt shares a storage slot with the closed flag. Owner history is queried in pages. The optimizer is enabled, but no claim of globally optimal gas usage is made; the measured samples are reported in Section 9.')
page()

h('7 Application Design')
p('The interface groups goal creation, savings progress and transaction history on one screen. A lock acknowledgement appears before goal creation, alongside a test-ETH and public-data notice. Progress cards show balance, target, release time and lifecycle state. Only actions appropriate to the chain snapshot are offered. The contract still validates every request independently.')
screenshot('01-local-funded-goal.png',(80,410,1290,1030),'funded-detail.png')
p('Figure 2. Actual local-chain browser run: a 0.05 ETH goal holds 0.02 ETH and remains locked. The automated wallet interface is a test adapter, not the MetaMask extension.','SmallX')
h('8 Implementation')
p('The browser uses ethers BrowserProvider and a wallet-backed signer [3]. It checks the configured chain before connection and before sending transactions. Account, chain and disconnect events clear stale state and require reconnection. Amounts reject negatives, exponent notation and more than 18 decimal places. Goal labels are rendered as text nodes, preventing label content from becoming executable HTML.')
p('The transaction status distinguishes wallet approval, pending hash, mined success and failure. Wallet rejection returns an actionable message. A two-minute confirmation timeout warns that a transaction may still be pending, discouraging accidental resubmission. Replacement transactions can resolve to the replacement receipt; a confirmed write is distinguished from a later display-refresh failure.')
p('The Flask backend verifies chain ID and exact compiled runtime bytecode before returning blockchain data. Its GET-only APIs validate addresses and range parameters, return at most 20 goals per page, and read each goal page at one block snapshot. History filters contract logs by the owner topic over windows of up to 2,000 blocks, with an older-range cursor. RPC errors return HTTP 503 without exposing credentials. The server supplies security headers and serves ethers locally, avoiding a runtime CDN dependency.')
page()

h('9 Testing and Results')
p('Tests ran against a local EVM with Solidity 0.8.30, Node.js 24.19.0 and Python 3.12. The contract/backend suites passed 27 of 27 cases; the browser suite passed 13 of 13 checks. These are functional checks, not an independent security audit or evidence of public-network performance.')
table(['Coverage','Observed result and evidence'],[
('Contract lifecycle and inputs','18 contract tests passed: deployment, ownership, bounds, deposits, maturity, closing, failed transfers, reentrancy and balance invariants.'),
('Backend integration','9 Flask tests passed: live reads, owner-filtered events, input validation, read-only routes, assets, headers and readiness failures.'),
('Browser workflow','13 Flask/Gunicorn browser checks passed, including create/deposit/withdraw, missing wallet, rejection, wrong chain, invalid amounts, reload and account change.'),
('Responsive layout','A 390px viewport had no horizontal page overflow; a full mobile screenshot is included. No user study was conducted.'),
('Manual acceptance','Real MetaMask prompts and Sepolia deployment were not executed. README provides the remaining verification procedure.')],[120,W-120])
p('The browser run created goal #0 in block 2, deposited 0.02 ETH in block 3, advanced the local clock, and withdrew in block 5. The final balance was zero and the goal was closed. The target remained 0.05 ETH, demonstrating that maturity, rather than target completion, governs withdrawal. Reloading rebuilt history from chain logs.')
screenshot('02-local-withdrawn-goal.png',(105,1053,1265,1345),'withdraw-history.png')
p('Figure 3. Actual local event history after withdrawal. Local time advancement is a test facility and is not available to application users on Sepolia. Full-size screenshots and transaction hashes are retained in evidence/.','SmallX')
table(['Sample transaction','Gas units'],[(k.capitalize(),f'{int(v):,}') for k,v in gas.items()],[W-130,130])
p('Gas values are individual successful receipts from the contract test run, not averages. Create is the final helper-created goal; deposit and withdrawal are the named recorded samples in contract.test.mjs. Costs vary with storage state and label length. Local mining speed was not used to estimate Sepolia latency or throughput.','SmallX')
page()

h('10 Challenges Encountered')
sub('Timing and reproducible tests')
p('A test initially scheduled a goal exactly 60 seconds after the latest block. By the time the transaction was mined, the next block could have advanced by a second, making that timestamp too short. Lifecycle tests were changed to use a 120-second margin; exact minimum and maximum bounds are checked through simulation against the current block. The interface likewise requires a margin rather than promising a boundary-time transaction will succeed.')
sub('Separating financial state from display state')
p('A wallet can change accounts or networks while a read is in flight. The frontend increments a session generation on change and ignores stale read responses. It also disables write buttons during a transaction. Monetary values stay as bigint or decimal strings through the contract/API path; conversion to a Number is limited to visual progress and timestamps, not transfer amounts.')
sub('Making failure evidence meaningful')
p('Input validation alone does not prove that contract rules hold. Tests therefore send an actual early-withdrawal transaction with an explicit gas limit and verify that its mined receipt reverts without releasing funds. Separate malicious receiver contracts attempt a callback withdrawal or reject the ETH transfer. The tests verify single payment and complete accounting rollback, respectively.')
h('11 Limitations')
p('The current evidence establishes the local functional lifecycle and browser-provider integration. It does not establish successful use of the real MetaMask extension, public RPC reliability, Sepolia finality, or deployed HTTPS hosting. The supplied manual procedure is therefore an acceptance task rather than a completed result. No questionnaire or real-user usability study was performed.')
p('GoalVault provides no interest or stable fiat value. ETH volatility, transaction fees, lost keys and irreversible lock commitments limit financial suitability. It has no emergency unlock, recovery administrator or insurance. Contract wallets that cannot receive ETH may be unable to withdraw. Public labels and balances are visible to others; this design offers transparency rather than financial confidentiality.')
p('The API still depends on a trusted display/configuration service and RPC provider. Event windows reduce query size but are not a durable reorganization-aware indexer. The UI does not persist pending or failed transaction history across reloads. Production rate limiting, load testing, dependency hardening and an independent audit are not complete. A passing test suite cannot exclude untested vulnerabilities.')
h('12 Future Improvements')
p('The first priority is to complete real-wallet and Sepolia acceptance with deployment receipts and screenshots. Next steps are maintained local-chain tooling, fuzzed accounting invariants, a reorganization-aware event index with durable pending-status tracking, and public-hosting operational controls. ERC-20 support or optional recovery rules would require a separate threat model and contract version; adding them casually would change the custody promise.')
page()

h('13 Conclusion')
p('GoalVault implements a complete local financial DApp lifecycle with contract-enforced release rules, wallet-authorized writes and a backend that reconstructs state and history from the blockchain. The central design decision is that a savings target measures progress while time controls withdrawal. This avoids trapping an underfunded goal while preserving the agreed lock period.')
p('The local evidence supports the implemented ownership rules, accounting, failure handling and end-to-end web workflow: 27 contract/backend tests and 13 browser checks passed. The result remains a coursework prototype. Actual MetaMask interaction, Sepolia deployment and the Render URL remain pending. Repository access and workspace confirmation are required to deploy.')
sub('Reproducibility and evidence index')
table(['File or command','Purpose'],[
('pip install -r requirements.txt; npm ci; npm run compile','Install Python and Node dependencies; reproduce ABI and bytecode.'),
('npm run chain; npm run deploy:local; python app.py','Start the ephemeral local chain, deploy the contract and serve the DApp.'),
('npm test; npm run test:ui','Execute isolated contract/API tests and browser lifecycle checks.'),
('evidence/test-results.txt','18 contract tests plus 9 passing Python Flask integration tests.'),
('evidence/browser-results.json','13 browser checks with an explicit local test-provider scope.'),
('evidence/ui-chain-history.json','Actual deployment and create/deposit/withdraw transaction hashes.'),
('README.md and START_HERE_CN.md','Setup, MetaMask connection, Sepolia deployment and remaining acceptance steps.')],[200,W-200])
p('The source includes .sol, standalone abi.json, app.py, requirements.txt, HTML/CSS/JS, render.yaml, tests and screenshots. No database or video is needed. Full-size evidence images supplement the cropped figures in this report. The test adapter is confined to the test harness; the application itself expects an injected wallet provider.','SmallX')
sub('References')
refs=[
('[1] Solidity contributors. Security Considerations.','https://docs.soliditylang.org/en/latest/security-considerations.html'),
('[2] Ethereum Improvement Proposals. EIP-1193 Ethereum Provider JavaScript API.','https://eips.ethereum.org/EIPS/eip-1193'),
('[3] ethers. Version 6 Providers documentation.','https://docs.ethers.org/v6/api/providers/'),
('[4] Ethereum.org. Networks.','https://ethereum.org/en/developers/docs/networks/'),
('[5] ConsenSys archive. Ganache repository and project status.','https://github.com/ConsenSys-archive/ganache'),
('[6] Render. Deploy a Flask App on Render.','https://render.com/docs/deploy-flask')]
for title,url in refs:p(escape(title)+'<br/><link href="'+url+'" color="#315e49">'+url+'</link>','RefX')
p('All web references accessed 10 October 2026. Implementation-specific claims are supported by the supplied source files and execution evidence, not by the reference documents.','SmallX')
SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=43,bottomMargin=49,title='GoalVault Financial DApp',author='SC6113 Individual Assignment').build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
