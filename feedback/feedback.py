from redbot.core import commands, Config, checks
from redbot.core.bot import Red
from redbot.core.utils import menus
import discord


class Feedback(commands.Cog):
  """Allows a user to anonymously submit feedback to a mod team"""

  def __init__(self, red: Red):
    self.bot = red
    self.config = Config.get_conf(
        self, identifier=901101100011101010110111001100001)
    default_guild = {
        "enabled": False,
        "channel": None,
    }
    self.config.register_guild(**default_guild)

    self.guildChooserControls = {
        "✅": self._accept_guild,
        "⬅": menus.prev_page,
        "❌": menus.close_menu,
        "➡": menus.next_page
    }

    self.feedbackConfirmControls = {
        "✅": self._confirm_send,
        "❌": self._cancel_send,
    }

    self.warning_icon_url = "https://cdn.discordapp.com/attachments/376577301007171584/518911438379548717/notice-yellow.png"
    self.confirm_icon_url = "https://cdn.discordapp.com/attachments/376577301007171584/518910666917281813/security-green.png"
    self.choosey_icon_url = "https://cdn.discordapp.com/attachments/376577301007171584/518914001929764881/choose-blue.png"

  async def _accept_guild(
      self,
      ctx: commands.Context,
      pages: list,
      controls: dict,
      message: discord.Message,
      page: int,
      timeout: float,
      emoji: str,
  ):
    if message:
      guild_id = pages[page].footer.text
      await self._process_feedback(ctx, guild_id)
    return None

  async def _cancel_send(
      self,
      ctx: commands.Context,
      pages: list,
      controls: dict,
      message: discord.Message,
      page: int,
      timeout: float,
      emoji: str,
  ):
    if message:
      await ctx.send("Ok, your feedback has been discarded.")
    return None

  async def _confirm_send(
      self,
      ctx: commands.Context,
      pages: list,
      controls: dict,
      message: discord.Message,
      page: int,
      timeout: float,
      emoji: str,
  ):
    if message:
      #TODO: relay the message to the configured channel
      feedback_embed = discord.Embed(
          type="rich",
          colour=discord.Colour.from_rgb(r=255, g=0, b=255)
      )
      feedback_embed.set_author(
          name="New anonymous feedback!", icon_url=self.warning_icon_url)
      feedback_embed.add_field(name="Message", value=ctx.feedback)
      await ctx.target_channel.send(embed=feedback_embed)
      await ctx.send("Your anonymous feedback has been sent!")
    return None

  async def _process_feedback(self, ctx: commands.Context, guild_id: str):
    #TODO: check config to be sure the server has feedback enabled
    chosen_guild = self.bot.get_guild(int(guild_id))
    if not chosen_guild:
      await ctx.send(f"Sorry! There was a problem finding that guild...Report this to the bot owner!")
      return
    g = await self.config.guild(chosen_guild).all()
    if not g["enabled"]:
        await ctx.send(f"Sorry! {chosen_guild.name} has not enabled anonymous feedback.")
    elif not g["channel"]:
      await ctx.send(f"Sorry! {chosen_guild.name} has not configured this cog.")
    else:
      ctx.target_channel = self.bot.get_channel(g["channel"])
      #TODO: call another menu to confirm
      confirm_embed = discord.Embed(
          colour=discord.Colour.from_rgb(r=182, g=82, b=19)
      )
      confirm_embed.set_author(
          name="Confirm your feedback!", icon_url=self.confirm_icon_url)
      confirm_embed.add_field(name="Message", value=ctx.feedback)
      confirm_embed.set_footer(text=f"Server: {chosen_guild.name}")
      await menus.menu(ctx, [confirm_embed], self.feedbackConfirmControls)

  def _get_mutual_servers(self, member: discord.Member):
    """Returns a list of server objects in which the bot and member are mutuals"""
    return [g for g in self.bot.guilds if g.get_member(member.id)]

  @commands.command()
  async def feedback(self, ctx: commands.Context, *, the_feedback: str):
    #check if we're in tells or not
    if type(ctx.message.channel) is not discord.DMChannel:
      #if not in tells, delete the invocation and send a tell to the user
      #TODO: do we need to make sure the user can receive tells??
      await ctx.message.author.send(f"You need to use the <feedback> command here in DMs!")
      await ctx.message.delete()
    else:
      ctx.feedback = the_feedback
    #look for mutual servers
      mutuals = self._get_mutual_servers(ctx.message.author)
      #TODO: interactively ask which server to send to
      if len(mutuals) > 1:
        embed_pages = []
        for mutual in mutuals:
          this_embed = discord.Embed(
              colour=discord.Colour.from_rgb(r=82, g=182, b=119)
          )
          this_embed.set_author(
              name="Which server do you want to send feedback to?", icon_url=self.choosey_icon_url)
          this_embed.add_field(name="Server", value=mutual.name)
          this_embed.set_thumbnail(url=mutual.icon_url)
          this_embed.set_footer(text=mutual.id)
          embed_pages.append(this_embed)

        await menus.menu(ctx, embed_pages, self.guildChooserControls)
      elif len(mutuals) == 1:
        await self._process_feedback(ctx, mutuals[0].id)
      else:
        await ctx.send("We don't appear to share any servers!")

  @commands.group()
  @checks.mod()
  async def feedbackset(self, ctx: commands.Context):
    """Adjust Feedback settings"""

  @feedbackset.command(name="enable")
  async def fb_enable(self, ctx: commands.Context):
    """Enable Feedback cog for this server"""
    enabled = await self.config.guild(ctx.guild).enabled()
    if enabled:
      await ctx.send("Feedback cog is already enabled for this server")
    else:
      await self.config.guild(ctx.guild).enabled.set(True)
      await ctx.send("Enabled Feedback cog for this server")

  @feedbackset.command(name="channel")
  async def fb_channel(self, ctx: commands.Context, new_channel: discord.TextChannel):
    old_channel = await self.config.guild(ctx.guild).channel()
    if old_channel:
      await ctx.send(f"Updating channel from {self.bot.get_channel(old_channel).name} to {new_channel}")
    await self.config.guild(ctx.guild).channel.set(new_channel.id)
    current_channel = await self.config.guild(ctx.guild).channel()
    await ctx.send(f"Feedback will now go to {self.bot.get_channel(current_channel)}")
