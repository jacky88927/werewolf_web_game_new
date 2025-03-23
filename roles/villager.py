from .base_role import BaseRole

class Villager(BaseRole):
    """村民角色"""
    
    def __init__(self, player_id, name=None):
        """初始化村民角色
        
        Args:
            player_id (int): 玩家 ID
            name (str, optional): 玩家名稱
        """
        super().__init__(player_id, name)
        self.role_name = "村民"
        self.team = "村民陣營"
    
    async def night_action(self, game_state, api_handler):
        """夜晚行動 - 村民沒有特殊行動
        
        Args:
            game_state (dict): 當前遊戲狀態
            api_handler: API 處理程序
            
        Returns:
            dict: 行動結果，村民只能等待
        """
        return {"action": "wait", "target": None, "result": None}
    
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
        system_message = f"""你是一名狼人殺遊戲中的村民角色，名字是{self.name}。
你的目標是找出潛藏的狼人並幫助村民陣營獲勝。
在討論中要注意觀察其他玩家的行為和發言。"""
        
        response = await api_handler.get_response(prompt, system_message, temperature=0.7, max_tokens=300)
        return response
    
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
        
        # 添加遊戲歷史
        prompt += "\n遊戲歷史：\n"
        for event in self.game_history[-15:]:  # 只使用最近的15個事件
            prompt += f"- {event}\n"
        
        # 添加今天已有的討論
        if game_state["current_discussions"]:
            prompt += "\n今天的討論：\n"
            for discussion in game_state["current_discussions"]:
                prompt += f"- {discussion['player_name']}（玩家{discussion['player_id']}）說：「{discussion['content']}」\n"
        
        prompt += "\n請以第一人稱發表你的看法和分析，試圖找出狼人。你的發言應該包括你對其他玩家的觀察和你認為誰可能是狼人的猜測。"
        
        return prompt
