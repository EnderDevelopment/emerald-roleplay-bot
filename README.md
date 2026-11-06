# Emerald RolePlay Discord Bot

Emerald RolePlay is a Discord bot for science roleplay servers that provides support tickets, science-team applications, private ticket channels, application review buttons, and a staff command to move members into a `suport` voice channel.

## Install

1. Create a Discord application and bot in the Discord Developer Portal.
2. Enable the Server Members intent.
3. Invite the bot with the `bot` and `applications.commands` scopes.
4. Grant the bot these permissions:
   - Manage Channels
   - Move Members
   - View Channels
   - Send Messages
   - Embed Links
   - Read Message History
5. Copy `.env.example` to `.env`.
6. Configure the environment values:
   - `DISCORD_TOKEN`: Your bot token, stored only in your local `.env` file.
   - `APPLICATION_CHANNEL_ID`: The channel ID where submitted applications are reviewed.
   - `SUPPORT_CATEGORY_ID`: Optional category ID for support ticket channels.
   - `SUPPORT_VOICE_CATEGORY_ID`: Optional category ID for the support voice channel.
7. Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

8. Start the bot:

```bash
python main.py
```

## Use

1. Run `/setup` in the channel where the support and application panel should appear. This command requires Administrator permission.
2. Members can select `Open support ticket` to create a private ticket channel.
3. Members can select `Apply for science team` to open and submit the application form.
4. Submitted applications are sent as embeds to the configured `APPLICATION_CHANNEL_ID`.
5. Staff with Manage Channels permission can use the `Accept` or `Decline` buttons on applications.
6. Staff with Manage Channels and Move Members permissions can run:

```text
/move_support member
```

The command creates or reuses a voice channel named `suport` and moves the selected member into it. The selected member must already be connected to a voice channel.

7. Ticket owners can close their own tickets with the ticket button. Staff with Manage Channels permission can also use:

```text
/close_ticket
```

This command must be used inside a Science RP support ticket.

---

More Discord bot projects by EnderDevelopment: https://github.com/EnderDevelopment

Project page: https://dash.enderdevelopment.com/community/119beb79-cbd2-40c6-a68c-ebf133d2fe81?utm_source=github&utm_medium=readme&utm_campaign=auto_publish&utm_content=119beb79-cbd2-40c6-a68c-ebf133d2fe81
