#!/bin/python3

from textsum.summarize import Summarizer
import discord
import logging
import dotenv
import os
import asyncio
from functools import wraps, partial

logging.basicConfig(level=logging.INFO)

# load summarizer
summarizer = Summarizer(model_name_or_path="philschmid/bart-large-cnn-samsum", token_batch_length=1024,use_cuda=False, max_length=100)

# load dotenv
dotenv.load_dotenv()

TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
intents.message_content = True

def wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run

@wrap
def generate_summ(messages_to_summ):
    return summarizer.summarize_string(messages_to_summ)


bot = discord.Bot()


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.slash_command(name="tldr", description="TLDRs the last n messages")
async def tldr(ctx, num_messages: int):
    if num_messages > 500:
        # return ephemeral message
        await ctx.respond("Please enter a number less than 500", ephemeral=True)
        return

    await ctx.respond("Generating summary now!")
    messages = await ctx.channel.history(limit=num_messages).flatten()
    extracted = []
    for message in messages:
        extracted.append(
            f'{message.author.display_name} : {message.content} \n')
    extracted.reverse()
    text = ''.join(str(value) for value in extracted)
    summary = await generate_summ(text)
    print("generated a summary with a length of " + str(len(summary)))
    await ctx.respond(summary)

# @bot.slash_command(name="params", description="Returns the parameters of the summarizer")
# async def params(ctx):
#     await ctx.respond(summarizer.get_inference_params())


@bot.slash_command(name="ping", description="Pong!")
async def ping(ctx):
    await ctx.respond(f'Pong! {round(bot.latency * 1000)}ms')

bot.run(TOKEN)
