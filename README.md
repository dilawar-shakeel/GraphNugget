# GraphNugget
🐣 A cute, LangGraph-powered Discord bot that scoops up messy chat context and fries it into golden, structured emails.


## Where things stand

The bot is live-capable and does one job so far: it listens to **you** on Discord, works out whether your message is a job post, and answers accordingly. Nothing is turned into emails yet — that's the next stage.

### What it does today

1. You send the bot a direct message on Discord. It ignores everyone else.
2. A decision step asks OpenAI's Decisions API (`gpt-6-luna`) one yes/no question: *is this message a job post?* It gets back a probability, and anything at 50% or above counts as a job post.
3. If it **is** a job post, the bot replies "Job post detected." (a placeholder for the real handling we'll build next).
4. If it **isn't**, the bot just chats with you like a normal assistant and remembers the conversation until it restarts.

### The files

- `src/graphnugget/discord_boy.py` — the Discord side. Starts the bot and gives two simple functions: `read_message()` and `send_message()`. Only the owner can talk to it.
- `src/graphnugget/workflow.py` — the LangGraph workflow (decide → job post or chat), plus the code that draws the graph as an image.
- `Dockerfile`, `docker-compose.yml` — run the bot in a container that restarts itself.
- `justfile` — short commands for everything below.

### How to run it

Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY` and `DISCORD_TOKEN`. Optionally set `DISCORD_OWNER_ID`; if left empty, the owner of the bot application is used. In the Discord developer portal, turn on **Message Content Intent**.

| Command | What it does |
|---|---|
| `just up` | Run the bot directly |
| `just docker-up` | Build and run it in Docker, in the background |
| `just docker-logs` | Watch the Docker logs |
| `just docker-down` | Stop the Docker version |
| `just graph` | Draw the workflow to `graph.png` and open it |

### Still to do

- Real handling for job posts (the placeholder reply is temporary).
- Turning chat context into structured emails via the Google APIs, which are already listed as dependencies.
- Memory currently lives in RAM, so it's forgotten on restart.
