from .base_role import BaseRole

class Seer(BaseRole):
    """預言家角色"""
    
    def __init__(self, player_id, name=None):
        """初始化預言家角色
        
        Args:
            player_id (int): 玩家 ID
            name (str, optional): 玩家名稱
        """
        super().__init__(player_id, name)
        self.role_name = "預言家"
        self.team = "村民陣營"
        self.checked_players = {}  # 已查驗的玩家 {player_id: result}
    
    async def night_action(self, game_state, api_handler):
        """夜晚行動 - 查驗一名玩家的身份
        
        Args:
            game_state (dict): 當前遊戲狀態
            api_handler: API 處理程序
            
        Returns:
            dict: 行動結果，包含目標玩家 ID 和查驗結果
        """
        # 構建夜間行動提示
        prompt = self._build_night_action_prompt(game_state)
        
        # 使用 API 獲取決策
        system_message = f"""你是一名狼人殺遊戲中的預言家角色，名字是{self.name}。
現在是夜晚，你需要選擇一名玩家進行查驗，了解他是否是狼人。
作為預言家，你應該選擇最有價值的目標進行查驗。"""
        
        response = await api_handler.get_response(prompt, system_message)
        
        # 解析響應以獲取目標玩家 ID
        try:
            # 嘗試找到數字ID引用
            import re
            target_ids = re.findall(r'玩家(\d+)', response)
            if target_ids:
                target_id = int(target_ids[0])
                # 確保是有效的存活玩家且不是自己
                valid_targets = [p for p in game_state["players"] 
                               if p["is_alive"] and p["player_id"] != self.player_id]
                if any(p["player_id"] == target_id for p in valid_targets):
                    # 獲取查驗結果
                    target_player = next((p for p in game_state["players"] if p["player_id"] == target_id), None)
                    if target_player:
                        is_werewolf = target_player.get("role") == "werewolf"
                        result = "狼人" if is_werewolf else "好人"
                        
                        # 記錄查驗結果
                        self.checked_players[target_id] = result
                        
                        return {"action": "check", "target": target_id, "result": result}
            
            # 如果沒有找到有效的ID，隨機選擇一個
            import random
            valid_targets = [p for p in game_state["players"] 
                           if p["is_alive"] and p["player_id"] != self.player_id]
            if valid_targets:
                target = random.choice(valid_targets)
                target_id = target["player_id"]
                
                # 獲取查驗結果
                is_werewolf = target.get("role") == "werewolf"
                result = "狼人" if is_werewolf else "好人"
                
                # 記錄查驗結果
                self.checked_players[target_id] = result
                
                return {"action": "check", "target": target_id, "result": result}
                
            return {"action": "wait", "target": None, "result": "無有效目標"}
        except Exception as e:
            # 出錯時返回等待
            return {"action": "wait", "target": None, "result": f"錯誤：{str(e)}"}
    
    async def day_discussion(self, game_state, api_handler):
        """白天討論
        
        Args:
            game_state (dict): 當前遊戲狀態
            api_handler: API 處理程序
            
        Returns:
            str: 討論發言
        """
        # 構建討論提示
        prompt = self._build_discussion_prompt(game_state)
        
        # 使用 API 獲取發言
        system_message = f"""你是一名狼人殺遊戲中的預言家角色，名字是{self.name}。
你的目標是幫助村民找出狼人並獲勝。
作為預言家，你掌握著重要信息，但要小心狼人可能會針對你。
在適當的時機公布你的身份和查驗結果可以幫助村民，但也可能使你成為狼人的目標。"""
        
        response = await api_handler.get_response(prompt, system_message, temperature=0.7, max_tokens=300)
        return response
    
    def _build_night_action_prompt(self, game_state):
        """構建夜間行動提示
        
        Args:
            game_state (dict): 當前遊戲狀態
            
        Returns:
            str: 夜間行動提示
        """
        prompt = f"現在是狼人殺遊戲的第{game_state['day']}天夜晚，預言家行動階段。\n\n"
        
        # 添加遊戲現狀
        prompt += "遊戲現狀：\n"
        prompt += f"- 你是預言家，可以查驗一名玩家的身份（是否為狼人）\n"
        
        # 添加已查驗的玩家
        if self.checked_players:
            prompt += "- 你已經查驗過的玩家：\n"
            for player_id, result in self.checked_players.items():
                player = next((p for p in game_state["players"] if p["player_id"] == player_id), None)
                if player:
                    prompt += f"  - 玩家{player_id}（{player['name']}）：{result}\n"
        
        # 添加可選目標
        prompt += "\n可選的查驗目標：\n"
        for player in game_state["players"]:
            if player["is_alive"] and player["player_id"] != self.player_id:
                already_checked = player["player_id"] in self.checked_players
                prompt += f"- 玩家{player['player_id']}（{player['name']}）{' - 已查驗過' if already_checked else ''}\n"
        
        # 添加遊戲歷史上下文
        prompt += "\n遊戲歷史：\n"
        for event in self.game_history[-10:]:  # 只使用最近的10個事件
            prompt += f"- {event}\n"
        
        prompt += "\n請選擇一名玩家進行查驗。考慮誰的行為最可疑，或是誰最可能影響遊戲局勢。回答格式：'我選擇查驗玩家X'，其中X是玩家ID。"
        
        return prompt
    
    def _build_discussion_prompt(self, game_state):
        """構建討論提示
        
        Args:
            game_state (dict): 當前遊戲狀態
            
        Returns:
            str: 討論提示
        """
        prompt = f"現在是狼人殺遊戲的第{game_state['day']}天，白天討論階段。\n\n"
        
        # 添加遊戲現狀
        prompt += "遊戲現狀：\n"
        prompt += f"- 存活玩家：{len([p for p in game_state['players'] if p['is_alive']])}人\n"
        prompt += f"- 昨晚死亡：{game_state['last_night_deaths'] or '無'}\n"
        
        # 添加預言家信息
        prompt += "- 你是預言家，掌握著重要信息\n"
        
        # 添加已查驗的玩家
        if self.checked_players:
            prompt += "- 你已經查驗過的玩家：\n"
            for player_id, result in self.checked_players.items():
                player = next((p for p in game_state["players"] if p["player_id"] == player_id), None)
                if player:
                    is_alive = "存活" if player["is_alive"] else "已死亡"
                    prompt += f"  - 玩家{player_id}（{player['name']}）：{result}，現在{is_alive}\n"
        
        # 添加遊戲歷史
        prompt += "\n遊戲歷史：\n"
        for event in self.game_history[-15:]:  # 只使用最近的15個事件
            prompt += f"- {event}\n"
        
        # 添加今天已有的討論
        if game_state["current_discussions"]:
            prompt += "\n今天的討論：\n"
            for discussion in game_state["current_discussions"]:
                prompt += f"- {discussion['player_name']}（玩家{discussion['player_id']}）說：「{discussion['content']}」\n"
        
        prompt += "\n請以第一人稱發表你的看法和分析。你需要考慮是否現在公開自己的預言家身份並分享查驗結果，或者先觀察一下局勢。你的目標是幫助村民找出狼人，同時避免自己過早被狼人盯上。"
        
        return prompt
