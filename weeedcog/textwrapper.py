"""
    Thanks to Igor Pomoaranskiy (https://stackoverflow.com/users/535884/igor-pomaranskiy) for this class
    Found posted to stackexchange here: https://stackoverflow.com/questions/7698231/python-pil-draw-multiline-text-on-image
"""

from PIL import Image, ImageDraw


class TextWrapper(object):
    """
        Helper class to wrap text in lines, based on given text, font
        and max allowed line width.
    """

    def __init__(self, text, font, max_width):
        self.text = text
        self.text_lines = [
            ' '.join([w.strip() for w in l.split(' ') if w])
            for l in text.split('\n')
            if l
        ]
        self.font = font
        self.max_width = max_width

        self.draw = ImageDraw.Draw(
            Image.new(
                mode='RGB',
                size=(100, 100)
            )
        )

        self.space_width = self.draw.textsize(
            text=' ',
            font=self.font
        )[0]

    def get_text_width(self, text):
        return self.draw.textsize(
            text=text,
            font=self.font
        )[0]

    def wrapped_text(self):
        wrapped_lines = []
        buf = []
        buf_width = 0

        for line in self.text_lines:
            for word in line.split(' '):
                word_width = self.get_text_width(word)

                expected_width = word_width if not buf else \
                    buf_width + self.space_width + word_width

                if expected_width <= self.max_width:
                    # word fits in line
                    buf_width = expected_width
                    buf.append(word)
                else:
                    # word doesn't fit in line
                    wrapped_lines.append(' '.join(buf))
                    buf = [word]
                    buf_width = word_width

            if buf:
                wrapped_lines.append(' '.join(buf))
                buf = []
                buf_width = 0

        return '\n'.join(wrapped_lines)
