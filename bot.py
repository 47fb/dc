import discord
from discord.ext import commands
from discord import app_commands, ui, ButtonStyle
import os

# Pobierz token ze zmiennych środowiskowych Railway
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

if not DISCORD_TOKEN:
    print('❌ Brak tokenu DISCORD_TOKEN. Ustaw go w Railway Variables!')
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Ceny produktów (kawy i ciasta)
CENY = {
    "napoje": {
        "☕ Expresso": 1100,
        "☕ Americano": 1200,
        "☕ Macchiato": 1200,
        "☕ Latte": 1100,
        "☕ Cappuccino": 900,
        "☕ Mocha": 1100
    },
    "dania": {
        "🍰 Szarlotka": 1400,
        "🍰 Brownie": 1400,
        "🍰 Sernik": 1300
    },
    "zestawy": {
        "📦 Beam Mini": 1500,
        "📦 Beam Basic": 5000
    }
}

class GlownyView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.koszyk = {}
    
    @ui.button(label="☕ Kupno pojedyncze", style=ButtonStyle.primary, emoji="☕", custom_id="kupno_pojedyncze")
    async def kupno_pojedyncze(self, interaction: discord.Interaction, button: ui.Button):
        await self.pokaz_kategorie(interaction, "Wybierz kategorię:")
    
    @ui.button(label="📦 Kalkulator zestawów", style=ButtonStyle.success, emoji="📦", custom_id="kalkulator_zestawow")
    async def kalkulator_zestawow(self, interaction: discord.Interaction, button: ui.Button):
        await self.pokaz_zestawy(interaction)
    
    async def pokaz_kategorie(self, interaction, title):
        embed = discord.Embed(title=title, color=0xFF7600)
        view = KategoriaView(self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def pokaz_zestawy(self, interaction):
        embed = discord.Embed(title="📦 Kalkulator Zestawów", color=0xFF7600)
        for zestaw, cena in CENY["zestawy"].items():
            embed.add_field(name=zestaw, value=f"**{cena} $**", inline=True)
        view = ZestawyView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class KategoriaView(ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent = parent_view
    
    @ui.button(label="🍰 Dania", style=ButtonStyle.green, emoji="🍰")
    async def dania(self, interaction: discord.Interaction, button: ui.Button):
        await self.pokaz_produkty(interaction, "dania")
    
    @ui.button(label="☕ Napoje", style=ButtonStyle.blurple, emoji="☕")
    async def napoje(self, interaction: discord.Interaction, button: ui.Button):
        await self.pokaz_produkty(interaction, "napoje")
    
    async def pokaz_produkty(self, interaction, kategoria):
        embed = discord.Embed(title=f"Wybierz produkt z {kategoria}", color=0xFF7600)
        view = ProduktyView(kategoria, self.parent)
        await interaction.response.edit_message(embed=embed, view=view)

class ProduktyView(ui.View):
    def __init__(self, kategoria, parent_view):
        super().__init__(timeout=60)
        self.kategoria = kategoria
        self.parent = parent_view
        for produkt in CENY[kategoria].keys():
            self.add_item(ProduktButton(produkt, kategoria, parent_view))

class ProduktButton(ui.Button):
    def __init__(self, produkt, kategoria, parent):
        super().__init__(label=produkt, style=ButtonStyle.secondary)
        self.produkt = produkt
        self.kategoria = kategoria
        self.parent = parent
    
    async def callback(self, interaction: discord.Interaction):
        cena = CENY[self.kategoria][self.produkt]
        view = IloscView(self.produkt, cena, self.parent)
        embed = discord.Embed(title="Wybierz ilość", color=0xFF7600)
        embed.add_field(name="Produkt", value=self.produkt, inline=True)
        embed.add_field(name="Cena za sztukę", value=f"{cena} $", inline=True)
        await interaction.response.edit_message(embed=embed, view=view)

class IloscView(ui.View):
    def __init__(self, produkt, cena, parent):
        super().__init__(timeout=60)
        self.produkt = produkt
        self.cena = cena
        self.parent = parent
        self.ilosc = 1
    
    @ui.button(label="➖", style=ButtonStyle.red)
    async def decrease(self, interaction: discord.Interaction, button: ui.Button):
        if self.ilosc > 1:
            self.ilosc -= 1
            await self.update_message(interaction)
    
    @ui.button(label="Ilość: 1", style=ButtonStyle.gray)
    async def display_count(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
    
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
        embed.set_footer(text=f"📦 × Cena za {self.ilosc} produkt/ów to {total} $")
        view = ui.View()
        view.add_item(ZamknijButton())
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def update_message(self, interaction: discord.Interaction):
        for child in self.children:
            if child.label and "Ilość:" in child.label:
                child.label = f"Ilość: {self.ilosc}"
                break
        total = self.cena * self.ilosc
        embed = discord.Embed(title="Wybierz ilość", color=0xFF7600)
        embed.add_field(name="Produkt", value=self.produkt, inline=True)
        embed.add_field(name="Cena za sztukę", value=f"{self.cena} $", inline=True)
        embed.add_field(name="Razem", value=f"**{total} $**", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

class ZestawyView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        for zestaw in CENY["zestawy"].keys():
            self.add_item(ZestawButton(zestaw))

class ZestawButton(ui.Button):
    def __init__(self, zestaw):
        super().__init__(label=zestaw, style=ButtonStyle.primary)
        self.zestaw = zestaw
    
    async def callback(self, interaction: discord.Interaction):
        cena = CENY["zestawy"][self.zestaw]
        embed = discord.Embed(title="📦 Kalkulator Zestawów", color=0xFF7600)
        embed.add_field(name="Wybrany zestaw", value=self.zestaw, inline=True)
        embed.add_field(name="Cena", value=f"**{cena} $**", inline=True)
        embed.set_footer(text=f"📦 × Cena za 1 produkt/ów to {cena} $")
        view = ui.View()
        view.add_item(ZamknijButton())
        await interaction.response.edit_message(embed=embed, view=view)

class ZamknijButton(ui.Button):
    def __init__(self):
        super().__init__(label="❌ Zamknij", style=ButtonStyle.danger)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.message.delete()

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} jest online!')
    try:
        synced = await bot.tree.sync()
        print(f"✅ Zsynchroniczowano {len(synced)} komend")
    except Exception as e:
        print(f"❌ Błąd synchronizacji: {e}")

@bot.tree.command(name="cennik", description="Pokazuje menu kawiarni")
async def cennik(interaction: discord.Interaction):
    # Stylizacja embeda na wzór Beam Machine
    embed = discord.Embed(title="**Beam Machine - Menu**", color=0xFF7600)
    
    # Kategoria DANIA
    dania_desc = ""
    for produkt, cena in CENY["dania"].items():
        dania_desc += f"{produkt}\n**{cena} $**\n\n"
    embed.add_field(name="🍰 Dania", value=dania_desc, inline=True)
    
    # Kategoria NAPOJE
    napoje_desc = ""
    for produkt, cena in CENY["napoje"].items():
        napoje_desc += f"{produkt}\n**{cena} $**\n\n"
    embed.add_field(name="☕ Napoje", value=napoje_desc, inline=True)
    
    # Stopka
    embed.set_footer(text="Smacznie, drogo i z klasą!")
    
    view = GlownyView()
    await interaction.response.send_message(embed=embed, view=view)

# Uruchomienie bota
bot.run(DISCORD_TOKEN)
