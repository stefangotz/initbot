# Setting Up a Discord Bot

This guide walks through creating a Discord bot account and inviting it to your server.
You need a Discord account and a server where you have the *Manage Server* permission.

## 1. Create an Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application**.
3. Enter a name (e.g. `initbot`) and click **Create**.

## 2. Create a Bot User

1. In the left sidebar, click **Bot**.
2. Click **Add Bot**, then confirm with **Yes, do it!**

## 3. Copy the Bot Token

1. Under the bot's username, click **Reset Token**, then confirm.
2. Click **Copy** to copy the token to your clipboard.

> **Keep this token secret.** Anyone who has it can control your bot.
> If it leaks, return here and reset it immediately.

You will paste this token into `sh ./tools/configure.sh` in the next section.

## 4. Enable the Message Content Intent

Prefix commands like `$init` require the bot to read message content.

1. Still on the **Bot** page, scroll down to **Privileged Gateway Intents**.
2. Enable **Message Content Intent**.
3. Click **Save Changes**.

## 5. Generate an Invite URL

1. In the left sidebar, click **OAuth2**, then **URL Generator**.
2. Under **Scopes**, check **bot**.
3. Under **Bot Permissions**, check all of the following:
   - **Read Messages/View Channels**
   - **Send Messages**
   - **Read Message History**
   - **Send Messages in Threads**
4. Copy the **Generated URL** at the bottom of the page.

## 6. Invite the Bot to Your Server

1. Open the copied URL in a browser.
2. Select the server you want to add the bot to and click **Continue**.
3. Confirm the permissions and click **Authorize**.

## Next Step

Run the setup wizard to enter your bot token and configure the app:

```sh
sh ./tools/configure.sh
```
