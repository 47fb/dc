# --- KOMENDA MINUS (Z DEGRADACJĄ I RESETEM) ---
@bot.tree.command(name="minus", description="Nadaje minusa i zarządza degradacjami")
@app_commands.describe(
    uzytkownik="Oznacz pracownika", 
    powod="Podaj powód kary", 
    rodzaj="Wybierz poziom minusa"
)
@app_commands.choices(rodzaj=[
    app_commands.Choice(name="1 Minus", value=1),
    app_commands.Choice(name="2 Minus", value=2),
    app_commands.Choice(name="3 Minus", value=3),
])
async def minus(interaction: discord.Interaction, uzytkownik: discord.Member, powod: str, rodzaj: app_commands.Choice[int]):
    # Sprawdzenie uprawnień
    req_role = interaction.guild.get_role(REQUIRED_ROLE_ID)
    if not req_role or not any(r.position >= req_role.position for r in interaction.user.roles):
        return await interaction.response.send_message("❌ Nie masz uprawnień do używania tej komendy!", ephemeral=True)

    try:
        # Pobieramy rolę wybranego minusa
        rola_minusa = interaction.guild.get_role(ROLE_MINUSY[rodzaj.value])
        
        # Usuwamy wszystkie obecne minusy przed nadaniem nowego (żeby się nie dublowały)
        for r_id in ROLE_MINUSY.values():
            r_obj = interaction.guild.get_role(r_id)
            if r_obj in uzytkownik.roles:
                await uzytkownik.remove_roles(r_obj)
        
        # Nadajemy nowy poziom minusa
        await uzytkownik.add_roles(rola_minusa)

        kara_info = ""
        # LOGIKA 3 MINUSA (Degradacja + Reset wszystkich minusów)
        if rodzaj.value == 3:
            degradowany = False
            # Sprawdzamy rangi od najwyższej w dół
            for akt_id, nizej_id in DEGRADACJA_MAP.items():
                if akt_id in [r.id for r in uzytkownik.roles]:
                    await uzytkownik.remove_roles(interaction.guild.get_role(akt_id))
                    await uzytkownik.add_roles(interaction.guild.get_role(nizej_id))
                    kara_info = f"\n\n📉 **DEGRADACJA!** Pracownik spadł na rangę: <@&{nizej_id}>"
                    degradowany = True
                    break
            
            # Jeśli jest Praktykantem i dostał 3 minusa - traci rangę całkowicie
            if not degradowany and PRAKTYKANT_ID in [r.id for r in uzytkownik.roles]:
                await uzytkownik.remove_roles(interaction.guild.get_role(PRAKTYKANT_ID))
                kara_info = f"\n\n🚫 **DYSCYPLINARKA!** Pracownik stracił rangę Praktykanta."

            # RESET: Usuwamy wszystkie minusy po degradacji/wyrzuceniu
            for r_id in ROLE_MINUSY.values():
                r_obj = interaction.guild.get_role(r_id)
                await uzytkownik.remove_roles(r_obj)

        # Tworzenie Embedu
        embed = discord.Embed(
            title="⚠️ Przyznano Minusa!", 
            color=0xE74C3C, 
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="👤 Kto:", value=uzytkownik.mention, inline=True)
        embed.add_field(name="🔻 Poziom:", value=f"**{rodzaj.value}/3**", inline=True)
        embed.add_field(name="📝 Powód:", value=f"*{powod}*{kara_info}", inline=False)
        
        # Dodanie awatara użytkownika
        if uzytkownik.display_avatar:
            embed.set_thumbnail(url=uzytkownik.display_avatar.url)
            
        embed.set_footer(
            text=f"Nadane przez: {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None
        )

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"❌ Wystąpił błąd: {e}", ephemeral=True)
