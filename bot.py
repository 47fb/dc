import discord
from discord.ext import commands
from discord import app_commands, ui, ButtonStyle
import os

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ALLOWED_CHANNEL_ID = 1309969415483297795  # ID Twojego kanału

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- TWOJE DANE ---
MENU = {
    "napoje": {
        "☕ Expresso": 1100, "☕ Americano": 1200, "☕ Macchiato": 1200,
        "☕ Latte": 1100, "☕ Cappuccino": 900, "☕ Mocha": 1100
    },
    "jedzenie": {
        "🍰 Szarlotka": 1400, "🍰 Brownie": 1400, "🍰 Sernik": 1300
    }
}

ZESTAWY = {
    "📦 Bean Mini (1+1)": 1500,
    "📦 Bean Basic (2+2)": 5000
}

# --- MODAL ---
class IloscModal(ui.Modal, title="Kalkulator"):
    def __init__(self, nazwa, cena):
        super().__init__()
        self.nazwa = nazwa
        self.cena = cena
        self.ilosc = ui.TextInput(label="Podaj ilość", placeholder="Wpisz liczbę...", default="1", min_length=1, max_length=3)
        self.add_item(self.ilosc)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            total = int(self.ilosc.value) * self.cena
            embed = discord.Embed(title="🛒 Wynik kalkulacji", color=0xFF7600)
            embed.add_field(name="Pozycja", value=f"** {self.nazwa}**", inline=True)
            embed.add_field(name="Ilość", value=f"**{self.ilosc.value}**", inline=True)
            embed.add_field(name="Suma", value=f"`` {total} $``", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Podaj poprawną liczbę!", ephemeral=True)

# --- SELECTY ---
class ProduktSelect(ui.Select):
    def __init__(self):
        options = []
        for kat, prods in MENU.items():
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

# --- BOT EVENTS ---
@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} gotowy!')
    await bot.tree.sync()

@bot.tree.command(name="menu", description="Wyświetla menu Bean Machine")
async def menu(interaction: discord.Interaction):
    # BLOKADA KANAŁU
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ Ta komenda może być używana tylko na kanale <#{ALLOWED_CHANNEL_ID}>!", 
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="**Bean Machine – Menu**",
        color=0xFF7600,
        description="`**`Najlepsza kawiarnia w mieście!!`**"
    )

    napoje = "\n".join([f"• **{p}** × {c} $" for p, c in MENU["napoje"].items()])
    jedzenie = "\n".join([f"• **{p}** × {c} $" for p, c in MENU["jedzenie"].items()])
    zestawy = "\n".join([f"• **{p}** × {c} $" for p, c in ZESTAWY.items()])

    embed.add_field(name="*** ☕ Napoje***", value=napoje, inline=False)
    embed.add_field(name="*** 🍰 Jedzenie***", value=jedzenie, inline=False)
    embed.add_field(name="*** 📦 Zestawy***", value=zestawy, inline=False)
    embed.set_footer(text="Smacznie i z klasą!")

    try:
        file = discord.File("b1.png", filename="b1.png")
        embed.set_image(url="attachment://b1.png")
        await interaction.response.send_message(file=file, embed=embed, view=MainView())
    except:
        await interaction.response.send_message(embed=embed, view=MainView())

bot.run(DISCORD_TOKEN)

