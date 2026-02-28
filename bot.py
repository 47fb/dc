import discord
from discord.ext import commands
from discord import app_commands, ui
import os
import json
from datetime import datetime

# --- KONFIGURACJA ID ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
REQUIRED_ROLE_ID = 1309969414099304448  # Zarząd+
GLOWNA_RANGA_PRAC_ID = 1474903301567938641 # Ranga "Pracownik"

# KANAŁY
CH_MENU = 1309969415483297795
CH_PLUSY = 1309969416565424156
CH_MINUSY = 1309969416565424157
CH_URLOPY = 1475468993212055572

# --- MAPOWANIE RANG I PLUSÓW ---
AWANS_MAP = {
    1309969414023811168: 1309969414023811169, 
    1309969414023811169: 1309969414023811170, 
    1309969414023811170: 1309969414023811171
}
DEGRADACJA_MAP = {
    1309969414023811171: 1309969414023811170, 
    1309969414023811170: 1309969414023811169, 
    1309969414023811169: 1309969414023811168
}
ROLE_PLUSY = {1: 1475172069653348423, 2: 1475172072685834354, 3: 1475172075365863688}
ROLE_MINUSY = {1: 1475172069653348423, 2: 1475172072685834354, 3: 1475172075365863688}

PLAKIETKI = {
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

# --- BAZA DANYCH ---
DANE_FILE = "imiona_rp.json"
def wczytaj_dane():
    if not os.path.exists(DANE_FILE): return {}
    with open(DANE_FILE, "r", encoding="utf-8") as f: return json.load(f)
def zapisz_dane(dane):
    with open(DANE_FILE, "w", encoding="utf-8") as f: json.dump(dane, f, indent=4)

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- KLASY KALKULATORA ---
MENU = {
    "napoje": {"☕ Expresso": 1100, "☕ Americano": 1200, "☕ Macchiato": 1200, "☕ Latte": 1100, "☕ Cappuccino": 900, "☕ Mocha": 1100},
    "jedzenie": {"🍰 Szarlotka": 1400, "🍰 Brownie": 1400, "🍰 Sernik": 1300}
}
ZESTAWY = {"📦 Bean Mini (1+1)": 1500, "📦 Bean Basic (2+2)": 5000}

class IloscModal(ui.Modal, title="Kalkulator"):
    def __init__(self, nazwa, cena):
        super().__init__()
        self.nazwa, self.cena = nazwa, cena
        self.ilosc = ui.TextInput(label="Podaj ilość", default="1", min_length=1, max_length=3)
        self.add_item(self.ilosc)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            total = int(self.ilosc.value) * self.cena
            embed = discord.Embed(title="🛒 Wynik kalkulacji", color=0xFF7600)
            embed.add_field(name="Pozycja", value=f"**{self.nazwa}**", inline=True)
            embed.add_field(name="Suma", value=f"`` {total} $``", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except: await interaction.response.send_message("❌ Błąd: Wpisz poprawną liczbę!", ephemeral=True)

class ProduktSelect(ui.Select):
    def __init__(self):
        options = []
        for cat in MENU.values():
            for n, c in cat.items(): options.append(discord.SelectOption(label=f"• {n}", value=f"{n}|{c}"))
        super().__init__(placeholder="🛒 Wybierz produkt...", options=options)
    async def callback(self, interaction: discord.Interaction):
        n, c = self.values[0].split('|'); await interaction.response.send_modal(IloscModal(n, int(c)))

class ZestawSelect(ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=f"• {n}", value=f"{n}|{c}") for n, c in ZESTAWY.items()]
        super().__init__(placeholder="📦 Wybierz zestaw...", options=options)
    async def callback(self, interaction: discord.Interaction):
        n, c = self.values[0].split('|'); await interaction.response.send_modal(IloscModal(n, int(c)))

class MainView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProduktSelect()); self.add_item(ZestawSelect())

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} online! Wszystkie funkcje działają.")

