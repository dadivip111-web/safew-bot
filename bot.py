import requests
import time
# 👇 只加了这两个保活需要的库，其他完全不动
import threading
from flask import Flask

# ========== 配置区 ==========
BOT_TOKEN = "13315694:3DeXn2PLZL87EKaCgSCUjTUwtTA_qEEoHyY"
API = "https://api.safew.org/bot" + BOT_TOKEN
PUSH_CHAT_ID = 10000550625

# 你的 Groq 密钥
API_KEY = "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"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

# 私聊白名单（你的ID已添加：12936171、13292834）
ALLOW_PRIV_IDS = {12936171, 13292834}
ADMIN_ID = 0

# 图片配置
PHOTO_ID = "tos-cn-i-a9rns2rl98/505333243eb24c6fbff2cc068c729cbb.png"

# 定时与冷却
INTERVAL = 5400
COOLDOWN = 10
last_reply_time = {}
# ===========================

# ======================================
# 👇 保活代码（完全不影响你原有功能）
# ======================================
app = Flask(__name__)

@app.route("/")
def index():
    return "✅ BOT RUNNING - KEEP ALIVE SUCCESS"

def run_keep_alive():
    app.run(host="0.0.0.0", port=5000)

# AI 聊天函数
def ai_chat(text):
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "你是一个友好、简洁、自然的群聊助手。"},
                {"role": "user", "content": text}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        res = requests.post(API_URL, headers=headers, json=data, timeout=15)
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("AI错误:", e)
        return "暂时无法回复，请稍后再试~"

# 发送文字
def send_text(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=8)
        return True
    except:
        return False

# 发送图文
def send_photo_or_text(chat_id, text):
    try:
        requests.post(f"{API}/sendPhoto", json={
            "chat_id": chat_id,
            "photo": PHOTO_ID,
            "caption": text
        }, timeout=8)
    except:
        send_text(chat_id, text)

def main():
    offset = 0
    print("✅ 机器人启动成功（Groq官方稳定AI）")
    last_push_time = time.time()
    
    while True:
        # 定时广告
        if time.time() - last_push_time >= INTERVAL:
            ad_text = """🎉 每日赛事精选更新啦

▫️ 实时赛事动态与分析
▫️ 专属服务入口与活动同步
▫️ 邀请好友一起玩，共享福利

📌 官方通道：https://sfw.vc/tiyubot/tiyuvip
🤝 好友邀请：ly9t.top
💬 合作咨询：@adao6"""
            send_photo_or_text(PUSH_CHAT_ID, ad_text)
            last_push_time = time.time()

        try:
            res = requests.get(f"{API}/getUpdates",
                params={"offset": offset, "timeout": 10}, timeout=15).json()
            if "result" not in res:
                time.sleep(2)
                continue

            for item in res["result"]:
                offset = item["update_id"] + 1
                msg = item.get("message", {})
                text = msg.get("text", "").strip()
                cid = msg.get("chat", {}).get("id")
                uid = msg.get("from", {}).get("id")

                # ======================
                # 私聊处理逻辑（已修复：变量名正确，白名单用户私聊支持AI回复）
                # ======================
                is_private = (cid == uid)
                if is_private:
                    if uid in ALLOW_PRIV_IDS:
                        if text == "我的id":
                            send_text(cid, f"🆔 你的用户ID：\n{uid}")
                        elif len(text) >= 2:
                            ai_res = ai_chat(text)
                            send_text(cid, ai_res)
                    continue

                # 管理员说话不回复
                if uid == ADMIN_ID:
                    continue
                # 防刷屏冷却
                if uid in last_reply_time and time.time() - last_reply_time[uid] < COOLDOWN:
                    continue
                last_reply_time[uid] = time.time()

                # 新人进群欢迎
                if msg.get("new_chat_members"):
                    welcome = """👋 欢迎新朋友加入本群！

这里是体育赛事官方合作平台，为你提供：
▫️ 每日赛事动态与前瞻
▫️ 专属服务入口与活动同步
▫️ 邀请好友一起玩，共享福利

📌 官方通道：https://sfw.vc/tiyubot/tiyuvip
如有任何问题，可联系客服 @adao6 咨询~"""
                    send_photo_or_text(cid, welcome)
                    continue

                # 关键词回复
                if text in ["/start", "开始", "你好", "您好", "hi", "哈喽"]:
                    content = """🎉 欢迎加入体育赛事专属福利平台！

这里为你提供：
▫️ 每日赛事动态与分析
▫️ 邀请好友福利活动
▫️ 专属客服1v1服务

回复关键词快速体验：
「邀请」- 查看好友邀请福利
「官网」- 进入官方服务通道
「客服」- 联系合作咨询"""
                    send_photo_or_text(cid, content)
                    continue

                elif text in ["邀请", "邀请链接", "赚钱", "/invite"]:
                    content = """🤝 好友邀请福利说明

▫️ 分享专属链接给好友，一起解锁平台福利
▫️ 邀请越多，可解锁的权益越多
▫️ 邀请链接：ly9t.top

📌 如有疑问，可联系客服 @adao6 咨询"""
                    send_photo_or_text(cid, content)
                    continue

                elif text in ["官网", "平台", "入口", "网站", "/website"]:
                    content = """📌 官方服务通道

▫️ 实时赛事资讯同步
▫️ 平台最新活动公告
▫️ 专属服务与活动入口

官方通道：https://sfw.vc/tiyubot/tiyuvip
请通过官方渠道访问，保障账户安全。"""
                    send_photo_or_text(cid, content)
                    continue

                elif text in ["客服", "联系", "代理", "咨询", "/contact"]:
                    send_photo_or_text(cid, "如需合作咨询，请联系 @adao6")
                    continue

                # 群里普通消息 → AI 智能回复
                if len(text) >= 2:
                    reply = ai_chat(text)
                    send_text(cid, reply)

        except KeyboardInterrupt:
            print("\n✅ 机器人已安全退出")
            break
        except Exception as e:
            print("⚠️ 异常，5秒后重试:", e)
            time.sleep(5)

if __name__ == "__main__":
    # 👇 只加了这一行启动保活，其他完全不动
    threading.Thread(target=run_keep_alive, daemon=True).start()
    main()