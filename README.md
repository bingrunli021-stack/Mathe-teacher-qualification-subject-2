# 2027 高中数学教资 · 科目二

私人学习网站。GitHub Pages 提供静态界面；Supabase Auth + RLS 保护教材及个人学习数据。

## 当前状态

- 已导入九章、47节目录；其他章节的知识点层级尚待数字化。
- 第一章24个知识点，以及教材第3—62页共60张原页已保存在受权限保护的数据库。
- OCR 全文仍待逐页校对，低置信度另行标注。相邻知识点共页时保留整页。
- 原页保留原始表格、重点框、段落；当前尚未完成结构化文字表格重建。
- AI解释、复习建议、易错点和自评题与教材分开。自测为口述自评题，尚需补充标准选择题。
- 已实现登录、会员访问控制、追加式同步、笔记历史、收藏、高亮、计时、每日计划、复习、深浅色及阅读设置。
- 已部署：https://bingrunli021-stack.github.io/Mathe-teacher-qualification-subject-2/ 。用户已明确批准公开代码仓库及其附带影响，GitHub Pages使用Actions部署并强制HTTPS。登录页已通过在线浏览器检查。

## 数据边界

唯一教材来源为用户上传的《（科目二瘦版）中公教资高中数学.pdf》。原PDF、扫描页与完整OCR均不提交GitHub，不放在web目录。

前端只有Supabase公开key；没有service_role。即使知道接口地址，匿名用户不能读取教材，未在tq_members中的登录账号也不能读取。个人事件按auth.uid()隔离，只能追加，不能更新或删除历史。每日计划和时间由服务器生成；持续三天未达标后减量，不累积旧任务。

## 开发与部署

`node --check web/app.js`、`node --check web/model.js` 和 `node --test tests/*.test.cjs`。

Pages发布目录为`web`。`.github/workflows/pages.yml`负责检查及发布。先在GitHub仓库设置中启用Pages（GitHub Actions来源）。

`db/schema.sql`是初始结构，`db/002_event_safety.sql`是后续加固。现有数据库已应用，请勿重复运行初始化脚本。新环境需要管理员将授权用户加入tq_members。

`scripts/prepare_import.py`以用户PDF、OCR目录和仓库外的输出目录为三个参数，生成私有导入数据。生成结果不得提交仓库。

## 验证及待办

通过：四项模型测试（重复同步、乱序多设备记录、笔记版本、北京时间日期），数据库计划生成回滚测试，匿名权限检查，非会员RLS隔离检查，60页完整性及同源哈希检查。

待办：第一章逐页OCR校对、精确知识点边界、结构化表格、补充自测题、真实登录后的跨设备与计时端到端验收。已完成线上登录页浏览器检查；登录后的阅读、计时与多设备同步仍待端到端验收。第一章验收前不批量导入其他章节正文。

安全顾问未报告教资表RLS问题；项目层面的泄露密码检测未启用，参考 https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection 。

## 依赖

`web/supabase.js`保留上一轮提供的固定2.57.4版Supabase JS浏览器包。使用版本固定的本地副本，不依赖浮动CDN版本。
