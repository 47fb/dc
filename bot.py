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

# --- MAPOWANIE RANG ---
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
def wczytaj_json(plik):
    if not os.path.exists(plik): return {}
    with open(plik, "r", encoding="utf-8") as f: return json.load(f)

def zapisz_json(plik, dane):
    with open(plik, "w", encoding="utf-8") as f: json.dump(dane, f, indent=4, ensure_ascii=False)

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} gotowy! Wszystkie komendy załadowane.")

# --- POWITANIA ---
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(CH_POWITANIA)
    if channel:
        embed = discord.Embed(description=f"☕ » Witaj {member.mention} na serwerze **Bean Machine**!", color=0xFF7600)
        if os.path.exists("hej.png"):
            file = discord.File("hej.png", filename="hej.png")
            embed.set_image(url="attachment://hej.png")
            await channel.send(file=file, embed=embed)
        else:
            await channel.send(embed=embed)

# --- KOMENDY ---

@bot.tree.command(name="imie", description="Ustaw dane RP")
async def imie_cmd(interaction: discord.Interaction, imie: str, nazwisko: str):
    pelne = f"{imie.capitalize()} {nazwisko.capitalize()}"
    dane = wczytaj_json("imiona_rp.json")
    dane[str(interaction.user.id)] = pelne
    zapisz_json("imiona_rp.json", dane)
    try: await interaction.user.edit(nick=pelne)
    except: pass
    await interaction.response.send_message(f"✅ Ustawiono dane RP: **{pelne}**", ephemeral=True)

