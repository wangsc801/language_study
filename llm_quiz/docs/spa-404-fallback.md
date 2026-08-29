# SPA 路由直达 404（`/quizzes` Not Found）问题排查

> 现象：从前端导航栏进入 `/quizzes` 正常，但从浏览器地址栏直接输入
> `http://<host>:8070/quizzes`（或在该页面刷新）时，返回 RESTful JSON：
> `{"detail":"Not Found"}`（HTTP 404）。

---

## 1. 根因

本项目前端是 **React Router v8 单页应用（SPA）**，构建产物（`index.html` + `assets/*`）
由 FastAPI 通过 `StaticFiles` 托管：

```python
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
```

`StaticFiles(html=True)` 的行为是：

- 当请求路径 **恰好是 `/`** 时，返回目录下的 `index.html`；
- 对**其它任何路径**，都在 `STATIC_DIR` 下按同名路径去**查找真实文件**，找不到就抛 404。

而 `/quizzes` 这类页面既没有 `quizzes.html` 文件，也没有 `quizzes/` 目录，它是纯客户端路由。

两种进入方式的差异：

| 方式 | 发生了什么 | 结果 |
| --- | --- | --- |
| 导航栏点击 | React Router 用 `history.pushState` 在**浏览器本地**切换路由，**不发 HTTP 请求**，SPA 仍停留在已加载的 `/` 页面上 | 正常渲染 |
| 地址栏直达 / 刷新 | 浏览器对 `/quizzes` 发起**完整 HTTP 请求**，后端按真实文件查找失败 → 404 | `{"detail":"Not Found"}` |

即：SPA 的客户端路由在服务端**没有对应的物理文件或回调路由**，缺一个「历史回退
（history fallback）：非 API 路径一律回落到 `index.html`」的兜底。

---

## 2. 额外发现：`/health` 也被 404

排查时用 `curl http://192.168.123.15:8070/health` 实测返回 `{"detail":"Not Found"}`。

原因：原代码里 `app.mount("/", ...)` 写在 `@app.get("/health")` **之前**。根挂载 `/`
会先于 `/health` 匹配，把 `/health` 的请求吞进 StaticFiles → 按文件查找 `health` 不存在 → 404。
也就是说这个探活端点此前一直是失效的。

---

## 3. 修复方案（`backend/main.py`）

改动两处：

### 3.1 把 `/health` 提到静态挂载之前

保证探活端点先被匹配，不再被根挂载吞掉：

```python
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

### 3.2 新增 404 异常兜底，非 API 路径回落到 `index.html`

```python
@app.exception_handler(StarletteHTTPException)
async def spa_fallback(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404 and not request.url.path.startswith("/api"):
        return FileResponse(INDEX_HTML)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
```

要点：

- `StaticFiles` 找不到 `index.html` 之外的文件时是「抛出」`HTTPException(404)`，而不是直接
  发送响应，因此能被 FastAPI 的全局异常处理器捕获。
- 对 `404` **且路径不以 `/api` 开头**的请求，返回 `index.html`，让 React Router 在浏览器端
  接管渲染该路由。
- 对**未知的 `/api/*`**，仍返回标准 JSON 404 `{"detail":"Not Found"}`，保证 API 客户端行为不变。
- 真实存在的静态文件（如 `/favicon.ico`、`/assets/*.js`）由 `StaticFiles` 正常返回，不落入兜底。

> 路由优先级最终为：`/api/*` 各路由 > `/health` > 静态文件 > SPA 兜底（index.html）。
> 注意 `/health` 具名路由必须写在 `app.mount("/", ...)` 之前，否则仍会被根挂载遮蔽。

---

## 4. 修复后验证结果

在本地以测试端口启动 `uvicorn main:app` 后逐项验证：

| 路径 | 期望 | 实测 |
| --- | --- | --- |
| `/` | 200 HTML | 200，返回 `index.html` |
| `/quizzes` | 200 HTML（SPA 兜底） | 200，返回 `index.html` |
| `/health` | 200 JSON | 200，`{"status":"ok"}` |
| `/favicon.ico` | 200 真实文件 | 200 |
| `/assets/*.css` | 200 真实文件 | 200 |
| `/api/settings` | 200 JSON | 200 |
| `/api/nope` | 404 JSON | 404，`{"detail":"Not Found"}` |

---

## 5. 如何让线上容器生效

当前服务运行在 Docker（`docker-compose.yml`，端口映射 `8070:8070`）。代码改动后需要**重建镜像**
才能把新的 `backend/main.py` 打进容器：

```bash
docker compose up -d --build
```

重建期间该服务会短暂中断；请在业务低峰执行。若只用单进程启动（非 compose），等同理重启
uvicorn 进程即可。