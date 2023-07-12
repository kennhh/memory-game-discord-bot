import interactions
from interactions import Client, Task, SlashContext, listen, slash_command, IntervalTrigger, Button, ButtonStyle, SlashCommandOption, OptionType


import logging
logging.basicConfig()
cls_log = logging.getLogger('MyLogger')
cls_log.setLevel(logging.DEBUG)
client = Client(intents=interactions.Intents.ALL, token='', sync_interactions=True, asyncio_debug=True, logger=cls_log, send_command_tracebacks=False)


@listen()
async def on_startup():
    print(f'{client.user} connected to discord')


from memory_game_logic import MemoryGame
game = MemoryGame()

@Task.create(IntervalTrigger(seconds=1.5))
async def memory_game_task(message, current_index):
    buttons = []
    if current_index < game.sequence_length:
        for i in range(25):
            if i == game.sequence[current_index]:
                buttons.append(
                    Button(style = ButtonStyle.BLUE, label = f'{i}' if game.hidden_game == False else '‍', custom_id = f'{i}', disabled=True)
                )
            else:
                buttons.append(
                    Button(style = ButtonStyle.GRAY, label = f'{i}' if game.hidden_game == False else '‍', custom_id = f'{i}', disabled=True)
                )
        actionrowbuttons = interactions.spread_to_rows(*buttons)
        await message.edit(components = actionrowbuttons)
        memory_game_task.restart(message, current_index + 1)
    else:
        for i in range(25):
            buttons.append(
                Button(style = ButtonStyle.GRAY, label = f'{i}' if game.hidden_game == False else '‍', custom_id = f'{i}', disabled=False)
            )
        actionrowbuttons = interactions.spread_to_rows(*buttons)
        await message.edit(components = actionrowbuttons)
        memory_game_task.stop()


@slash_command(
        name='memory_game',
        description='start a memory game',
        options=[
            SlashCommandOption(
                name='hidden_game',
                description='hidden numbers (off by default)',
                type=OptionType.BOOLEAN,
                required=False
            )
        ])
async def memory(ctx: SlashContext, hidden_game: bool = False):
    await ctx.defer()
    game.hidden_game = hidden_game
    game.generate_sequence()
    buttons = []
    for i in range(25):
        buttons.append(
            Button(style = ButtonStyle.GRAY, label = f'{i}' if game.hidden_game == False else '‍', custom_id = f'{i}', disabled=True)
        )
    actionrowbuttons = interactions.spread_to_rows(*buttons)
    message = await ctx.send(components=actionrowbuttons)
    memory_game_task.start(message, 0)


from interactions.api.events import Component

@listen()
async def on_component(event: Component):
    ctx = event.ctx
    sequence = game.sequence
    current_index = game.current_index
    custom_id = ctx.custom_id
    match ctx.custom_id:
        case str(custom_id):
            if int(custom_id) == int(sequence[current_index]):
                if len(sequence) == current_index + 1:
                    game.successful()
                    game.sequence_reset()
                    memory_game_task.start(ctx.message, 0)
                else:
                    game.correct_current_index()
                await ctx.send("", ephemeral=True)
            else:
                game.__init__()
                buttons = []
                for i in range(25):
                    if i == sequence[current_index]:
                        buttons.append(
                            Button(style = ButtonStyle.GREEN, label = f'{i}', custom_id = f'{i}', disabled=True)
                        )
                    elif i == int(custom_id):
                        buttons.append(
                            Button(style = ButtonStyle.RED, label = f'{i}', custom_id = f'{i}', disabled=True)
                        )
                    else:
                        buttons.append(
                            Button(style = ButtonStyle.GRAY, label = f'{i}', custom_id = f'{i}', disabled=True)
                        )
                actionrowbuttons = interactions.spread_to_rows(*buttons)
                embed = interactions.Embed(description=f'uh oh, you inputted {custom_id} instead of {sequence[current_index]}\n'
                                                       f'the correct sequence was {sequence} which is {len(sequence)} number(s) long')
                await ctx.edit_origin(embed=embed.to_dict(), components=actionrowbuttons)


client.start()