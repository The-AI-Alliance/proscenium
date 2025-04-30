# Slack App setup

## Create App

Go to [Your Apps](https://api.slack.com/apps) and click "Create New App"
in the upper right, and then "From Scratch".

Enter "Proscenium" for App Name, and then your workspace.

(Also see [api quickstart](https://api.slack.com/quickstart))

This will take you to the new app's page.

## Settings > Basic Information

Scroll down to the "App-Level Token" section, and then click
"Generate Token and Scopes".

For "Token Name", enter "app token".

Add all 3 available scopes: `connections:write`, `authorizations:read`,
and `app_configurations:write`.

Then click "Generate".

Copy the value of the "Token" field.
Note this as the `SLACK_APP_TOKEN`, and then click "Done".

## Settings > Socket Mode

Toggle the "Enable Socket Mode" button to the on position.

## Feature > Event Subscriptions

On the left hand side in the "Features" section,
click "Event Subscriptions".

Toggle the "Enable Events" button to "on".

Below that in "Subscribe to events on behalf of users",
click "Add Workspace Event" and add:

- `message:im`

## Features > Incoming Webhooks

Toggle the "Activate Incoming Webhooks" button to "on".

## Features > OAuth and Permissions

### Add Scopes

In the "Scopes" section of the page,
there is a "Bot Token Scopes" subsection.
Click "Add an OAuth Scope" and add the following:

- `app_mentions:read`
- `assistant:write`
- `channels:history`
- `channels:join`
- `channels:read`
- `chat:write`
- `commands`
- `emoji:read`
- `groups:history`
- `groups:read`
- `groups:write`
- `im:history`
- `im:read`
- `im:write`
- `links:read`
- `mpim:read`
- `reactions:read`
- `reactions:write`
- `users:write`

### Add a bot token

In the "OAuth Tokens" section of the page,
click the "Install to *Your Workspace*" button.

Then click the "Allow" button.

This will return to the "OAuth Tokens" section.

Copy the "Bot User OAuth Token" as the `SLACK_BOT_TOKEN`.
