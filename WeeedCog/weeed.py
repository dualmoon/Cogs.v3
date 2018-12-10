from redbot.core import commands, Config, checks
import discord
from PIL import Image, ImageOps, ImageDraw, ImageFont
from redbot.core.data_manager import bundled_data_path
from redbot.core.bot import Red
from io import BytesIO
from random import choices, choice
from os import listdir
from .textwrapper import TextWrapper


class Weeedbot(commands.Cog):
    """It's weeedbot"""

    def __init__(self, red: Red):
        self.bot = red
        configID = 901101100011101010110111001100001
        self.config = Config.get_conf(self, identifier=configID)
        self.comicSans = ImageFont.truetype(f"{self.datapath}/font/ComicBD.ttf", size=15)
        self.textWidth = 300

    # def _img_to_file(img: Image):
    #     fileInMemory = BytesIO()
    #     img.save(fileInMemory, format="PNG")

    @property
    def datapath(self):
        return str(bundled_data_path(self))

    @commands.group()
    async def weeed(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            pass

    @weeed.command()
    async def comic(self, ctx: commands.Context, count: int):
        if count > 10:
            await ctx.send("Please limit yourself to 10 or less messages. I can't do everything, you know.")
            return
        # Get the specified number of messages
        messages = await ctx.history(before=ctx.message,
                                     limit=count,
                                     reverse=True).flatten()
        # Now get a list of authors
        authors = list(set([m.author.id for m in messages]))
        # Next up, get a specified number of characters
        chars = listdir(f"{self.datapath}/char")
        actors = choices(chars, k=len(authors))
        # And then we create a dictionary of actors for authors
        actorMap = dict(zip(authors, actors))
        # At this point we should have all the necessary data
        # From here on, we build the scene
        # ----------------------------------------------------
        comic = []
        panel = []
        for index, action in enumerate(messages):
            if index == 0:
                panel.append({
                    'char': actorMap[action.author.id],
                    'text': action.content,
                    'id': action.author.id
                })
            else:
                if len(panel) == 1:  # We're looking at the "right" side
                    # Blank panel if last author and this one are the same
                    # Blank panel if last message height is over 80 pixels
                    prevTextRenderedWrapper = TextWrapper(messages[index-1].content, self.comicSans, self.textWidth)
                    prevTextRendered = prevTextRenderedWrapper.wrapped_text()
                    if action.author == messages[index-1].author or len(prevTextRendered.split('\n')) > 3:
                        panel.append({'char': None, 'text': None})
                        comic.append(panel)
                        panel = []
                        panel.append({
                            'char': actorMap[action.author.id],
                            'text': action.content,
                            'id': action.author.id
                        })
                    else:
                        panel.append({
                            'char': actorMap[action.author.id],
                            'text': action.content,
                            'id': action.author.id
                        })
                        if len(panel) == 2:
                            comic.append(panel)
                            panel = []
                else:
                    panel.append({
                        'char': actorMap[action.author.id],
                        'text': action.content,
                        'id': action.author.id
                    })
                    if len(panel) == 2:
                        comic.append(panel)
                        panel = []
        if len(panel) > 0:
            comic.append(panel)
        # Our data is now ready. Time to build an image!
        panelWidth = 450
        panelHeight = 300
        canvasHeight = panelHeight*len(comic)
        canvas = Image.new("RGBA", (panelWidth, canvasHeight))
        canvasBytes = BytesIO()
        background = Image.open(f"{self.datapath}/background/beach-paradise-beach-desktop.jpg")
        draw = ImageDraw.Draw(canvas)
        textBuffer = 10
        charImageMap = {}
        for id in authors:
            charImageMap[id] = Image.open(f"{self.datapath}/char/{actorMap[id]}")
        for panelCount in range(0, len(comic)):
            canvas.paste(background, (0, (panelHeight*panelCount)))
            bottomEdge = panelHeight*(panelCount+1)
            # Next we need to draw text...
            ## We start by wrapping the text using our helper class
            leftTextWrapper = TextWrapper(comic[panelCount][0]['text'], self.comicSans, self.textWidth)
            leftText = leftTextWrapper.wrapped_text()
            (_, leftTextHeight) = draw.multiline_textsize(leftText, font=self.comicSans)
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
            thumb = charImageMap[comic[panelCount][0]['id']].copy()
            thumb.thumbnail((charWidth,charHeight))
            canvas.paste(thumb, (textBuffer,(panelHeight*(panelCount+1))-thumb.height), mask=thumb)
            ## Now we draw the left side text, easy
            ### left side buffer
            leftBuffer = textBuffer
            ### top side buffer based on which panel we're in
            topBuffer = textBuffer+(panelHeight*panelCount)
            draw.multiline_text((leftBuffer, topBuffer), leftText, font=self.comicSans, fill="white")

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
            draw.line([(0,bottomEdge-1),(panelWidth, bottomEdge-1)], width=4, fill="black")
        canvas.save(canvasBytes, format="PNG")
        await ctx.send("A comic, starring... some weirdos.", file=discord.File(canvasBytes.getvalue(), filename="weeed.png"))
