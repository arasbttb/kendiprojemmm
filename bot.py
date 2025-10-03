import discord
import sqlite3
import datetime
from config import TOKEN  # config.py içinde TOKEN = '...' şeklinde tanımlı olmalı

DB_NAME = 'sarkilar.db'

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Client(intents=intents)

def search_db(keyword, field='title'):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = f"SELECT title, channel, view_count, channel_url FROM data WHERE LOWER({field}) LIKE LOWER(?) LIMIT 10"
    c.execute(query, ('%' + keyword + '%',))
    results = c.fetchall()
    conn.close()
    return results

@bot.event
async def on_ready():
    print(f'{bot.user} olarak giriş yapıldı.')

@bot.event
async def on_user_update(before, after):
    if before.name != after.name:
        for guild in bot.guilds:
            for channel in guild.text_channels:
                try:
                    async for msg in channel.history(limit=100):
                        if msg.author == after:
                            await channel.send(f'🔔 Kullanıcı adı değişti: `{before.name}` → `{after.name}`')
                            return
                except Exception:
                    continue

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # !ban komutu
    if message.content.startswith('!ban'):
        if message.author.guild_permissions.administrator:
            await message.channel.send(f"{message.author.mention}, bot bu sunucudan ayrılıyor.")
            await message.guild.leave()
            print(f'Bot {message.guild.name} sunucusundan atıldı.')
        else:
            await message.channel.send(f"{message.author.mention}, bu komutu kullanmak için yönetici izniniz olmalı.")
        return

    # !sorgu komutu
    if message.content.startswith('!sorgu'):
        if not message.author.guild_permissions.administrator:
            await message.channel.send(f"{message.author.mention}, bu komutu kullanmak için yönetici izniniz olmalı.")
            return

        parts = message.content.split()
        if len(parts) > 1:
            if message.mentions:
                kullanıcı = message.mentions[0]
            else:
                try:
                    kullanıcı = await message.guild.fetch_member(int(parts[1]))
                except Exception:
                    kullanıcı = message.author
        else:
            kullanıcı = message.author

        embed = discord.Embed(
            title=f"{kullanıcı.name} hakkında bilgi",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=kullanıcı.display_avatar.url)
        embed.add_field(name="👤 Kullanıcı Adı", value=kullanıcı.name, inline=True)
        embed.add_field(name="🆔 Kullanıcı ID", value=kullanıcı.id, inline=False)
        embed.add_field(name="📷 Profil Fotoğrafı", value=kullanıcı.display_avatar.url, inline=False)
        embed.set_footer(text="Auras tarafından oluşturuldu", icon_url=message.author.display_avatar.url)

        await message.channel.send(embed=embed)
        return

    # !ara komutu
    if message.content.startswith('!ara'):
        parts = message.content.split()
        field_map = {
            'kanal': 'channel',
            'başlık': 'title',
            'açıklama': 'description'
        }

        if len(parts) < 2:
            await message.channel.send("Kullanım: `!ara kelime` veya `!ara başlık kelime`")
            return

        field = 'title'
        keyword = " ".join(parts[1:])

        if parts[1] in field_map:
            field = field_map[parts[1]]
            if len(parts) < 3:
                await message.channel.send("Anahtar kelime eksik.")
                return
            keyword = " ".join(parts[2:])

        results = search_db(keyword, field)
        if results:
            msg = "\n\n".join([
                f"📺 **{r['title']}**\n👤 {r['channel']} | 👁️ {r['view_count']}\n🔗 Kanal: {r['channel_url']}\n🔗 "
                for r in results
            ])
        else:
            msg = "Hiçbir sonuç bulunamadı."
        await message.channel.send(msg)

bot.run(TOKEN)