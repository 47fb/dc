import discord
from discord.ext import commands
from discord import app_commands, ui
import os
import json
from datetime import datetime, timedelta

# --- KONFIGURACJA ID ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
REQUIRED_ROLE_ID = 1309969414099304448  # Kierownik+ (Zarząd)
GLOWNA_RANGA_PRAC_ID = 1474903301567938641
CH_POWITANIA = 1309969414862536705

# KANAŁY
CH_MENU = 1309969415483297795
CH_PLUSY = 1309969416565424156
CH_MINUSY = 1309969416565424157
CH_URLOPY = 1475468993212055572

# --- MAPOWANIE RANG (BEZ ZMIAN) ---
AWANS_MAP = {1309969414023811168: 1309969414023811169, 1309969414023811169: 1309969414023811170, 1309969414023811170: 1309969414023811171}
DEGRADACJA_MAP = {1309969414023811171: 1309969414023811170, 1309969414023811170: 1309969414023811169, 1309969414023811169: 1309969414023811168}
ROLE_PLUSY = {1: 1475172069653348423, 2: 1475172072685834354, 3: 1475172075365863688}
ROLE_MINUSY = {1: 1475172078435959086, 2: 1475172080483045469, 3: 1475172083100291276}

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

# --- BAZA DANYCH ---
DANE_FILE = "imiona_rp.json"
GODZINKI_FILE = "godzinki.json"

def wczytaj_dane():
    if not os.path.exists(DANE_FILE): return {}
    with open(DANE_FILE, "r", encoding="utf-8") as f: return json.load(f)

def zapisz_dane(dane):
    with open(DANE_FILE, "w", encoding="utf-8") as f: json.dump(dane, f, indent=4, ensure_ascii=False)

def wczytaj_godzinki():
    if not os.path.exists(GODZINKI_FILE): return {}
    with open(GODZINKI_FILE, "r", encoding="utf-8") as f: return json.load(f)

def zapisz_godzinki(dane):
    with open(GODZINKI_FILE, "w", encoding="utf-8") as f: json.dump(dane, f, indent=4, ensure_ascii=False)

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} online!")

# --- POWITANIA ---
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(CH_POWITANIA)
    if channel:
        embed = discord.Embed(
            description=f"☕ » Witaj {member.mention} na serwerze **Bean Machine**!",
            color=0xFF7600
        )
        if os.path.exists("hej.png"):
            file = discord.File("hej.png", filename="hej.png")
            embed.set_image(url="attachment://hej.png")
            await channel.send(file=file, embed=embed)
        else:
            await channel.send(embed=embed)

# --- KOMENDY PLUS/MINUS/URLOP/PLAKIETKA (TE SAME CO WCZEŚNIEJ) ---
# ... (Tutaj zachowaj poprzedni kod dla tych komend) ...

# --- MODYFIKACJA USUNG (NIEWIDOCZNE) ---
@bot.tree.command(name="usung", description="Zarządzaj godzinami pracownika (Widoczne tylko dla Ciebie)")
async def usung_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, ilosc: str):
    req = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not any(r.position >= req.position for r in interaction.user.roles): 
        return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
    
    dane = wczytaj_godzinki()
    uid = str(uzytkownik.id)
    aktualne = dane.get(uid, 0.0)
    
    ilosc_clean = ilosc.lower().strip()
    odejmowane = 0.0
    
    if ilosc_clean == "wszystkie":
        odejmowane = aktualne
    elif ilosc_clean.endswith("h"):
        odejmowane = float(ilosc_clean[:-1])
    elif ilosc_clean.endswith("m"):
        odejmowane = float(ilosc_clean[:-1]) / 60.0
    else:
        odejmowane = float(ilosc_clean)
        
    dane[uid] = max(0.0, aktualne - odejmowane)
    zapisz_godzinki(dane)
    
    await interaction.response.send_message(f"✅ Pomyślnie zmodyfikowano godziny dla {uzytkownik.display_name}. Obecny stan: **{round(dane[uid], 2)}h**", ephemeral=True)

# --- KOMENDA TOPKA ---
@bot.tree.command(name="topka", description="Ranking 10 najbardziej pracowitych osób")
async def topka_cmd(interaction: discord.Interaction):
    dane = wczytaj_godzinki()
    if not dane:
        return await interaction.response.send_message("❌ Ranking jest obecnie pusty!", ephemeral=True)
    
    # Sortowanie od największej liczby godzin
    posortowane = sorted(dane.items(), key=lambda x: x[1], reverse=True)[:10]
    
    embed = discord.Embed(title="🏆 TOP 10 Pracowników • Bean Machine", color=0xF1C40F)
    opis = ""
    
    for i, (uid, godz) in enumerate(posortowane, 1):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else f"Nieznany ({uid})"
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "☕"
        opis += f"{medal} **{i}. {name}** — `{round(godz, 2)}h` \n"
    
    embed.description = opis
    embed.set_footer(text="Godziny aktualizowane na bieżąco")
    await interaction.response.send_message(embed=embed)

# 4. PLUS (AUTO) - KOD Z POPRZEDNIEJ WIADOMOŚCI
@bot.tree.command(name="plus", description="Daje plusa automatycznie (Kierownik+)")
async def plus_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str):
    if interaction.channel_id != CH_PLUSY: return await interaction.response.send_message(f"❌ Komenda tylko na <#{CH_PLUSY}>!", ephemeral=True)
    req = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not any(r.position >= req.position for r in interaction.user.roles): return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
    
    has_p1 = interaction.guild.get_role(ROLE_PLUSY[1]) in uzytkownik.roles
    has_p2 = interaction.guild.get_role(ROLE_PLUSY[2]) in uzytkownik.roles
    
    status_text = ""
    awans = False
    grafika = "plus.png"
    
    if has_p2:
        await uzytkownik.remove_roles(interaction.guild.get_role(ROLE_PLUSY[2]))
        status_text = "🟢 **AWANS (3 Plusy)**"; awans = True; grafika = "awans.png"
        for s, n in AWANS_MAP.items():
            if interaction.guild.get_role(s) in uzytkownik.roles:
                await uzytkownik.remove_roles(interaction.guild.get_role(s)); await uzytkownik.add_roles(interaction.guild.get_role(n)); break
    elif has_p1:
        await uzytkownik.remove_roles(interaction.guild.get_role(ROLE_PLUSY[1])); await uzytkownik.add_roles(interaction.guild.get_role(ROLE_PLUSY[2]))
        status_text = "🟢 **Status: 2 Plusy**"
    else:
        await uzytkownik.add_roles(interaction.guild.get_role(ROLE_PLUSY[1]))
        status_text = "🟢 **Status: 1 Plus**"

    embed = discord.Embed(title="🌟 Przyznano Plusa", color=0x2ECC71)
    embed.add_field(name="Dla:", value=uzytkownik.mention, inline=True)
    embed.add_field(name="Status:", value=status_text, inline=True)
    embed.add_field(name="Powód:", value=powod + ("\n🎊 **AWANS!**" if awans else ""), inline=False)
    embed.set_footer(text=f"Nadano przez: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    
    if os.path.exists(grafika):
        file = discord.File(grafika, filename=grafika)
        embed.set_image(url=f"attachment://{grafika}")
        await interaction.response.send_message(file=file, embed=embed)
    else:
        await interaction.response.send_message(embed=embed)

# (Dodaj analogicznie komendę MINUS, URLOP, IMIE, PLAKIETKA i GODZINKI z poprzedniej wersji)

bot.run(DISCORD_TOKEN)
