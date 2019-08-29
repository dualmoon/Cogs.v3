import re
from io import BytesIO
from os import listdir
from typing import List
from random import shuffle
import discord
from redbot.core import commands, Config, checks
from redbot.core.data_manager import bundled_data_path
from redbot.core.bot import Red
from PIL import Image, ImageOps, ImageDraw, ImageFont
from .textwrapper import TextWrapper


class WeeedBot(commands.Cog):

    """It's weeedbot."""

    def __init__(self, red: Red):
        self.bot = red
        # In case anyone's wondering, this is "luna" in binary
        # but with a 9 at the front
        config_id = 901101100011101010110111001100001
        # Grab our config object
        self.config = Config.get_conf(self, identifier=config_id)
        self.deafult_config_guild = {
            "max_messages": 10,
            "background_image": 'beach-paradise-beach-desktop.jpg',
            "comic_text": None,
            "font": 'ComicBD.ttf'
            }
        self.config.register_guild(**self.deafult_config_guild)
        # Panels are 450px wide, so we make the text 300 wide to keep the
        # noticable offset of the left and right text blocks
        # This is our global text block width
        self.text_width = 300

    # self.datapath is a property here since the data path doesn't exist
    # yet when we create the cog's instance
    # For anyone unfamiliar, the @property decorator makes the subsequent
    # function a getter for a property of the same name as the function
    @property
    def datapath(self):
        """Returns the path to the bundled data folder."""
        return str(bundled_data_path(self))

    def _get_font(self, font):
        font_path = f"{self.datapath}/font/{font}"
        return ImageFont.truetype(font_path, size=15)

    # This decorator defines the cog's command group, basically our own
    # namespace where we can make all our commands common words without
    # worrying about command name collisions
    @commands.group()
    async def weeed(self, ctx: commands.Context):
        """This is the primary cog group. Try ``"""
        pass

    @weeed.group(name='set')
    @checks.mod()
    async def wset(self, ctx: commands.Context):
        """Configure various WeeedCog settings."""
        pass

    @wset.command()
    async def background_image(self, ctx, filename: str = None):
        """Changes the background to use for the comics, or "list"."""
        if not filename:
            current_bg = await self.config.guild(ctx.guild).background_image()
            await ctx.send(f"background_image is currently `{current_bg}` for this guild.")
        elif filename == "list":
            files = listdir(f"{self.datapath}/background")
            await ctx.send(f"backgrounds: {files}")
        else:
            files = listdir(f"{self.datapath}/background")
            if filename in files:
                await self.config.guild(ctx.guild).background_image.set(filename)
                new_bg = await self.config.guild(ctx.guild).background_image()
                await ctx.send(f"New background_image for this guild is {new_bg}")
            else:
                await ctx.send(f"Couldn't find a background file called '{filename}'")

    @wset.command()
    async def font(self, ctx, filename: str = None):
        """Changes the font to use for the comics, or "list"."""
        if not filename:
            current_font = await self.config.guild(ctx.guild).font()
            await ctx.send(f"font is currently `{current_font}` for this guild.")
        elif filename == "list":
            files = listdir(f"{self.datapath}/font")
            await ctx.send(f"fonts: {files}")
        else:
            files = listdir(f"{self.datapath}/font")
            if filename in files:
                await self.config.guild(ctx.guild).font.set(filename)
                new_font = await self.config.guild(ctx.guild).font()
                await ctx.send(f"New font for this guild is {new_font}")
            else:
                await ctx.send(f"Couldn't find a font file called '{filename}'")

    @wset.command()
    async def max_messages(self, ctx: commands.Context, max: int = None):
        """ The max number of messages you can put in a comic """
        if not max:
            current_max = await self.config.guild(ctx.guild).max_messages()
            await ctx.send(f"max_messages is currently {current_max} for this guild.")
        elif max < 1:
            await ctx.send("That number is too small.")
        elif max > 80:
            await ctx.send("Setting this higher than 80 will result in files too big to post.")
        elif max not in range(1, 81):
            await ctx.send("Invalid value for max_messages")
        else:
            await self.config.guild(ctx.guild).max_messages.set(max)
            new_max = await self.config.guild(ctx.guild).max_messages()
            await ctx.send(f"max_messages for this guild is now set to {new_max}")

    @wset.command()
    async def comic_text(self, ctx: commands.Context, *, text: str = None):
        """ Optional text element to accompany the post e.g. "Whoa, here's a comic:", or 'none' """
        if not text:
            current_text = await self.config.guild(ctx.guild).comic_text()
            await ctx.send(f"comic_text is currently {current_text} for this guild.")
        elif text.lower() == "none":
            await self.config.guild(ctx.guild).comic_text.set(None)
            await ctx.send("comic_text has been removed for this guild.")
        else:
            await self.config.guild(ctx.guild).comic_text.set(text)
            new_text = await self.config.guild(ctx.guild).comic_text()
            await ctx.send(f"comic_text is now set to {new_text}")

    async def _get_rendered_text(self, text, font, width):
        wrapper = TextWrapper(text, font, width)
        return wrapper.wrapped_text()

    @staticmethod
    def _sanitize_usernames(guild, text):
        regex = re.compile(r"(?:<@!?)([0-9]+)(?:>)")
        result = re.sub(
                    regex,
                    lambda m: guild.get_member(int(m.group(1))).display_name,
                    text)
        return result

    @staticmethod
    def _sanitize_channelnames(guild, text):
        regex = re.compile(r"(?:<#)([0-9]+)(?:>)")
        result = re.sub(
                    regex,
                    lambda m: f"#{guild.get_channel(int(m.group(1))).name}",
                    text
                    )
        return result

    @staticmethod
    def _sanitize_emojinames(text):
        regex = re.compile(r"(?:<a?)(\:[0-9a-zA-Z]+\:)(?:[0-9]+>)")
        result = re.sub(
                    regex,
                    lambda m: m.group(1),
                    text
                    )
        return result

    # This takes a list of discord messages and converts them to a dict that we
    # can easily use to generate the comic.
    async def _messages_to_comicdata(self, messages: List[discord.Message]):
        """Convert list of discord messages to comic data."""
        comic = []
        panel = []
        # Using enumerate so we can carry an index for lookahead, lookbehind
        for index, action in enumerate(messages):
            # The very first message always goes in the same spot
            # TODO: sanitize these messages as we go, replacing user snowflakes
            # with user names, emoji snowflakes with :emojiname:, etc. etc.
            prev_text = self._sanitize_usernames(action.guild, messages[index-1].content)
            prev_text = self._sanitize_channelnames(action.guild, prev_text)
            prev_text = self._sanitize_emojinames(prev_text)
            this_text = self._sanitize_usernames(action.guild, action.content)
            this_text = self._sanitize_channelnames(action.guild, this_text)
            this_text = self._sanitize_emojinames(this_text)
            # TODO: build a frankenfont that has all codepoints that Comic Sans
            # doesn't cover replaced with Noto Emoji font glyphs for better
            # rendering of unicode emojis
            if len(panel) == 1:  # We're looking at the "right" side
                guild_font = await self.config.guild(action.guild).font()
                font = self._get_font(guild_font)
                prev_text_rendered = await self._get_rendered_text(prev_text, font, self.text_width)
                # Blank panel if last author and this one are the same
                # Blank panel if last message height is over 3 lines tall
                if action.author == messages[index-1].author or len(prev_text_rendered.split('\n')) > 3:
                    # So in this case we want to only have one action
                    # in the panel instead of two because of either
                    # a monologue or a big text block
                    # We probably want to change 'char' to the user's ID
                    # when we switch to not pulling char image names
                    panel.append({'char': None, 'text': None})
                    comic.append(panel)
                    panel = []
                    panel.append({
                        'text': this_text,
                        'id': action.author.id
                        })
                    continue
            panel.append({
                'text': this_text,
                'id': action.author.id
                })
            if len(panel) == 2:
                comic.append(panel)
                panel = []
        # Now we check for any stragglers and append them.
        if len(panel) > 0:
            comic.append(panel)
        # Our data is now ready. Time to build an image!
        print(f"[WEEEDCOG] Comic data generated! Data follows:\n{comic}")
        return comic

    # Defines our main 'comic' command
    # Takes one int for comic length and another optional int to let us pick
    # what message should be the last
    # TODO: make the count var optional, and if it's not defined the comic
    # should be the last N messages where N is the number of messages in the
    # past 120 seconds or until there's a gap greater than 20 seconds between
    # any message and the one prior
    @weeed.command()
    async def comic(self, ctx: commands.Context, count: int, message_id: int = None):
        """
            Generates a comic using the last specified number of messages. Can optionally send a message ID as well
            and it will grab that message and the specified number prior to it. If "comic_text" option is set,
            the comic will be accompanied by that configured text.
        """
        server_cfg = self.config.guild(ctx.guild)
        max_messages = await server_cfg.max_messages()
        background_image = await server_cfg.background_image()
        comic_text = await server_cfg.comic_text()

        if count > max_messages:
            await ctx.send("Whoa there, shitlord! You expect me to parse _All That Shit_ by _you_?")
            return
        # Yeah yeah ok so -1 is technically an integer... Let's handle that
        elif count < 1:
            await ctx.send("Nice try there ;-]")
            return
        # Now let's just catch any other input that's invalid.
        elif count not in range(1, max_messages+1):
            await ctx.send("What to heck are u doin??? The number needs to be between 1 and 10.")
            return
        # TODO: also make the messages either configurable, i18n, or both
        # So if we're passed a message ID as a second argument...
        if message_id:
            # ...see if we can pull a valid message object...
            try:
                anchor_msg = await ctx.fetch_message(message_id)
            # ...and if we can't, throw an error
            # TODO: expand this to actually catch the exceptions this can throw
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as error:
                await ctx.send(f"Unable to find a message with that ID...{error}")
                return
            # So the except returns, which means this happens only if we
            # were successful. We subtract 1 from the count so that we can
            # later make up for the offset inherent to ctx.history()
            finally:
                count = count-1
        # By default if we're not given a message, we use the message that
        # called the command as our "anchor"
        else:
            anchor_msg = ctx.message
        # Get the specified number of messages using ctx.history()
        messages = await ctx.history(before=anchor_msg,
                                     limit=count,
                                     oldest_first=False).flatten()
        messages.reverse()
        # Again, if given a message ID, we need to get the history but also
        # add the message with the ID that was passed and, since we're using
        # reverse=True we append (otherwise we'd prepend)
        if message_id:
            messages.append(anchor_msg)

        comic = await self._messages_to_comicdata(messages)
        # These have been the defaults since the dawn of time. Do we ever want
        # to make them configurable? That would require some other changes too.
        panel_width = 450
        panel_height = 300
        # Create a canvas for us to put our stuff in
        # TODO: look into the bug where over 100 messages breaks this somehow?
        # No issue filed for the above todo yet
        canvas_height = panel_height*len(comic)
        canvas = Image.new("RGBA", (panel_width, canvas_height))
        # canvas_bytes is the in-memory image since we can't use the Image
        # object directly as our attached file.
        canvas_bytes = BytesIO()
        # Again, since the dawn of time this is the only background the comic
        # has ever used, but prescriptivism is shit so...
        # TODO: make this configurable per-server. One option is a specific
        # background with the default being the standard one, and the other
        # option should be to pick a random background and use it for every
        # panel, and maybe even one last option of a random background per panel
        background = Image.open(f"{self.datapath}/background/{background_image}").convert("RGBA")
        # Create our Draw object
        draw = ImageDraw.Draw(canvas)
        # This is the top and sides margin size for text and characters
        # TODO: make this configurable per-server and take into account how
        # changing this changes text and char rendering
        text_buffer = 10
        # Here's where we load our characters. The stuff way above where we
        # pick a bunch of chars for each unique author should probably just be
        # a simple list of unique IDs and we'll do the rest here instead.
        # TODO: refactor per previous comment
        # Now get a list of authors of messages that will be in the comic
        # Specifically we are getting _unique_ authors, thus the list(set())
        author_ids = list(set([m.author.id for m in messages]))
        char_img_map = {}
        all_chars = listdir(f"{self.datapath}/char")
        shuffle(all_chars)
        for inc, id in enumerate(author_ids):
            char_img_map[id] = Image.open(f"{self.datapath}/char/{all_chars[inc]}")
        # I think instead of iterating against a range like this, we should
        # probably iterate against the comic object directly?
        # This is where things get messy tbh, lots of possible refactoring and
        # optimizing inside this for-loop
        for panel_count in range(0, len(comic)):
            # Paste in our background first
            canvas.paste(background, (0, (panel_height*panel_count)))
            # Calculate the bottom edge for various reasons
            bottom_edge = panel_height*(panel_count+1)
            # Next we need to draw text...
            # We start by wrapping the text using our helper class
            # TextWrapper, just to be clear, calculates the length of rendered
            # text and wraps any words that would be wider than a given width
            guild_font = await self.config.guild(ctx.guild).font()
            font = self._get_font(guild_font)
            left_text = await self._get_rendered_text(
                                    comic[panel_count][0]['text'],
                                    font,
                                    self.text_width
                                    )
            # Now we find out how tall the left side text is so we can scale
            # the chars properly beneath it.
            (_, left_text_height) = draw.multiline_textsize(left_text, font=font)
            # We also need to calculate the right side text height because we
            # have the two chars scaled to be as tall as the space left beneath
            # both of the rendered text blocks
            # Here we check if there's going to be right side text at all
            if len(comic[panel_count]) == 1 or not comic[panel_count][1]['text']:
                right_text_height = 0
            else:
                right_text = await self._get_rendered_text(
                    comic[panel_count][1]['text'],
                    font,
                    self.text_width
                    )
                # left side buffer is rendered text width + text_buffer and find
                # the difference between that and panel_width
                (right_text_width, right_text_height) = draw.multiline_textsize(right_text, font=font)
            # Left side character time
            # We want to thumbnail the character to fit between the bottom of
            # the left text and the bottom of the panel, taking into account
            # buffers at the top and bottom
            left_bottom_edge = left_text_height+(text_buffer*2)
            char_height = panel_height-left_bottom_edge-(text_buffer*2)-right_text_height
            if char_height < 150:
                char_height = 150
            char_width = 225-(text_buffer*2)
            # Here we make a copy of the image so we can scale per-panel
            # without worrying about destroying the char loaded into memory
            thumb = char_img_map[comic[panel_count][0]['id']].copy()
            thumb.thumbnail((char_width, char_height))
            canvas.paste(thumb, (text_buffer, (panel_height*(panel_count+1))-thumb.height), mask=thumb)
            # Now we draw the left side text, easy
            # left side buffer
            left_buffer = text_buffer
            # top side buffer based on which panel we're in
            top_buffer = text_buffer+(panel_height*panel_count)
            # TODO: make this font pull from config instead of defaulting to
            # our font object. Maybe make the text color configurable too?
            draw.multiline_text((left_buffer, top_buffer), left_text, font=font, fill="white")

            # Non-DRY code here, checking again if there's a right side of
            # this panel
            if len(comic[panel_count]) == 1 or not comic[panel_count][1]['text']:
                continue

            # And then we need to draw the right size text, giving it a top
            # buffer equal to the height of the left text + 10 + text_buffer
            left_buffer = panel_width - (right_text_width+text_buffer)
            # top side buffer should be the same, but add previous text height and text_buffer and an extra 20
            top_buffer = top_buffer+left_text_height+text_buffer
            # Time for right side char
            thumb = char_img_map[comic[panel_count][1]['id']].copy()
            thumb.thumbnail((char_width, char_height))
            thumb = ImageOps.mirror(thumb)
            left_char_buffer = panel_width-(text_buffer+thumb.width)
            canvas.paste(thumb, (left_char_buffer, (panel_height*(panel_count+1))-thumb.height), mask=thumb)
            draw.multiline_text((left_buffer, top_buffer), right_text, font=font, fill="white")
            # Now we need to draw a line to separate panels
            # TODO: don't draw this line on the last panel
            draw.line([(0, bottom_edge-1), (panel_width, bottom_edge-1)], width=4, fill="black")
        # Write the Image object to our BytesIO file-in-memory object
        canvas.save(canvas_bytes, format="PNG")
        # Send the file away~~
        # TODO: make the filename a unique hash or something so that we can
        # also store comic data under the same name with a different extension
        # This would let us debug any weird stuff rendered into comics.
        canvas_bytes.seek(0)
        await ctx.send(
            content=comic_text, file=discord.File(
                canvas_bytes,
                filename="comic.png"
                )
            )
