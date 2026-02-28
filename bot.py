import discord
from discord.ext import commands
from discord import app_commands, ui
import os

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ALLOWED_CHANNEL_ID = 1309969415483297795
REQUIRED_ROLE_ID = 1309969414099304448  # Ranga Zarząd+

# --- MAPOWANIE RANG ---
# Awans: Stara -> Nowa
AWANS_MAP = {
    1309969414023811168: 1309969414023811169,
    1309969414023811169: 1309969414023811170,
    1309969414023811170: 1309969414023811171
}

# Degradacja: Aktualna -> Niższa
DEGRADACJA_MAP = {
    1309969414023811171: 1309969414023811170,
    1309969414023811170: 1309969414023811169,
    1309969414023811169: 1309969414023811168
}

PRAKTYKANT_ID = 1309969414023811168
STARSZY_BARISTA_ID = 1309969414023811171

# --- ROLE PLUSÓW I MINUSÓW ---
ROLE_PLUSY = {
    1: 1475172069653348423,
    2: 1475172072685834354,
    3: 1475172075365863688
}

# Zmień te ID na poprawne role minusów na Twoim serwerze!
ROLE_MINUSY = {
    1: 1475172069653348423, # Przykład (wpisz ID roli 1 minusa)
    2: 1475172072685834354, # Przykład (wpisz ID roli 2 minusa)
    3: 1475172075365863688  # Przykład (wpisz ID roli 3 minusa)
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- TWOJE DANE MENU (bez zmian) ---
MENU = {
    "napoje": {"☕ Expresso": 1100, "☕ Americano": 1200, "☕ Macchiato": 1200, "☕ Latte": 1100, "☕ Cappuccino": 900, "☕ Mocha": 1100},
    "jedzenie": {"🍰 Szarlotka": 1400, "🍰 Brownie": 1400, "🍰 Sernik": 1300}
}
ZESTAWY = {"📦 Bean Mini (1+1)": 1500, "📦 Bean Basic (2+2)": 5000}

# --- KLASY UI (bez zmian) ---
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
        except: await interaction.response.send_message("❌ Błąd!", ephemeral=True)

class MainView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Tu uproszczone dla czytelności kodu
        pass

# --- EVENTS ---
@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} gotowy!')
    await bot.tree.sync()

# --- KOMENDA PLUS (Z AWANSEM) ---
@bot.tree.command(name="plus", description="Nadaje plusa i zarządza awansami")
async def plus(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str, rodzaj: app_commands.Choice[int]):
    req_role = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not req_role or not any(r.position >= req_role.position for r in interaction.user.roles):
        return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)

    try:
        # Nadawanie roli plusa
        rola_plusa = interaction.guild.get_role(ROLE_PLUSY[rodzaj.value])
        for r_id in ROLE_PLUSY.values(): await uzytkownik.remove_roles(interaction.guild.get_role(r_id))
        await uzytkownik.add_roles(rola_plusa)

        awans_info = ""
        if rodzaj.value == 3:
            for stara_id, nowa_id in AWANS_MAP.items():
                if stara_id in [r.id for r in uzytkownik.roles]:
                    await uzytkownik.remove_roles(interaction.guild.get_role(stara_id))
                    await uzytkownik.add_roles(interaction.guild.get_role(nowa_id))
                    await uzytkownik.remove_roles(rola_plusa) # Czyścimy plusy po awansie
                    awans_info = f"\n\n🎊 **AWANS!** Nowa ranga: <@&{nowa_id}>"
                    break

        embed = discord.Embed(title="🌟 Przyznano Plusa!", color=0x2ECC71, timestamp=discord.utils.utcnow())
        embed.add_field(name="👤 Kto:", value=uzytkownik.mention, inline=True)
        embed.add_field(name="⭐ Poziom:", value=f"**{rodzaj.value}/3**", inline=True)
        embed.add_field(name="📝 Powód:", value=f"*{powod}*{awans_info}", inline=False)
        
        if STARSZY_BARISTA_ID in [r.id for r in uzytkownik.roles]:
            embed.set_footer(text="Aby awansować wyżej niż Starszy Barista, musisz się wykazać!")

        await interaction.response.send_message(embed=embed)
    except Exception as e: await interaction.response.send_message(f"Błąd: {e}", ephemeral=True)

# --- KOMENDA MINUS (Z DEGRADACJĄ) ---
@bot.tree.command(name="minus", description="Nadaje minusa i zarządza degradacjami")
@app_commands.describe(uzytkownik="Pracownik", powod="Powód kary", rodzaj="Poziom minusa")
@app_commands.choices(rodzaj=[
    app_commands.Choice(name="1 Minus", value=1),
    app_commands.Choice(name="2 Minus", value=2),
    app_commands.Choice(name="3 Minus", value=3),
])
async def minus(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str, rodzaj: app_commands.Choice[int]):
    req_role = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not req_role or not any(r.position >= req_role.position for r in interaction.user.roles):
        return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)

    try:
        # Nadawanie roli minusa
        rola_minusa = interaction.guild.get_role(ROLE_MINUSY[rodzaj.value])
        for r_id in ROLE_MINUSY.values(): await uzytkownik.remove_roles(interaction.guild.get_role(r_id))
        await uzytkownik.add_roles(rola_minusa)

        kara_info = ""
        if rodzaj.value == 3:
            degradowany = False
            # Sprawdzamy rangi od najwyższej w dół
            for akt_id, nizej_id in DEGRADACJA_MAP.items():
                if akt_id in [r.id for r in uzytkownik.roles]:
                    await uzytkownik.remove_roles(interaction.guild.get_role(akt_id))
                    await uzytkownik.add_roles(interaction.guild.get_role(nizej_id))
                    kara_info = f"\n\n📉 **DEGRADACJA!** Nowa ranga: <@&{nizej_id}>"
                    degradowany = True
                    break
            
            # Jeśli nie był degradowany wyżej, sprawdzamy czy jest Praktykantem
            if not degradowany and PRAKTYKANT_ID in [r.id for r in uzytkownik.roles]:
                await uzytkownik.remove_roles(interaction.guild.get_role(PRAKTYKANT_ID))
                kara_info = f"\n\n🚫 **USUNIĘCIE!** Pracownik stracił rangę Praktykanta."
            
            # Czyścimy minusy po degradacji
            await uzytkownik.remove_roles(rola_minusa)

        embed = discord.Embed(title="⚠️ Przyznano Minusa!", color=0xE74C3C, timestamp=discord.utils.utcnow())
        embed.add_field(name="👤 Kto:", value=uzytkownik.mention, inline=True)
        embed.add_field(name="🔻 Poziom:", value=f"**{rodzaj.value}/3**", inline=True)
        embed.add_field(name="📝 Powód:", value=f"*{powod}*{kara_info}", inline=False)
        embed.set_footer(text=f"Nadane przez: {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)
    except Exception as e: await interaction.response.send_message(f"Błąd: {e}", ephemeral=True)

bot.run(DISCORD_TOKEN)
