import discord
from discord.ext import commands
from discord import app_commands, ui
import os

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ALLOWED_CHANNEL_ID = 1309969415483297795
REQUIRED_ROLE_ID = 1309969414099304448  # Ranga Zarząd+

# Mapowanie awansów (Stara ranga -> Nowa ranga)
AWANS_MAP = {
    1309969414023811168: 1309969414023811169,
    1309969414023811169: 1309969414023811170,
    1309969414023811170: 1309969414023811171  # To jest Starszy Barista
}

STARSZY_BARISTA_ID = 1309969414023811171

# ID ról plusów
ROLE_PLUSY = {
    1: 1475172069653348423,
    2: 1475172072685834354,
    3: 1475172075365863688
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

# --- MODAL I SELECTY (bez zmian) ---
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

class ProduktSelect(ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=f"• {n}", value=f"{n}|{c}") for kat in MENU.values() for n, c in kat.items()]
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

# --- EVENTS ---
@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} gotowy!')
    # Wymuszenie synchronizacji na serwerze (naprawia brak komend slash)
    for guild in bot.guilds:
        await bot.tree.sync(guild=guild)
    await bot.tree.sync()

@bot.tree.command(name="menu", description="Wyświetla menu Bean Machine")
async def menu(interaction: discord.Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return await interaction.response.send_message(f"❌ Tylko na <#{ALLOWED_CHANNEL_ID}>!", ephemeral=True)
    embed = discord.Embed(title="**Bean Machine – Menu**", color=0xFF7600, description="**`Najlepsza kawiarnia w mieście!!!`**")
    for k, v in {"☕ Napoje": "napoje", "🍰 Jedzenie": "jedzenie"}.items():
        embed.add_field(name=f"*** {k}***", value="\n".join([f"• **{p}** × {c} $" for p, c in MENU[v].items()]), inline=False)
    embed.add_field(name="*** 📦 Zestawy***", value="\n".join([f"• **{p}** × {c} $" for p, c in ZESTAWY.items()]), inline=False)
    try:
        file = discord.File("b1.png", filename="b1.png")
        embed.set_image(url="attachment://b1.png")
        await interaction.response.send_message(file=file, embed=embed, view=MainView())
    except: await interaction.response.send_message(embed=embed, view=MainView())

# --- KOMENDA PLUS Z AWANSEM ---
@bot.tree.command(name="plus", description="Nadaje plusa i zarządza awansami")
@app_commands.describe(uzytkownik="Oznacz pracownika", powod="Powód plusa", rodzaj="Poziom plusa")
@app_commands.choices(rodzaj=[
    app_commands.Choice(name="1 Plus", value=1),
    app_commands.Choice(name="2 Plus", value=2),
    app_commands.Choice(name="3 Plus", value=3),
])
async def plus(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str, rodzaj: app_commands.Choice[int]):
    # Sprawdzenie uprawnień
    req_role = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not req_role or not any(r.position >= req_role.position for r in interaction.user.roles):
        return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)

    rola_plusa = interaction.guild.get_role(ROLE_PLUSY[rodzaj.value])
    
    try:
        # Usuwamy poprzednie plusy, żeby nie miał wszystkich na raz
        for r_id in ROLE_PLUSY.values():
            await uzytkownik.remove_roles(interaction.guild.get_role(r_id))
        
        # Nadajemy nowego plusa
        await uzytkownik.add_roles(rola_plusa)

        awans_info = ""
        # LOGIKA AWANSU (Tylko przy 3 plusie)
        if rodzaj.value == 3:
            for stara_id, nowa_id in AWANS_MAP.items():
                stara_rola = interaction.guild.get_role(stara_id)
                if stara_rola in uzytkownik.roles:
                    nowa_rola = interaction.guild.get_role(nowa_id)
                    await uzytkownik.remove_roles(stara_rola)
                    await uzytkownik.add_roles(nowa_rola)
                    # Przy awansie zazwyczaj czyścimy plusy
                    await uzytkownik.remove_roles(rola_plusa)
                    awans_info = f"\n\n🎊 **AWANS!** Pracownik awansował na: {nowa_rola.mention}!"
                    break

        # Embed główny
        embed = discord.Embed(title="🌟 Przyznano Plusa!", color=0x2ECC71, timestamp=discord.utils.utcnow())
        embed.add_field(name="👤 Kto:", value=uzytkownik.mention, inline=True)
        embed.add_field(name="⭐ Poziom:", value=f"**{rodzaj.value}/3**", inline=True)
        embed.add_field(name="📝 Powód:", value=f"*{powod}*{awans_info}", inline=False)

        # Informacja o dalszej ścieżce
        if STARSZY_BARISTA_ID in [r.id for r in uzytkownik.roles]:
            embed.set_footer(text="Aby otrzymać awans wyżej niż Starszy Barista, musisz wykazać się wyjątkową inicjatywą i zaangażowaniem!")
        else:
            embed.set_footer(text=f"Nadane przez: {interaction.user.display_name}")

        if uzytkownik.display_avatar: embed.set_thumbnail(url=uzytkownik.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"❌ Błąd: {e}", ephemeral=True)

bot.run(DISCORD_TOKEN)
