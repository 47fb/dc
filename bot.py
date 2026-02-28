import discord
from discord.ext import commands
from discord import app_commands, ui
import os
import json
from datetime import datetime

# --- KONFIGURACJA ID ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
REQUIRED_ROLE_ID = 1309969414099304448
CH_POWITANIA = 1309969414862536705
CH_PLUSY = 1309969416565424156
CH_MINUSY = 1309969416565424157
GLOWNA_RANGA_PRAC_ID = 1474903301567938641

# CENNIK
PRODUKTY = {
    "☕ Espresso": 1100, "☕ Americano": 1200, "☕ Macchiato": 1200, 
    "☕ Latte": 1100, "☕ Cappuccino": 900, "☕ Mocha": 1100,
    "🍰 Szarlotka": 1400, "🍰 Brownie": 1400, "🍰 Sernik": 1300
}
ZESTAWY = {
    "📦 Bean Mini (1+1)": 1500, 
    "📦 Bean Basic (2+2)": 5000
}

# MAPOWANIA RANG
AWANS_MAP = {1309969414023811168: 1309969414023811169, 1309969414023811169: 1309969414023811170, 1309969414023811170: 1309969414023811171}
DEGRADACJA_MAP = {1309969414023811171: 1309969414023811170, 1309969414023811170: 1309969414023811169, 1309969414023811169: 1309969414023811168}
ROLE_PLUSY = {1: 1475172069653348423, 2: 1475172072685834354}
ROLE_MINUSY = {1: 1475172078435959086, 2: 1475172080483045469}

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

