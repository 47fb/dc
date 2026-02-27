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

# Menu – produkty i ceny (zgodne z obrazkiem Club 777)
MENU = {
    "dania": {
        "🍔 Cheesburger": 1500,
        "🍔 Nachos": 1300,
        "🥗 Sałatka grecka": 1000
    },
    "napoje": {
        "🥤 Sok porzeczkowy": 1500,
        "🥤 Mojito bez alkoholu": 1300,
        "🥤 Woda mineralna": 1000
    },
    "drinki": {
        "🍸 77 Special": 2000,
        "🍸 Negroni": 1800,
        "🍸 Pina colada": 1600,
        "🍸 Cuba Libre": 1400,
        "🍸 Toxic wasted": 1200,
        "🍸 Hiroshima": 1000
    }
}

# Zestawy
ZESTAWY = {
    "📦 Beam Mini (1 danie + 1 napój/drink)": 1500,
    "📦 Beam Basic (2 dania + 2 napoje/drinki)": 5000
}

class GlownyView(ui.View):
    """Główny widok z dwoma przyciskami – persistent"""
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🛒 Kalkulator pojedynczego produktu", style=ButtonStyle.primary, emoji="🛒", custom_id="kalkulator_poj")
    async def pojedynczy_button(self, interaction: discord.Interaction, button: ui.Button):
        # Wyświetlamy select z wszystkimi produktami
        await self.pokaz_wybor_produktu(interaction)

    @ui.button(label="📦 Kalkulator zestawów", style=ButtonStyle.success, emoji="📦", custom_id="kalkulator_zest")
    async def zestawy_button(self, interaction: discord.Interaction, button: ui.Button):
        # Wyświetlamy select z zestawami
        await self.pokaz_wybor_zestawu(interaction)

    async def pokaz_wybor_produktu(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Wybierz produkt", color=0xFF7600)
        # Tworzymy listę opcji dla selecta
        options = []
        for kategoria, produkty in MENU.items():
            for nazwa, cena in produkty.items():
                # Dodajemy emoji z kategorii do nazwy dla lepszej orientacji
                opis = f"{cena} $"
                options.append(discord.SelectOption(label=nazwa, value=f"{kategoria}|{nazwa}", description=opis, emoji=nazwa.split()[0]))
        view = WyborProduktuView(options)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def pokaz_wybor_zestawu(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Wybierz zestaw", color=0xFF7600)
        options = []
        for nazwa, cena in ZESTAWY.items():
            options.append(discord.SelectOption(label=nazwa, value=nazwa, description=f"{cena} $", emoji="📦"))
        view = WyborZestawuView(options)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class WyborProduktuView(ui.View):
    def __init__(self, options):
        super().__init__(timeout=60)
        self.add_item(ProduktSelect(options))
        # Dodajemy przycisk anulowania
        self.add_item(AnulujButton())

class ProduktSelect(ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Wybierz produkt...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Pobieramy wartość: kategoria|nazwa
        kategoria, nazwa = self.values[0].split('|', 1)
        cena = MENU[kategoria][nazwa]
        # Przechodzimy do ustawiania ilości
        view = IloscViewProdukt(nazwa, cena)
        embed = discord.Embed(title="Ustaw ilość", color=0xFF7600)
        embed.add_field(name="Produkt", value=nazwa, inline=True)
        embed.add_field(name="Cena za sztukę", value=f"{cena} $", inline=True)
        await interaction.response.edit_message(embed=embed, view=view)

class WyborZestawuView(ui.View):
    def __init__(self, options):
        super().__init__(timeout=60)
        self.add_item(ZestawSelect(options))
        self.add_item(AnulujButton())

class ZestawSelect(ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Wybierz zestaw...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        nazwa = self.values[0]
        cena = ZESTAWY[nazwa]
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
        embed.set_footer(text=f"Łącznie: {total} $")
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
        embed.set_footer(text=f"Łącznie: {total} $")
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

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} online')
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} komend zsynchronizowanych")
    except Exception as e:
        print(f"❌ Błąd synchronizacji: {e}")

@bot.tree.command(name="cennik", description="Wyświetla menu Club 777")
async def cennik(interaction: discord.Interaction):
    # Embed z menu – czytelny, z dużymi nagłówkami
    embed = discord.Embed(title="**Club 777**", color=0xFF7600)
    
    # Formatowanie kategorii
    dania = "\n".join([f"• {p} – **{c} $**" for p, c in MENU["dania"].items()])
    napoje = "\n".join([f"• {p} – **{c} $**" for p, c in MENU["napoje"].items()])
    drinki = "\n".join([f"• {p} – **{c} $**" for p, c in MENU["drinki"].items()])
    
    embed.add_field(name="🍔 **DANIA**", value=dania, inline=False)
    embed.add_field(name="🥤 **NAPOJE**", value=napoje, inline=False)
    embed.add_field(name="🍸 **DRINKI**", value=drinki, inline=False)
    embed.set_footer(text="Smacznie, drogo i z klasą!")
    
    view = GlownyView()
    await interaction.response.send_message(embed=embed, view=view)

bot.run(DISCORD_TOKEN)
