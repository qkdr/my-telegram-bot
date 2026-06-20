import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import json
import os
import html

# CONFIGURATION / الإعدادات الأساسية
TOKEN = "8836591522:AAEj-UUm8vrxpItR04jsHRSWZ6Dl0-QuPCo"
DEV_ID = 8005094095
bot = telebot.TeleBot(TOKEN)

# DATA FILES / ملفات حفظ البيانات
USERS_FILE = "users.json"
CHANNELS_FILE = "channels.json"
GROUPS_FILE = "groups.json"

def load_data(file_name, default_data):
    if not os.path.exists(file_name):
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(default_data, f)
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(file_name, data):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

users = load_data(USERS_FILE, [])
channels = load_data(CHANNELS_FILE, [])
groups = load_data(GROUPS_FILE, [])

# لحفظ بيانات التصفح والبحث
user_states = {}
search_states = {}

# === FUNCTIONS / دالات التحقق ===

def is_subscribed(user_id):
    if user_id == DEV_ID: return True
    if not channels: return True
    for ch in channels:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status in ['left', 'kicked']: return False
        except Exception:
            continue
    return True

def force_sub_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        try:
            ch_name = bot.get_chat(ch).title
        except Exception:
            ch_name = ch
        link = f"https://t.me/{ch.replace('@', '')}"
        markup.add(InlineKeyboardButton(text=f"📢 {ch_name}", url=link))
    markup.add(InlineKeyboardButton(text="✅ تحقق من الاشتراك", callback_data="check_sub"))
    return markup

def main_menu_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🔹 سكربتات", callback_data="menu_scripts"),
        InlineKeyboardButton("🔥 هاكات روبلكس", callback_data="menu_hacks"),
        InlineKeyboardButton("➕ أضفني لمجموعتك", callback_data="menu_add_group")
    )
    return markup

def format_script_message(script):
    desc = html.escape(script.get("title", "بدون وصف"))
    game_name = html.escape(script.get("game", {}).get("name", "ماب عام / Universal"))
    key_sys = "نعم 🔐" if script.get("key") else "لا 🔓"
    verified = "نعم ✅" if script.get("verified") else "لا ❌"
    views = script.get("views", 0)
    
    created_at = script.get("createdAt", "")
    date_str = created_at[:10] if len(created_at) >= 10 else "غير معروف"
    
    script_code = html.escape(script.get("script", "لا يوجد كود"))
    
    img_url = script.get("image", "")
    if img_url.startswith("/"):
        img_url = f"https://scriptblox.com{img_url}"
    elif not img_url:
        img_url = script.get("game", {}).get("imageUrl", "")
        if img_url.startswith("/"):
            img_url = f"https://scriptblox.com{img_url}"

    preview_link = f'<a href="{img_url}">&#8205;</a>' if img_url else ""
    
    text = (f"{preview_link}🔹 الوصف: {desc}\n"
            f"🎮 الماب: {game_name}\n"
            f"🔐 نظام مفاتيح: {key_sys}\n"
            f"✅ تم التحقق: {verified}\n"
            f"👁️ مشاهدات: {views}\n"
            f"🕘 تاريخ النشر: {date_str}\n\n"
            f"📜 السكربت:\n"
            f'<pre><code class="language-lua">{script_code}</code></pre>')
    return text

# === NEW CHAT MEMBERS / حدث إضافة البوت للمجموعة ===

