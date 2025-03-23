# 狼人殺 Web 遊戲

這是一個基於 Web 的狼人殺遊戲，使用 AI 來扮演遊戲角色。

## 功能特點

- 支持多種 AI 模型 (OpenAI GPT 和 Anthropic Claude)
- 基於 Web 的用戶界面，無需安裝其他軟件
- 即時遊戲更新和聊天功能
- 支持不同角色：村民、狼人、預言家

## 安裝

1. 克隆本項目
```bash
git clone https://github.com/yourusername/werewolf_web_game.git
cd werewolf_web_game
```

2. 安裝依賴
```bash
pip install -r requirements.txt
```

3. 設置環境變量

複製 `.env.example` 文件為 `.env` 並填入你的 API keys:
```bash
cp .env.example .env
```

編輯 `.env` 文件，設置 API keys:
```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
SECRET_KEY=your_secret_key
```

## 運行

啟動 Flask 服務器:
```bash
python app.py
```

打開瀏覽器訪問：http://localhost:5000

## 遊戲規則

狼人殺是一款經典的多人推理遊戲，玩家扮演村民或狼人，進行推理和欺騙。

### 角色介紹

- **村民**: 普通村民沒有特殊技能，他們的目標是識別並投票處決狼人。
- **狼人**: 每晚可以選擇一名玩家進行襲擊。狼人的目標是消滅所有非狼人玩家。
- **預言家**: 每晚可以查驗一名玩家，得知其是否為狼人。預言家是村民陣營的重要角色。

### 遊戲流程

1. **夜晚階段**:
   - 狼人選擇一名玩家進行襲擊
   - 預言家選擇一名玩家進行查驗

2. **白天階段**:
   - 公布夜晚死亡的玩家
   - 所有玩家進行討論，嘗試推理出狼人的身份

3. **投票階段**:
   - 所有存活的玩家投票選出一名可疑的玩家
   - 得票最多的玩家被處決，公布其真實身份

### 勝利條件

- **村民陣營勝利**: 當所有狼人都被處決
- **狼人陣營勝利**: 當狼人數量大於或等於村民數量

## 技術棧

- **後端**: Flask, Socket.IO
- **前端**: HTML, CSS, JavaScript, Bootstrap
- **AI**: OpenAI GPT, Anthropic Claude

## 貢獻

歡迎提交 Issues 和 Pull Requests!

## 許可

MIT License