# 1. MENU + BANER
@bot.tree.command(name="menu", description="Pokazuje menu i kalkulator")
async def menu_cmd(interaction: discord.Interaction):
    if interaction.channel_id != CH_MENU: return await interaction.response.send_message(f"❌ Komenda tylko na <#{CH_MENU}>!", ephemeral=True)
    
    embed = discord.Embed(title="**Bean Machine – Menu**", color=0xFF7600)
    for k, v in MENU.items():
        txt = "\n".join([f"• **{p}** × {c} $" for p, c in v.items()])
        embed.add_field(name=f"*** {k.upper()}***", value=txt, inline=False)

    if os.path.exists("b1.png"):
        file = discord.File("b1.png", filename="b1.png")
        embed.set_image(url="attachment://b1.png")
        await interaction.response.send_message(file=file, embed=embed, view=MainView())
    else:
        await interaction.response.send_message(embed=embed, view=MainView())

# 2. PLUS (Tylko Kanał Plusy)
@bot.tree.command(name="plus", description="Daje plusa pracownikowi")
@app_commands.choices(rodzaj=[app_commands.Choice(name="1 Plus", value=1), app_commands.Choice(name="2 Plus", value=2), app_commands.Choice(name="3 Plus (Awans)", value=3)])
async def plus_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str, rodzaj: app_commands.Choice[int]):
    if interaction.channel_id != CH_PLUSY: return await interaction.response.send_message(f"❌ Komenda tylko na <#{CH_PLUSY}>!", ephemeral=True)
    req = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not any(r.position >= req.position for r in interaction.user.roles): return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
    
    stare = [interaction.guild.get_role(rid) for rid in ROLE_PLUSY.values() if interaction.guild.get_role(rid)]
    await uzytkownik.remove_roles(*[r for r in stare if r in uzytkownik.roles])
    
    notka = ""
    if rodzaj.value == 3:
        for s, n in AWANS_MAP.items():
            if s in [r.id for r in uzytkownik.roles]:
                await uzytkownik.remove_roles(interaction.guild.get_role(s)); await uzytkownik.add_roles(interaction.guild.get_role(n))
                notka = f"\n🎊 **AWANS!**"; break
    else: await uzytkownik.add_roles(interaction.guild.get_role(ROLE_PLUSY[rodzaj.value]))
    
    embed = discord.Embed(title="🌟 Przyznano Plusa", color=0x2ECC71); embed.add_field(name="Dla:", value=uzytkownik.mention).add_field(name="Powód:", value=f"{powod}{notka}")
    await interaction.response.send_message(embed=embed)

# 3. MINUS (Tylko Kanał Minusy)
@bot.tree.command(name="minus", description="Daje minusa pracownikowi")
@app_commands.choices(rodzaj=[app_commands.Choice(name="1 Minus", value=1), app_commands.Choice(name="2 Minus", value=2), app_commands.Choice(name="3 Minus (Degradacja)", value=3)])
async def minus_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str, rodzaj: app_commands.Choice[int]):
    if interaction.channel_id != CH_MINUSY: return await interaction.response.send_message(f"❌ Komenda tylko na <#{CH_MINUSY}>!", ephemeral=True)
    req = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not any(r.position >= req.position for r in interaction.user.roles): return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
    
    stare = [interaction.guild.get_role(rid) for rid in ROLE_MINUSY.values() if interaction.guild.get_role(rid)]
    await uzytkownik.remove_roles(*[r for r in stare if r in uzytkownik.roles])
    
    notka = ""
    if rodzaj.value == 3:
        for s, n in DEGRADACJA_MAP.items():
            if s in [r.id for r in uzytkownik.roles]:
                await uzytkownik.remove_roles(interaction.guild.get_role(s)); await uzytkownik.add_roles(interaction.guild.get_role(n))
                notka = f"\n📉 **DEGRADACJA!**"; break
    else: await uzytkownik.add_roles(interaction.guild.get_role(ROLE_MINUSY[rodzaj.value]))
    
    embed = discord.Embed(title="⚠️ Przyznano Minusa", color=0xE74C3C); embed.add_field(name="Dla:", value=uzytkownik.mention).add_field(name="Powód:", value=f"{powod}{notka}")
    await interaction.response.send_message(embed=embed)

