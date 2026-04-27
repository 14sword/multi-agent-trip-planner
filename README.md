# AI智能旅行助手

基于Multi-Agent架构的智能旅行规划系统，支持景点搜索、天气查询、酒店推荐等核心功能。

## 项目简介

本项目是一个智能旅行规划助手，能够根据用户输入的目的地、天数、偏好等条件，自动生成完整的旅行计划。系统采用多Agent协作架构，通过LLM实现智能决策，并集成高德地图API实现路线可视化展示。

## 技术栈

### 前端
- **框架**: Vue3 + Composition API
- **语言**: TypeScript
- **UI组件**: Ant Design Vue
- **构建工具**: Vite
- **地图服务**: 高德地图 JavaScript API

### 后端
- **框架**: FastAPI
- **语言**: Python 3.12
- **AI服务**: LLM (支持多种模型)
- **工具协议**: MCP (Model Context Protocol)
- **地图API**: 高德地图 Web服务API

### 架构特点
- 前后端分离架构
- Multi-Agent多智能体协作
- 工具调用自动化
- RESTful API设计

## 核心功能

- [x] AI智能行程规划
- [x] 多Agent协作系统 (景点/天气/酒店专家Agent)
- [x] 高德地图路线展示
- [x] 每日行程详情展示
- [x] 天气信息查询
- [x] 行程编辑与调整
- [x] 预算自动计算
- [x] PDF导出
- [x] 本地收藏功能

## 项目结构

```
helloagents-trip-planner/
├── backend/
│   ├── app/
│   │   ├── agents/          # Agent实现
│   │   │   ├── trip_planner.py  # 旅行规划Agent
│   │   │   └── prompts.py       # 提示词模板
│   │   ├── api/             # API路由
│   │   │   └── routes.py     # 旅行规划接口
│   │   ├── models/          # 数据模型
│   │   │   └── schemas.py    # Pydantic模型
│   │   ├── services/         # 服务层
│   │   │   ├── llm.py        # LLM服务
│   │   │   ├── mcp_client.py # MCP客户端
│   │   │   └── unsplash.py   # 图片服务
│   │   └── config.py         # 配置
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   │   ├── Home.vue      # 首页(表单输入)
│   │   │   └── Result.vue    # 结果页(行程展示)
│   │   ├── services/        # API服务
│   │   │   └── api.ts       # API调用封装
│   │   └── types/           # TypeScript类型
│   │       └── index.ts     # 类型定义
│   ├── package.json
│   └── vite.config.ts
└── start.sh                  # 一键启动脚本
```

## 快速启动

### 环境要求
- Node.js >= 18
- Python >= 3.12
- 高德地图 API Key
- OpenAI API Key (或兼容的LLM服务)

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env，填入你的API密钥

# 启动服务
uvicorn app.main:app --reload --port 8000
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 一键启动

```bash
# 项目根目录下执行
chmod +x start.sh
./start.sh
```

访问 http://localhost:5173 即可使用。

## Agent系统设计

### 架构概述

系统采用多Agent协作架构，包含4个专业Agent：

1. **景点搜索专家** (Attraction Agent)
   - 负责搜索目的地景点信息
   - 调用高德地图POI搜索API

2. **天气查询专家** (Weather Agent)
   - 负责查询目的地天气预报
   - 调用高德地图天气API

3. **酒店推荐专家** (Hotel Agent)
   - 负责搜索合适酒店
   - 根据用户偏好推荐住宿

4. **行程规划专家** (Planner Agent)
   - 负责综合信息生成行程
   - 不调用工具，利用已有信息规划

### 工作流程

```
用户请求 → 景点Agent ─┐
                 ├─→ Planner Agent → 最终行程
     天气Agent ─┤
                 │
     酒店Agent ─┘
```

1. 三个专业Agent并行获取信息
2. Planner Agent综合所有信息生成最终行程
3. 返回结构化的TripPlan数据

## API接口

### 创建旅行计划

```
POST /api/trip/plan
Content-Type: application/json

{
  "city": "北京",
  "days": 3,
  "start_date": "2024-01-15",
  "end_date": "2024-01-17",
  "preferences": "历史文化",
  "budget": "中等",
  "transportation": "公共交通",
  "accommodation": "经济型酒店"
}
```

### 编辑旅行计划

```
POST /api/trip/edit
Content-Type: application/json

{
  "trip_plan": { ... },
  "changes": "调整第二天行程"
}
```

## 配置说明

### 环境变量 (.env)

```env
# 高德地图API
AMAP_API_KEY=your_amap_key

# LLM服务
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

### 高德地图Key申请

1. 访问[高德开放平台](https://lbs.amap.com/)
2. 注册账号并创建应用
3. 获取Web服务API Key
4. 启用地理/搜索/天气服务

## 未来优化方向

- [ ] 添加用户认证系统
- [ ] 实现数据库持久化存储
- [ ] 添加分享功能(云端同步)
- [ ] 扩展更多工具集成(机票预订等)
- [ ] 添加Agent反思和自检能力
- [ ] 实现多轮对话交互
- [ ] 添加图片导出功能
- [ ] Docker容器化部署

## 注意事项

1. 本项目需要有效的API密钥才能正常运行
2. 部分功能(如分享)需要部署云服务器后才能使用
3. 请注意保护个人隐私，不要在公开场合分享API密钥

## License

MIT License