import discord
from discord.ext import commands
from discord import app_commands, ui, ButtonStyle
import os

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    print('❌ Brak tokenu DISCORD_TOKEN')
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Menu kawiarni Bean Machine (poprawiona nazwa)
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

ZESTAWY = {
    "📦 Bean Mini (1 kawa + 1 ciasto)": 1500,
    "📦 Bean Basic (2 kawy + 2 ciasta)": 5000
}

# Główny select do wyboru kalkulatora
class MainSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🛒 kalkulator pojedynczego produktu", value="produkt", emoji="🛒"),
            discord.SelectOption(label="📦 kalkulator zestawów", value="zestaw", emoji="📦")
        ]
        super().__init__(placeholder="Wybierz opcję...", min_values=1, max_values=1, options=options, custom_id="main_select")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "produkt":
            await interaction.response.send_message(
                embed=discord.Embed(title="Wybierz produkt", color=0xFF7600),
                view=ProduktSelectView(),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(title="Wybierz zestaw", color=0xFF7600),
                view=ZestawSelectView(),
                ephemeral=True
            )

class MainView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MainSelect())

# Widok z selectem produktów
class ProduktSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        options = []
        for kategoria, produkty in MENU.items():
            for nazwa, cena in produkty.items():
                options.append(discord.SelectOption(label=nazwa, value=f"{nazwa}|{cena}", emoji=nazwa.split()[0]))
        self.add_item(ProduktSelect(options))
        self.add_item(AnulujButton())

class ProduktSelect(ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Wybierz produkt...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        nazwa, cena_str = self.values[0].split('|')
        cena = int(cena_str)
        await interaction.response.send_modal(IloscModal(nazwa, cena, typ="produkt"))

# Widok z selectem zestawów
class ZestawSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        options = [
            discord.SelectOption(label=nazwa, value=f"{nazwa}|{cena}", emoji="📦")
            for nazwa, cena in ZESTAWY.items()
        ]
        self.add_item(ZestawSelect(options))
        self.add_item(AnulujButton())

class ZestawSelect(ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Wybierz zestaw...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        nazwa, cena_str = self.values[0].split('|')
        cena = int(cena_str)
        await interaction.response.send_modal(IloscModal(nazwa, cena, typ="zestaw"))

# Modal do wpisania ilości
class IloscModal(ui.Modal, title="Ile sprzedajesz?"):
    def __init__(self, nazwa, cena, typ):
        super().__init__()
        self.nazwa = nazwa
        self.cena = cena
        self.typ = typ
        self.ilosc = ui.TextInput(label="Ilość", placeholder="Wpisz liczbę", default="1", min_length=1, max_length=3)
        self.add_item(self.ilosc)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            ilosc = int(self.ilosc.value)
            if ilosc < 1:
                await interaction.response.send_message("❌ Ilość musi być co najmniej 1.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Wpisz poprawną liczbę.", ephemeral=True)
            return

        total = self.cena * ilosc
        embed = discord.Embed(color=0xFF7600)
        if self.typ == "produkt":
            embed.title = "🛒 Wynik kalkulacji"
            embed.add_field(name="Produkt", value=self.nazwa, inline=True)
            embed.add_field(name="Cena za sztukę", value=f"{self.cena} $", inline=True)
        else:
            embed.title = "📦 Wynik kalkulacji zestawu"
            embed.add_field(name="Zestaw", value=self.nazwa, inline=True)
            embed.add_field(name="Cena za zestaw", value=f"{self.cena} $", inline=True)
        embed.add_field(name="Ilość", value=str(ilosc), inline=True)
        embed.add_field(name="Łączna cena", value=f"**{total} $**", inline=False)
        embed.set_footer(text="Menu najlepszej kawiarni w mieście!!")

        view = ui.View()
        view.add_item(ZamknijButton())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Przyciski do zamykania
class AnulujButton(ui.Button):
    def __init__(self):
        super().__init__(label="❌ Anuluj", style=ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.message.delete()

class ZamknijButton(ui.Button):
    def __init__(self):
        super().__init__(label="❌ Zamknij", style=ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.message.delete()

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} online')
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} komend zsynchronizowanych")
    except Exception as e:
        print(f"❌ Błąd synchronizacji: {e}")

@bot.tree.command(name="menu", description="Wyświetla menu Bean Machine")
async def menu(interaction: discord.Interaction):
    # Większy embed z obrazkiem
    embed = discord.Embed(
        title="**Bean Machine – Menu**",
        color=0xFF7600,
        description="Menu najlepszej kawiarni w mieście!!"
    )

    # Dodanie obrazka jako banner (jeśli plik istnieje)
    file = None
    try:
        with open("b1.png", "rb") as f:
            file = discord.File(f, filename="b1.png")
            embed.set_image(url="attachment://b1.png")
    except FileNotFoundError:
        pass  # Brak obrazka – wyświetlamy bez

    # Formatowanie menu – nagłówki z # i emotką, produkty w formacie "• nazwa × cena $"
    napoje = "\n".join([f"• {produkt} × {cena} $" for produkt, cena in MENU["napoje"].items()])
    jedzenie = "\n".join([f"• {produkt} × {cena} $" for produkt, cena in MENU["jedzenie"].items()])

    embed.add_field(name=" ☕ #Napoje", value=napoje, inline=False)
    embed.add_field(name=" 🍰 Jedzenie", value=jedzenie, inline=False)
    embed.set_footer(text="Menu najlepszej kawiarni w mieście!!")

    view = MainView()
    if file:
        await interaction.response.send_message(embed=embed, file=file, view=view)
    else:
        await interaction.response.send_message(embed=embed, view=view)

bot.run(DISCORD_TOKEN)


