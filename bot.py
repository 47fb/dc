import discord
from discord.ext import commands
from discord import app_commands, ui
import os
import json
from datetime import datetime, timedelta

# --- KONFIGURACJA ID ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
REQUIRED_ROLE_ID = 1309969414099304448  # Kierownik+
CH_POWITANIA = 1309969414862536705
CH_MENU = 1309969415483297795
CH_PLUSY = 1309969416565424156
CH_MINUSY = 1309969416565424157
CH_URLOPY = 1475468993212055572

# MAPOWANIA (BEZ ZMIAN)
AWANS_MAP = {1309969414023811168: 1309969414023811169, 1309969414023811169: 1309969414023811170, 1309969414023811170: 1309969414023811171}
DEGRADACJA_MAP = {1309969414023811171: 1309969414023811170, 1309969414023811170: 1309969414023811169, 1309969414023811169: 1309969414023811168}
ROLE_PLUSY = {1: 1475172069653348423, 2: 1475172072685834354, 3: 1475172075365863688}
ROLE_MINUSY = {1: 1475172078435959086, 2: 1475172080483045469, 3: 1475172083100291276}

# --- KALKULATOR LOGIKA ---
MENU_DATA = {
    "☕ Espresso": 1100, "☕ Americano": 1200, "☕ Macchiato": 1200, 
    "☕ Latte": 1100, "☕ Cappuccino": 900, "☕ Mocha": 1100,
    "🍰 Szarlotka": 1400, "🍰 Brownie": 1400, "🍰 Sernik": 1300
}
ZESTAWY_DATA = {"📦 Bean Mini (1+1)": 1500, "📦 Bean Basic (2+2)": 5000}

class KalkulatorModal(ui.Modal, title="Kalkulator"):
    def __init__(self, produkt, cena):
        super().__init__()
        self.produkt, self.cena = produkt, cena
        self.ilosc = ui.TextInput(label="Podaj ilość", default="1", min_length=1, max_length=3)
        self.add_item(self.ilosc)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            total = int(self.ilosc.value) * self.cena
            embed = discord.Embed(title="🛒 Wynik", description=f"Produkt: **{self.produkt}**\nIlość: **{self.ilosc.value}**\nDo zapłaty: **{total} $**", color=0xFF7600)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except: await interaction.response.send_message("Błąd ilości!", ephemeral=True)

class MenuDropdown(ui.Select):
    def __init__(self, placeholder, opcje_dict):
        options = [discord.SelectOption(label=name, value=name) for name in opcje_dict.keys()]
        super().__init__(placeholder=placeholder, options=options)
        self.opcje_dict = opcje_dict
    async def callback(self, interaction: discord.Interaction):
        name = self.values[0]
        await interaction.response.send_modal(KalkulatorModal(name, self.opcje_dict[name]))

class MenuView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MenuDropdown("🛒 Wybierz produkt...", MENU_DATA))
        self.add_item(MenuDropdown("📦 Wybierz zestaw...", ZESTAWY_DATA))

# --- BAZA DANYCH ---
def db(file):
    if not os.path.exists(file): return {}
    with open(file, "r", encoding="utf-8") as f: return json.load(f)
def save(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

# --- BOT ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} gotowy!")

@bot.event
async def on_member_join(member):
    ch = bot.get_channel(CH_POWITANIA)
    if ch:
        embed = discord.Embed(description=f"☕ » Witaj {member.mention} na serwerze **Bean Machine**!", color=0xFF7600)
        if os.path.exists("hej.png"):
            file = discord.File("hej.png", filename="hej.png")
            embed.set_image(url="attachment://hej.png")
            await ch.send(file=file, embed=embed)
        else: await ch.send(embed=embed)

# --- KOMENDY ---

@bot.tree.command(name="menu", description="Pokazuje menu i kalkulator")
async def menu_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="**Bean Machine – Menu**", color=0xFF7600)
    txt = "\n".join([f"• **{p}** — {c}$" for p, c in MENU_DATA.items()])
    zestawy = "\n".join([f"• **{p}** — {c}$" for p, c in ZESTAWY_DATA.items()])
    embed.add_field(name="☕ Produkty", value=txt, inline=False)
    embed.add_field(name="📦 Zestawy", value=zestawy, inline=False)
    
    if os.path.exists("b1.png"):
        file = discord.File("b1.png", filename="b1.png")
        embed.set_image(url="attachment://b1.png")
        await interaction.response.send_message(file=file, embed=embed, view=MenuView())
    else:
        await interaction.response.send_message(embed=embed, view=MenuView())

@bot.tree.command(name="godzinki", description="Zapisz czas pracy (np. 12:00 14:30)")
async def godzinki_cmd(interaction: discord.Interaction, od_kiedy: str, do_kiedy: str):
    try:
        t1 = datetime.strptime(od_kiedy.replace(".", ":"), "%H:%M")
        t2 = datetime.strptime(do_kiedy.replace(".", ":"), "%H:%M")
        diff = (t2 - t1).total_seconds() / 3600.0
        if diff < 0: diff += 24
        
        d = db("godzinki.json")
        uid = str(interaction.user.id)
        d[uid] = d.get(uid, 0.0) + diff
        save("godzinki.json", d)
        
        embed = discord.Embed(title="⏰ Czas pracy", description=f"Zapisano: **{round(diff,2)}h**\nSuma: **{round(d[uid],2)}h**", color=0xF1C40F)
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("❌ Błędny format! Użyj HH:MM (np. 12:22)", ephemeral=True)

