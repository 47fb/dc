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

# Persistentny select w głównym menu
class MainSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🛒 kalkulator pojedynczego produktu", value="produkt", emoji="🛒"),
            discord.SelectOption(label="📦 kalkulator zestawów", value="zestaw", emoji="📦")
        ]
        super().__init__(placeholder="Wybierz opcję...", min_values=1, max_values=1, options=options, custom_id="main_select")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "produkt":
            await self.pokaz_wybor_produktu(interaction)
        else:
            await self.pokaz_wybor_zestawu(interaction)

    async def pokaz_wybor_produktu(self, interaction: discord.Interaction):
        # Tworzymy select z produktami (wszystkie kategorie)
        options = []
        for kategoria, produkty in MENU.items():
            for nazwa, cena in produkty.items():
                emoji = nazwa.split()[0]  # np. ☕
                options.append(discord.SelectOption(label=nazwa, value=f"{kategoria}|{nazwa}|{cena}", emoji=emoji))
        
        view = ui.View(timeout=60)
        view.add_item(ProduktSelect(options))
        view.add_item(AnulujButton())
        
        embed = discord.Embed(title="Wybierz produkt", color=0xFF7600)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def pokaz_wybor_zestawu(self, interaction: discord.Interaction):
        options = []
        for nazwa, cena in ZESTAWY.items():
            options.append(discord.SelectOption(label=nazwa, value=f"{nazwa}|{cena}", emoji="📦"))
        
        view = ui.View(timeout=60)
        view.add_item(ZestawSelect(options))
        view.add_item(AnulujButton())
        
        embed = discord.Embed(title="Wybierz zestaw", color=0xFF7600)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ProduktSelect(ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Wybierz produkt...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Oczekujemy formatu: kategoria|nazwa|cena
        kategoria, nazwa, cena_str = self.values[0].split('|')
        cena = int(cena_str)
        view = IloscViewProdukt(nazwa, cena)
        embed = discord.Embed(title="Ustaw ilość", color=0xFF7600)
        embed.add_field(name="Produkt", value=nazwa, inline=True)
        embed.add_field(name="Cena za sztukę", value=f"{cena} $", inline=True)
        await interaction.response.edit_message(embed=embed, view=view)

class ZestawSelect(ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Wybierz zestaw...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        nazwa, cena_str = self.values[0].split('|')
        cena = int(cena_str)
        view = IloscViewZestaw(nazwa, cena)
        embed = discord.Embed(title="Ustaw ilość zestawów", color=0xFF7600)
        embed.add_field(name="Zestaw", value=nazwa, inline=True)
        embed.add_field(name="Cena za zestaw", value=f"{cena} $", inline=True)
        await interaction.response.edit_message(embed=embed, view=view)

class IloscViewProdukt(ui.View):
    def __init__(self, produkt, cena):
        super().__init__(timeout=60)
        self.produkt = produkt
        self.cena = cena
        self.ilosc = 1

    @ui.button(label="➖", style=ButtonStyle.red)
    async def decrease(self, interaction: discord.Interaction, button: ui.Button):
        if self.ilosc > 1:
            self.ilosc -= 1
            await self.update_message(interaction)

    @ui.button(label="Ilość: 1", style=ButtonStyle.gray, disabled=True)
    async def display_count(self, interaction: discord.Interaction, button: ui.Button):
        pass

    @ui.button(label="➕", style=ButtonStyle.green)
    async def increase(self, interaction: discord.Interaction, button: ui.Button):
        self.ilosc += 1
        await self.update_message(interaction)

    @ui.button(label="💰 Oblicz cenę", style=ButtonStyle.primary)
    async def calculate(self, interaction: discord.Interaction, button: ui.Button):
        total = self.cena * self.ilosc
        embed = discord.Embed(title="🛒 Wynik kalkulacji", color=0xFF7600)
        embed.add_field(name="Produkt", value=self.produkt, inline=True)
        embed.add_field(name="Ilość", value=self.ilosc, inline=True)
        embed.add_field(name="Cena całkowita", value=f"**{total} $**", inline=False)
        embed.set_footer(text="Menu najlepszej kawiarni w mieście!!")
        view = ui.View()
        view.add_item(ZamknijButton())
        await interaction.response.edit_message(embed=embed, view=view)

    async def update_message(self, interaction: discord.Interaction):
        for child in self.children:
            if isinstance(child, ui.Button) and child.label and child.label.startswith("Ilość:"):
                child.label = f"Ilość: {self.ilosc}"
                break
        total = self.cena * self.ilosc
        embed = discord.Embed(title="Ustaw ilość", color=0xFF7600)
        embed.add_field(name="Produkt", value=self.produkt, inline=True)
        embed.add_field(name="Cena za sztukę", value=f"{self.cena} $", inline=True)
        embed.add_field(name="Razem", value=f"**{total} $**", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

class IloscViewZestaw(ui.View):
    def __init__(self, nazwa, cena):
        super().__init__(timeout=60)
        self.nazwa = nazwa
        self.cena = cena
        self.ilosc = 1

    @ui.button(label="➖", style=ButtonStyle.red)
    async def decrease(self, interaction: discord.Interaction, button: ui.Button):
        if self.ilosc > 1:
            self.ilosc -= 1
            await self.update_message(interaction)

    @ui.button(label="Ilość: 1", style=ButtonStyle.gray, disabled=True)
    async def display_count(self, interaction: discord.Interaction, button: ui.Button):
        pass

    @ui.button(label="➕", style=ButtonStyle.green)
    async def increase(self, interaction: discord.Interaction, button: ui.Button):
        self.ilosc += 1
        await self.update_message(interaction)

    @ui.button(label="💰 Oblicz cenę", style=ButtonStyle.primary)
    async def calculate(self, interaction: discord.Interaction, button: ui.Button):
        total = self.cena * self.ilosc
        embed = discord.Embed(title="📦 Wynik kalkulacji zestawu", color=0xFF7600)
        embed.add_field(name="Zestaw", value=self.nazwa, inline=True)
        embed.add_field(name="Ilość zestawów", value=self.ilosc, inline=True)
        embed.add_field(name="Cena całkowita", value=f"**{total} $**", inline=False)
        embed.set_footer(text="Menu najlepszej kawiarni w mieście!!")
        view = ui.View()
        view.add_item(ZamknijButton())
        await interaction.response.edit_message(embed=embed, view=view)

    async def update_message(self, interaction: discord.Interaction):
        for child in self.children:
            if isinstance(child, ui.Button) and child.label and child.label.startswith("Ilość:"):
                child.label = f"Ilość: {self.ilosc}"
                break
        total = self.cena * self.ilosc
        embed = discord.Embed(title="Ustaw ilość zestawów", color=0xFF7600)
        embed.add_field(name="Zestaw", value=self.nazwa, inline=True)
        embed.add_field(name="Cena za zestaw", value=f"{self.cena} $", inline=True)
        embed.add_field(name="Razem", value=f"**{total} $**", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

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

class MainView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MainSelect())

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} online')
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} komend zsynchronizowanych")
    except Exception as e:
        print(f"❌ Błąd synchronizacji: {e}")

@bot.tree.command(name="menu", description="Wyświetla menu Beam Machine")
async def menu(interaction: discord.Interaction):
    # Embed z menu – czytelny, z dużymi nagłówkami
    embed = discord.Embed(title="**Beam Machine – Menu**", color=0xFF7600)
    
    # Dodanie obrazka jako banner (jeśli plik istnieje w katalogu)
    file = None
    try:
        with open("b1.png", "rb") as f:
            file = discord.File(f, filename="b1.png")
            embed.set_image(url="attachment://b1.png")
    except FileNotFoundError:
        print("Plik b1.png nie znaleziony, pomijam banner.")
    
    # Formatowanie kategorii – nagłówki z # spacją i emotką
    napoje = "\n".join([f"• {p} **``×`` {c} $**" for p, c in MENU["napoje"].items()])
    jedzenie = "\n".join([f"• {p} **``×`` {c} $**" for p, c in MENU["jedzenie"].items()])
    
    embed.add_field(name="# ☕ Napoje", value=napoje, inline=False)
    embed.add_field(name="# 🍰 Jedzenie", value=jedzenie, inline=False)
    embed.set_footer(text="Menu najlepszej kawiarni w mieście!!")
    
    view = MainView()
    
    if file:
        await interaction.response.send_message(embed=embed, view=view, file=file)
    else:
        await interaction.response.send_message(embed=embed, view=view)

bot.run(DISCORD_TOKEN)
