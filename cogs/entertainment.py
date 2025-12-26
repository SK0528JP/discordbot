# ... JankenView 内の process_janken の一部 ...
        embed = discord.Embed(title="✊✌️✋ じゃんけん結果", color=0x00aaff)
        embed.add_field(name="君の手", value=user_choice, inline=True)
        embed.add_field(name="私の手", value=bot_choice, inline=True)
        embed.add_field(name="判定", value=f"**{result}**", inline=False)
        
        await it.response.edit_message(content=None, embed=embed, view=None)