@bot.message_handler(content_types=['new_chat_members'])
def on_bot_added(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            chat = message.chat
            
            # جلب معلومات المجموعة والمشرفين
            try:
                admins = bot.get_chat_administrators(chat.id)
                owner = next((admin for admin in admins if admin.status == 'creator'), None)
                admin_count = len(admins)
            except:
                owner = None
                admin_count = "غير معروف"

            try: member_count = bot.get_chat_member_count(chat.id)
            except: member_count = "غير معروف"
            
            desc = chat.description or "لا يوجد وصف"
            
            try: link = bot.export_chat_invite_link(chat.id)
            except: link = f"@{chat.username}" if chat.username else "لا يمكن توليد الرابط (البوت ليس مشرفاً)"

            owner_name = owner.user.first_name if owner else "غير معروف"
            owner_user = f"@{owner.user.username}" if owner and owner.user.username else owner_name
            owner_url = f"tg://user?id={owner.user.id}" if owner else None

            # 1. إرسال التفاصيل للمطور
            dev_msg = (f"📥 تم اضافة البوت في مجموعة جديدة!\n\n"
                       f"• اسم المجموعة: {chat.title}\n"
                       f"• وصف المجموعة: {desc}\n"
                       f"• عدد الاعضاء: {member_count}\n"
                       f"• عدد المشرفين: {admin_count}\n"
                       f"• رابط المجموعة: {link}\n"
                       f"• مالك المجموعة: {owner_user}")
            try: bot.send_message(DEV_ID, dev_msg)
            except: pass

            # 2. إرسال الترحيب في المجموعة
            welcome_text = (f"شكراً على الاضافه البوت الى مجموعه {chat.title}\n"
                            f"🤖 هذا البوت يوفر لك:\n"
                            f"• سكربتات Roblox متنوعة\n"
                            f"• أحدث السكربتات المضافة\n"
                            f"• بحث سريع وسهل\n"
                            f"• تحديثات مستمرة\n\n"
                            f"📋 استخدم الأزرار بالأسفل للتنقل بين الأقسام واختيار السكربت الذي تريده.\n\n"
                            f"📌 بدون حقوق مجانا بالكامل")
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔹 استكشف السكربتات", callback_data="menu_scripts"))
            if owner_url:
                markup.add(InlineKeyboardButton("مالك الكروب 👑", url=owner_url))
            
            bot.send_message(chat.id, welcome_text, reply_markup=markup)

# === COMMANDS / الأوامر الأساسية ===

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # تعطيل البداية في المجموعات المعطلة
    if message.chat.type in ['group', 'supergroup'] and message.chat.id not in groups:
        return

    if user_id not in users:
        users.append(user_id)
        save_data(USERS_FILE, users)
        username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"
        total_users = len(users)
        
        dev_msg = (f"تم دخول شخص جديد إلى البوت 👾\n"
                   f"• الاسم : {message.from_user.first_name}\n"
                   f"• معرف : {username}\n"
                   f"• الايدي : {user_id}\n"
                   f"• عدد الأعضاء الكلي : {total_users}")
        try: bot.send_message(DEV_ID, dev_msg)
        except Exception: pass

    if not is_subscribed(user_id):
        bot.send_message(message.chat.id, "⚠️ يرجى الانضمام الى القنوات التالية ثم اضغط تحقق:", reply_markup=force_sub_markup())
        return

    text = "أهلاً بك في بوت السكربتات والهاكات المطور 🎮!\nاختر القسم الذي تريده من الأزرار الشفافة أدناه:"
    bot.send_message(message.chat.id, text, reply_markup=main_menu_markup())

# === تفعيل وتعطيل المجموعات ===

@bot.message_handler(func=lambda m: m.text in ['تفعيل البوت', 'تعطيل البوت'] and m.chat.type in ['group', 'supergroup'])
def manage_group_activation(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # التحقق من الصلاحيات
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status not in ['creator', 'administrator'] and user_id != DEV_ID:
            name = message.from_user.first_name or f"@{message.from_user.username}"
            bot.reply_to(message, f"❌ ليس لديك الاذن يا {name}")
            return
    except:
        bot.reply_to(message, "❌ حدث خطأ في التحقق من الصلاحيات (يرجى التأكد من أن البوت مشرف).")
        return

    if message.text == 'تفعيل البوت':
        if chat_id not in groups:
            groups.append(chat_id)
            save_data(GROUPS_FILE, groups)
        bot.reply_to(message, "✅ تم تفعيل البوت في هذه المجموعة بنجاح. يمكن للأعضاء الآن استخدامه.")
    
    elif message.text == 'تعطيل البوت':
        if chat_id in groups:
            groups.remove(chat_id)
            save_data(GROUPS_FILE, groups)
        bot.reply_to(message, "🛑 تم تعطيل البوت في هذه المجموعة بنجاح. لن يتفاعل البوت مع أي أوامر هنا.")

# === SEARCH COMMANDS / أوامر البحث ===

@bot.message_handler(func=lambda m: m.text and (m.text.startswith('سكربت ') or m.text.startswith('ماب ')))
def custom_search_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # تجاهل الرسائل في المجموعات المعطلة
    if message.chat.type in ['group', 'supergroup'] and chat_id not in groups:
        return

    if not is_subscribed(user_id):
        bot.reply_to(message, "⚠️ يرجى استخدام أمر /start والاشتراك في قنوات البوت أولاً.")
        return

    is_map_search = message.text.startswith('ماب ')
    query = message.text.replace('ماب ', '').replace('سكربت ', '').strip()
    
    if not query: return
    
    wait_msg = bot.reply_to(message, "⏳ جاري البحث وجلب البيانات...")
    
    try:
        url = f"https://scriptblox.com/api/script/search?q={query}"
        response = requests.get(url, timeout=10).json()
        all_scripts = response.get("result", {}).get("scripts", [])
        
        if is_map_search:
            filtered = [s for s in all_scripts if query.lower() in s.get("game", {}).get("name", "").lower()]
            scripts = filtered if filtered else all_scripts
        else:
            scripts = all_scripts

        if not scripts:
            bot.edit_message_text("❌ لم يتم العثور على أي نتائج تطابق بحثك.", chat_id, wait_msg.message_id)
            return

        search_id = str(message.message_id)
        search_states[search_id] = {'scripts': scripts, 'index': 0, 'requester': user_id}
        
        send_search_result(chat_id, wait_msg.message_id, search_id)

    except Exception:
        bot.edit_message_text("❌ حدث خطأ أثناء الاتصال بالموقع، يرجى المحاولة لاحقاً.", chat_id, wait_msg.message_id)

def send_search_result(chat_id, message_id, search_id):
    state = search_states.get(search_id)
    if not state: return
    scripts = state['scripts']
    idx = state['index']
    script = scripts[idx]
    
    text = format_script_message(script)
    markup = InlineKeyboardMarkup(row_width=2)
    nav_buttons = []
    
    if len(scripts) > 1:
        if idx > 0: nav_buttons.append(InlineKeyboardButton("➡️ رجوع", callback_data=f"sprev_{search_id}"))
        if idx < len(scripts) - 1: nav_buttons.append(InlineKeyboardButton("التالي ⬅️", callback_data=f"snext_{search_id}"))
        if nav_buttons: markup.row(*nav_buttons)
        
    markup.add(InlineKeyboardButton("إغلاق ❌", callback_data="close_msg"))
    bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)

# === CALLBACK QUERY HANDLER / الأزرار الشفافة ===

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == "check_sub":
        if is_subscribed(user_id):
            bot.delete_message(chat_id, message_id)
            bot.send_message(chat_id, "✅ تم التحقق بنجاح! يمكنك الآن استخدام البوت بكل حرية.", reply_markup=main_menu_markup())
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات بعد، يرجى الانضمام أولاً.", show_alert=True)
        return

    if not is_subscribed(user_id):
        bot.answer_callback_query(call.id, "❌ يرجى الاشتراك في القنوات أولاً.", show_alert=True)
        return

    if call.data == "main_menu":
        bot.edit_message_text("أهلاً بك في القائمة الرئيسية 🎮:", chat_id, message_id, reply_markup=main_menu_markup())

    elif call.data == "menu_hacks":
        markup = InlineKeyboardMarkup(row_width=1)
        hacks = [
            ("Delta Executor", "https://delta-executor.com/download/"),
            ("Codex Executor", "https://codexexecutor.net/android/"),
            ("Krnl", "https://wearedevs.net/d/Krnl"),
            ("Arceus X", "https://arceusx.com/"),
            ("Trigon Evo", "https://trigonevo.com/android/"),
            ("Ronix", "https://wearedevs.net/d/Ronix"),
            ("Vega X", "https://www.vegax.gg/")
        ]
        for name, url in hacks: markup.add(InlineKeyboardButton(name, url=url))
        markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="main_menu"))
        bot.edit_message_text("🔥 قائمة تحميل هاكات ومشغلات روبلكس الرسمية:", chat_id, message_id, reply_markup=markup)

    elif call.data == "menu_add_group":
        text = ("⚠️ لتفعيل البوت في قناتك أو مجموعتك:\n\n"
                "1. أضف البوت كمسؤول (Admin) في قناتك أو مجموعتك.\n"
                "2. تأكد من إعطاء البوت صلاحية قراءة الرسائل وإرسالها.\n"
                "3. أرسل الأمر التالي في المجموعة/القناة التي تريد تفعيلها:\n"
                "تفعيل البوت\n\n"
                "بعد إرسال الأمر، سيصبح البوت جاهزًا للاستخدام فيها.")
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("➕ أضفني لمجموعتك", url="https://t.me/Scripts1bot?startgroup=start"))
        markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="main_menu"))
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)

    elif call.data == "close_msg":
        bot.delete_message(chat_id, message_id)

    # --- أزرار أوامر البحث المخصصة ---
    elif call.data.startswith("snext_") or call.data.startswith("sprev_"):
        action, search_id = call.data.split("_")
        state = search_states.get(search_id)
        if not state:
            bot.answer_callback_query(call.id, "❌ انتهت جلسة البحث.", show_alert=True)
            return
        if user_id != state['requester']:
            bot.answer_callback_query(call.id, "❌ غير مسموح لك، هذا البحث يخص شخص آخر.", show_alert=True)
            return
            
        if action == "snext": state['index'] += 1
        elif action == "sprev": state['index'] -= 1
        send_search_result(chat_id, message_id, search_id)

    # --- القائمة الرئيسية للسكربتات ---
    elif call.data == "menu_scripts":
        user_states[user_id] = {'api_page': 1, 'games_list': [], 'display_page': 0, 'all_fetched_scripts': []}
        fetch_and_process_scripts(call.message, user_id, initial=True)

    elif call.data.startswith("gpage_"):
        user_states[user_id]['display_page'] = int(call.data.split("_")[1])
        show_games_page(call.message, user_id)

    elif call.data == "fetch_more_scripts":
        user_states[user_id]['api_page'] += 1
        fetch_and_process_scripts(call.message, user_id, initial=False)

    elif call.data.startswith("showgame_"):
        game_idx = int(call.data.split("_")[1])
        if user_states.get(user_id):
            user_states[user_id]['current_game_scripts'] = user_states[user_id]['games_list'][game_idx][1]
            user_states[user_id]['script_idx'] = 0
            show_script_details(call.message, user_id)

    elif call.data.startswith("nextscript_"):
        if user_states.get(user_id):
            user_states[user_id]['script_idx'] = int(call.data.split("_")[1])
            show_script_details(call.message, user_id)

    # --- لوحة الإدارة والإذاعة ---
    elif call.data.startswith("admin_"):
        if user_id != DEV_ID: return
        
        if call.data == "admin_stats":
            text = (f"📊 إحصائيات البوت الحالية:\n\n"
                    f"• مستخدمين (خاص): {len(users)}\n"
                    f"• المجموعات المفعلة: {len(groups)}\n"
                    f"• قنوات الاشتراك الإجباري: {len(channels)}")
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 العودة للوحة الإدارة", callback_data="admin_panel_back"))
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
            
        elif call.data == "admin_fsub":
            show_fsub_management(call.message)
            
        elif call.data == "admin_add_fsub":
            msg = bot.send_message(chat_id, "ℹ️ أرسل معرف القناة أو الكروب المراد إضافته (مثال: @channel):")
            bot.register_next_step_handler(msg, save_new_fsub_channel)
            
        elif call.data == "admin_contact":
            bot.answer_callback_query(call.id, f"المطور هو الحساب المالك: {DEV_ID}", show_alert=True)
            
        elif call.data == "admin_broadcast":
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(InlineKeyboardButton("الخاص 👤", callback_data="bc_users"),
                       InlineKeyboardButton("الكروبات 👥", callback_data="bc_groups"))
            markup.add(InlineKeyboardButton("القنوات 📢", callback_data="bc_channels"))
            markup.add(InlineKeyboardButton("🔙 العودة للوحة الإدارة", callback_data="admin_panel_back"))
            bot.edit_message_text("📣 اختر الجهة التي تريد إرسال الإذاعة لها:", chat_id, message_id, reply_markup=markup)

        elif call.data == "admin_panel_back":
            bot.edit_message_text("🛠️ أهلاً بك في لوحة الإدارة:", chat_id, message_id, reply_markup=admin_menu_markup())

    elif call.data.startswith("bc_"):
        if user_id != DEV_ID: return
        target = call.data.split("_")[1] # users, groups, or channels
        msg = bot.send_message(chat_id, "✍️ الرجاء إرسال الرسالة الآن (نص، صورة، أو فيديو) ليتم إذاعتها:")
        bot.register_next_step_handler(msg, process_broadcast, target)

    elif call.data.startswith("delch_"):
        if user_id != DEV_ID: return
        ch_to_del = call.data.replace("delch_", "")
        if ch_to_del in channels:
            channels.remove(ch_to_del)
            save_data(CHANNELS_FILE, channels)
            bot.answer_callback_query(call.id, "✅ تم حذف القناة بنجاح.", show_alert=True)
            show_fsub_management(call.message)