@bot.tree.command(name="plus", description="Daje plusa (Automat)")
async def plus_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str):
    if interaction.channel_id != CH_PLUSY: return await interaction.response.send_message("Zły kanał!", ephemeral=True)
    if not any(r.id == REQUIRED_ROLE_ID or r.position > interaction.guild.get_role(REQUIRED_ROLE_ID).position for r in interaction.user.roles):
        return await interaction.response.send_message("Brak uprawnień!", ephemeral=True)
    
    r1, r2 = interaction.guild.get_role(ROLE_PLUSY[1]), interaction.guild.get_role(ROLE_PLUSY[2])
    status, img = "🟢 1 Plus", "plus.png"
    
    if r2 in uzytkownik.roles:
        await uzytkownik.remove_roles(r2)
        status = "🎉 **AWANS!**"
        img = "awans.png"
        for s, n in AWANS_MAP.items():
            if interaction.guild.get_role(s) in uzytkownik.roles:
                await uzytkownik.remove_roles(interaction.guild.get_role(s)); await uzytkownik.add_roles(interaction.guild.get_role(n)); break
    elif r1 in uzytkownik.roles:
        await uzytkownik.remove_roles(r1); await uzytkownik.add_roles(r2)
        status = "🟢 2 Plusy"
    else:
        await uzytkownik.add_roles(r1)

    embed = discord.Embed(title="🌟 Plus", description=f"Dla: {uzytkownik.mention}\nStatus: {status}\nPowód: {powod}", color=0x2ECC71)
    embed.set_footer(text=f"Nadano przez: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    if os.path.exists(img):
        f = discord.File(img, filename=img)
        embed.set_image(url=f"attachment://{img}")
        await interaction.response.send_message(file=f, embed=embed)
    else: await interaction.response.send_message(embed=embed)

@bot.tree.command(name="minus", description="Daje minusa (Automat)")
async def minus_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str):
    if interaction.channel_id != CH_MINUSY: return await interaction.response.send_message("Zły kanał!", ephemeral=True)
    if not any(r.id == REQUIRED_ROLE_ID or r.position > interaction.guild.get_role(REQUIRED_ROLE_ID).position for r in interaction.user.roles):
        return await interaction.response.send_message("Brak uprawnień!", ephemeral=True)
    
    m1, m2 = interaction.guild.get_role(ROLE_MINUSY[1]), interaction.guild.get_role(ROLE_MINUSY[2])
    status = "🔴 1/3 Minusy"
    
    if m2 in uzytkownik.roles:
        await uzytkownik.remove_roles(m2)
        status = "📉 **DEGRADACJA!**"
        for s, n in DEGRADACJA_MAP.items():
            if interaction.guild.get_role(s) in uzytkownik.roles:
                await uzytkownik.remove_roles(interaction.guild.get_role(s)); await uzytkownik.add_roles(interaction.guild.get_role(n)); break
    elif m1 in uzytkownik.roles:
        await uzytkownik.remove_roles(m1); await uzytkownik.add_roles(m2)
        status = "🔴 2/3 Minusy"
    else:
        await uzytkownik.add_roles(m1)

    embed = discord.Embed(title="⚠️ Minus", description=f"Dla: {uzytkownik.mention}\nStatus: {status}\nPowód: {powod}", color=0xE74C3C)
    embed.set_footer(text=f"Nadano przez: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    if os.path.exists("minus.png"):
        f = discord.File("minus.png", filename="minus.png")
        embed.set_image(url="attachment://minus.png")
        await interaction.response.send_message(file=f, embed=embed)
    else: await interaction.response.send_message(embed=embed)

@bot.tree.command(name="usung", description="Usuń godziny (Prywatne)")
async def usung_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, ilosc: str):
    if not any(r.id == REQUIRED_ROLE_ID or r.position > interaction.guild.get_role(REQUIRED_ROLE_ID).position for r in interaction.user.roles):
        return await interaction.response.send_message("Brak uprawnień!", ephemeral=True)
    d = db("godzinki.json")
    uid = str(uzytkownik.id)
    if ilosc.lower() == "wszystkie": d[uid] = 0.0
    elif "h" in ilosc.lower(): d[uid] = max(0, d.get(uid,0) - float(ilosc.lower().replace("h","")))
    elif "m" in ilosc.lower(): d[uid] = max(0, d.get(uid,0) - float(ilosc.lower().replace("m",""))/60)
    save("godzinki.json", d)
    await interaction.response.send_message(f"✅ Zmieniono godziny {uzytkownik.display_name} na {round(d[uid],2)}h", ephemeral=True)

@bot.tree.command(name="topka", description="Ranking 10 osób")
async def topka_cmd(interaction: discord.Interaction):
    d = db("godzinki.json")
    top = sorted(d.items(), key=lambda x: x[1], reverse=True)[:10]
    txt = "\n".join([f"**{i+1}.** <@{u}> — `{round(g,2)}h`" for i, (u, g) in enumerate(top)])
    await interaction.response.send_message(embed=discord.Embed(title="🏆 TOP 10 Godzin", description=txt or "Brak danych", color=0xF1C40F))

@bot.tree.command(name="imie", description="Ustaw dane RP")
async def imie_cmd(interaction: discord.Interaction, imie: str, nazwisko: str):
    name = f"{imie.capitalize()} {nazwisko.capitalize()}"
    d = db("imiona_rp.json"); d[str(interaction.user.id)] = name; save("imiona_rp.json", d)
    try: await interaction.user.edit(nick=name)
    except: pass
    await interaction.response.send_message(f"✅ Ustawiono: {name}", ephemeral=True)

bot.run(DISCORD_TOKEN)
