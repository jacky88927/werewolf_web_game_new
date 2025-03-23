from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
from dotenv import load_dotenv
import uuid
import json
import asyncio
from models.game_state import GameState
from models.game_manager import GameManager

# 載入環境變數
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'werewolf_game_secret')
socketio = SocketIO(app, cors_allowed_origins="*")

# 存儲所有活躍遊戲
active_games = {}

@app.route('/')
def index():
    """首頁"""
    return render_template('index.html')

@app.route('/create_game', methods=['POST'])
def create_game():
    """創建新遊戲"""
    data = request.json
    player_count = int(data.get('player_count', 6))
    werewolf_count = int(data.get('werewolf_count', 2))
    special_roles = data.get('special_roles', ['seer']).split(',')
    api_type = data.get('api_type', 'openai')
    model_name = data.get('model_name', 'gpt-4o-mini')
    
    # 獲取人類玩家設定 (0 = 全部AI, 1 = 有人類玩家)
    human_player = int(data.get('human_player', 1))
    
    # 設定人類玩家列表
    human_players = [1] if human_player == 1 else []
    
    # 生成遊戲ID
    game_id = str(uuid.uuid4())
    
    # 創建遊戲管理器
    game_manager = GameManager()
    game_manager.setup_game(
        player_count=player_count,
        werewolf_count=werewolf_count,
        special_roles=special_roles,
        human_players=human_players,  # 根據設定決定是否有人類玩家
        api_type=api_type,
        model_name=model_name
    )
    
    # 存儲遊戲
    active_games[game_id] = game_manager
    
    # 返回遊戲信息
    return jsonify({
        'success': True,
        'game_id': game_id,
        'player_id': 1  # 人類玩家ID (如果有的話)
    })

@app.route('/join_game/<game_id>')
def join_game(game_id):
    """加入遊戲"""
    if game_id not in active_games:
        return redirect(url_for('index'))
    
    return render_template('game.html', game_id=game_id)

@app.route('/api/game_state/<game_id>')
def get_game_state(game_id):
    """獲取遊戲狀態"""
    if game_id not in active_games:
        return jsonify({'success': False, 'error': '遊戲不存在'})
    
    game_manager = active_games[game_id]
    player_id = 1  # 默認人類玩家ID
    
    # 檢查是否是全AI遊戲
    is_all_ai = 1 not in game_manager.human_players
    
    # 獲取遊戲狀態
    if is_all_ai:
        # 全AI遊戲 - 讓使用者可以看到所有信息
        game_state = {
            "day": game_manager.game_state.day,
            "phase": game_manager.game_state.phase,
            "players": game_manager.game_state.players,  # 可以看到所有玩家的角色
            "current_discussions": game_manager.game_state.current_discussions,
            "last_night_deaths": game_manager.game_state.last_night_deaths,
            "game_over": game_manager.game_state.game_over,
            "winner": game_manager.game_state.winner,
            "is_all_ai": True,  # 標記為全AI遊戲
            "player_role": "觀察者",  # 標記玩家為觀察者
            "player_history": game_manager.game_state.log  # 使用遊戲日誌作為歷史記錄
        }
    else:
        # 有人類玩家的遊戲
        game_state = game_manager.game_state.get_state_for_player(player_id)
        
        # 添加玩家在遊戲中的角色和歷史記錄
        player_obj = game_manager.game_state.player_objects.get(player_id)
        if player_obj:
            game_state['player_role'] = player_obj.role_name
            game_state['player_history'] = player_obj.game_history
            game_state['is_all_ai'] = False
    
    return jsonify({
        'success': True,
        'game_state': game_state
    })

