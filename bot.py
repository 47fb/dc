import discord
from discord.ext import commands
from discord import app_commands, ui
import os
import json

# --- KONFIGURACJA ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ALLOWED_CHANNEL_ID = 1309969415483297795
REQUIRED_ROLE_ID = 1309969414099304448  # Zarząd+

# Mapowanie awansów i degradacji (ID rang)
AWANS_MAP = {
    1309969414023811168: 1309969414023811169, # Praktykant -> Młodszy Barista
    1309969414023811169: 1309969414023811170, # Młodszy Barista -> Barista
    1309969414023811170: 1309969414023811171  # Barista -> Starszy Barista
}

DEGRADACJA_MAP = {
    1309969414023811171: 1309969414023811170, # Starszy -> Barista
    1309969414023811170: 1309969414023811169, # Barista -> Młodszy
    1309969414023811169: 1309969414023811168  # Młodszy -> Praktykant
}

PRAKTYKANT_ID = 1309969414023811168
STARSZY_BARISTA_ID = 1309969414023811171

# Role Plusów i Minusów
ROLE_PLUSY = {
    1: 1475172069653348423,
    2: 1475172072685834354,
    3: 1475172075365863688
}

ROLE_MINUSY = {
    1: 1475172069653348423, # Uzupełnij właściwe ID jeśli są inne
    2: 1475172072685834354,
    3: 1475172075365863688
}

# Mapowanie Plakietek (Ranga -> Kod /opis)
PLAKIETKI = {
    1474774583294038106: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_2~ [Właściciel]",
    1309969414099304450: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_90~ [Szef]",
    1474774495406325831: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_43~ [Zastępca Szefa]",
    1309969414099304449: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_39~ [Menadżer]",
    1309969414099304448: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_85~ [Kierownik]",
    1475088765931487252: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [Szef ochrony]",
    1475213940584878261: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [Zastępca szefa ochrony]",
    1475137663739891793: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [S Ochroniarz]",
    1475088876749197505: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [Ochrona]",
    1475137600523075664: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [M ochroniarz]",
    1309969414023811171: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_32~ [Starszy Barista]",
    1309969414023811170: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_53~ [Barista]",
    1309969414023811169: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_38~ [Młodszy Barista]",
    1309969414023811168: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_141~ [Praktykant]"
}

# --- BAZA DANYCH ---
DANE_FILE = "imiona_rp.json"

def wczytaj_dane():
    if not os.path.exists(DANE_FILE): return {}
    with open(DANE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def zapisz_dane(dane):
    with open(DANE_FILE, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

# --- BOT INIT ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # WAŻNE: Do zmiany nicków i ról
bot = commands.Bot(command_prefix='!', intents=intents)

# --- MENU DATA ---
MENU = {
    "napoje": {"☕ Expresso": 1100, "☕ Americano": 1200, "☕ Macchiato": 1200, "☕ Latte": 1100, "☕ Cappuccino": 900, "☕ Mocha": 1100},
    "jedzenie": {"🍰 Szarlotka": 1400, "🍰 Brownie": 1400, "🍰 Sernik": 1300}
}
ZESTAWY = {"📦 Bean Mini (1+1)": 1500, "📦 Bean Basic (2+2)": 5000}

# --- UI COMPONENTS ---
class IloscModal(ui.Modal, title="Kalkulator"):
    def __init__(self, nazwa, cena):
        super().__init__()
        self.nazwa, self.cena = nazwa, cena
        self.ilosc = ui.TextInput(label="Podaj ilość", placeholder="Wpisz liczbę...", default="1", min_length=1, max_length=3)
        self.add_item(self.ilosc)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            total = int(self.ilosc.value) * self.cena
            embed = discord.Embed(title="🛒 Wynik kalkulacji", color=0xFF7600)
            embed.add_field(name="Pozycja", value=f"**{self.nazwa}**", inline=True)
            embed.add_field(name="Ilość", value=f"**{self.ilosc.value}**", inline=True)
            embed.add_field(name="Suma", value=f"`` {total} $``", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except: await interaction.response.send_message("❌ Wprowadź poprawną liczbę!", ephemeral=True)

class ProduktSelect(ui.Select):
    def __init__(self):
        options = []
        for cat in MENU.values():
            for n, c in cat.items(): options.append(discord.SelectOption(label=f"• {n}", value=f"{n}|{c}"))
        super().__init__(placeholder="🛒 Wybierz produkt...", options=options)
    async def callback(self, interaction: discord.Interaction):
        n, c = self.values[0].split('|')
        await interaction.response.send_modal(IloscModal(n, int(c)))

class ZestawSelect(ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=f"• {n}", value=f"{n}|{c}") for n, c in ZESTAWY.items()]
        super().__init__(placeholder="📦 Wybierz zestaw...", options=options)
    async def callback(self, interaction: discord.Interaction):
        n, c = self.values[0].split('|')
        await interaction.response.send_modal(IloscModal(n, int(c)))

class MainView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProduktSelect()); self.add_item(ZestawSelect())

# --- COMMANDS ---
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} gotowy!")