# 4. URLOP + Walidacja Daty
@bot.tree.command(name="urlop", description="Zgłoś urlop (Format: DD.MM)")
async def urlop_cmd(interaction: discord.Interaction, od_kiedy: str, do_kiedy: str, powod: str):
    if interaction.channel_id != CH_URLOPY: return await interaction.response.send_message(f"❌ Komenda tylko na <#{CH_URLOPY}>!", ephemeral=True)
    
    def validate_date(date_str):
        try:
            datetime.strptime(date_str, '%d.%m')
            return True
        except: return False

    if not validate_date(od_kiedy) or not validate_date(do_kiedy):
        return await interaction.response.send_message("❌ Nieprawidłowa data! Użyj formatu **DD.MM** (np. `05.10`)!", ephemeral=True)

    embed = discord.Embed(title="🏖️ Zgłoszenie Urlopu", color=0x3498DB)
    embed.add_field(name="Pracownik:", value=interaction.user.mention, inline=False)
    embed.add_field(name="Termin:", value=f"🗓️ `{od_kiedy}` — `{do_kiedy}`", inline=False)
    embed.add_field(name="Powód:", value=f"📝 {powod}", inline=False)
    await interaction.response.send_message(embed=embed)

# 5. IMIE
@bot.tree.command(name="imie", description="Ustaw dane RP i zmień nick")
async def imie_cmd(interaction: discord.Interaction, imie: str, nazwisko: str):
    pelne = f"{imie.strip().capitalize()} {nazwisko.strip().capitalize()}"
    dane = wczytaj_dane(); dane[str(interaction.user.id)] = pelne; zapisz_dane(dane)
    try: await interaction.user.edit(nick=pelne)
    except: pass
    await interaction.response.send_message(f"✅ Ustawiono pomyślnie: **{pelne}**", ephemeral=True)

# 6. PLAKIETKA
@bot.tree.command(name="plakietka", description="Generuje plakietkę firmową")
async def plakietka_cmd(interaction: discord.Interaction):
    user_roles = [r.id for r in interaction.user.roles]
    if not any(r in PLAKIETKI for r in user_roles): return await interaction.response.send_message("❌ Tylko dla pracowników!", ephemeral=True)
    dane = wczytaj_dane()
    if str(interaction.user.id) not in dane: return await interaction.response.send_message("❌ Ustaw najpierw imię przez `/imie`!", ephemeral=True)
    wzor = next((v for k, v in PLAKIETKI.items() if k in user_roles), None)
    kod = wzor.format(dane=dane[str(interaction.user.id)])
    embed = discord.Embed(title="🏷️ Twoja Plakietka", color=0xFF7600)
    embed.add_field(name="Kod do gry:", value=f"```{kod}```")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 7. ZWOLNIJ
@bot.tree.command(name="zwolnij", description="Zwalnia pracownika i zabiera rangi")
async def zwolnij_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str):
    req = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not any(r.position >= req.position for r in interaction.user.roles): return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
    
    wszystkie = list(PLAKIETKI.keys()) + [GLOWNA_RANGA_PRAC_ID] + list(ROLE_PLUSY.values())
    do_zabrania = [interaction.guild.get_role(rid) for rid in wszystkie if interaction.guild.get_role(rid)]
    
    await uzytkownik.remove_roles(*[r for r in do_zabrania if r in uzytkownik.roles])
    
    embed = discord.Embed(title="🚫 Zwolnienie Dyscyplinarne", color=0x000000)
    embed.add_field(name="Pracownik:", value=uzytkownik.mention).add_field(name="Powód:", value=powod)
    await interaction.response.send_message(embed=embed)

bot.run(DISCORD_TOKEN)
