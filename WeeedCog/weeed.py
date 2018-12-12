from redbot.core import commands, Config, checks
import discord
from PIL import Image, ImageOps, ImageDraw, ImageFont
from redbot.core.data_manager import bundled_data_path
from redbot.core.bot import Red
from io import BytesIO
from random import sample, choice
from os import listdir
from .textwrapper import TextWrapper


class Weeedbot(commands.Cog):
    """It's weeedbot"""

    def __init__(self, red: Red):
        self.bot = red
        # In case anyone's wondering, this is "luna" in binary
        # but with a 9 at the front
        configID = 901101100011101010110111001100001
        # Grab our config object
        self.config = Config.get_conf(self, identifier=configID)
        defaultConfigGuild = {
            "maxMessages": 10,
            "backgroundImage": 'beach-paradise-beach-desktop.jpg',
            "comicText": None
        }
        self.config.register_guild(**default_guild)
        # This is our font object that we'll end up using basically everywhere
        # TODO: make this configurable - both the typeface and the size
        self.comicSans = ImageFont.truetype(f"{self.datapath}/font/ComicBD.ttf", size=15)
        # This is our global text block width
        # Panels are 450px wide, so we make the text 300 wide to keep the
        # noticable offset of the left and right text blocks
        self.textWidth = 300

    # self.datapath is a property here since the data path doesn't exist
    # yet when we create the cog's instance
    # For anyone unfamiliar, the @property decorator makes the subsequent
    # function a getter for a property of the same name as the function
    @property
    def datapath(self):
        return str(bundled_data_path(self))

    # This decorator defines the cog's command group, basically our own
    # namespace where we can make all our commands common words without
    # worrying about command name collisions
    @commands.group()
    async def weeed(self, ctx: commands.Context):
        # I believe this is superfluous, but it's here anyway?
        # Basically, if we don't call a subcommand we do nothing.
        # Might be worth making this spit out help later
        if ctx.invoked_subcommand is None:
            pass

    # Defines our main 'comic' command
    # Takes one int for comic length and another optional int to let us pick
    # what message should be the last
    # TODO: make the count var optional, and if it's not defined the comic
    # should be the last N messages where N is the number of messages in the
    # past 120 seconds or until there's a gap greater than 20 seconds between
    # any message and the one prior
    @weeed.command()
    async def comic(self, ctx: commands.Context, count: int, messageID: int=None):
        serverConfig = self.config.guild(ctx.guild)
        # Limit the comic to 10 for now as a sane default
        # TODO: make this configurable per-server using our config object
        if count > serverConfig.maxMessages:
            await ctx.send("Whoa there, shitlord! You expect me to parse _All That Shit_ by _you_?")
            return
        # Yeah yeah ok so -1 is technically an integer... Let's handle that
        elif count < 1:
            await ctx.send("Nice try there ;-]")
            return
        # Now let's just catch any other input that's invalid.
        # TODO: expand this to take into account server-specific maximums
        # once implemented.
    elif count not in range(1, (serverConfig.maxMessages)):
            await ctx.send("What to heck are u doin??? The number needs to be between 1 and 10.")
            return
        # TODO: also make the messages either configurable, i18n, or both
        # So if we're passed a message ID as a second argument...
        if messageID:
            # ...see if we can pull a valid message object...
            try:
                anchorMessage = await ctx.get_message(messageID)
            # ...and if we can't, throw an error
            # TODO: expand this to actually catch the exceptions this can throw
            except:
                await ctx.send("Unable to find a message with that ID...")
                return
            # So the except returns, which means this happens only if we
            # were successful. We subtract 1 from the count so that we can
            # later make up for the offset inherent to ctx.history()
            finally:
                count = count-1
        # By default if we're not given a message, we use the message that
        # called the command as our "anchor"
        else:
            anchorMessage = ctx.message
        # Get the specified number of messages using ctx.history()
        messages = await ctx.history(before=anchorMessage,
                                     limit=count,
                                     reverse=True).flatten()
        # Again, if given a message ID, we need to get the history but also
        # add the message with the ID that was passed and, since we're using
        # reverse=True we append (otherwise we'd prepend)
        if messageID: messages.append(anchorMessage)
        # Now get a list of authors of messages that will be in the comic
        # Specifically we are getting _unique_ authors, thus the list(set())
        authors = list(set([m.author.id for m in messages]))
        # Now we'll grab every character filename so we can grab random ones
        chars = listdir(f"{self.datapath}/char")
        # We get one character per unique author. We use random.sample()
        # because random.choices() doesn't pull unique values for some reason.
        actors = sample(chars, k=len(authors))
        # And then we create a dictioary of actors for authors. This probably
        # should change since later we have to do another map of user IDs to
        # PIL.Image objects. I don't think we want to load images in this
        # section of code though, since we will break this out into its own
        # function of essentially list of message -> comic object
        # Probably we'll actually just have a list of IDs that we don't map
        # to Images or char names or anything until the second function
        actorMap = dict(zip(authors, actors))
        # At this point we should have all the necessary data
        # From here on, we build the scene
        # ----------------------------------------------------
        comic = []
        panel = []
        # Using enumerate so we can carry an index for lookahead, lookbehind
        for index, action in enumerate(messages):
            # The very first message always goes in the same spot
            # TODO: sanitize these messages as we go, replacing user snowflakes
            # with user names, emoji snowflakes with :emojiname:, etc. etc.
            # TODO: build a frankenfont that has all codepoints that Comic Sans
            # doesn't cover replaced with Noto Emoji font glyphs for better
            # rendering of unicode emojis
            if index == 0:
                panel.append({
                    'char': actorMap[action.author.id],
                    'text': action.content,
                    'id': action.author.id
                })
            else:
                if len(panel) == 1:  # We're looking at the "right" side
                    # Might be worth abstracting TextWrapper since it will
                    # always take self.comicSans (or later, self.font) as well
                    # as self.textWidth
                    prevTextRenderedWrapper = TextWrapper(messages[index-1].content, self.comicSans, self.textWidth)
                    # Would also be nice to have that abstraction do this part
                    # too, since you can't inline the wrapped_text() func
                    prevTextRendered = prevTextRenderedWrapper.wrapped_text()
                    # Blank panel if last author and this one are the same
                    # Blank panel if last message height is over 3 lines tall
                    if action.author == messages[index-1].author or len(prevTextRendered.split('\n')) > 3:
                        # So in this case we want to only have one action
                        # in the panel instead of two because of either
                        # a monologue or a big text block
                        # We probably want to change 'char' to the user's ID
                        # when we switch to not pulling char image names
                        panel.append({'char': None, 'text': None})
                        comic.append(panel)
                        panel = []
                        panel.append({
                            'char': actorMap[action.author.id],
                            'text': action.content,
                            'id': action.author.id
                        })
                    else:
                        # This isn't DRY.
                        # TODO: move this append-check action to a helper func
                        panel.append({
                            'char': actorMap[action.author.id],
                            'text': action.content,
                            'id': action.author.id
                        })
                        if len(panel) == 2:
                            comic.append(panel)
                            panel = []
                # I'm pretty sure we don't need two elses here? They do the
                # same thing.
                else:
                    panel.append({
                        'char': actorMap[action.author.id],
                        'text': action.content,
                        'id': action.author.id
                    })
                    if len(panel) == 2:
                        comic.append(panel)
                        panel = []
        # Now we check for any stragglers and append them.
        if len(panel) > 0:
            comic.append(panel)
        # Our data is now ready. Time to build an image!
        # These have been the defaults since the dawn of time. Do we ever want
        # to make them configurable? That would require some other changes too.
        panelWidth = 450
        panelHeight = 300
        # Create a canvas for us to put our stuff in
        # TODO: look into the bug where over 100 messages breaks this somehow?
        # No issue filed for the above todo yet
        canvasHeight = panelHeight*len(comic)
        canvas = Image.new("RGBA", (panelWidth, canvasHeight))
        # canvasBytes is the in-memory image since we can't use the Image object
        # directly as our attached file.
        canvasBytes = BytesIO()
        # Again, since the dawn of time this is the only background the comic
        # has ever used, but prescriptivism is shit so...
        # TODO: make this configurable per-server. One option is a specific
        # background with the default being the standard one, and the other
        # option should be to pick a random background and use it for every
        # panel, and maybe even one last option of a random background per panel
        background = Image.open(f"{self.datapath}/background/{serverConfig.backgroundImage}")
        # Create our Draw object
        draw = ImageDraw.Draw(canvas)
        # This is the top and sides margin size for text and characters
        # TODO: make this configurable per-server and take into account how
        # changing this changes text and char rendering
        textBuffer = 10
        # Here's where we load our characters. The stuff way above where we pick
        # a bunch of chars for each unique author should probably just be a
        # simple list of unique IDs and we'll do the rest here instead.
        # TODO: refactor per previous comment
        charImageMap = {}
        for id in authors:
            charImageMap[id] = Image.open(f"{self.datapath}/char/{actorMap[id]}")
        # I think instead of iterating against a range like this, we should
        # probably iterate against the comic object directly?
        # This is where things get messy tbh, lots of possible refactoring and
        # optimizing inside this for-loop
        for panelCount in range(0, len(comic)):
            # Paste in our background first
            canvas.paste(background, (0, (panelHeight*panelCount)))
            # Calculate the bottom edge for various reasons
            bottomEdge = panelHeight*(panelCount+1)
            # Next we need to draw text...
            ## We start by wrapping the text using our helper class
            # TextWrapper, just to be clear, calculates the length of rendered
            # text and wraps any words that would be wider than a given width
            leftTextWrapper = TextWrapper(comic[panelCount][0]['text'], self.comicSans, self.textWidth)
            leftText = leftTextWrapper.wrapped_text()
            # Now we find out how tall the left side text is so we can scale
            # the chars properly beneath it.
            (_, leftTextHeight) = draw.multiline_textsize(leftText, font=self.comicSans)
            # We also need to calculate the right side text height because we
            # have the two chars scaled to be as tall as the space left beneath
            # both of the rendered text blocks
            # Here we check if there's going to be right side text at all
            if len(comic[panelCount])==1 or not comic[panelCount][1]['text']:
                rightTextHeight = 0
            else:
                rightTextWrapper = TextWrapper(comic[panelCount][1]['text'], self.comicSans, self.textWidth)
                rightText = rightTextWrapper.wrapped_text()
                ### left side buffer is rendered text width + textBuffer and find the difference between that and panelWidth
                (rightTextWidth, rightTextHeight) = draw.multiline_textsize(rightText, font=self.comicSans)
            # Left side character time
            ## We want to thumbnail the character to fit between the bottom of
            ## the left text and the bottom of the panel, taking into account
            ## buffers at the top and bottom
            leftBottomEdge = leftTextHeight+(textBuffer*2)
            charHeight = panelHeight-leftBottomEdge-(textBuffer*2)-rightTextHeight
            if charHeight < 150: charHeight = 150
            charWidth = 225-(textBuffer*2)
            # Here we make a copy of the image so we can scale per-panel
            # without worrying about destroying the char loaded into memory
            thumb = charImageMap[comic[panelCount][0]['id']].copy()
            thumb.thumbnail((charWidth,charHeight))
            canvas.paste(thumb, (textBuffer,(panelHeight*(panelCount+1))-thumb.height), mask=thumb)
            ## Now we draw the left side text, easy
            ### left side buffer
            leftBuffer = textBuffer
            ### top side buffer based on which panel we're in
            topBuffer = textBuffer+(panelHeight*panelCount)
            # TODO: make this font pull from config instead of defaulting to
            # our comicSans object. Maybe make the text color configurable too?
            draw.multiline_text((leftBuffer, topBuffer), leftText, font=self.comicSans, fill="white")

            # Non-DRY code here, checking again if there's a right side of this panel
            if len(comic[panelCount])==1 or not comic[panelCount][1]['text']: continue

            ## And then we need to draw the right size text, giving it a top buffer equal to the height of the left text + 10 + textBuffer
            leftBuffer = panelWidth - (rightTextWidth+textBuffer)
            ### top side buffer should be the same, but add previous text height and textBuffer and an extra 20
            topBuffer = topBuffer+leftTextHeight+textBuffer
            ## Time for right side char
            thumb = charImageMap[comic[panelCount][1]['id']].copy()
            thumb.thumbnail((charWidth, charHeight))
            thumb = ImageOps.mirror(thumb)
            leftCharBuffer = panelWidth-(textBuffer+thumb.width)
            canvas.paste(thumb, (leftCharBuffer,(panelHeight*(panelCount+1))-thumb.height), mask=thumb)
            draw.multiline_text((leftBuffer, topBuffer), rightText, font=self.comicSans, fill="white")
            # Now we need to draw a line to separate panels
            # TODO: don't draw this line on the last panel
            draw.line([(0,bottomEdge-1),(panelWidth, bottomEdge-1)], width=4, fill="black")
        # Write the Image object to our BytesIO file-in-memory object
        canvas.save(canvasBytes, format="PNG")
        # Send the file away~~
        # TODO: per-server configuration for text to send along with this
        # default to none, let the server admin pick their string
        # TODO: make the filename a unique hash or something so that we can
        # also store comic data under the same name with a different extension
        # This would let us debug any weird stuff rendered into comics.
        await ctx.send(content=serverConfig.comicText, file=discord.File(canvasBytes.getvalue(), filename="weeed.png"))
