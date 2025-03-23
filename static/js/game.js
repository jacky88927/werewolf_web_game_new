document.addEventListener('DOMContentLoaded', function() {
    // 獲取遊戲ID
    const gameId = document.querySelector('meta[name="game-id"]').content;
    
    // DOM元素
    const gameDayElem = document.getElementById('game-day');
    const gamePhaseElem = document.getElementById('game-phase');
    const playerRoleElem = document.getElementById('player-role');
    const playerListElem = document.getElementById('player-list');
    const gameLogElem = document.getElementById('game-log');
    const playerHistoryElem = document.getElementById('player-history');
    const gameStatusElem = document.getElementById('game-status');
    const nextPhaseBtn = document.getElementById('next-phase-btn');
    
    // 討論區域
    const discussionArea = document.getElementById('discussion-area');
    const discussionLog = document.getElementById('discussion-log');
    const discussionForm = document.getElementById('discussion-form');
    const discussionInput = document.getElementById('discussion-input');
    
    // 投票區域
    const voteArea = document.getElementById('vote-area');
    const voteOptions = document.getElementById('vote-options');
    const submitVoteBtn = document.getElementById('submit-vote');
    
    // 夜晚行動區域
    const nightActionArea = document.getElementById('night-action-area');
    const nightActionPrompt = document.getElementById('night-action-prompt');
    const nightActionOptions = document.getElementById('night-action-options');
    const submitNightActionBtn = document.getElementById('submit-night-action');
    
    // 遊戲結束區域
    const gameOverArea = document.getElementById('game-over-area');
    const winnerTextElem = document.getElementById('winner-text');
    
    // 聊天區域
    const chatLog = document.getElementById('chat-log');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    
    // 遊戲狀態變量
    let gameState = null;
    let selectedVoteTarget = null;
    let selectedNightTarget = null;
    let playerRole = null;
    let isAllAI = false; // 是否是全AI遊戲
    
    // 初始化Socket.io
    const socket = io();
    
    // 加入遊戲房間
    socket.emit('join', { game_id: gameId });
    
    // 監聽遊戲更新
    socket.on('game_update', function(data) {
        if (data.game_id === gameId) {
            loadGameState();
        }
    });
    
    // 監聽聊天訊息
    socket.on('chat_message', function(data) {
        addChatMessage(data.player_name, data.player_id, data.message);
    });
    
    // 載入遊戲狀態
    function loadGameState() {
        fetch(`/api/game_state/${gameId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    gameState = data.game_state;
                    isAllAI = gameState.is_all_ai || false;
                    updateGameUI();
                } else {
                    console.error('加載遊戲狀態失敗:', data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }
    
    // 更新遊戲UI
    function updateGameUI() {
        // 基本遊戲信息
        gameDayElem.textContent = gameState.day;
        gamePhaseElem.textContent = translatePhase(gameState.phase);
        playerRole = gameState.player_role;
        playerRoleElem.textContent = playerRole;
        
        // 設定角色樣式
        if (playerRole === '觀察者') {
            playerRoleElem.className = 'fw-bold';
        } else {
            playerRoleElem.className = `fw-bold role-${playerRole === '狼人' ? 'werewolf' : (playerRole === '預言家' ? 'seer' : 'villager')}`;
        }
        
        // 更新玩家歷史
        updatePlayerHistory();
        
        // 更新玩家列表
        updatePlayerList();
        
        // 根據遊戲階段更新UI
        updatePhaseUI();
        
        // 更新遊戲狀態標籤
        updateGameStatus();
    }
    
    // 更新玩家歷史
    function updatePlayerHistory() {
        if (gameState.player_history) {
            playerHistoryElem.innerHTML = '';
            gameState.player_history.forEach(history => {
                const historyElem = document.createElement('div');
                historyElem.className = 'log-entry';
                historyElem.textContent = history;
                playerHistoryElem.appendChild(historyElem);
            });
            
            // 自動滾動到底部
            playerHistoryElem.scrollTop = playerHistoryElem.scrollHeight;
        }
    }
    
    // 更新玩家列表
    function updatePlayerList() {
        playerListElem.innerHTML = '';
        
        gameState.players.forEach(player => {
            const playerElem = document.createElement('li');
            playerElem.className = `list-group-item d-flex justify-content-between align-items-center`;
            
            // 判斷是否是自己（全AI模式無"自己"）
            const isSelf = !isAllAI && player.player_id === 1;
            
            // 玩家名稱
            let playerNameHtml = `${player.name}`;
            if (isSelf) {
                playerNameHtml += ` <span class="badge bg-info">你</span>`;
            }
            
            // 玩家狀態和角色
            let statusHtml = '';
            if (player.is_alive) {
                statusHtml = `<span class="player-status-alive">存活</span>`;
            } else {
                statusHtml = `<span class="player-status-dead">死亡</span>`;
            }
            
            // 如果玩家已死亡或者有權限看到角色信息（全AI模式或者是狼人查看其他狼人），則顯示角色
            if (!player.is_alive || isAllAI || player.role) {
                const roleClass = player.role === 'werewolf' ? 'werewolf' : (player.role === 'seer' ? 'seer' : 'villager');
                statusHtml += ` <span class="role-${roleClass}">${translateRole(player.role)}</span>`;
            }
            
            playerElem.innerHTML = `
                <div>${playerNameHtml}</div>
                <div>${statusHtml}</div>
            `;
            
            playerListElem.appendChild(playerElem);
        });
    }
    
    // 根據遊戲階段更新UI
    function updatePhaseUI() {
        // 隱藏所有操作區域
        discussionArea.style.display = 'none';
        voteArea.style.display = 'none';
        nightActionArea.style.display = 'none';
        gameOverArea.style.display = 'none';
        nextPhaseBtn.style.display = 'none';
        
        // 全AI模式只顯示「下一階段」按鈕
        if (isAllAI) {
            nextPhaseBtn.style.display = 'block';
            nextPhaseBtn.textContent = gameState.phase === 'gameover' ? '遊戲已結束' : '進入下一階段';
            nextPhaseBtn.disabled = gameState.phase === 'gameover';
            
            // 更新討論記錄
            updateDiscussionLog();
            
            // 如果是遊戲結束階段，顯示結果
            if (gameState.phase === 'gameover') {
                gameOverArea.style.display = 'block';
                winnerTextElem.textContent = `${gameState.winner}獲勝！`;
            }
            
            return; // 全AI模式下不顯示其他操作區域
        }
        
        // 根據階段顯示相應區域（人類參與模式）
        if (gameState.phase === 'day') {
            // 白天討論階段
            discussionArea.style.display = 'block';
            updateDiscussionLog();
            nextPhaseBtn.style.display = 'block';
            nextPhaseBtn.textContent = '結束討論，進入投票';
        }
        else if (gameState.phase === 'vote') {
            // 投票階段
            voteArea.style.display = 'block';
            updateVoteOptions();
        }
        else if (gameState.phase === 'night') {
            // 夜晚行動階段
            nightActionArea.style.display = 'block';
            updateNightActionOptions();
        }
        else if (gameState.phase === 'gameover') {
            // 遊戲結束
            gameOverArea.style.display = 'block';
            winnerTextElem.textContent = `${gameState.winner}獲勝！`;
        }
    }
    
    // 更新討論記錄
    function updateDiscussionLog() {
        discussionLog.innerHTML = '';
        
        if (gameState.current_discussions && gameState.current_discussions.length > 0) {
            gameState.current_discussions.forEach(discussion => {
                const messageElem = document.createElement('div');
                messageElem.className = 'log-entry';
                
                // 判斷是否是自己的發言
                const isSelf = !isAllAI && discussion.player_id === 1;
                
                messageElem.innerHTML = `
                    <strong>${discussion.player_name}${isSelf ? '（你）' : ''}:</strong> ${discussion.content}
                `;
                
                discussionLog.appendChild(messageElem);
            });
            
            // 自動滾動到底部
            discussionLog.scrollTop = discussionLog.scrollHeight;
        }
    }
    
    // 更新投票選項
    function updateVoteOptions() {
        voteOptions.innerHTML = '';
        selectedVoteTarget = null;
        submitVoteBtn.disabled = true;
        
        // 獲取存活玩家作為投票選項
        const alivePlayersExceptSelf = gameState.players.filter(
            player => player.is_alive && player.player_id !== 1 // 排除自己
        );
        
        alivePlayersExceptSelf.forEach(player => {
            const optionElem = document.createElement('button');
            optionElem.className = 'list-group-item list-group-item-action';
            optionElem.textContent = `${player.name}（玩家${player.player_id}）`;
            optionElem.dataset.playerId = player.player_id;
            
            optionElem.addEventListener('click', function() {
                // 取消之前的選擇
                document.querySelectorAll('#vote-options .selected').forEach(elem => {
                    elem.classList.remove('selected');
                });
                
                // 選中當前選項
                this.classList.add('selected');
                selectedVoteTarget = parseInt(this.dataset.playerId);
                submitVoteBtn.disabled = false;
            });
            
            voteOptions.appendChild(optionElem);
        });
    }
    
    // 更新夜晚行動選項
    function updateNightActionOptions() {
        nightActionOptions.innerHTML = '';
        selectedNightTarget = null;
        submitNightActionBtn.disabled = true;
        
        // 根據角色類型顯示不同的行動選項
        if (playerRole === '狼人') {
            nightActionPrompt.textContent = '請選擇你要襲擊的目標：';
            
            // 獲取存活的非狼人玩家作為目標
            const targetPlayers = gameState.players.filter(player => {
                // 排除已死亡玩家和自己
                if (!player.is_alive || player.player_id === 1) return false;
                
                // 如果可以看到角色（狼人可以看到其他狼人），則排除狼人
                if (player.role === 'werewolf') return false;
                
                return true;
            });
            
            targetPlayers.forEach(player => {
                addNightActionOption(player);
            });
        }
        else if (playerRole === '預言家') {
            nightActionPrompt.textContent = '請選擇你要查驗的目標：';
            
            // 獲取存活的非自己玩家作為目標
            const targetPlayers = gameState.players.filter(
                player => player.is_alive && player.player_id !== 1
            );
            
            targetPlayers.forEach(player => {
                addNightActionOption(player);
            });
        }
        else {
            // 普通村民沒有夜間行動
            nightActionPrompt.textContent = '你沒有特殊能力，請等待天亮...';
            submitNightActionBtn.style.display = 'none';
            
            // 自動提交無操作
            setTimeout(() => {
                submitNightAction(null);
            }, 2000);
        }
    }
    
    // 添加夜晚行動選項
    function addNightActionOption(player) {
        const optionElem = document.createElement('button');
        optionElem.className = 'list-group-item list-group-item-action';
        optionElem.textContent = `${player.name}（玩家${player.player_id}）`;
        optionElem.dataset.playerId = player.player_id;
        
        optionElem.addEventListener('click', function() {
            // 取消之前的選擇
            document.querySelectorAll('#night-action-options .selected').forEach(elem => {
                elem.classList.remove('selected');
            });
            
            // 選中當前選項
            this.classList.add('selected');
            selectedNightTarget = parseInt(this.dataset.playerId);
            submitNightActionBtn.disabled = false;
        });
        
        nightActionOptions.appendChild(optionElem);
    }
    
    // 更新遊戲狀態標籤
    function updateGameStatus() {
        if (gameState.game_over) {
            gameStatusElem.textContent = '遊戲結束';
            gameStatusElem.className = 'badge bg-danger';
            return;
        }
        
        const phase = gameState.phase;
        if (phase === 'day') {
            gameStatusElem.textContent = '白天討論';
            gameStatusElem.className = 'badge bg-warning text-dark';
        }
        else if (phase === 'vote') {
            gameStatusElem.textContent = '投票階段';
            gameStatusElem.className = 'badge bg-danger';
        }
        else if (phase === 'night') {
            gameStatusElem.textContent = '夜晚';
            gameStatusElem.className = 'badge bg-primary';
        }
    }
    
    // 表單提交處理
    
    // 討論發言
    discussionForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 全AI模式不允許討論
        if (isAllAI) return;
        
        const content = discussionInput.value.trim();
        if (!content) return;
        
        // 發送討論
        fetch(`/api/player_action/${gameId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action_type: 'discussion',
                content: content
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                discussionInput.value = '';
                loadGameState(); // 重新加載遊戲狀態
            } else {
                alert('發送失敗: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
    
    // 提交投票
    submitVoteBtn.addEventListener('click', function() {
        if (!selectedVoteTarget || isAllAI) return;
        
        // 發送投票
        fetch(`/api/player_action/${gameId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action_type: 'vote',
                content: selectedVoteTarget.toString()
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addSystemLog(`你投票給了玩家${selectedVoteTarget}`);
                
                // 進入下一階段
                goToNextPhase();
            } else {
                alert('投票失敗: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
    
    // 提交夜晚行動
    submitNightActionBtn.addEventListener('click', function() {
        if (isAllAI) return;
        submitNightAction(selectedNightTarget);
    });
    
    function submitNightAction(targetId) {
        if (isAllAI) return;
        
        const targetContent = targetId ? targetId.toString() : '';
        
        // 發送夜晚行動
        fetch(`/api/player_action/${gameId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action_type: 'night_action',
                content: targetContent
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (targetId) {
                    if (playerRole === '狼人') {
                        addSystemLog(`你選擇襲擊玩家${targetId}`);
                    } else if (playerRole === '預言家') {
                        addSystemLog(`你選擇查驗玩家${targetId}`);
                    }
                }
                
                // 進入下一階段
                goToNextPhase();
            } else {
                alert('行動失敗: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
    
    // 進入下一階段
    nextPhaseBtn.addEventListener('click', goToNextPhase);
    
    function goToNextPhase() {
        fetch(`/api/player_action/${gameId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action_type: 'next_phase',
                content: ''
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addSystemLog('進入下一階段');
                loadGameState(); // 重新加載遊戲狀態
            } else {
                alert('操作失敗: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
    
    // 聊天功能
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // 發送聊天
        fetch(`/api/chat/${gameId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                chatInput.value = '';
                // 聊天訊息通過Socket.io更新
            } else {
                alert('發送失敗: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
    
    // 添加聊天訊息
    function addChatMessage(playerName, playerId, message) {
        const messageElem = document.createElement('div');
        const isSelf = !isAllAI && playerId === 1; // 全AI模式下沒有"自己"
        
        messageElem.className = `message ${isSelf ? 'self' : 'other'}`;
        messageElem.innerHTML = `
            <div class="message-header">${playerName}${isSelf ? '（你）' : ''}</div>
            <div>${message}</div>
        `;
        
        chatLog.appendChild(messageElem);
        chatLog.scrollTop = chatLog.scrollHeight; // 自動滾動到底部
    }
    
    // 添加系統日誌
    function addSystemLog(message) {
        const logElem = document.createElement('div');
        logElem.className = 'system-message';
        logElem.textContent = message;
        
        gameLogElem.appendChild(logElem);
        gameLogElem.scrollTop = gameLogElem.scrollHeight; // 自動滾動到底部
    }
    
    // 輔助函數: 翻譯遊戲階段
    function translatePhase(phase) {
        const phaseTranslations = {
            'setup': '設置',
            'day': '白天',
            'vote': '投票',
            'night': '夜晚',
            'gameover': '遊戲結束'
        };
        
        return phaseTranslations[phase] || phase;
    }
    
    // 輔助函數: 翻譯角色名稱
    function translateRole(role) {
        if (!role) return '未知';
        
        const roleTranslations = {
            'werewolf': '狼人',
            'villager': '村民',
            'seer': '預言家'
        };
        
        return roleTranslations[role] || role;
    }
    
    // 初始加載遊戲狀態
    loadGameState();
});