@bot.tree.command(name="plus", description="Daje plusa (Automatyczny status)")
async def plus_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str):
    if interaction.channel_id != CH_PLUSY: return await interaction.response.send_message("Zły kanał!", ephemeral=True)
    req = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not any(r.position >= req.position for r in interaction.user.roles): return await interaction.response.send_message("Brak uprawnień!", ephemeral=True)
    
    h1, h2 = interaction.guild.get_role(ROLE_PLUSY[1]), interaction.guild.get_role(ROLE_PLUSY[2])
    status, awans, grafika = "", False, "plus.png"

    if h2 in uzytkownik.roles:
        await uzytkownik.remove_roles(h2); status = "🟢 **AWANS (3 Plusy)**"; awans = True; grafika = "awans.png"
        for s, n in AWANS_MAP.items():
            if interaction.guild.get_role(s) in uzytkownik.roles:
                await uzytkownik.remove_roles(interaction.guild.get_role(s)); await uzytkownik.add_roles(interaction.guild.get_role(n)); break
    elif h1 in uzytkownik.roles:
        await uzytkownik.remove_roles(h1); await uzytkownik.add_roles(h2); status = "🟢 **Status: 2 Plusy**"
    else:
        await uzytkownik.add_roles(h1); status = "🟢 **Status: 1 Plus**"

    embed = discord.Embed(title="🌟 Przyznano Plusa", color=0x2ECC71)
    embed.add_field(name="Dla:", value=uzytkownik.mention, inline=True)
    embed.add_field(name="Status:", value=status, inline=True)
    embed.add_field(name="Powód:", value=powod + ("\n🎊 **AWANS!**" if awans else ""), inline=False)
    embed.set_footer(text=f"Nadano przez: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    
    if os.path.exists(grafika):
        file = discord.File(grafika, filename=grafika)
        embed.set_image(url=f"attachment://{grafika}")
        await interaction.response.send_message(file=file, embed=embed)
    else: await interaction.response.send_message(embed=embed)

@bot.tree.command(name="minus", description="Daje minusa (Automatyczny status)")
async def minus_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str):
    if interaction.channel_id != CH_MINUSY: return await interaction.response.send_message("Zły kanał!", ephemeral=True)
    req = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not any(r.position >= req.position for r in interaction.user.roles): return await interaction.response.send_message("Brak uprawnień!", ephemeral=True)
    
    m1, m2 = interaction.guild.get_role(ROLE_MINUSY[1]), interaction.guild.get_role(ROLE_MINUSY[2])
    status, degradacja = "", False

    if m2 in uzytkownik.roles:
        await uzytkownik.remove_roles(m2); status = "📉 **DEGRADACJA (3 Minusy)**"; degradacja = True
        for s, n in DEGRADACJA_MAP.items():
            if interaction.guild.get_role(s) in uzytkownik.roles:
                await uzytkownik.remove_roles(interaction.guild.get_role(s)); await uzytkownik.add_roles(interaction.guild.get_role(n)); break
    elif m1 in uzytkownik.roles:
        await uzytkownik.remove_roles(m1); await uzytkownik.add_roles(m2); status = "🔴 **Poziom: 2/3**"
    else:
        await uzytkownik.add_roles(m1); status = "🔴 **Poziom: 1/3**"

    embed = discord.Embed(title="⚠️ Przyznano Minusa", color=0xE74C3C)
    embed.add_field(name="Dla:", value=uzytkownik.mention, inline=True)
    embed.add_field(name="Status:", value=status, inline=True)
    embed.add_field(name="Powód:", value=powod + ("\n⬇️ **DEGRADACJA!**" if degradacja else ""), inline=False)
    embed.set_footer(text=f"Nadano przez: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    
    if os.path.exists("minus.png"):
        file = discord.File("minus.png", filename="minus.png")
        embed.set_image(url="attachment://minus.png")
        await interaction.response.send_message(file=file, embed=embed)
    else: await interaction.response.send_message(embed=embed)

@bot.tree.command(name="godzinki", description="Zapisz czas pracy")
async def godzinki_cmd(interaction: discord.Interaction, od_kiedy: str, do_kiedy: str):
    try:
        t1, t2 = datetime.strptime(od_kiedy, "%H:%M"), datetime.strptime(do_kiedy, "%H:%M")
        diff = (t2 - t1).total_seconds() / 3600.0
        if diff < 0: diff += 24
        dane = wczytaj_json("godzinki.json")
        uid = str(interaction.user.id)
        dane[uid] = dane.get(uid, 0.0) + diff
        zapisz_json("godzinki.json", dane)
        await interaction.response.send_message(f"✅ Zapisano **{round(diff,2)}h**. Suma: **{round(dane[uid],2)}h**")
    except: await interaction.response.send_message("Format HH:MM!", ephemeral=True)

@bot.tree.command(name="usung", description="Usuń godziny (Prywatne)")
async def usung_cmd(interaction: discord.Interaction, uzytkownik: discord.Member, ilosc: str):
    req = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not any(r.position >= req.position for r in interaction.user.roles): return await interaction.response.send_message("Brak uprawnień!", ephemeral=True)
    dane = wczytaj_json("godzinki.json")
    uid = str(uzytkownik.id)
    if ilosc.lower() == "wszystkie": dane[uid] = 0.0
    elif "h" in ilosc: dane[uid] = max(0, dane.get(uid, 0) - float(ilosc.replace("h","")))
    elif "m" in ilosc: dane[uid] = max(0, dane.get(uid, 0) - float(ilosc.replace("m",""))/60)
    zapisz_json("godzinki.json", dane)
    await interaction.response.send_message(f"✅ Zaktualizowano godziny {uzytkownik.display_name}. Stan: {round(dane.get(uid,0),2)}h", ephemeral=True)

@bot.tree.command(name="topka", description="Ranking TOP 10")
async def topka_cmd(interaction: discord.Interaction):
    dane = wczytaj_json("godzinki.json")
    top = sorted(dane.items(), key=lambda x: x[1], reverse=True)[:10]
    opis = "\n".join([f"{'🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else '☕'} **{i+1}.** <@{u}> — `{round(g,2)}h`" for i, (u, g) in enumerate(top)])
    embed = discord.Embed(title="🏆 TOP 10 Pracowników", description=opis or "Brak danych", color=0xF1C40F)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="plakietka", description="Generuj kod plakietki")
async def plakietka_cmd(interaction: discord.Interaction):
    dane_rp = wczytaj_json("imiona_rp.json")
    imie = dane_rp.get(str(interaction.user.id), interaction.user.display_name)
    wzor = next((v for k, v in PLAKIETKI.items() if any(r.id == k for r in interaction.user.roles)), None)
    if not wzor: return await interaction.response.send_message("Brak rangi pracowniczej!", ephemeral=True)
    await interaction.response.send_message(f"🏷️ Twój kod:\n```{wzor.format(dane=imie)}```", ephemeral=True)

@bot.tree.command(name="urlop", description="Zgłoś urlop")
async def urlop_cmd(interaction: discord.Interaction, od_kiedy: str, do_kiedy: str, powod: str):
    embed = discord.Embed(title="🏖️ Urlop", color=0x3498DB)
    embed.add_field(name="Pracownik:", value=interaction.user.mention)
    embed.add_field(name="Termin:", value=f"{od_kiedy} - {do_kiedy}")
    embed.add_field(name="Powód:", value=powod)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="menu", description="Kalkulator i menu")
async def menu_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="☕ Menu Bean Machine", description="Użyj kalkulatora poniżej", color=0xFF7600)
    await interaction.response.send_message(embed=embed)

bot.run(DISCORD_TOKEN)
