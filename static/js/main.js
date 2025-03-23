document.addEventListener('DOMContentLoaded', function() {
    // 遊戲創建表單
    const gameForm = document.getElementById('gameForm');
    
    // API類型和模型選擇聯動
    const apiTypeSelect = document.getElementById('api_type');
    const modelNameSelect = document.getElementById('model_name');
    
    // 根據API類型更新模型選項
    apiTypeSelect.addEventListener('change', function() {
        const apiType = this.value;
        
        // 清空現有選項
        modelNameSelect.innerHTML = '';
        
        // 根據API類型添加對應的模型選項
        if (apiType === 'openai') {
            // 添加最新的 OpenAI 模型選項
            addOption(modelNameSelect, 'gpt-4o', 'GPT-4o');
            addOption(modelNameSelect, 'gpt-4o-mini', 'GPT-4o Mini');
            addOption(modelNameSelect, 'gpt-4-turbo', 'GPT-4 Turbo');
            addOption(modelNameSelect, 'gpt-4', 'GPT-4');
            addOption(modelNameSelect, 'gpt-3.5-turbo', 'GPT-3.5 Turbo');
        } else if (apiType === 'anthropic') {
            addOption(modelNameSelect, 'claude-3-opus-20240229', 'Claude 3 Opus');
            addOption(modelNameSelect, 'claude-3-sonnet-20240229', 'Claude 3 Sonnet');
            addOption(modelNameSelect, 'claude-3-haiku-20240307', 'Claude 3 Haiku');
        }
    });
    
    // 表單提交處理
    gameForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 獲取特殊角色選擇
        const specialRoles = [];
        document.querySelectorAll('input[name="special_roles"]:checked').forEach(function(checkbox) {
            specialRoles.push(checkbox.value);
        });
        
        // 獲取人類玩家設定
        const humanPlayer = parseInt(document.getElementById('human_player').value);
        
        // 準備提交數據
        const formData = {
            player_count: document.getElementById('player_count').value,
            werewolf_count: document.getElementById('werewolf_count').value,
            special_roles: specialRoles.join(','),
            human_player: humanPlayer,
            api_type: document.getElementById('api_type').value,
            model_name: document.getElementById('model_name').value
        };
        
        // 發送創建遊戲請求
        fetch('/create_game', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 跳轉到遊戲頁面
                window.location.href = `/join_game/${data.game_id}`;
            } else {
                alert('創建遊戲失敗: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('發生錯誤，請查看控制台');
        });
    });
    
    // 輔助函數: 添加選項到select元素
    function addOption(selectElement, value, text) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = text;
        selectElement.appendChild(option);
    }
    
    // 初始設置
    apiTypeSelect.dispatchEvent(new Event('change'));
});