# === دالات جلب السكربتات الأساسية ===

def fetch_and_process_scripts(message, user_id, initial=True):
    state = user_states[user_id]
    api_page = state['api_page']
    try:
        response = requests.get(f"https://scriptblox.com/api/script/fetch?page={api_page}", timeout=10).json()
        new_scripts = response.get("result", {}).get("scripts", [])
        if not new_scripts:
            bot.send_message(message.chat.id, "⚠️ لا توجد سكربتات إضافية حالياً بالموقع.")
            return

        state['all_fetched_scripts'].extend(new_scripts)
        unique_games = {}
        for s in state['all_fetched_scripts']:
            game_name = s.get("game", {}).get("name", "ماب عام / Universal")
            if game_name not in unique_games: unique_games[game_name] = []
            unique_games[game_name].append(s)
            
        state['games_list'] = list(unique_games.items())
        if not initial: state['display_page'] += 1
        show_games_page(message, user_id)
    except Exception:
        bot.send_message(message.chat.id, "❌ حدث خطأ غير متوقع أثناء جلب السكربتات.")

def show_games_page(message, user_id):
    state = user_states.get(user_id)
    if not state: return
    games = state['games_list']
    display_page = state['display_page']
    start_idx = display_page * 6
    end_idx = start_idx + 6
    current_games = games[start_idx:end_idx]
    
    markup = InlineKeyboardMarkup(row_width=1)
    for i, (game_name, _) in enumerate(current_games):
        markup.add(InlineKeyboardButton(f"🎮 {game_name}", callback_data=f"showgame_{start_idx + i}"))
    
    nav_buttons = []
    if display_page > 0: nav_buttons.append(InlineKeyboardButton("➡️ السابق", callback_data=f"gpage_{display_page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"📄 ص {display_page+1}", callback_data="ignore_click"))
    
    if end_idx < len(games):
        nav_buttons.append(InlineKeyboardButton("التالي ⬅️", callback_data=f"gpage_{display_page+1}"))
        if nav_buttons: markup.row(*nav_buttons)
    else:
        if nav_buttons: markup.row(*nav_buttons)
        markup.add(InlineKeyboardButton("🔄 جلب صفحات أكثر (أقدم)", callback_data="fetch_more_scripts"))
        
    markup.add(InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu"))
    bot.edit_message_text("📊 اختر الماب لعرض أحدث السكربتات المتوفرة له:", message.chat.id, message.message_id, reply_markup=markup)

def show_script_details(message, user_id):
    state = user_states.get(user_id)
    if not state: return
    scripts = state['current_game_scripts']
    idx = state['script_idx']
    
    text = format_script_message(scripts[idx])
    markup = InlineKeyboardMarkup(row_width=2)
    nav = []
    if len(scripts) > 1:
        if idx > 0: nav.append(InlineKeyboardButton("➡️ السابق", callback_data=f"nextscript_{idx-1}"))
        if idx < len(scripts) - 1: nav.append(InlineKeyboardButton("التالي ⬅️", callback_data=f"nextscript_{idx+1}"))
        
    if nav: markup.row(*nav)
    markup.add(InlineKeyboardButton("🔙 رجوع لقائمة المابات", callback_data=f"gpage_{state['display_page']}"))
    markup.add(InlineKeyboardButton("إغلاق الرسالة ❌", callback_data="close_msg"))

    try: bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)
    except: bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=False)

# === ADMIN PANEL & BROADCAST LOGIC ===

@bot.message_handler(commands=['admin'])
def show_admin_panel(message):
    if message.from_user.id != DEV_ID: return
    bot.send_message(message.chat.id, "🛠️ أهلاً بك في لوحة الإدارة:", reply_markup=admin_menu_markup())

def admin_menu_markup():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
               InlineKeyboardButton("⚙️ الاشتراك الإجباري", callback_data="admin_fsub"))
    markup.add(InlineKeyboardButton("📢 إضافة قناة", callback_data="admin_add_fsub"),
               InlineKeyboardButton("💬 تواصل", callback_data="admin_contact"))
    markup.add(InlineKeyboardButton("📣 إذاعة", callback_data="admin_broadcast"))
    return markup

