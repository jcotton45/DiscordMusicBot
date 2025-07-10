# music.py
import discord
from discord.ext import commands
from discord import app_commands
from yt_dlp import YoutubeDL
from imageio_ffmpeg import get_ffmpeg_exe


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        ffmpeg_path = get_ffmpeg_exe()
        self.is_playing = {}
        self.is_paused = {}

        self.music_queue = {}
        self.yt_dl_options = {
            'format': 'bestaudio[abr>160]bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '192',
            }],
            'noplaylist': True
        }
        self.ffmpeg_options = {
            'executable': ffmpeg_path,
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -ar 48000 -ac 2 -b:a 256k -bufsize 8192k'
        }

        self.vc = {}

    async def play_first(self, ctx, song):
        guild_id = ctx.guild.id
        m_url = song['source']
        self.is_playing[guild_id] = True
        if self.vc[guild_id] is None or not self.vc[guild_id].is_connected():
            print("Bot is not connected, trying to connect now...")
            self.vc[guild_id] = await ctx.author.voice.channel.connect()
            self.vc[guild_id].play(discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options),
                                   after=lambda e: self.play_next(guild_id))
            if self.vc[guild_id] is None:
                await ctx.send("Could not connect to the voice channel")
                print("Failed to connect to voice channel")
                return

        else:
            print("Bot is already connected, moving to the correct channel")
            await self.vc[guild_id].move_to(ctx.author.voice.channel)


            print("Playing song now...")
            self.vc[guild_id].play(discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options),
                                   after=lambda e: self.play_next(guild_id))

    async def play_music(self, ctx):
        guild_id = ctx.guild.id

        if len(self.music_queue[guild_id]) > 0:
            self.is_playing[guild_id] = True
            m_url = self.music_queue[guild_id][0][0]['source']

            print(f"Next song URL: {m_url}")

            if self.vc[guild_id] is None or not self.vc[guild_id].is_connected():
                print("Bot is not connected, trying to connect now...")
                self.vc[guild_id] = await ctx.author.voice.channel.connect()
                self.vc[guild_id].play(discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options), after=lambda e: self.play_next(guild_id))
                if self.vc[guild_id] is None:
                    await ctx.send("Could not connect to the voice channel")
                    print("Failed to connect to voice channel")
                    return

            else:
                print("Bot is already connected, moving to the correct channel")
                await self.vc[guild_id].move_to(ctx.author.voice.channel)

                self.music_queue[guild_id].pop(0)

                print("Playing song now...")
                self.vc[guild_id].play(discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options), after=lambda e: self.play_next(guild_id))

        else:
            print("No more songs in queue.")
            self.is_playing[guild_id] = False

    def search_yt(self, item):
        with YoutubeDL(self.yt_dl_options) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
                print(f"Video Title: {info['title']}")

                audio_format = next((fmt for fmt in info['formats'] if fmt.get('acodec') and fmt['acodec'] != 'none'), None)
                if audio_format:
                    print(f'Selected audio format: {audio_format}')
                    return {'source': audio_format['url'], 'title': info['title']}
                else:
                    print("No suitable audio format found.")
                    return False
            except Exception as e:
                print(f"Error searching for video: {e}")
                return False

    def play_next(self, guild_id):
        if len(self.music_queue[guild_id]) > 0:
            print(f'music queue length: {len(self.music_queue[guild_id])}'
                  f' setting is_playing for guild_id: {guild_id} to true')
            self.is_playing[guild_id] = True

            m_url = self.music_queue[guild_id][0][0]['source']

            self.music_queue[guild_id].pop(0)
            print(f"Playing URL: {m_url}")
            self.vc[guild_id].play(discord.FFmpegPCMAudio(m_url, **self.ffmpeg_options), after=lambda e: self.play_next(guild_id) if not e else print(f"Error playing audio: {e}"))
        else:
            print(f'music queue empty setting is_playing for guild_id: {guild_id} to false ')
            self.is_playing[guild_id] = False

    @commands.command(name="play", aliases=["p", "playing"], help="Play the selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)
        guild_id = ctx.guild.id
        voice_channel = ctx.author.voice.channel

        if guild_id not in self.is_playing:
            print("Adding guild_id to is playing dict")
            self.is_playing[guild_id] = False
        if guild_id not in self.is_paused:
            print("Adding guild_id to is paused dict")
            self.is_paused[guild_id] = False
        if guild_id not in self.music_queue:
            print("Adding guild_id to music queue dict")
            self.music_queue[guild_id] = []
        if guild_id not in self.vc:
            print("Adding guild_id to voice chat dict")
            self.vc[guild_id] = None

        if voice_channel is None:
            await ctx.send("Connet to a voice channel")

        elif self.is_paused[guild_id]:
            print("resuming paused music in def_play")
            self.vc[guild_id].resume()
        else:
            print("searching song in def_play")
            song = self.search_yt(query)
            if not song:
                await ctx.send("Could not download the song. Incorrect format, try a different keyword")
            else:
                if not self.is_playing[guild_id] and len(self.music_queue[guild_id]) == 0:
                    await self.play_first(ctx, song)
                else:
                    await ctx.send("Song added to the queue")
                    self.music_queue[guild_id].append([song, voice_channel])
                    if self.is_playing[guild_id] == False:
                        print(f'play_music call with {ctx} from def_play')
                        await self.play_music(ctx)

    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        guild_id = ctx.guild.id
        if self.is_playing[guild_id]:
            print(f'pausing music for {guild_id}')
            self.is_playing[guild_id] = False
            self.is_paused[guild_id] = True
            self.vc[guild_id].pause()
        elif self.is_paused[guild_id]:
            print(f'music was paused ... resuming music for {guild_id}')
            self.vc[guild_id].resume()

    @commands.command(name="resume", aliases=["r"], help="Resumes playing the current song")
    async def resume(self, ctx, *args):
        guild_id = ctx.guild.id
        if self.is_paused[guild_id]:
            print(f'resuming music for {guild_id}')
            self.is_playing[guild_id] = True
            self.is_paused[guild_id] = False
            self.vc[guild_id].resume()

    @commands.command(name="skip", aliases=["s"], help="skips the currently played song")
    async def skip(self, ctx, *args):
        guild_id = ctx.guild.id
        if self.vc[guild_id] != None and self.vc[guild_id]:
            print('VC found skipping song... ')
            print('vc_guild_id.stop()')
            self.vc[guild_id].stop()
            print('call to play_music from def_skip')
            await self.play_music(ctx) #bug clears queue
            #await self.play_next(guild_id)

    @commands.command(name="queue", aliases=["q"], help="displays all the songs currently in the queue")
    async def queue(self, ctx):
        guild_id = ctx.guild.id
        retval = ""
        for i in range(0, len(self.music_queue[guild_id])):
            if i > 4: break
            retval += self.music_queue[guild_id][i][0]['title'] + '\n'

        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in the queue.")

    @commands.command(name="clear", aliases=["c", "bin"], help="stops the current song and clears the queue")
    async def clear(self, ctx, *args):
        guild_id = ctx.guild.id
        if self.vc[guild_id] is not None and self.is_playing[guild_id]:
            self.vc[guild_id].stop()
        self.music_queue[guild_id] = []
        await ctx.send("Music queue cleared")

#    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="kick the bot from the voice channel")
#    async def leave(self, ctx):
#        self.is_playing = False
#        self.is_paused = False
#        await self.vc.disconnect()
