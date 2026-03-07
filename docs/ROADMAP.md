# Desktop Trading Suite Roadmap

## Phase 1: High-Speed Market Data (Current Focus)
- [ ] Transition from polling REST APIs (Tradier quotes) to a WebSocket stream connection. This is the biggest immediate bottleneck for "blistering speed" on the frontend.
- [ ] Connect the frontend UI to consume the live streaming data.

## Phase 2: The Electron Desktop Wrapper
- [ ] Initialize Electron project in the `/desktop` folder.
- [ ] Configure `main.js` to bundle and launch the Python FastAPI backend (`api/main.py`) as a child process.
- [ ] Migrate the current `/frontend` (HTML/JS/CSS) to be the Electron frontend.
- [ ] Ensure the app builds into a standalone executable that runs entirely locally.

## Phase 3: Trading UI & Order Execution
- [ ] Build the visual "Order Entry" module in the frontend (calls `/api/trade/execute`).
- [ ] Build the "Position Management" module (close/roll positions).
- [ ] Integrate the VoPR engine directly into the options chain view.

## Phase 4: Strategy & AI Optimization
- [ ] **Vectorization:** Implement a backtesting/scanning engine that uses vectorized Pandas/NumPy operations instead of loops.
- [ ] Add explicit tool calls to MCP for order execution (e.g., Copilot asks "Do you want me to route this limit order?").
