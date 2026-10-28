set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# run the discord LLM bot
up:
    uv run python -m graphnugget.workflow

# run the bot in docker (background, restarts automatically)
docker-up:
    docker compose up -d --build

docker-down:
    docker compose down

docker-logs:
    docker compose logs -f

# render the workflow graph to graph.png and open it
graph:
    uv run python -m graphnugget.workflow --draw 