# --- FUNKCJE BAZY DANYCH ---
def load_db(file):
    if not os.path.exists(file): return {}
    with open(file, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_db(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- KALKULATOR UI ---
class CalcModal(ui.Modal, title="Bean Machine - Kalkulator"):
    def __init__(self, produkt, cena):
        super().__init__()
        self.produkt, self.cena = produkt, cena
        self.ilosc = ui.TextInput(label="Podaj ilość", default="1", min_length=1, max_length=3)
        self.add_item(self.ilosc)
    async def on_submit(self, it: discord.Interaction):
        try:
            total = int(self.ilosc.value) * self.cena
            emb = discord.Embed(title="🛒 Wynik Kalkulatora", description=f"Produkt: **{self.produkt}**\nIlość: **{self.ilosc.value}**\n\nDo zapłaty: **{total} $**", color=0xFF7600)
            await it.response.send_message(embed=emb, ephemeral=True)
        except: await it.response.send_message("❌ Błąd! Wpisz liczbę.", ephemeral=True)

class MenuDrop(ui.Select):
    def __init__(self, placeholder, opcje):
        super().__init__(placeholder=placeholder, options=[discord.SelectOption(label=k, value=k, description=f"Cena: {v}$") for k, v in opcje.items()])
        self.opcje = opcje
    async def callback(self, it: discord.Interaction):
        await it.response.send_modal(CalcModal(self.values[0], self.opcje[self.values[0]]))

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} online! 10 komend zsynchronizowanych.")

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

# 1. MENU & KALKULATOR
@bot.tree.command(name="menu", description="Pokazuje cennik i otwiera kalkulator")
async def menu_cmd(it: discord.Interaction):
    emb = discord.Embed(title="☕ Cennik Bean Machine", color=0xFF7600)
    txt = "\n".join([f"• **{p}** — {c}$" for p, c in PRODUKTY.items()])
    emb.add_field(name="Produkty", value=txt, inline=False)
    emb.add_field(name="📦 Zestawy", value="\n".join([f"• **{p}** — {c}$" for p, c in ZESTAWY.items()]), inline=False)
    
    view = ui.View()
    view.add_item(MenuDrop("🛒 Wybierz produkt...", PRODUKTY))
    view.add_item(MenuDrop("📦 Wybierz zestaw...", ZESTAWY))
    
    if os.path.exists("b1.png"):
        f = discord.File("b1.png", filename="b1.png")
        emb.set_image(url="attachment://b1.png")
        await it.response.send_message(file=f, embed=emb, view=view)
    else: await it.response.send_message(embed=emb, view=view)

# 2. GODZINKI (EMBED + JSON)
@bot.tree.command(name="godzinki", description="Zapisz czas pracy (format 12:22 14:33)")
async def godzinki_cmd(it: discord.Interaction, od_kiedy: str, do_kiedy: str):
    try:
        t1_str = od_kiedy.replace(".", ":").strip()
        t2_str = do_kiedy.replace(".", ":").strip()
        t1 = datetime.strptime(t1_str, "%H:%M")
        t2 = datetime.strptime(t2_str, "%H:%M")
        delta = (t2 - t1).total_seconds() / 3600.0
        if delta < 0: delta += 24
        
        d = load_db("godzinki.json")
        uid = str(it.user.id)
        suma = d.get(uid, 0.0) + delta
        d[uid] = suma
        save_db("godzinki.json", d)
        
        emb = discord.Embed(title="⏰ Raport Pracy", color=0xFF7600, timestamp=datetime.now())
        emb.set_author(name=it.user.display_name, icon_url=it.user.display_avatar.url)
        emb.set_thumbnail(url=it.user.display_avatar.url)
        emb.add_field(name="⏰ Sesja", value=f"Od: `{t1_str}` Do: `{t2_str}`", inline=True)
        emb.add_field(name="📊 Wynik", value=f"**+{round(delta, 2)}h**", inline=True)
        emb.add_field(name="🏢 Łącznie", value=f"**{round(suma, 2)}h**", inline=False)
        await it.response.send_message(embed=emb)
    except: await it.response.send_message("❌ Błędny format! Użyj HH:MM", ephemeral=True)

# 3. TOPKA
@bot.tree.command(name="topka", description="Ranking TOP 10 godzin")
async def topka_cmd(it: discord.Interaction):
    d = load_db("godzinki.json")
    top = sorted(d.items(), key=lambda x: x[1], reverse=True)[:10]
    txt = "\n".join([f"**{i+1}.** <@{u}> — `{round(g,2)}h`" for i, (u, g) in enumerate(top)])
    await it.response.send_message(embed=discord.Embed(title="🏆 Ranking Godzin", description=txt or "Brak danych", color=0xF1C40F))

# 4. PLAKIETKA
@bot.tree.command(name="plakietka", description="Kod plakietki RP")
async def plakietka_cmd(it: discord.Interaction):
    d_rp = load_db("imiona_rp.json")
    imie_rp = d_rp.get(str(it.user.id), it.user.display_name)
    user_roles = [r.id for r in it.user.roles]
    wzor = None
    for r_id, tekst in PLAKIETKI.items():
        if r_id in user_roles:
            wzor = tekst; break
    if wzor: await it.response.send_message(f"🏷️ Twój kod:\n```{wzor.format(dane=imie_rp)}```", ephemeral=True)
    else: await it.response.send_message("❌ Brak rangi!", ephemeral=True)

# 5. PLUS
@bot.tree.command(name="plus", description="Nadaj plusa")
async def plus_cmd(it: discord.Interaction, uzytkownik: discord.Member, powod: str):
    if it.channel_id != CH_PLUSY: return await it.response.send_message("Zły kanał!", ephemeral=True)
    r1, r2 = it.guild.get_role(ROLE_PLUSY[1]), it.guild.get_role(ROLE_PLUSY[2])
    st, img = "🟢 1 Plus", "plus.png"
    if r2 in uzytkownik.roles:
        await uzytkownik.remove_roles(r2); st = "🎉 AWANS"; img = "awans.png"
        for s, n in AWANS_MAP.items():
            if it.guild.get_role(s) in uzytkownik.roles:
                await uzytkownik.remove_roles(it.guild.get_role(s)); await uzytkownik.add_roles(it.guild.get_role(n)); break
    elif r1 in uzytkownik.roles:
        await uzytkownik.remove_roles(r1); await uzytkownik.add_roles(r2); st = "🟢 2 Plusy"
    else: await uzytkownik.add_roles(r1)
    
    emb = discord.Embed(title="🌟 Plus", description=f"{uzytkownik.mention}\nStatus: {st}\nPowód: {powod}", color=0x2ECC71)
    if os.path.exists(img):
        f = discord.File(img, filename=img); emb.set_image(url=f"attachment://{img}")
        await it.response.send_message(file=f, embed=emb)
    else: await it.response.send_message(embed=emb)

# 6. MINUS
@bot.tree.command(name="minus", description="Nadaj minusa")
async def minus_cmd(it: discord.Interaction, uzytkownik: discord.Member, powod: str):
    if it.channel_id != CH_MINUSY: return await it.response.send_message("Zły kanał!", ephemeral=True)
    m1, m2 = it.guild.get_role(ROLE_MINUSY[1]), it.guild.get_role(ROLE_MINUSY[2])
    st = "🔴 1/3 Minusy"
    if m2 in uzytkownik.roles:
        await uzytkownik.remove_roles(m2); st = "📉 DEGRADACJA"
        for s, n in DEGRADACJA_MAP.items():
            if it.guild.get_role(s) in uzytkownik.roles:
                await uzytkownik.remove_roles(it.guild.get_role(s)); await uzytkownik.add_roles(it.guild.get_role(n)); break
    elif m1 in uzytkownik.roles:
        await uzytkownik.remove_roles(m1); await uzytkownik.add_roles(m2); st = "🔴 2/3 Minusy"
    else: await uzytkownik.add_roles(m1)
    await it.response.send_message(embed=discord.Embed(title="⚠️ Minus", description=f"{uzytkownik.mention}\nStatus: {st}\nPowód: {powod}", color=0xE74C3C))

# 7. IMIE
@bot.tree.command(name="imie", description="Ustaw dane RP")
async def imie_cmd(it: discord.Interaction, imie: str, nazwisko: str):
    nick = f"{imie.capitalize()} {nazwisko.capitalize()}"
    d = load_db("imiona_rp.json"); d[str(it.user.id)] = nick; save_db("imiona_rp.json", d)
    try: await it.user.edit(nick=nick)
    except: pass
    await it.response.send_message(f"✅ Ustawiono nick: {nick}", ephemeral=True)

# 8. ZWOLNIJ
@bot.tree.command(name="zwolnij", description="Usuwa wszystkie rangi pracownicze")
async def zwolnij_cmd(it: discord.Interaction, uzytkownik: discord.Member, powod: str):
    wszystkie = list(PLAKIETKI.keys()) + [GLOWNA_RANGA_PRAC_ID] + list(ROLE_PLUSY.values()) + list(ROLE_MINUSY.values())
    await uzytkownik.remove_roles(*[r for r in [it.guild.get_role(rid) for rid in wszystkie] if r and r in uzytkownik.roles])
    await it.response.send_message(embed=discord.Embed(title="🚫 Zwolnienie", description=f"Pracownik: {uzytkownik.mention}\nPowód: {powod}", color=0x000000))

# 9. USUNG
@bot.tree.command(name="usung", description="Usuń/Edytuj godziny (Prywatne)")
async def usung_cmd(it: discord.Interaction, uzytkownik: discord.Member, ilosc: str):
    d = load_db("godzinki.json"); uid = str(uzytkownik.id)
    if ilosc.lower() == "wszystkie": d[uid] = 0.0
    elif "h" in ilosc: d[uid] = max(0, d.get(uid,0) - float(ilosc.replace("h","")))
    save_db("godzinki.json", d)
    await it.response.send_message(f"✅ Zmieniono godziny dla {uzytkownik.display_name}.", ephemeral=True)

# 10. EMBED
@bot.tree.command(name="embed", description="Wyślij ogłoszenie")
async def embed_cmd(it: discord.Interaction, tytul: str, tresc: str, kolor: str = "FF7600"):
    try:
        c = int(kolor.replace("#", ""), 16)
        emb = discord.Embed(title=tytul, description=tresc.replace("\\n", "\n"), color=c)
        await it.response.send_message("Wysłano!", ephemeral=True); await it.channel.send(embed=emb)
    except: await it.response.send_message("Błędny kolor HEX.", ephemeral=True)

bot.run(DISCORD_TOKEN)
