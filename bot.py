import discord
from discord.ext import commands
from discord import app_commands, ui
import os

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

# --- INICJALIZACJA BOTA ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- DANE MENU ---
MENU = {
    "napoje": {
        "☕ Expresso": 1100, "☕ Americano": 1200, "☕ Macchiato": 1200,
        "☕ Latte": 1100, "☕ Cappuccino": 900, "☕ Mocha": 1100
    },
    "jedzenie": {
        "🍰 Szarlotka": 1400, "🍰 Brownie": 1400, "🍰 Sernik": 1300
    }
}
ZESTAWY = {"📦 Bean Mini (1+1)": 1500, "📦 Bean Basic (2+2)": 5000}

# --- KLASY INTERFEJSU (Kalkulator) ---
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
        except:
            await interaction.response.send_message("❌ Wprowadź poprawną liczbę!", ephemeral=True)

class ProduktSelect(ui.Select):
    def __init__(self):
        options = []
        for prods in MENU.values():
            for nazwa, cena in prods.items():
                options.append(discord.SelectOption(label=f"• {nazwa}", value=f"{nazwa}|{cena}"))
        super().__init__(placeholder="🛒 Wybierz produkt...", options=options)

    async def callback(self, interaction: discord.Interaction):
        nazwa, cena = self.values[0].split('|')
        await interaction.response.send_modal(IloscModal(nazwa, int(cena)))

class ZestawSelect(ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=f"• {n}", value=f"{n}|{c}") for n, c in ZESTAWY.items()]
        super().__init__(placeholder="📦 Wybierz zestaw...", options=options)

    async def callback(self, interaction: discord.Interaction):
        nazwa, cena = self.values[0].split('|')
        await interaction.response.send_modal(IloscModal(nazwa, int(cena)))

class MainView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProduktSelect())
        self.add_item(ZestawSelect())

# --- SYSTEM EVENTS ---
@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} zalogowany!')
    # Wymuszenie odświeżenia komend slash
    synced = await bot.tree.sync()
    print(f"✅ Zsynchronizowano {len(synced)} komend!")

# --- KOMENDY SLASH ---

