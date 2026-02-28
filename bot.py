import discord
from discord.ext import commands
from discord import app_commands, ui
import os
import json
from datetime import datetime

# --- KONFIGURACJA ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
REQUIRED_ROLE_ID = 1309969414099304448
CH_POWITANIA = 1309969414862536705
CH_PLUSY = 1309969416565424156
CH_MINUSY = 1309969416565424157
GLOWNA_RANGA_PRAC_ID = 1474903301567938641

# MAPOWANIA RANG (Automatyczne plusy/minusy)
AWANS_MAP = {1309969414023811168: 1309969414023811169, 1309969414023811169: 1309969414023811170, 1309969414023811170: 1309969414023811171}
DEGRADACJA_MAP = {1309969414023811171: 1309969414023811170, 1309969414023811170: 1309969414023811169, 1309969414023811169: 1309969414023811168}
ROLE_PLUSY = {1: 1475172069653348423, 2: 1475172072685834354}
ROLE_MINUSY = {1: 1475172078435959086, 2: 1475172080483045469}

# WZORY PLAKIETEK
PLAKIETKI = {
    1475088765931487252: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [Szef Ochrony]",
    1475213940584878261: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [Zastępca Szefa Ochrony]",
    1475137663739891793: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [S Ochroniarz]",
    1475088876749197505: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [Ochrona]",
    1475137600523075664: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [M Ochroniarz]",
    1474774583294038106: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_2~ [Właściciel]",
    1309969414099304450: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_90~ [Szef]",
    1474774495406325831: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_43~ [Zastępca Szefa]",
    1309969414099304449: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_39~ [Menadżer]",
    1309969414099304448: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_85~ [Kierownik]",
    1309969414023811171: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_32~ [Starszy Barista]",
    1309969414023811170: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_53~ [Barista]",
    1309969414023811169: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_38~ [Młodszy Barista]",
    1309969414023811168: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_141~ [Praktykant]"
}

