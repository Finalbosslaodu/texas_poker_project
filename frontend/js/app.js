const { createApp, ref, computed, onMounted } = Vue;

const app = createApp({
    setup() {
        const connected = ref(false);
        const gameState = ref(null);
        const socket = ref(null);
        
        // LOBBY 状态
        const showBotModal = ref(false);
        const selectedSeat = ref(-1);
        const mySeatIdx = ref(-1);
        const aiLevels = ["Drunk", "Nit", "Passive", "Maniac", "Math", "Shark", "GTO", "God"];

        // GAME 状态
        const raiseAmount = ref(100);

        const connect = () => {
            socket.value = new WebSocket("ws://localhost:8000/ws");
            socket.value.onopen = () => connected.value = true;
            socket.value.onclose = () => setTimeout(connect, 3000);
            socket.value.onmessage = (e) => {
                gameState.value = JSON.parse(e.data);
                // 如果是新局开始，重置加注金额
                if (gameState.value.current_bet) {
                    raiseAmount.value = Math.max(gameState.value.current_bet * 2, (gameState.value.current_bet || 0) + 20);
                }
            };
        };
        onMounted(connect);

        // --- 通用计算 ---
        const seats = computed(() => gameState.value?.seats || Array(12).fill(null));
        const playerCount = computed(() => seats.value.filter(p => p !== null).length);
        const communityCards = computed(() => gameState.value?.community_cards || []);
        const activePlayers = computed(() => gameState.value?.players || []);

        // --- 游戏内计算 ---
        const mySeatPlayer = computed(() => {
            if(mySeatIdx.value === -1) return null;
            return seats.value[mySeatIdx.value];
        });

        const isMyTurn = computed(() => gameState.value?.current_player === 'You');
        
        const toCallAmount = computed(() => {
             if (!gameState.value || !mySeatPlayer.value) return 0;
             return gameState.value.current_bet - mySeatPlayer.value.round_bet;
        });
        
        const canCheck = computed(() => toCallAmount.value === 0);
        
        const minRaise = computed(() => (gameState.value?.current_bet || 0) + 20);
        
        const imReady = computed(() => mySeatPlayer.value?.is_ready || false);

        // --- Actions ---
        
        // [修复] 智能处理 action 参数
        const sendAction = (action, payload = {}) => {
            if (!socket.value) return;
            
            let data = {};
            // 如果传入的是数字（比如 raiseAmount），自动包装成 { amount: 100 }
            if (typeof payload === 'number') {
                data = { amount: payload };
            } else {
                data = payload;
            }

            socket.value.send(JSON.stringify({ action, playerName: 'You', ...data }));
        };

        const sit = (seat) => {
            mySeatIdx.value = seat;
            sendAction('sit', { seat, name: 'You', chips: 10000 });
        };

        const openBotModal = (seat) => {
            selectedSeat.value = seat;
            showBotModal.value = true;
        };

        const addBot = (level) => {
            sendAction('add_bot', { seat: selectedSeat.value, level });
            showBotModal.value = false;
        };

        const adjustRaise = (delta) => {
            let newVal = raiseAmount.value + delta;
            newVal = Math.max(minRaise.value, newVal);
            if (mySeatPlayer.value) {
                const maxVal = mySeatPlayer.value.chips + mySeatPlayer.value.round_bet;
                newVal = Math.min(newVal, maxVal);
            }
            raiseAmount.value = newVal;
        };

        const getSuitColor = (suit) => (suit === '♥' || suit === '♦') ? 'text-red-500' : 'text-black';

        const getLobbySeatStyle = (i) => {
            const total = 12;
            const w = 900;
            const h = 500;
            const offsetX = -48; 
            const offsetY = -48;
            const angle = (i / total) * 2 * Math.PI + (Math.PI / 2);
            const rx = w / 2 + 45; 
            const ry = h / 2 + 35;
            const x = Math.cos(angle) * rx + (w / 2) + offsetX;
            const y = Math.sin(angle) * ry + (h / 2) + offsetY;
            return { left: `${x}px`, top: `${y}px` };
        };

        return {
            gameState, seats, playerCount, aiLevels, showBotModal, selectedSeat,
            mySeatIdx, mySeatPlayer, communityCards, activePlayers,
            isMyTurn, toCallAmount, canCheck, minRaise, raiseAmount, imReady,
            sit, openBotModal, addBot, sendAction, getSuitColor,
            getLobbySeatStyle, adjustRaise
        };
    }
});

// --- 组件: 保持不变，为了确保完整性我一并列出 ---
app.component('seat-node', {
    props: ['idx', 'seat'],
    template: `
    <div class="w-24 h-24 rounded-full border-4 flex flex-col items-center justify-center cursor-pointer transition-all shadow-lg transform hover:scale-110 bg-gray-800 z-20"
         :class="seat ? 'border-blue-500' : 'border-gray-600 border-dashed hover:border-yellow-400'"
         @click="handleClick">
        <div v-if="seat" class="text-center">
            <div class="text-xs font-bold text-blue-300">{{ seat.is_ai ? 'AI Lv'+seat.ai_level : 'HUMAN' }}</div>
            <div class="font-bold text-white truncate w-20">{{ seat.name }}</div>
        </div>
        <div v-else class="text-gray-500 font-bold text-xl">+</div>
    </div>
    `,
    methods: {
        handleClick() {
            if (this.seat) return;
            if (this.$root.mySeatIdx === -1) {
                this.$root.sit(this.idx);
            } else {
                this.$root.openBotModal(this.idx);
            }
        }
    }
});

