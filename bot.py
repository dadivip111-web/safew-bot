import requests
import time
import threading
from flask import Flask

# ========== 配置区 ==========
BOT_TOKEN = "13315694:3DeXn2PLZL87EKaCgSCUjTUwtTA_qEEoHyY"
API = "https://api.safew.org/bot" + BOT_TOKEN
PUSH_CHAT_ID = 10000550625

# Groq配置
API_KEY = "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"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

# 私聊&控制指令白名单
ALLOW_PRIV_IDS = {12936171, 13292834}
ADMIN_ID = 0

# 图片配置
PHOTO_ID = "tos-cn-i-a9rns2r198/505333243eb24c6fbff2cc068c729cbb.png"

# 定时与冷却
INTERVAL = 5400
COOLDOWN = 10
last_reply_time = {}

# AI全局开关：默认一直开启
ai_enabled = True
# ===========================

# 保活服务
app = Flask("")
@app.route('/')
def home():
    return "Bot is alive"

def run_server():
    app.run(host='0.0.0.0', port=8080)

# AI聊天
def ai_chat(text):
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "你是体育交流群高情商老群友风格，会主动接群里日常聊天、暖场互动。看到群里发赛事计划和走势推荐时，偶尔自然带动气氛，可以说：机会来了可以跟上计划员吃肉啦、行情不错看准节奏跟上稳稳吃肉、把握时机跟着计划员节奏就行这类话术，不要刷屏。遇到群友抱怨、心情不好、心态崩溃时，只会共情安抚、温柔鼓励打气，绝不讲大道理、不说教。有人问网址、入口、想参与要玩链接时，委婉引导对方私聊管理获取正规官方通道，不要自己发链接。全程只围绕体育赛事、赛事计划、走势闲聊，严禁出现违法、违规、风险、劝阻、戒玩等敏感说教字眼，语气接地气、智能化、像真人一样聊天。"},
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

# 发文字
def send_text(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=8)
        return True
    except:
        return False

# 发图文
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
    global ai_enabled
    offset = 0
    print("✅ 机器人启动成功")
    last_push_time = time.time()
    
    while True:
        # 定时广告推送
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

                # ========== 白名单专属：开启 / 关闭 只回复收到 ==========
                if uid in ALLOW_PRIV_IDS:
                    if text == "开启":
                        ai_enabled = True
                        send_text(cid, "收到")
                        continue
                    if text == "关闭":
                        ai_enabled = False
                        send_text(cid, "收到")
                        continue
                # =============================================

                # AI没开启直接跳过所有AI回复
                if not ai_enabled:
                    continue

                # 私聊处理
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
    # 启动保活（防止 Railway 休眠断线）
    threading.Thread(target=run_server, daemon=True).start()
    # 启动机器人
    main()
