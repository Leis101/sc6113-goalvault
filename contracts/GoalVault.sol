// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

/// @title GoalVault - owner-controlled, time-locked test-ETH savings
/// @notice No yield, admin, upgrade, fees or early withdrawal. Goal labels are public.
contract GoalVault {
    uint256 public constant MIN_LOCK = 60;
    uint256 public constant MAX_LOCK = 365 days;
    struct Goal {
        address owner;
        string label;
        uint256 target;
        uint256 balance;
        uint64 unlockAt;
        bool closed;
    }
    uint256 public nextId;
    uint256 public totalLiabilities;
    mapping(uint256 => Goal) public goals;
    mapping(address => uint256[]) private owned;
    uint256 private entered = 1;
    error InvalidLabel();
    error InvalidTarget();
    error InvalidUnlock();
    error NotOwner();
    error Closed();
    error Locked();
    error Matured();
    error ZeroDeposit();
    error TransferFailed();
    error Reentrancy();
    event GoalCreated(uint256 indexed id, address indexed owner, string label, uint256 target, uint64 unlockAt);
    event Deposited(uint256 indexed id, address indexed owner, uint256 amount, uint256 balance);
    event Withdrawn(uint256 indexed id, address indexed owner, uint256 amount);

    modifier nonReentrant() {
        if (entered != 1) revert Reentrancy();
        entered = 2;
        _;
        entered = 1;
    }
    function createGoal(string calldata label, uint256 target, uint64 unlockAt)
        external nonReentrant returns (uint256 id)
    {
        if (bytes(label).length == 0 || bytes(label).length > 64) revert InvalidLabel();
        if (target == 0) revert InvalidTarget();
        if (unlockAt < block.timestamp + MIN_LOCK || unlockAt > block.timestamp + MAX_LOCK) revert InvalidUnlock();
        id = nextId++;
        goals[id] = Goal(msg.sender, label, target, 0, unlockAt, false);
        owned[msg.sender].push(id);
        emit GoalCreated(id, msg.sender, label, target, unlockAt);
    }
    function deposit(uint256 id) external payable nonReentrant {
        Goal storage g = goals[id];
        if (g.owner != msg.sender) revert NotOwner();
        if (g.closed) revert Closed();
        if (block.timestamp >= g.unlockAt) revert Matured();
        if (msg.value == 0) revert ZeroDeposit();
        g.balance += msg.value;
        totalLiabilities += msg.value;
        emit Deposited(id, msg.sender, msg.value, g.balance);
    }
    function withdraw(uint256 id) external nonReentrant {
        Goal storage g = goals[id];
        if (g.owner != msg.sender) revert NotOwner();
        if (g.closed) revert Closed();
        if (block.timestamp < g.unlockAt) revert Locked();
        uint256 amount = g.balance;
        g.balance = 0;
        g.closed = true;
        totalLiabilities -= amount;
        emit Withdrawn(id, msg.sender, amount);
        if (amount != 0) {
            (bool ok,) = payable(msg.sender).call{value: amount}("");
            if (!ok) revert TransferFailed();
        }
    }
    function goalCount(address owner) external view returns (uint256) { return owned[owner].length; }
    function goalIdAt(address owner, uint256 index) external view returns (uint256) { return owned[owner][index]; }
}
