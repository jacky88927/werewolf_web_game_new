    // 根據遊戲階段更新UI
    function updatePhaseUI() {
        // 隱藏所有操作區域
        discussionArea.style.display = 'none';
        voteArea.style.display = 'none';
        nightActionArea.style.display = 'none';
        gameOverArea.style.display = 'none';
        nextPhaseBtn.style.display = 'none';
        
        // 全AI模式只顯示「下一階段」按鈕，但總是顯示討論區
        if (isAllAI) {
            // 顯示討論區域，以便查看 AI 討論內容
            discussionArea.style.display = 'block';
            // 禁用發言輸入
            discussionInput.disabled = true;
            discussionForm.querySelector('button').disabled = true;
            
            // 顯示下一階段按鈕
            nextPhaseBtn.style.display = 'block';
            
            // 如果是遊戲結束階段，顯示結果
            if (gameState.phase === 'gameover') {
                gameOverArea.style.display = 'block';
                winnerTextElem.textContent = `${gameState.winner}獲勝！`;
                nextPhaseBtn.textContent = '遊戲已結束';
                nextPhaseBtn.disabled = true;
            }
            
            return; // 全AI模式下不顯示其他操作區域
        }
        
        // 根據階段顯示相應區域（人類參與模式）
        if (gameState.phase === 'day') {
            // 白天討論階段
            discussionArea.style.display = 'block';
            discussionInput.disabled = false;
            discussionForm.querySelector('button').disabled = false;
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