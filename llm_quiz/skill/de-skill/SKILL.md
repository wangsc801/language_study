---
name: german-article-quiz (de)
description: Run a German dative/accusative article fill-in-the-blank quiz — fetch questions via skill/SOP.py, present them, grade the user's answers, and give 解析. Invoke when the user wants to practice 第三/第四格 阳性冠词 (dem/einem/den/einen).
---

# 德语第三/第四格阳性冠词练习

运行 `skill/SOP.py` 拉取一批全新题目（POST `http://localhost:8070/api/quiz/generate?lang=de&slug=article-case`），
组织成一次填空测验，批改并解析。

## 触发条件
用户想练习德语第三格（Dativ）/第四格（Akkusativ）阳性冠词、`dem/einem` vs `den/einen`、定/不定冠词。

## 步骤

1. 运行 `python skill/SOP.py`（stdout 即 JSON，含 `questions` 与 `answers` 两块）。
   - SOP.py 已自动剥离 `keyword`，并保证 `questions` 不含答案。
   - 若请求失败（后端未启动），向用户报告，不编造题目。

2. 把 `questions` 中每个题目的 `sentenceQuiz`（`____` 处）作为考题展示给用户。
   每题展示：`number`、`category`（Dativ/Akkusativ）、`type`（定冠词/不定冠词）、
   `sentenceQuiz`、`translation`、`hintZh`（如需）。
   **绝不展示 `answers` 里的 `rightAnswer`/`sentence`。**

3. 让用户作答。答案格式不唯一，按 `[，,、\s]+` 切分即可：
   - `"dem, einen"` / `"dem einen"` / `"dem，einen"` 均可。
   - 接受顺序任意；若用户按题目顺序逐题作答也可对照 `number`。

4. 批改（对 `answers` 中各题 `rightAnswer`，忽略大小写）：
   - 标记每题对/错。
   - 只把用户答对的题替换为 `✓`，随后**重点解析做错的题**。

5. 解析时至少讲清两点（尤其针对错题）：
   - **格**：`Dativ`（第三格，间接宾语/指向对象，常伴随 mit/von/bei/nach）阳性用
     定冠词 `dem` / 不定冠词 `einem`；`Akkusativ`（第四格，直接宾语/承受者，常伴随
     für/ohne/gegen）阳性定冠词 `den` / 不定冠词 `einen`。
   - **定/不定**：确指、上文提过、或语境唯一用定冠词（den/dem）；泛指、首次引入用
     不定冠词（einen/einem）。
   - 用 `answers[*].sentence` 还原完整句示范正确冠词在句中的位置。

## 输出
- 先给出题号 + `sentenceQuiz` + translation，让用户作答。
- 作答后：正确项打 `✓`，错误项给出 `rightAnswer` + 对应句子 + 上面 5 的解析。
- 结束可汇总得分（对 N / 共 M）。

## 边界
- `answers` 仅供批改与解析，不得展示给用户。
- 保持 `sentenceQuiz` 原样，不要把答案填回 `____` 作为考题。