@bot.tree.command(name="menu", description="Pokazuje menu i kalkulator")
async def menu_cmd(interaction: discord.Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID: return await interaction.response.send_message("❌ Zły kanał!", ephemeral=True)
    embed = discord.Embed(title="**Bean Machine – Menu**", color=0xFF7600)
    for k, v in MENU.items():
        txt = "\n".join([f"• **{p}** × {c} $" for p, c in v.items()])
        embed.add_field(name=f"*** {k.capitalize()}***", value=txt, inline=False)
    await interaction.response.send_message(embed=embed, view=MainView())

@bot.tree.command(name="imie", description="Ustaw dane RP i zmień nick na DC")
async def imie_cmd(interaction: discord.Interaction, imie: str, nazwisko: str):
    pelne = f"{imie.strip().capitalize()} {nazwisko.strip().capitalize()}"
    dane = wczytaj_dane(); dane[str(interaction.user.id)] = pelne; zapisz_dane(dane)
    
    msg = f"✅ **Ustawiono pomyślnie!** Twoje imię i nazwisko to **{pelne}**"
    try: await interaction.user.edit(nick=pelne)
    except: msg += "\n*(Błąd: Nie mogłem zmienić Twojego nicku - sprawdź moją rangę)*"
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="plakietka", description="Generuje plakietkę dla pracowników")
async def plakietka_cmd(interaction: discord.Interaction):
    user_roles = [r.id for r in interaction.user.roles]
    if not any(r in PLAKIETKI for r in user_roles):
        return await interaction.response.send_message("❌ Komenda tylko dla pracowników!", ephemeral=True)
    
    dane = wczytaj_dane()
    if str(interaction.user.id) not in dane:
        return await interaction.response.send_message("❌ Ustaw najpierw imię przez `/imie`!", ephemeral=True)
    
    # Szukamy najwyższej rangi
    wzor = None
    for r_id, txt in PLAKIETKI.items():
        if r_id in user_roles:
            wzor = txt; break
    
    kod = wzor.format(dane=dane[str(interaction.user.id)])
    embed = discord.Embed(title="🏷️ Twoja Plakietka", color=0xFF7600)
    embed.add_field(name="Instrukcja:", value="Skopiuj poniższą plakietke i wklej w grze", inline=False)
    embed.add_field(name="Kod:", value=f"```{kod}```")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="plus", description="Daje plusa pracownikowi")
@app_commands.choices(rodzaj=[app_commands.Choice(name="1 Plus", value=1), app_commands.Choice(name="2 Plus", value=2), app_commands.Choice(name="3 Plus", value=3)])
async def plus_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str, rodzaj: app_commands.Choice[int]):
    req = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not any(r.position >= req.position for r in interaction.user.roles): return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)

    # USUWANIE STARYCH PLUSÓW
    stare = [interaction.guild.get_role(rid) for rid in ROLE_PLUSY.values() if interaction.guild.get_role(rid)]
    await uzytkownik.remove_roles(*[r for r in stare if r in uzytkownik.roles])

    notka = ""
    if rodzaj.value == 3:
        for s, n in AWANS_MAP.items():
            if s in [r.id for r in uzytkownik.roles]:
                await uzytkownik.remove_roles(interaction.guild.get_role(s))
                await uzytkownik.add_roles(interaction.guild.get_role(n))
                notka = f"\n🎊 **AWANS!** Nowa ranga: <@&{n}>"; break
    else:
        await uzytkownik.add_roles(interaction.guild.get_role(ROLE_PLUSY[rodzaj.value]))

    embed = discord.Embed(title="🌟 Plus!", color=0x2ECC71)
    embed.add_field(name="Kto:", value=uzytkownik.mention).add_field(name="Powód:", value=f"{powod}{notka}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="minus", description="Daje minusa pracownikowi")
@app_commands.choices(rodzaj=[app_commands.Choice(name="1 Minus", value=1), app_commands.Choice(name="2 Minus", value=2), app_commands.Choice(name="3 Minus", value=3)])
async def minus_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str, rodzaj: app_commands.Choice[int]):
    req = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not any(r.position >= req.position for r in interaction.user.roles): return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)

    # USUWANIE STARYCH MINUSÓW
    stare = [interaction.guild.get_role(rid) for rid in ROLE_MINUSY.values() if interaction.guild.get_role(rid)]
    await uzytkownik.remove_roles(*[r for r in stare if r in uzytkownik.roles])

    notka = ""
    if rodzaj.value == 3:
        for s, n in DEGRADACJA_MAP.items():
            if s in [r.id for r in uzytkownik.roles]:
                await uzytkownik.remove_roles(interaction.guild.get_role(s))
                await uzytkownik.add_roles(interaction.guild.get_role(n))
                notka = f"\n📉 **DEGRADACJA!** Nowa ranga: <@&{n}>"; break
    else:
        await uzytkownik.add_roles(interaction.guild.get_role(ROLE_MINUSY[rodzaj.value]))

    embed = discord.Embed(title="⚠️ Minus!", color=0xE74C3C)
    embed.add_field(name="Kto:", value=uzytkownik.mention).add_field(name="Powód:", value=f"{powod}{notka}")
    await interaction.response.send_message(embed=embed)

bot.run(DISCORD_TOKEN)
