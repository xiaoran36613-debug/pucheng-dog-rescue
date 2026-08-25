# 浦城仁爱流浪动物救助基地网站

## 📁 项目结构

```
pucheng-dog-rescue/           ← 项目根目录
│
├── api/
│   └── app.py                ← 后端代码（Flask）
│
├── templates/                ← 网页模板
│   ├── index.html            ← 首页（展示待领养狗狗）
│   ├── dog\_detail.html       ← 狗狗详情页
│   ├── donate.html           ← 爱心捐助页
│   ├── about.html            ← 关于我们页
│   └── admin/
│       ├── login.html        ← 管理员登录页
│       ├── dashboard.html    ← 后台首页（狗狗列表）
│       ├── dog\_form.html     ← 添加/编辑狗狗表单
│       └── settings.html     ← 基地设置页
│
├── static/                   ← 静态文件
│   ├── css/
│   │   ├── style.css         ← 前台样式
│   │   └── admin.css         ← 后台样式
│   └── js/                   ← 以后可以在这里放 JS 文件
│
├── requirements.txt          ← Python 依赖包列表
├── vercel.json             ← Vercel 部署配置
└── README.md               ← 本文件（部署教程）
```

\---

## 🚀 部署步骤（按顺序做）

### 第一步：注册 MongoDB Atlas（数据库）

1. 打开 https://www.mongodb.com/atlas
2. 用邮箱注册一个免费账户
3. 创建新集群，选择 **M0（免费版）**
4. 区域选 **Asia Pacific (Singapore)** 或 **Asia Pacific (Mumbai)**
5. 创建数据库用户，记住用户名和密码
6. 在 Network Access 里，点击 **Add IP Address** → 选 **Allow Access from Anywhere**（0.0.0.0/0）
7. 回到 Database → 点击 **Connect** → 选 **Drivers** → Python → 复制连接字符串
8. 连接字符串长这样：

```
   mongodb+srv://用户名:密码@cluster0.xxxxx.mongodb.net/pucheng\_dogs?retryWrites=true\&w=majority
   ```

   把 `用户名` 和 `密码` 替换成你刚才创建的

### 第二步：注册 Vercel（网站托管）

1. 打开 https://vercel.com
2. 用 GitHub 账号登录（如果没有 GitHub，先注册 https://github.com）
3. 登录后进入 Vercel Dashboard

### 第三步：把代码上传到 GitHub

1. 在 GitHub 上创建一个新仓库（Repository），名字叫 `pucheng-dog-rescue`
2. 把本项目的所有文件上传到这个仓库

   * 可以直接在 GitHub 网页上逐个上传文件
   * 或者用 Git 命令（如果你会用的话）
3. **重要**：确保文件结构和上面列的一致

### 第四步：在 Vercel 部署

1. 在 Vercel Dashboard 点击 **Add New...** → **Project**
2. 选择你刚才创建的 GitHub 仓库 `pucheng-dog-rescue`
3. 点击 **Import**
4. 配置项目：

   * Framework Preset: **Other**
   * Root Directory: `./`（默认）
5. 点击 **Environment Variables**，添加：

   * 1\.
   * Name: MONGODB\_URI
   * Value: 你第一步复制的 MongoDB 连接字符串
   * 
   * 2\.
   * Name: SECRET\_KEY
   * Value: 一串足够长的随机字符串
   * 
   * 3\.
   * Name: ADMIN\_USERNAME
   * Value: admin
   * 
   * 4\.
   * Name: ADMIN\_PASSWORD
   * Value: 你自己设置的管理员密码
6. 点击 **Deploy**
7. 等待 1-2 分钟，部署完成后会显示一个网址，比如 `https://pucheng-dog-rescue.vercel.app`

### 第五步：访问后台

1. 打开 `https://你的网址/admin`
2. 用户名：使用部署时设置的 `ADMIN\_USERNAME`（默认是 `admin`）
3. 密码：使用部署时设置的 `ADMIN\_PASSWORD`
4. 登录后可以：

   * 添加/编辑/删除狗狗
   * 修改基地信息（微信、电话、地址等）
   * 上传微信群二维码
   * 修改管理员密码

\---

## 📝 叔叔如何使用

### 添加一只新狗狗

1. 打开 `https://你的网址/admin`
2. 用密码登录
3. 点击右上角 **"+ 添加新狗狗"**
4. 填写：

   * 名字（必填）
   * 年龄、性别、品种
   * 性格特点、健康状况
   * 它的故事（可选）
   * 上传照片（点击"选择照片"）
5. 点击 **"保存"**
6. 回到首页就能看到这只狗狗了

### 修改基地信息

1. 后台左侧点击 **"基地设置"**
2. 修改：基地名称、简介、微信号、电话、地址
3. 上传微信群二维码（捐助页面会显示）
4. 点击 **"保存设置"**

### 狗狗被领养了怎么办？

1. 在狗狗列表找到这只狗
2. 点击 **"编辑"**
3. 把"状态"改成 **"已领养"**
4. 保存后，首页就不会再显示了

\---

## 🔧 常见问题

**Q: 部署失败怎么办？**
A: 检查 Vercel 的 Build Logs，通常是 MongoDB 连接字符串写错了。确保密码里没有特殊字符，如果有，需要 URL 编码。

**Q: 照片上传不了？**
A: MongoDB 免费版有 512MB 限制，照片不要太大（建议每张 500KB 以内）。如果超限，需要清理旧照片或升级数据库。

**Q: 访问很慢？**
A: Vercel 免费版服务器在国外，国内访问可能稍慢。如果在意速度，可以考虑买国内服务器（阿里云/腾讯云，约 100 元/年）。

**Q: 想换密码？**
A: 在后台"基地设置"页面最下面，可以修改管理员密码。

\---

## 💡 给叔叔的小红书/抖音引流建议

叔叔发视频/图文时，在文案最后加一句：

> "更多待领养的毛孩子请看主页链接 👉 \[你的网站地址]"

把网站地址放在：

* 小红书：主页简介（放链接）
* 抖音：主页简介或评论区置顶

\---

**技术栈**：Python + Flask + MongoDB + Vercel
**制作日期**：2026年8月

