import discord
from discord.ext import commands
from discord import app_commands, ui, ButtonStyle
import os

# --- KONFIGURACJA ---
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Menu kawiarni Bean Machine
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

# --- MODAL DO WPISANIA ILOŚCI ---
class IloscModal(ui.Modal, title="Ile sprzedajesz?"):
    def __init__(self, nazwa, cena):
        super().__init__()
        self.nazwa = nazwa
        self.cena = cena
        self.ilosc = ui.TextInput(
            label="Podaj ilość", 
            placeholder="Wpisz liczbę...", 
            default="1", 
            min_length=1, 
            max_length=3
        )
        self.add_item(self.ilosc)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            ilosc = int(self.ilosc.value)
            if ilosc < 1: raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ Wpisz poprawną liczbę!", ephemeral=True)
            return

        total = self.cena * ilosc
        embed = discord.Embed(title="🛒 Wynik kalkulacji", color=0xFF7600)
        embed.add_field(name="Pozycja", value=f"**{self.nazwa}**", inline=True)
        embed.add_field(name="Ilość", value=f"**{ilosc}**", inline=True)
        embed.add_field(name="Łączna cena", value=f"# **{total} $**", inline=False)
        embed.set_footer(text="Bean Machine - Najlepsza kawa w mieście!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- LISTA ROZWIJANA (IDENTYCZNA JAK NA SCREENIE) ---
class KalkulatorSelect(ui.Select):
    def __init__(self):
        options = []
        # Dodawanie produktów
        for kategoria, produkty in MENU.items():
            for nazwa, cena in produkty.items():
                emoji = nazwa.split()[0]
                czysta_nazwa = " ".join(nazwa.split()[1:])
                options.append(discord.SelectOption(label=f"• {czysta_nazwa}", value=f"{nazwa}|{cena}", emoji=emoji))
        
        # Dodawanie zestawów
        for nazwa, cena in ZESTAWY.items():
            options.append(discord.SelectOption(label=f"• {nazwa}", value=f"{nazwa}|{cena}", emoji="📦"))

        super().__init__(placeholder="Dokonaj wyboru", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        nazwa, cena_str = self.values[0].split('|')
        await interaction.response.send_modal(IloscModal(nazwa, int(cena_str)))

class KalkulatorView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(KalkulatorSelect())

# --- GŁÓWNY WIDOK Z PRZYCISKIEM ---
class MainView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🛒 Otwórz Kalkulator", style=ButtonStyle.success, custom_id="open_calc")
    async def open_calc(self, interaction: discord.Interaction):
        # Wygląd wiadomości identyczny jak na Twoim screenie
        await interaction.response.send_message(
            "📦 **• Wybierz produkt**", 
            view=KalkulatorView(), 
            ephemeral=True
        )

# --- KOMENDA /MENU ---
@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} gotowy!')
    await bot.tree.sync()

@bot.tree.command(name="menu", description="Wyświetla menu Bean Machine")
async def menu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="**Bean Machine – Menu**",
        color=0xFF7600,
        description="Menu najlepszej kawiarni w mieście!!"
    )

    # Formatowanie: Duże nagłówki (#) i pogrubione produkty (**)
    napoje = "\n".join([f"• **{p}** × {c} $" for p, c in MENU["napoje"].items()])
    jedzenie = "\n".join([f"• **{p}** × {c} $" for p, c in MENU["jedzenie"].items()])
    zestawy = "\n".join([f"• **{p}** × {c} $" for p, c in ZESTAWY.items()])

    embed.add_field(name="# ☕ Napoje", value=napoje, inline=False)
    embed.add_field(name="# 🍰 Jedzenie", value=jedzenie, inline=False)
    embed.add_field(name="# 📦 Zestawy", value=zestawy, inline=False)
    
    embed.set_footer(text="Bean Machine - Smak, który uzależnia!")

    try:
        file = discord.File("b1.png", filename="b1.png")
        embed.set_image(url="attachment://b1.png")
        await interaction.response.send_message(file=file, embed=embed, view=MainView())
    except FileNotFoundError:
        await interaction.response.send_message(embed=embed, view=MainView())

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