@app.route('/api/player_action/<game_id>', methods=['POST'])
def player_action(game_id):
    """處理玩家動作"""
    if game_id not in active_games:
        return jsonify({'success': False, 'error': '遊戲不存在'})
    
    data = request.json
    action_type = data.get('action_type')
    content = data.get('content')
    player_id = 1  # 默認人類玩家ID
    
    game_manager = active_games[game_id]
    
    # 檢查是否是全AI遊戲
    is_all_ai = 1 not in game_manager.human_players
    
    if is_all_ai and action_type != 'next_phase':
        # 全AI遊戲中，只能進行「下一階段」操作
        return jsonify({'success': False, 'error': '全AI遊戲中只能進行下一階段操作'})
    
    # 根據遊戲階段和動作類型處理不同動作
    if action_type == 'discussion':
        # 人類玩家的發言將直接添加到討論中
        player_info = next((p for p in game_manager.game_state.players if p["player_id"] == player_id), None)
        if player_info:
            game_manager.game_state.current_discussions.append({
                "player_id": player_id,
                "player_name": player_info["name"],
                "content": content
            })
            
            # 更新所有玩家的歷史記錄
            for p_id, player_obj in game_manager.game_state.player_objects.items():
                if p_id != player_id and player_info["is_alive"]:
                    player_obj.add_history(
                        f"第{game_manager.game_state.day}天白天：{player_info['name']}（玩家{player_id}）說：「{content}」"
                    )
            
            # 更新自己的歷史記錄
            player_obj = game_manager.game_state.player_objects.get(player_id)
            if player_obj:
                player_obj.add_history(f"第{game_manager.game_state.day}天白天：你說：「{content}」")
            
            return jsonify({'success': True})
    
    elif action_type == 'vote':
        # 人類玩家投票
        target_id = int(content)
        game_manager.game_state.votes[player_id] = target_id
        
        # 添加到玩家歷史記錄
        player_obj = game_manager.game_state.player_objects.get(player_id)
        target_player = next((p for p in game_manager.game_state.players if p["player_id"] == target_id), None)
        
        if player_obj and target_player:
            player_obj.add_history(f"第{game_manager.game_state.day}天投票：你投票給了玩家{target_id}（{target_player['name']}）")
        
        return jsonify({'success': True})
    
    elif action_type == 'night_action':
        # 人類玩家的夜間動作
        player_obj = game_manager.game_state.player_objects.get(player_id)
        target_id = int(content) if content.isdigit() else None
        
        if player_obj:
            role = player_obj.role_name
            
            if role == "狼人":
                # 狼人的攻擊行動
                game_manager.game_state.night_actions[player_id] = {
                    "action": "attack",
                    "target": target_id,
                    "result": None
                }
                player_obj.add_history(f"第{game_manager.game_state.day}天夜晚：你選擇攻擊玩家{target_id}")
            
            elif role == "預言家":
                # 預言家的查驗行動
                target_player = next((p for p in game_manager.game_state.players if p["player_id"] == target_id), None)
                if target_player:
                    is_werewolf = target_player["role"] == "werewolf"
                    result = "狼人" if is_werewolf else "好人"
                    game_manager.game_state.night_actions[player_id] = {
                        "action": "check",
                        "target": target_id,
                        "result": result
                    }
                    player_obj.add_history(f"第{game_manager.game_state.day}天夜晚：你查驗了玩家{target_id}（{target_player['name']}），結果是{result}")
            
            else:
                # 普通村民沒有夜間行動
                game_manager.game_state.night_actions[player_id] = {
                    "action": "wait",
                    "target": None,
                    "result": None
                }
        
        return jsonify({'success': True})
    
    elif action_type == 'next_phase':
        # 推進遊戲到下一階段
        current_phase = game_manager.game_state.phase
        
        # 根據當前階段執行相應的處理
        if current_phase == "day":
            # 如果是全AI遊戲或已經完成討論，處理AI玩家討論
            if is_all_ai or game_manager.game_state.current_discussions:
                # 觸發AI玩家發言
                asyncio.run(process_ai_discussions(game_id))
            game_manager.game_state.next_phase()  # 進入投票階段
        
        elif current_phase == "vote":
            # 如果是全AI遊戲或人類玩家已投票，處理AI投票
            if is_all_ai or player_id in game_manager.game_state.votes:
                # 觸發AI玩家投票
                asyncio.run(process_ai_votes(game_id))
            game_manager.game_state._process_votes()  # 處理投票結果
            game_manager.game_state.next_phase()  # 進入下一階段
        
        elif current_phase == "night":
            # 如果是全AI遊戲或人類玩家已完成夜間行動，處理AI夜間行動
            if is_all_ai or player_id in game_manager.game_state.night_actions:
                # 觸發AI玩家夜間行動
                asyncio.run(process_ai_night_actions(game_id))
            game_manager.game_state._process_werewolf_attacks()  # 處理狼人攻擊
            game_manager.game_state._update_player_history()  # 更新歷史記錄
            game_manager.game_state.next_phase()  # 進入白天階段
        
        # 檢查遊戲是否結束
        game_manager.game_state.check_game_over()
        
        # 更新客戶端
        socketio.emit('game_update', {'game_id': game_id}, room=game_id)
        
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': '無效的動作'})

