---
name: japanese-verb-conjugation-quiz (ja)
description: Run a Japanese verb-conjugation fill-in-the-blank quiz — fetch questions via skill/ja-skill/SOP.py, present them, grade the user's answers, and give 解析. Invoke when the user wants to practice 动词变形 (て形/た形/ます形) 或一段/五段/カ変/サ変动词.
---

# 日语动词变形练习

运行 `skill/ja-skill/SOP.py` 拉取一批全新题目（POST `http://localhost:8070/api/quiz/generate?lang=ja&slug=verb-conjugation`），
组织成一次填空测验，批改并解析。

## 触发条件
用户想练习日语动词变形填空，如 `て形`/`た形`/`ます形`，或一段/五段/カ変/サ変动词。

## 步骤

1. 运行 `python skill/ja-skill/SOP.py`（stdout 即 JSON，含 `questions` 与 `answers` 两块）。
   - SOP.py 已自动剥离 `keyword`，并保证 `questions` 不含答案。
   - 若请求失败（后端未启动），向用户报告，不编造题目。

2. 把 `questions` 中每个题目的 `sentenceQuiz`（`____` 处）作为考题展示给用户。
   每题展示：`number`、`category`（一段/五段/カ変/サ変动词）、`type`（て形/た形/ます形）、
   `sentenceQuiz`、`translation`、`hintZh`（如需）。
   **绝不展示 `answers` 里的 `rightAnswer`/`sentence`/`keyword`。**

3. 让用户作答。答案格式不唯一，按 `[，,、\s]+` 切分即可：
   - `"食べて, 寝た"` / `"食べて 寝た"` / `"食べて、寝た"` 均可。
   - 接受顺序任意；若用户按题目顺序逐题作答也可对照 `number`。

4. 批改（对 `answers` 中各题 `rightAnswer`，忽略大小写）：
   - 标记每题对/错。
   - 只把用户答对的题替换为 `✓`，随后**重点解析做错的题**。

5. 解析至少讲清两点（尤其针对错题）：
   - **变形规则**：
     - 一段动词（Ｖる）：去 `る` 接 `て/た/ます`（如 食べる→食べて/食べた/食べます）。
     - 五段动词：按词尾对应音变形——
       て形常见：書く→書いて、飲む→飲んで、使・行く→行って；
       た形即把 て 变 た（行った、飲んだ、読んだ）；
       ます形：连用形 + ます（書きます、飲みます、読みます）。
     - カ変（来る→来て/来た/来ます）、サ変（する→して/した/します）。
   - **语义**：`て形`（连用，表示方式/先后/并列等）、`た形`（过去/完成）、`ます形`（礼貌体）。
   - 结合 `category` 判断用户是否搞错动词类别，用 `answers[*].sentence` 还原完整句示范。

## 输出
- 先给出题号 + `sentenceQuiz` + translation，让用户作答。
- 作答后：正确项打 `✓`，错误项给出 `rightAnswer` + 对应句子 + 上面 5 的解析。
- 结束可汇总得分（对 N / 共 M）。

## 边界
- `answers` 仅供批改与解析，不得展示给用户。
- 保持 `sentenceQuiz` 原样，不要把答案填回 `____` 作为考题。