# --- FUNKCJE BAZY ---
def load_db(file):
    if not os.path.exists(file): return {}
    try:
        with open(file, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_db(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

# --- BOT ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} online i komendy zsynchronizowane!")

@bot.event
async def on_member_join(member):
    ch = bot.get_channel(CH_POWITANIA)
    if ch:
        emb = discord.Embed(description=f"☕ » Witaj {member.mention} na serwerze **Bean Machine**!", color=0xFF7600)
        if os.path.exists("hej.png"):
            file = discord.File("hej.png", filename="hej.png")
            emb.set_image(url="attachment://hej.png")
            await ch.send(file=file, embed=emb)
        else: await ch.send(embed=emb)

# --- KOMENDY ---

@bot.tree.command(name="godzinki", description="Zapisz czas pracy (format np. 12:00 14:00)")
async def godzinki_cmd(it: discord.Interaction, od_kiedy: str, do_kiedy: str):
    try:
        # Próba naprawienia formatu wpisanego przez użytkownika
        t1_str = od_kiedy.replace(".", ":").strip()
        t2_str = do_kiedy.replace(".", ":").strip()
        
        t1 = datetime.strptime(t1_str, "%H:%M")
        t2 = datetime.strptime(t2_str, "%H:%M")
        
        delta = (t2 - t1).total_seconds() / 3600.0
        if delta < 0: delta += 24 # Jeśli praca była przez północ
        
        d = load_db("godzinki.json")
        uid = str(it.user.id)
        d[uid] = d.get(uid, 0.0) + delta
        save_db("godzinki.json", d)
        
        await it.response.send_message(f"✅ Dodano **{round(delta, 2)}h**. Łącznie masz: **{round(d[uid], 2)}h**")
    except:
        await it.response.send_message("❌ Błąd formatu! Wpisz np. `12:22` i `14:33` (użyj dwukropka).", ephemeral=True)

@bot.tree.command(name="plakietka", description="Generuje kod plakietki firmowej")
async def plakietka_cmd(it: discord.Interaction):
    d_rp = load_db("imiona_rp.json")
    imie_rp = d_rp.get(str(it.user.id), it.user.display_name)
    
    # Szukanie wzoru dla rang użytkownika
    wzor = None
    user_role_ids = [r.id for r in it.user.roles]
    
    # Sprawdzamy po kolei każdą rangę z listy PLAKIETKI
    for role_id, text in PLAKIETKI.items():
        if role_id in user_role_ids:
            wzor = text
            break # Znaleziono najwyższą pasującą rangę
            
    if wzor:
        kod = wzor.format(dane=imie_rp)
        await it.response.send_message(f"🏷️ Twój kod plakietki:\n```{kod}```", ephemeral=True)
    else:
        await it.response.send_message("❌ Nie posiadasplusz rangi pracowniczej!", ephemeral=True)

@bot.tree.command(name="plus", description="Daje plusa (Automatycznie wykrywa status)")
async def plus_cmd(it: discord.Interaction, uzytkownik: discord.Member, powod: str):
    if it.channel_id != CH_PLUSY: return await it.response.send_message("Zły kanał!", ephemeral=True)
    
    r1, r2 = it.guild.get_role(ROLE_PLUSY[1]), it.guild.get_role(ROLE_PLUSY[2])
    status, img = "🟢 1 Plus", "plus.png"
    
    if r2 in uzytkownik.roles:
        await uzytkownik.remove_roles(r2); status = "🎉 **AWANS!**"; img = "awans.png"
        for s, n in AWANS_MAP.items():
            if it.guild.get_role(s) in uzytkownik.roles:
                await uzytkownik.remove_roles(it.guild.get_role(s)); await uzytkownik.add_roles(it.guild.get_role(n)); break
    elif r1 in uzytkownik.roles:
        await uzytkownik.remove_roles(r1); await uzytkownik.add_roles(r2); status = "🟢 2 Plusy"
    else: await uzytkownik.add_roles(r1)

    emb = discord.Embed(title="🌟 Plus", description=f"Dla: {uzytkownik.mention}\nStatus: {status}\nPowód: {powod}", color=0x2ECC71)
    emb.set_footer(text=f"Nadano przez: {it.user.display_name}", icon_url=it.user.display_avatar.url)
    if os.path.exists(img):
        f = discord.File(img, filename=img)
        emb.set_image(url=f"attachment://{img}")
        await it.response.send_message(file=f, embed=emb)
    else: await it.response.send_message(embed=emb)

@bot.tree.command(name="minus", description="Daje minusa (Automatycznie wykrywa status)")
async def minus_cmd(it: discord.Interaction, uzytkownik: discord.Member, powod: str):
    if it.channel_id != CH_MINUSY: return await it.response.send_message("Zły kanał!", ephemeral=True)
    
    m1, m2 = it.guild.get_role(ROLE_MINUSY[1]), it.guild.get_role(ROLE_MINUSY[2])
    status = "🔴 1/3 Minusy"
    
    if m2 in uzytkownik.roles:
        await uzytkownik.remove_roles(m2); status = "📉 **DEGRADACJA!**"
        for s, n in DEGRADACJA_MAP.items():
            if it.guild.get_role(s) in uzytkownik.roles:
                await uzytkownik.remove_roles(it.guild.get_role(s)); await uzytkownik.add_roles(it.guild.get_role(n)); break
    elif m1 in uzytkownik.roles:
        await uzytkownik.remove_roles(m1); await uzytkownik.add_roles(m2); status = "🔴 2/3 Minusy"
    else: await uzytkownik.add_roles(m1)

    emb = discord.Embed(title="⚠️ Minus", description=f"Dla: {uzytkownik.mention}\nStatus: {status}\nPowód: {powod}", color=0xE74C3C)
    emb.set_footer(text=f"Nadano przez: {it.user.display_name}", icon_url=it.user.display_avatar.url)
    if os.path.exists("minus.png"):
        f = discord.File("minus.png", filename="minus.png")
        emb.set_image(url="attachment://minus.png")
        await it.response.send_message(file=f, embed=emb)
    else: await it.response.send_message(embed=emb)

@bot.tree.command(name="topka", description="Ranking TOP 10 godzin")
async def topka_cmd(it: discord.Interaction):
    d = load_db("godzinki.json")
    top = sorted(d.items(), key=lambda x: x[1], reverse=True)[:10]
    txt = ""
    for i, (u_id, g) in enumerate(top, 1):
        txt += f"**{i}.** <@{u_id}> — `{round(g, 2)}h` \n"
    
    emb = discord.Embed(title="🏆 TOP 10 Godzin Pracy", description=txt or "Brak danych", color=0xF1C40F)
    await it.response.send_message(embed=emb)

@bot.tree.command(name="usung", description="Usuń godziny (Prywatne)")
async def usung_cmd(it: discord.Interaction, uzytkownik: discord.Member, ilosc: str):
    d = load_db("godzinki.json")
    uid = str(uzytkownik.id)
    if ilosc.lower() == "wszystkie": d[uid] = 0.0
    elif "h" in ilosc.lower():
        val = float(ilosc.lower().replace("h", ""))
        d[uid] = max(0, d.get(uid, 0) - val)
    save_db("godzinki.json", d)
    await it.response.send_message(f"✅ Zaktualizowano godziny dla {uzytkownik.display_name}.", ephemeral=True)

@bot.tree.command(name="zwolnij", description="Zwalnia pracownika")
async def zwolnij_cmd(it: discord.Interaction, uzytkownik: discord.Member, powod: str):
    wszystkie = list(PLAKIETKI.keys()) + [GLOWNA_RANGA_PRAC_ID] + list(ROLE_PLUSY.values()) + list(ROLE_MINUSY.values())
    await uzytkownik.remove_roles(*[r for r in [it.guild.get_role(rid) for rid in wszystkie] if r and r in uzytkownik.roles])
    emb = discord.Embed(title="🚫 Zwolnienie", description=f"Pracownik: {uzytkownik.mention}\nPowód: {powod}", color=0x000000)
    await it.response.send_message(embed=emb)

@bot.tree.command(name="imie", description="Ustaw imię i nazwisko RP")
async def imie_cmd(it: discord.Interaction, imie: str, nazwisko: str):
    nick = f"{imie.capitalize()} {nazwisko.capitalize()}"
    d = load_db("imiona_rp.json"); d[str(it.user.id)] = nick; save_db("imiona_rp.json", d)
    try: await it.user.edit(nick=nick)
    except: pass
    await it.response.send_message(f"✅ Ustawiono nick RP: **{nick}**", ephemeral=True)

bot.run(DISCORD_TOKEN)
