# 🚀 Multi-Agent Trip Planner

### 基于Multi-Agent架构的AI智能旅行规划系统

[![Stars](https://img.shields.io/github/stars/14sword/multi-agent-trip-planner?style=flat-square)](https://github.com/14sword/multi-agent-trip-planner)
[![License](https://img.shields.io/github/license/14sword/multi-agent-trip-planner?style=flat-square)](https://github.com/14sword/multi-agent-trip-planner)
[![Tech Stack](https://img.shields.io/badge/tech-vue3%20%7C%20fastapi%20%7C%20typescript%20%7C%20python-blue?style=flat-square)](https://github.com/14sword/multi-agent-trip-planner)

---

## 🎯 项目亮点

> "3分钟生成个性化旅行计划，让AI Agent帮你做攻略"

### 核心价值
- **AI智能推荐**：基于用户偏好，自动生成专属旅行方案
- **多Agent协作**：景点、天气、酒店专家Agent并行工作，智能决策
- **实时信息整合**：集成高德地图API，获取最新景点和天气数据
- **用户体验优先**：简洁美观的界面，流畅的交互体验

### 技术亮点

| 亮点 | 说明 |
|------|------|
| 🤖 **Multi-Agent架构** | 4个专业Agent并行协作，模拟真实旅行顾问团队 |
| 🔗 **MCP协议应用** | 创新性地将Model Context Protocol应用于工具调用 |
| 🧠 **LLM智能决策** | 利用大语言模型理解用户意图，生成合理行程 |
| 🗺️ **路线可视化** | 高德地图API实现景点路线展示 |
| 📱 **响应式设计** | 适配移动端和桌面端，提供一致体验 |

---

## 💡 技术难点与解决方案

### 难点1：Multi-Agent协作稳定性
**问题**：多个Agent并行调用外部API，如何保证数据一致性？
**解决**：采用"专业Agent获取信息 → Planner Agent综合决策"的架构，通过结构化数据传递保证稳定性。

### 难点2：LLM输出格式控制
**问题**：LLM生成的行程数据格式不稳定，难以直接使用
**解决**：设计严格的Prompt工程，结合JSON解析和格式验证，确保输出可用。

### 难点3：用户体验与功能的平衡
**问题**：功能复杂但要保持界面简洁
**解决**：采用分步式交互，先获取核心信息，再逐步完善细节，降低用户决策负担。

---

## 🛠️ 技术栈

### 前端
<div>
<img src="https://img.shields.io/badge/Vue3-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white" alt="Vue3">
<img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript">
<img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite">
<img src="https://img.shields.io/badge/Ant%20Design%20Vue-1890FF?style=for-the-badge&logo=antdesign&logoColor=white" alt="Ant Design Vue">
</div>

### 后端
<div>
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/LLM-GPT--4o--mini?style=for-the-badge&logo=openai&logoColor=white" alt="LLM">
<img src="https://img.shields.io/badge/MCP-FF6B6B?style=for-the-badge" alt="MCP Protocol">
</div>

### 基础设施
<div>
<img src="https://img.shields.io/badge/Amap-1E90FF?style=for-the-badge&logo=amap&logoColor=white" alt="高德地图">
<img src="https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=node.js&logoColor=white" alt="Node.js">
</div>

---

## 📋 核心功能

- [x] **AI行程规划**：输入目的地和偏好，生成完整旅行方案
- [x] **多Agent协作**：景点/天气/酒店专家Agent智能协作
- [x] **高德地图展示**：景点位置和路线可视化
- [x] **每日行程详情**：景点、时间、费用一目了然
- [x] **天气预报查询**：出发地/目的地实时天气
- [x] **行程编辑调整**：灵活修改行程安排
- [x] **预算自动计算**：智能费用估算
- [x] **PDF导出**：一键导出旅行计划
- [x] **本地收藏**：保存喜欢的行程

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层 (Vue3)                       │
│              Home.vue (输入) → Result.vue (展示)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API层 (FastAPI)                         │
│                  POST /api/trip/plan                        │
│                  POST /api/trip/edit                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent协作层                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Attraction  │  │   Weather    │  │    Hotel     │      │
│  │    Agent     │  │    Agent     │  │    Agent     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│          │                │                │                 │
│          └────────────────┼────────────────┘                 │
│                           ▼                                  │
│                  ┌──────────────┐                           │
│                  │   Planner    │                           │
│                  │    Agent     │                           │
│                  └──────────────┘                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      工具层 (MCP)                            │
│         高德地图POI │ 天气API │ 图片服务 │ LLM服务            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速启动

### 环境要求
- Node.js >= 18
- Python >= 3.12
- 高德地图 API Key
- OpenAI API Key (或其他LLM服务)

### 安装运行

```bash
# 克隆项目
git clone https://github.com/14sword/multi-agent-trip-planner.git
cd multi-agent-trip-planner

# 一键启动（推荐）
chmod +x start.sh && ./start.sh

# 或手动启动
# 1. 后端
cd backend && pip install -r requirements.txt
cp .env.example .env  # 配置API密钥
uvicorn app.main:app --reload --port 8000

# 2. 前端
cd frontend && npm install
npm run dev
```

访问 http://localhost:5173 即可使用。

---

## 📖 Agent系统设计

### 核心思想

传统的旅行规划需要用户自己搜索景点、查天气、找酒店，信息碎片化严重。本项目通过Multi-Agent架构，让AI Agent模拟真实旅行顾问团队的工作方式：

> **用户输入偏好 → Agent团队并行工作 → Planner综合决策 → 输出完整行程**

### 四个专业Agent

| Agent | 职责 | 调用工具 |
|-------|------|---------|
| **Attraction Agent** | 搜索目的地景点 | 高德POI搜索 |
| **Weather Agent** | 查询天气预报 | 高德天气API |
| **Hotel Agent** | 推荐合适住宿 | 高德POI搜索 |
| **Planner Agent** | 综合信息生成行程 | 无（仅做决策） |

### 为什么这样设计？

1. **并行提效**：三个专业Agent同时工作，减少等待时间
2. **专业专注**：每个Agent只做一个领域，信息更精准
3. **智能决策**：Planner Agent综合所有信息，做出合理规划
4. **易于扩展**：新增需求只需添加新的Agent

---

## 🎓 学习心得

作为一个正在学习AI产品经理的大三学生，这个项目让我深刻理解了：

### 技术层面
- **Agent架构**：理解了Multi-Agent协作的实际应用场景
- **Prompt工程**：学会了如何设计有效的提示词
- **系统设计**：前后端分离、API设计、错误处理

### 产品层面
- **用户需求**：旅行规划的核心痛点是"做攻略太麻烦"
- **MVP思维**：先做核心功能，再逐步完善
- **用户体验**：技术强大不够，还要用起来顺手

### 未来规划
- [ ] 添加用户认证系统
- [ ] 实现数据库持久化存储
- [ ] 添加云端分享功能
- [ ] 扩展更多工具集成（机票预订等）
- [ ] 实现Agent反思和自检能力

---

## 📝 License

MIT License - 欢迎star和fork！

---

<div align="center">

**如果你觉得这个项目有帮助，欢迎给我一个⭐**

Made with ❤️ by [14sword](https://github.com/14sword)

</div>