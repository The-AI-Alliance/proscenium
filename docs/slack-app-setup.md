# Slack App setup

## Create App

Go to [Your Apps](https://api.slack.com/apps) and click "Create New App"
in the upper right, and then "From Scratch".

Enter "Proscenium" for App Name, and then your workspace.

(Also see [api quickstart](https://api.slack.com/quickstart))

This will take you to the new app's URL.

## Create app token

Scroll down to the "App-Level Token" section, and then click
"Generate Token and Scopes".

For "Token Name", enter "app token".

Add all 3 available scopes: `connections:write`, `authorizations:read`,
and `app_configurations:write`.

Then click "Generate".

Copy the value of the "Token" field.
Note this as the `SLACK_APP_TOKEN`, and then click "Done".

You will now be back at the app's "Basic Information" page.

## Enable socket mode

On the left hand side in the "Settings" section,
click on "Socket Mode".

Toggle the "Enable Socket Mode" button to the on position.

## Subscribe to events

On the left hand side in the "Features" section,
click "Event Subscriptions".

Toggle the "Enable Events" button to "on".

## Activate incoming webhooks

On the left hand side in the "Features" section,
click "Incoming Webhooks".

Toggle the "Activate Incoming Webhooks" button to "on".

## Add bot token scopes

On the left hand side in the "Features" section,
click "OAuth & Permissions".

In the "Scopes" section of the resulting page,
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

## Add a bot token

Stay on the "OAuth & Permissions" tab from the previous step.

In the "OAuth Tokens" section of the resulting page,
click the "Install to *Your Workspace*" button.

Then click the "Allow" button.

This will return to the "OAuth Tokens" section.

Copy the "Bot User OAuth Token" as the `SLACK_BOT_TOKEN`.