def show_fsub_management(message):
    markup = InlineKeyboardMarkup(row_width=1)
    for ch in channels: markup.add(InlineKeyboardButton(f"🗑️ حذف {ch}", callback_data=f"delch_{ch}"))
    markup.add(InlineKeyboardButton("🔙 العودة للوحة الإدارة", callback_data="admin_panel_back"))
    bot.edit_message_text("⚙️ القنوات المضافة للاشتراك الإجباري:", message.chat.id, message.message_id, reply_markup=markup)

def save_new_fsub_channel(message):
    if message.from_user.id != DEV_ID: return
    ch_username = message.text.strip()
    if not ch_username.startswith("@"):
        bot.send_message(message.chat.id, "❌ المعرف يجب أن يبدأ بـ @")
        return
    if ch_username not in channels:
        channels.append(ch_username)
        save_data(CHANNELS_FILE, channels)
        bot.send_message(message.chat.id, f"✅ تمت إضافة {ch_username} للاشتراك الإجباري.")
    else: bot.send_message(message.chat.id, "ℹ️ مضافة مسبقاً.")

def process_broadcast(message, target):
    if message.from_user.id != DEV_ID: return
    
    success = 0
    fail = 0
    
    if target == "users": target_list = users
    elif target == "groups": target_list = groups
    elif target == "channels": target_list = channels
    else: return
    
    bot.send_message(message.chat.id, f"⏳ جاري الإذاعة لـ {len(target_list)} جهة...")
    
    for chat_id in target_list:
        try:
            bot.copy_message(chat_id, message.chat.id, message.message_id)
            success += 1
        except Exception:
            fail += 1
            
    bot.send_message(message.chat.id, f"✅ اكتملت الإذاعة!\nنجاح: {success}\nفشل: {fail}")

if __name__ == '__main__':
    print("🚀 البوت المحدث يعمل الآن بنجاح...")
    bot.infinity_polling()
