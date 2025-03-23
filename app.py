async def process_ai_night_actions(game_id, game_manager=None):
    """處理AI玩家的夜間行動"""
    if game_manager is None:
        game_manager = active_games.get(game_id)
        if not game_manager:
            return
    
    # 獲取所有存活的AI玩家
    ai_players = [(p["player_id"], game_manager.game_state.player_objects[p["player_id"]])
                 for p in game_manager.game_state.players
                 if p["is_alive"] and p["player_id"] not in game_manager.human_players]  # 排除人類玩家
    
    # 為每個AI玩家執行夜間行動
    for player_id, player_obj in ai_players:
        api_handler = game_manager.api_handlers.get(player_id)
        if api_handler:
            action_result = await player_obj.night_action(
                game_manager.game_state.get_state_for_player(player_id),
                api_handler
            )
            game_manager.game_state.night_actions[player_id] = action_result