app.component('game-seat', {
    props: ['player', 'idx', 'current', 'stage'],
    template: `
    <div v-if="player" class="absolute flex flex-col items-center w-24 transition-all duration-500"
         :style="positionStyle">
        
        <!-- 头像圈 -->
        <div class="w-14 h-14 rounded-full border-4 flex flex-col items-center justify-center bg-gray-800 shadow-xl z-10 relative"
             :class="isTurn ? 'border-yellow-400 ring-4 ring-yellow-400/30' : 'border-gray-600'"
             :style="{ opacity: player.status==='folded' ? 0.5 : 1, transform: isTurn ? 'scale(1.2)' : 'scale(1)' }">
             
            <div class="font-bold text-[10px] text-center leading-tight">
                {{ player.name }}
                <div class="text-yellow-500">💰{{ player.chips }}</div>
            </div>
            
            <!-- [新增] 风格标签 (仅 AI 显示) -->
            <div v-if="player.is_ai" class="mt-[-2px] text-[8px] text-gray-400 scale-90">
                Lv{{ player.ai_level }} {{ player.ai_style_label?.split(' ')[0] }} 
            </div>
            
            <!-- Bet 筹码 -->
            <div v-if="player.round_bet > 0" class="absolute top-[-15px] bg-blue-600 px-2 py-0.5 rounded-full text-[10px] font-bold shadow whitespace-nowrap">
                {{ player.round_bet }}
            </div>
        </div>
        
        <!-- ... 手牌和 Rebuy 部分保持不变 ... -->
        <div class="flex -space-x-3 mt-[-8px] z-0 relative">
            <template v-if="shouldShowHand">
                <div v-for="(c, i) in player.hand" :key="i" 
                     class="w-8 h-12 bg-white rounded border border-gray-400 text-black flex items-center justify-center shadow-lg transform origin-bottom-left" 
                     :style="{ transform: i===0 ? 'rotate(-10deg)' : 'rotate(10deg)' }">
                    <span class="font-bold text-xs" :class="c.suit === '♥' || c.suit === '♦' ? 'text-red-500' : 'text-black'">
                        {{ c.rank_str }}<span class="text-[8px]">{{ c.suit }}</span>
                    </span>
                </div>
            </template>
            <template v-else>
                <div class="w-8 h-12 bg-blue-800 rounded border border-white/20 shadow-lg transform -rotate-6"></div>
                <div class="w-8 h-12 bg-blue-800 rounded border border-white/20 shadow-lg transform rotate-6"></div>
            </template>
        </div>

        <div v-if="player.rebuy_count > 0" class="mt-1 bg-red-600 px-2 py-0.5 rounded-full text-[8px] font-bold border border-white shadow-md z-20">
            🔄 {{ player.rebuy_count }}
        </div>
    </div>
    `,
    // ... computed 保持不变
    computed: {
        isTurn() { return this.current === this.player.name; },
        shouldShowHand() {
            if (!this.player.hand || this.player.hand.length === 0) return false;
            if (this.player.name === 'You') return true;
            if (this.stage === 'SHOWDOWN') return true;
            return false;
        },
        positionStyle() {
            const total = 12;
            const angle = (this.idx / total) * 2 * Math.PI + (Math.PI / 2);
            const rx = 42; const ry = 42; 
            const x = 50 + Math.cos(angle) * rx;
            const y = 50 + Math.sin(angle) * ry;
            return { left: `${x}%`, top: `${y}%`, transform: 'translate(-50%, -50%)' };
        }
    }
});

// 还要修改 seat-node 里的显示，让它也显示风格
app.component('seat-node', {
    props: ['idx', 'seat'],
    template: `
    <div class="w-24 h-24 rounded-full border-4 flex flex-col items-center justify-center cursor-pointer transition-all shadow-lg transform hover:scale-110 bg-gray-800 z-20"
         :class="seat ? 'border-blue-500' : 'border-gray-600 border-dashed hover:border-yellow-400'"
         @click="handleClick">
        <div v-if="seat" class="text-center">
            <!-- [修改] 显示风格 -->
            <div class="text-[10px] font-bold text-blue-300" v-if="seat.is_ai">
                Lv{{ seat.ai_level }} {{ seat.ai_style_label }}
            </div>
            <div class="text-xs font-bold text-green-400" v-else>HUMAN</div>
            
            <div class="font-bold text-white truncate w-20 text-xs mt-1">{{ seat.name }}</div>
        </div>
        <div v-else class="text-gray-500 font-bold text-xl">+</div>
    </div>
    `,
    methods: {
        handleClick() {
            if (this.seat) return;
            if (this.$root.mySeatIdx === -1) {
                this.$root.sit(this.idx);
            } else {
                this.$root.openBotModal(this.idx);
            }
        }
    }
});

app.mount('#app');