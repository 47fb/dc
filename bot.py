import discord
from discord.ext import commands
from discord import app_commands, ui, ButtonStyle
import os

# Token ze zmiennych środowiskowych
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    print('❌ Brak tokenu DISCORD_TOKEN')
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Menu kawiarni Beam Machine
MENU = {
    "napoje": {
        "☕ Expresso": 1100,
        "☕ Americano": 1200,
        "☕ Macchiato": 1200,
        "☕ Latte": 1100,
        "☕ Cappuccino": 900,
        "☕ Mocha": 1100
    },
    "jedzenie": {
        "🍰 Szarlotka": 1400,
        "🍰 Brownie": 1400,
        "🍰 Sernik": 1300
    }
}

# Zestawy
ZESTAWY = {
    "📦 Beam Mini (1 kawa + 1 ciasto)": 1500,
    "📦 Beam Basic (2 kawy + 2 ciasta)": 5000
}

# Główny select do wyboru kalkulatora – tylko jedna emotka w wartości, label bez emotki
class MainSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="kalkulator pojedynczego produktu", value="produkt", emoji="🛒"),
            discord.SelectOption(label="kalkulator zestawów", value="zestaw", emoji="📦")
        ]
        super().__init__(placeholder="Wybierz opcję...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "produkt":
            await interaction.response.send_modal(ProduktModal())
        else:
            await interaction.response.send_modal(ZestawModal())

class MainView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MainSelect())

# Modal dla pojedynczego produktu
class ProduktModal(ui.Modal, title="🛒 Kalkulator pojedynczego produktu"):
    # Tworzymy listę opcji dla selecta w modalu – każda z emotką w wartości
    produkty_opcje = []
    for kat in MENU.values():
        for nazwa, cena in kat.items():
            # Emotka jest już w nazwie, więc nie dodajemy osobno
            produkty_opcje.append(discord.SelectOption(label=nazwa, value=f"{nazwa}|{cena}"))

    produkt = ui.Select(
        placeholder="Wybierz produkt",
        options=produkty_opcje
    )
    ilosc = ui.TextInput(label="Ile produktów sprzedajesz?", placeholder="Wpisz liczbę", default="1", min_length=1, max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        nazwa, cena_str = self.produkt.values[0].split('|')
        cena = int(cena_str)
        try:
            ilosc = int(self.ilosc.value)
            if ilosc < 1:
                await interaction.response.send_message("❌ Ilość musi być co najmniej 1.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Wpisz poprawną liczbę.", ephemeral=True)
            return

        total = cena * ilosc
        embed = discord.Embed(title="🛒 Wynik kalkulacji", color=0xFF7600)
        embed.add_field(name="Produkt", value=nazwa, inline=True)
        embed.add_field(name="Cena za sztukę", value=f"{cena} $", inline=True)
        embed.add_field(name="Ilość", value=str(ilosc), inline=True)
        embed.add_field(name="Łączna cena", value=f"**{total} $**", inline=False)
        embed.set_footer(text="Menu najlepszej kawiarni w mieście!!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Modal dla zestawów
class ZestawModal(ui.Modal, title="📦 Kalkulator zestawów"):
    zestaw_opcje = [
        discord.SelectOption(label=nazwa, value=f"{nazwa}|{cena}")
        for nazwa, cena in ZESTAWY.items()
    ]
    zestaw = ui.Select(
        placeholder="Wybierz zestaw",
        options=zestaw_opcje
    )
    ilosc = ui.TextInput(label="Ile zestawów sprzedajesz?", placeholder="Wpisz liczbę", default="1", min_length=1, max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        nazwa, cena_str = self.zestaw.values[0].split('|')
        cena = int(cena_str)
        try:
            ilosc = int(self.ilosc.value)
            if ilosc < 1:
                await interaction.response.send_message("❌ Ilość musi być co najmniej 1.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Wpisz poprawną liczbę.", ephemeral=True)
            return

        total = cena * ilosc
        embed = discord.Embed(title="📦 Wynik kalkulacji zestawu", color=0xFF7600)
        embed.add_field(name="Zestaw", value=nazwa, inline=True)
        embed.add_field(name="Cena za zestaw", value=f"{cena} $", inline=True)
        embed.add_field(name="Ilość zestawów", value=str(ilosc), inline=True)
        embed.add_field(name="Łączna cena", value=f"**{total} $**", inline=False)
        embed.set_footer(text="Menu najlepszej kawiarni w mieście!!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} online')
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} komend zsynchronizowanych")
    except Exception as e:
        print(f"❌ Błąd synchronizacji: {e}")

@bot.tree.command(name="cennik", description="Wyświetla menu Beam Machine")
async def cennik(interaction: discord.Interaction):
    # Embed z menu – dokładnie według opisu
    embed = discord.Embed(title="**Beam Machine – Menu**", color=0xFF7600)
    
    # Napoje
    napoje_text = ""
    for produkt, cena in MENU["napoje"].items():
        # produkt zawiera już emotkę, np. "☕ Expresso"
        napoje_text += f"• {produkt} – **{cena} $**\n"
    embed.add_field(name="# ☕ × Napoje", value=napoje_text, inline=False)
    
    # Jedzenie
    jedzenie_text = ""
    for produkt, cena in MENU["jedzenie"].items():
        jedzenie_text += f"• {produkt} – **{cena} $**\n"
    embed.add_field(name="# 🍰 × Jedzenie", value=jedzenie_text, inline=False)
    
    embed.set_footer(text="Menu najlepszej kawiarni w mieście!!")
    
    view = MainView()
    await interaction.response.send_message(embed=embed, view=view)

bot.run(DISCORD_TOKEN)