@bot.tree.command(name="menu", description="Wyświetla menu Bean Machine i kalkulator")
async def menu(interaction: discord.Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return await interaction.response.send_message(f"❌ Komenda dostępna tylko na <#{ALLOWED_CHANNEL_ID}>!", ephemeral=True)

    embed = discord.Embed(title="**Bean Machine – Menu**", color=0xFF7600, description="**`Najlepsza kawiarnia w mieście!!!`**")
    
    napoje_txt = "\n".join([f"• **{p}** × {c} $" for p, c in MENU["napoje"].items()])
    jedzenie_txt = "\n".join([f"• **{p}** × {c} $" for p, c in MENU["jedzenie"].items()])
    zestawy_txt = "\n".join([f"• **{p}** × {c} $" for p, c in ZESTAWY.items()])

    embed.add_field(name="*** ☕ Napoje***", value=napoje_txt, inline=False)
    embed.add_field(name="*** 🍰 Jedzenie***", value=jedzenie_txt, inline=False)
    embed.add_field(name="*** 📦 Zestawy***", value=zestawy_txt, inline=False)
    embed.set_footer(text="Wybierz produkty z listy poniżej, aby obliczyć cenę.")

    try:
        file = discord.File("b1.png", filename="b1.png")
        embed.set_image(url="attachment://b1.png")
        await interaction.response.send_message(file=file, embed=embed, view=MainView())
    except:
        await interaction.response.send_message(embed=embed, view=MainView())

@bot.tree.command(name="plus", description="Nadaje plusa (zarządzanie awansami)")
@app_commands.describe(uzytkownik="Oznacz pracownika", powod="Powód", rodzaj="Poziom plusa")
@app_commands.choices(rodzaj=[
    app_commands.Choice(name="1 Plus", value=1),
    app_commands.Choice(name="2 Plus", value=2),
    app_commands.Choice(name="3 Plus", value=3),
])
async def plus(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str, rodzaj: app_commands.Choice[int]):
    req_role = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not req_role or not any(r.position >= req_role.position for r in interaction.user.roles):
        return await interaction.response.send_message("❌ Brak uprawnień Zarządu!", ephemeral=True)

    try:
        # Nadawanie roli plusa
        for r_id in ROLE_PLUSY.values(): await uzytkownik.remove_roles(interaction.guild.get_role(r_id))
        await uzytkownik.add_roles(interaction.guild.get_role(ROLE_PLUSY[rodzaj.value]))

        notka_awans = ""
        if rodzaj.value == 3:
            for stara, nowa in AWANS_MAP.items():
                if stara in [r.id for r in uzytkownik.roles]:
                    await uzytkownik.remove_roles(interaction.guild.get_role(stara))
                    await uzytkownik.add_roles(interaction.guild.get_role(nowa))
                    for r_id in ROLE_PLUSY.values(): await uzytkownik.remove_roles(interaction.guild.get_role(r_id))
                    notka_awans = f"\n\n🎊 **AWANS!** Nowa ranga: <@&{nowa}>"
                    break

        embed = discord.Embed(title="🌟 Przyznano Plusa!", color=0x2ECC71, timestamp=discord.utils.utcnow())
        embed.add_field(name="👤 Kto:", value=uzytkownik.mention, inline=True)
        embed.add_field(name="⭐ Poziom:", value=f"**{rodzaj.value}/3**", inline=True)
        embed.add_field(name="📝 Powód:", value=f"*{powod}*{notka_awans}", inline=False)
        
        if uzytkownik.display_avatar: embed.set_thumbnail(url=uzytkownik.display_avatar.url)
        if STARSZY_BARISTA_ID in [r.id for r in uzytkownik.roles]:
            embed.set_footer(text="Dalszy awans wymaga specjalnego wykazania się!")

        await interaction.response.send_message(embed=embed)
    except Exception as e: await interaction.response.send_message(f"Błąd: {e}", ephemeral=True)

@bot.tree.command(name="minus", description="Nadaje minusa (zarządzanie degradacjami)")
@app_commands.describe(uzytkownik="Oznacz pracownika", powod="Powód", rodzaj="Poziom minusa")
@app_commands.choices(rodzaj=[
    app_commands.Choice(name="1 Minus", value=1),
    app_commands.Choice(name="2 Minus", value=2),
    app_commands.Choice(name="3 Minus", value=3),
])
async def minus(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str, rodzaj: app_commands.Choice[int]):
    req_role = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not req_role or not any(r.position >= req_role.position for r in interaction.user.roles):
        return await interaction.response.send_message("❌ Brak uprawnień Zarządu!", ephemeral=True)

    try:
        # Nadawanie roli minusa
        for r_id in ROLE_MINUSY.values(): await uzytkownik.remove_roles(interaction.guild.get_role(r_id))
        await uzytkownik.add_roles(interaction.guild.get_role(ROLE_MINUSY[rodzaj.value]))

        notka_kara = ""
        if rodzaj.value == 3:
            degradowany = False
            for akt, nizej in DEGRADACJA_MAP.items():
                if akt in [r.id for r in uzytkownik.roles]:
                    await uzytkownik.remove_roles(interaction.guild.get_role(akt))
                    await uzytkownik.add_roles(interaction.guild.get_role(nizej))
                    notka_kara = f"\n\n📉 **DEGRADACJA!** Nowa ranga: <@&{nizej}>"
                    degradowany = True
                    break
            
            if not degradowany and PRAKTYKANT_ID in [r.id for r in uzytkownik.roles]:
                await uzytkownik.remove_roles(interaction.guild.get_role(PRAKTYKANT_ID))
                notka_kara = f"\n\n🚫 **USUNIĘCIE!** Strata rangi Praktykanta."
            
            for r_id in ROLE_MINUSY.values(): await uzytkownik.remove_roles(interaction.guild.get_role(r_id))

        embed = discord.Embed(title="⚠️ Przyznano Minusa!", color=0xE74C3C, timestamp=discord.utils.utcnow())
        embed.add_field(name="👤 Kto:", value=uzytkownik.mention, inline=True)
        embed.add_field(name="🔻 Poziom:", value=f"**{rodzaj.value}/3**", inline=True)
        embed.add_field(name="📝 Powód:", value=f"*{powod}*{notka_kara}", inline=False)
        
        if uzytkownik.display_avatar: embed.set_thumbnail(url=uzytkownik.display_avatar.url)
        embed.set_footer(text=f"Przez: {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)
    except Exception as e: await interaction.response.send_message(f"Błąd: {e}", ephemeral=True)

bot.run(DISCORD_TOKEN)
