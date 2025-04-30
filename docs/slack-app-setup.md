# Slack App setup

## Create App

Go to [Your Apps](https://api.slack.com/apps) and click "Create New App"
in the upper right, and then "From a Manifest".

Select your workspace and click "Next".

Remove the default JSON and paste the contents of 
the [Proscenium Slack App manifest.json](./slack-manifest.json)

Enter "Proscenium" for App Name, and then your workspace,
and then click "Next".

Review the information on the last step and click "Create".

Also see [Slack's docs](https://docs.slack.dev/))

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

## Features > OAuth and Permissions

### Add a bot token

In the "OAuth Tokens" section of the page,
click the "Install to *Your Workspace*" button.

Then click the "Allow" button.

This will return to the "OAuth Tokens" section.

Copy the "Bot User OAuth Token" as the `SLACK_BOT_TOKEN`.