async def process_ai_discussions(game_id):
    """處理AI玩家的討論"""
    game_manager = active_games[game_id]
    
    # 獲取所有存活的AI玩家
    ai_players = [(p["player_id"], game_manager.game_state.player_objects[p["player_id"]])
                 for p in game_manager.game_state.players
                 if p["is_alive"] and p["player_id"] not in game_manager.human_players]  # 排除人類玩家
    
    # 為每個AI玩家生成討論
    for player_id, player_obj in ai_players:
        api_handler = game_manager.api_handlers.get(player_id)
        if api_handler:
            discussion = await player_obj.day_discussion(
                game_manager.game_state.get_state_for_player(player_id),
                api_handler
            )
            
            # 添加到當前討論
            player_info = next((p for p in game_manager.game_state.players if p["player_id"] == player_id), None)
            if player_info:
                game_manager.game_state.current_discussions.append({
                    "player_id": player_id,
                    "player_name": player_info["name"],
                    "content": discussion
                })
                
                # 更新所有玩家的歷史記錄
                for p_id, p_obj in game_manager.game_state.player_objects.items():
                    if p_id != player_id:
                        p_obj.add_history(
                            f"第{game_manager.game_state.day}天白天：{player_info['name']}（玩家{player_id}）說：「{discussion}」"
                        )
                
                # 更新自己的歷史記錄
                player_obj.add_history(f"第{game_manager.game_state.day}天白天：你說：「{discussion}」")

async def process_ai_votes(game_id):
    """處理AI玩家的投票"""
    game_manager = active_games[game_id]
    
    # 獲取所有存活的AI玩家
    ai_players = [(p["player_id"], game_manager.game_state.player_objects[p["player_id"]])
                 for p in game_manager.game_state.players
                 if p["is_alive"] and p["player_id"] not in game_manager.human_players]  # 排除人類玩家
    
    # 為每個AI玩家進行投票
    for player_id, player_obj in ai_players:
        api_handler = game_manager.api_handlers.get(player_id)
        if api_handler:
            vote_target = await player_obj.vote(
                game_manager.game_state.get_state_for_player(player_id),
                api_handler
            )
            
            # 添加投票
            game_manager.game_state.votes[player_id] = vote_target
            
            # 添加到玩家歷史記錄
            target_player = next((p for p in game_manager.game_state.players if p["player_id"] == vote_target), None)
            if target_player:
                player_obj.add_history(
                    f"第{game_manager.game_state.day}天投票：你投票給了玩家{vote_target}（{target_player['name']}）"
                )

async def process_ai_night_actions(game_id):
    """處理AI玩家的夜間行動"""
    game_manager = active_games[game_id]
    
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

@socketio.on('join')
def on_join(data):
    """加入遊戲房間"""
    game_id = data.get('game_id')
    if game_id:
        # 正確使用join_room函數
        join_room(game_id)

@app.route('/api/chat/<game_id>', methods=['POST'])
def game_chat(game_id):
    """遊戲內聊天"""
    if game_id not in active_games:
        return jsonify({'success': False, 'error': '遊戲不存在'})
    
    data = request.json
    message = data.get('message')
    player_id = 1  # 人類玩家ID
    
    game_manager = active_games[game_id]
    
    # 檢查是否是全AI遊戲
    is_all_ai = 1 not in game_manager.human_players
    
    if is_all_ai:
        sender_name = "觀察者"
    else:
        player_info = next((p for p in game_manager.game_state.players if p["player_id"] == player_id), None)
        sender_name = player_info['name'] if player_info else "觀察者"
    
    # 廣播消息
    socketio.emit('chat_message', {
        'player_id': player_id,
        'player_name': sender_name,
        'message': message
    }, room=game_id)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    socketio.run(app, debug=True)
