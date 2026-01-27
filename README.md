# Professional Writing Assistant Telegram Bot

A Telegram bot that helps you write clear, professional messages using a local AI model.  
Built for emails, workplace communication, and polished writing directly inside Telegram.

---

## Features

This bot acts as a professional writing assistant and can:

- Rewrite informal notes or drafts into clear, professional emails
- Provide practical writing tips and common mistakes to avoid
- Check grammar, spelling, clarity, and tone
- Shorten long messages while preserving meaning and professionalism
- Translate and polish messages into other languages
- Analyze and explain technical images, diagrams, or screenshots

---

## Supported Commands

| Command       | Description                                   |
|---------------|-----------------------------------------------|
| `/rewrite`    | Rewrite a message into a professional version |
| `/tip`        | Get writing advice and best practices         |
| `/check`      | Review grammar, spelling, and tone            |
| `/shorten`    | Shorten a message while keeping clarity       |
| `/translate`  | Translate and polish text                     |
| `/explainimg` | Analyze and explain an image                  |
| `/help`       | Show all commands and usage examples          |

---

## Smart Message Handling

- The bot accepts messages **without commands** only if they are related to:
    - Emails
    - Professional or workplace communication
    - Formal written messages

- If a message is outside this scope, the bot responds that the request is not supported.

---

## User Experience Features

- Displays Telegram “typing” status while responses are being generated
- Shows temporary processing messages during AI inference
- Uses fully local AI processing with no external AI APIs