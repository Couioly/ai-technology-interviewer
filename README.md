# AI 技术面试官（interviewer-demo）

一个面向零基础教学的网页版 AI 面试官练习项目。面试官「王哥」是 Java 后端方向的技术考官：先出题，学生作答后打分并弹出评分卡，逐轮记录表现，最后可以把整场面试导出成一份 Markdown 报告。

技术栈：Python 3.11、FastAPI、Jinja2、LangChain 1.x（`create_agent`）、DeepSeek（OpenAI 兼容接口）。对话历史保存在服务进程的内存里（`InMemorySaver`），不依赖数据库。

## 目录结构（逐文件说明）

```
interviewer-demo/
├── README.md                        本文件，项目说明与上手步骤
├── requirements.txt                 依赖清单，共 7 个包，不要擅自新增
├── .env.example                     环境变量模板，复制成 .env 后填写
├── .gitignore                       忽略 .env、虚拟环境、Python 缓存等不应提交的文件
├── run.py                           启动入口，用 uvicorn 跑 app.main:app
└── app/
    ├── __init__.py                  包标记，空文件
    ├── config.py                    读取 .env，暴露三个配置变量，缺 Key 时直接报错
    ├── llm.py                       创建唯一的 ChatOpenAI 实例 llm，全项目共用
    ├── schemas.py                   所有 Pydantic 请求与响应模型
    ├── tools.py                     三个 @tool 工具（出题、打分、记录进度）与 tool_list
    ├── agent.py                     王哥的人设与流程，create_agent 与会话状态读写
    ├── main.py                      创建 FastAPI 应用并注册全部路由
    ├── routers/
    │   ├── __init__.py              包标记，空文件
    │   ├── pages.py                 GET / 渲染聊天页面
    │   ├── chat.py                  POST /api/chat 一轮完整对话
    │   ├── score.py                 POST /api/score 生成结构化评分卡
    │   ├── stream.py                POST /api/chat_stream 与 /api/agent_stream 流式输出
    │   └── report.py                GET /api/report 导出 Markdown 面试报告
    ├── services/
    │   ├── __init__.py              包标记，空文件
    │   ├── score_service.py         用 PydanticOutputParser 生成评分卡
    │   └── report_service.py        把会话历史整理成 Markdown 报告
    └── templates/
        └── index.html               唯一页面，CSS 与 JS 全部内联
```

## 安装步骤

需要 Python 3.11。以下命令都在项目根目录执行。

```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活虚拟环境
# Windows CMD / PowerShell：
.venv\Scripts\activate
# Windows Git Bash：
# source .venv/Scripts/activate
# Linux / macOS：
# source .venv/bin/activate

# 3. 安装依赖（后面 -i 是国内镜像，装得快一些，可省略）
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
```

依赖只有 7 个：`langchain`、`langchain-openai`、`langgraph`、`python-dotenv`、`fastapi`、`uvicorn`、`jinja2`。

已在下列版本组合上跑通，若新版出现不兼容可对照参考：`langchain 1.5.2`、`langchain-openai 1.8.5`、`langgraph 1.2.24`、`fastapi 0.165.0`、`uvicorn 0.54.0`、`jinja2 3.1.6`、`python-dotenv 1.2.4`、`pydantic 2.14.4`。

## .env 配置

把模板复制一份再填写，不要直接改模板：

```bash
# Windows
copy .env.example .env
# Linux / macOS
# cp .env.example .env
```

`.env` 里三项配置：

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | DeepSeek 密钥，必填，缺了启动会报错 | `sk-换成你自己的密钥` |
| `DEEPSEEK_BASE_URL` | 接口地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL_NAME` | 模型名 | `deepseek-chat` |

`.env` 已被 `.gitignore` 忽略，里面是真实密钥，不要提交、不要发给别人。代码统一通过 `app/config.py` 读取，不存在写死在代码里的密钥。

## 启动命令

```bash
python run.py
```

看到 `Application startup complete` 后：

- 聊天页面：http://127.0.0.1:8000
- 接口文档：http://127.0.0.1:8000/docs

`run.py` 固定监听 `127.0.0.1:8000`，并开启 `reload=True`，改代码会自动重启。

## 接口清单

打开 `/docs` 可以直接看到并试用全部接口。

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/` | 聊天页面 |
| POST | `/api/chat` | 一轮完整对话，返回 `reply`、`question`、`scored` |
| POST | `/api/score` | 对一道题和一份回答生成评分卡，返回分数、优缺点、建议 |
| POST | `/api/chat_stream` | 裸模型的流式输出（SSE），用于对比打字机效果 |
| POST | `/api/agent_stream` | Agent 的流式输出（SSE），逐字显示，末尾附带本轮是否打分 |
| GET | `/api/report` | 导出本次面试报告，浏览器直接下载 `interview-report.md` |

## 使用流程

1. 打开页面，输入「我准备好面试了，方向 java」，王哥会出一道题。
2. 认真作答后，页面弹出评分卡；只回「嗯」之类的话不会打分，也不会弹卡。
3. 想结束时点标题右侧的「导出报告」，下载 `interview-report.md`。

## 两点要注意

- 对话历史只存在服务进程的内存里，**重启服务会清空**。刚重启就导出报告，会得到一份「尚未产生题目、未评分」的空报告。
- 报告按「出题工具被调用的次数」划分轮次，模型偶尔一轮连出两道题，没作答的轮次会写「未记录」「未评分」，属于正常现象，不是报错。
