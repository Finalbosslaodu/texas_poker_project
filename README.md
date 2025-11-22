***

# 🃏 Modern Texas Hold'em AI Battle
> 一个基于 Python FastAPI 和 Vue 3 的现代化德州扑克对战平台，内置性格迥异的智能 AI。

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-green)
![Vue.js](https://img.shields.io/badge/Vue.js-3.0-emerald)
![TailwindCSS](https://img.shields.io/badge/Tailwind-3.0-cyan)
![AI](https://img.shields.io/badge/AI-Monte_Carlo-purple)

这是一个全栈德州扑克游戏项目。它采用**前后端分离**架构，后端使用 Python 处理核心游戏逻辑和 WebSocket 通信，前端使用 Vue.js 和 Tailwind CSS 构建响应式的现代化大厅与游戏界面。项目支持 **12 人大型对局**，拥有完善的**边池 (Side Pot)** 结算系统，并引入了 **“智力 + 风格”双维度 AI 系统**。

---

## ✨ 最新特性 (New Features)

### 🤖 全新双维度 AI 系统
不再是单一难度的机器人，每个 AI 现在拥有独立的**智力**和**性格**：
*   **8 个智力等级 (Intelligence)**：从随机乱玩的 Lv0 到基于高精度蒙特卡洛模拟 (Monte Carlo) 的 Lv7 宗师。
*   **6 种打牌风格 (Styles)**：
    *   🪨 **Rock (岩石)**：极度保守，只玩顶尖牌。
    *   🐟 **Fish (鱼)**：跟注站，很难放弃手牌。
    *   💣 **Maniac (疯子)**：极度激进，疯狂诈唬和加注。
    *   🦈 **Shark (鲨鱼)**：职业风格，平衡且致命。
    *   🎭 **Gambler (赌徒)**：偏爱听牌，追求高风险。
    *   🤖 **GTO**：数学平衡流，难以被剥削。
*   *AI 在创建时会随机获得一种风格，带来无限变数。*

### 💰 完善的经济与结算系统
*   **边池逻辑 (Side Pots)**：完美支持多人 All-in 场景。系统会自动计算主池和多个边池，确保筹码分配绝对公平。
*   **自动重买 (Auto Rebuy)**：输光筹码的 AI 会自动补筹码（10000），并获得一个 `🔄` 勋章标记。
*   **防破产保护**：严密的后端逻辑防止筹码扣减为负数，杜绝死锁 Bug。

### 🏟️ 12 人大型对局
*   支持至多 **12 名玩家** 同台竞技。
*   基于椭圆函数的动态座位布局算法，确保界面美观不遮挡。
*   优化的 UI 设计，适配高密度玩家展示。

---

## 🛠️ 技术架构 (Architecture)

```mermaid
graph LR
    A[Browser (Vue 3)] -- WebSocket (JSON) --> B[FastAPI Server]
    B -- Controls --> C[Game Engine]
    C -- Uses --> D[Poker Logic]
    C -- Queries --> E[AI Brain]
    E -- Config --> F[Styles & Levels]
```

*   **Backend (`/backend`)**:
    *   `main.py`: WebSocket 路由与游戏循环控制。
    *   `core/game_engine.py`: 核心状态机。处理座位管理、发牌、边池计算 (Side Pots)、盲注轮转。
    *   `core/ai.py`: **重构后的 AI 大脑**。包含蒙特卡洛模拟器和风格修正算法。
    *   `core/player.py`: 玩家数据模型，包含筹码、状态、风格标签。
*   **Frontend (`/frontend`)**:
    *   `index.html`: 单页应用，包含 Lobby (大厅) 和 Table (牌桌) 视图。
    *   `js/app.js`: Vue 3 逻辑。负责坐标计算、动画状态同步、指令发送。

---

## 🚀 快速启动 (Quick Start)

### 1. 环境准备
确保您的电脑已安装 **Python 3.10** 或更高版本。

### 2. 安装依赖
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 运行游戏
*   **Windows**: 直接双击根目录下的 `start_game.bat`。
*   **Mac/Linux**: 运行 `./start_game.sh`。
*   **手动启动**:
    ```bash
    uvicorn backend.main:app --reload
    ```
    然后用浏览器打开 `frontend/index.html`。

---

## 🎮 游戏指南

1.  **大厅选座**：
    *   点击任意空位的 `+` 号坐下。
    *   点击其他空位添加 AI。
    *   选择 AI 的 **智力等级** (Lv0 - Lv7)。系统会自动随机分配一种 **风格** (如 🦈 Shark)。
2.  **开始游戏**：
    *   至少 2 人即可开局。
    *   初始筹码均为 **10000**。
3.  **游戏操作**：
    *   **Check/Call**：过牌或跟注。
    *   **Bet/Raise**：在输入框输入金额，或使用 `1/2 Pot`, `Pot`, `All-in` 快捷键。
    *   **Fold**：弃牌。
4.  **结算与重买**：
    *   每局结束后自动摊牌，显示公共牌和盈亏。
    *   输光的玩家会自动重买，并增加重买计数标记。

---

## 🤖 AI 策略详解

AI 的决策基于公式：
$$ 最终决策 = f(基础胜率 \times 风格修正, 底池赔率) $$

*   **低智力 AI**：仅基于手牌大小或随机决策。
*   **高智力 AI**：进行 **蒙特卡洛模拟 (Monte Carlo Simulation)**。假设发完成千上万次牌，计算真实胜率 (Equity)。
*   **风格修正**：
    *   **Maniac** 会人为高估自己的胜率，导致更频繁的加注。
    *   **Rock** 会低估胜率，只有在拥有绝对优势时才入局。
    *   **Bluffing (诈唬)**：高等级 AI 会在胜率低但底池大时，随机尝试诈唬。

Enjoy the game! 🍀