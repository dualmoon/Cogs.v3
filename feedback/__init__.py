from .feedback import Feedback


def setup(bot):
  bot.add_cog(Feedback(bot))
