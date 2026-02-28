import discord
from discord.ext import commands
from discord import app_commands, ui
import os
import json # NOWE: Do zapisywania imion i nazwisk

# --- KONFIGURACJA ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ALLOWED_CHANNEL_ID = 1309969415483297795
REQUIRED_ROLE_ID = 1309969414099304448  # Zarząd+

# Mapowanie awansów i degradacji
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

PRAKTYKANT_ID = 1309969414023811168
STARSZY_BARISTA_ID = 1309969414023811171

# ID ról Plusów i Minusów
ROLE_PLUSY = {
    1: 1475172069653348423,
    2: 1475172072685834354,
    3: 1475172075365863688
}

ROLE_MINUSY = {
    1: 1475172069653348423, # WPISZ TU ID ROLI 1 MINUSA
    2: 1475172072685834354, # WPISZ TU ID ROLI 2 MINUSA
    3: 1475172075365863688  # WPISZ TU ID ROLI 3 MINUSA
}

# --- NOWE: MAPOWANIE PLAKIETEK ---
# Słownik ustawiony od najważniejszej roli do najniższej. Bot sprawdzi je po kolei.
PLAKIETKI = {
    # Szefostwo / Zarząd
    1474774583294038106: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_2~ [Właściciel]",
    1309969414099304450: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_90~ [Szef]",
    1474774495406325831: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_43~ [Zastępca Szefa]",
    1309969414099304449: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_39~ [Menadżer]",
    1309969414099304448: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_85~ [Kierownik]",
    
    # Ochrona (Ważniejsze)
    1475088765931487252: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [Szef ochrony]",
    1475213940584878261: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [Zastępca szefa ochrony]",
    1475137663739891793: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [S Ochroniarz]",
    1475088876749197505: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [Ochrona]",
    1475137600523075664: "/opis ~HC_13~ Bean Machine ~n~ ~s~ {dane} ~n~ ~HC_3~ [M ochroniarz]",

    # Barisci
    1309969414023811171: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_32~ [Starszy Barista]",
    1309969414023811170: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_53~ [Barista]",
    1309969414023811169: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_38~ [Młodszy Barista]",
    1309969414023811168: "/opis ~HC_13~ ☕Bean Machine☕ ~n~ ~s~ {dane} ~n~ ~HC_141~ [Praktykant]"
}

# --- FUNKCJE BAZY DANYCH RP ---
DANE_FILE = "imiona_rp.json"

def wczytaj_dane():
    if not os.path.exists(DANE_FILE): return {}
    with open(DANE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def zapisz_dane(dane):
    with open(DANE_FILE, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

# --- INICJALIZACJA BOTA ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ... [TUTAJ ZOSTAW KLASY MENU I KALKULATORA BEZ ZMIAN (Menu, Zestawy, MainView itd.)] ...

# --- SYSTEM EVENTS ---
@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} zalogowany!')
    synced = await bot.tree.sync()
    print(f"✅ Zsynchronizowano {len(synced)} komend!")

# --- KOMENDY SLASH ---

# ... [TUTAJ ZOSTAW KOMENDY /menu, /plus ORAZ /minus, KTÓRE POPRAWILIŚMY W POPRZEDNIEJ WIADOMOŚCI] ...

@bot.tree.command(name="imie", description="Ustaw swoje imię i nazwisko do plakietki (wymagane w RP)")
@app_commands.describe(imie="Twoje imię", nazwisko="Twoje nazwisko")
async def imie(interaction: discord.Interaction, imie: str, nazwisko: str):
    # Formatujemy, aby pierwsza litera zawsze była duża (np. jan kowalski -> Jan Kowalski)
    imie_format = imie.strip().capitalize()
    nazwisko_format = nazwisko.strip().capitalize()
    pelne_dane = f"{imie_format} {nazwisko_format}"

    dane_rp = wczytaj_dane()
    dane_rp[str(interaction.user.id)] = pelne_dane
    zapisz_dane(dane_rp)

    await interaction.response.send_message(f"✅ Ustawiono pomyślnie! Twoje dane RP to teraz: **{pelne_dane}**.\nMożesz użyć komendy `/plakietka`.", ephemeral=True)

@bot.tree.command(name="plakietka", description="Generuje gotowy kod do wklejenia w grze pod F8 / T")
async def plakietka(interaction: discord.Interaction):
    dane_rp = wczytaj_dane()
    user_id_str = str(interaction.user.id)

    # 1. Sprawdzanie czy gracz ustawił imię
    if user_id_str not in dane_rp:
        return await interaction.response.send_message("❌ Nie masz przypisanego imienia i nazwiska!\nUżyj najpierw komendy: `/imie <imię> <nazwisko>`", ephemeral=True)

    imie_nazwisko = dane_rp[user_id_str]
    user_roles = [r.id for r in interaction.user.roles]

    # 2. Wyszukiwanie odpowiedniej rangi
    wzor_plakietki = None
    for rola_id, wzor in PLAKIETKI.items():
        if rola_id in user_roles:
            wzor_plakietki = wzor
            break # Przerywamy przy znalezieniu pierwszej (najwyższej) pasującej roli

    # 3. Jeśli gracz nie ma roli uprawniającej do plakietki
    if not wzor_plakietki:
        return await interaction.response.send_message("❌ Nie posiadasz w tej chwili żadnej rangi w firmie, która uprawnia do plakietki.", ephemeral=True)

    # 4. Generowanie gotowej plakietki
    gotowa_plakietka = wzor_plakietki.format(dane=imie_nazwisko)

    embed = discord.Embed(title="🏷️ Twoja Plakietka", color=0xFF7600, description="Skopiuj poniższy kod i wklej go w grze:")
    embed.add_field(name="Kod do wklejenia:", value=f"```{gotowa_plakietka}```", inline=False)
    embed.set_footer(text=f"Wygenerowano dla: {imie_nazwisko}")

    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(DISCORD_TOKEN)
