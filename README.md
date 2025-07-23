# polls_pipeline

Local pipeline to track public opinion polls.

## Quick start

```bash
# activate env
cd ~/SHRKVSCODE/polls_pipeline
source .venv/bin/activate

# make sure LM Studio is running its local server
# Settings ▸ Developer ▸ “Start Local LLM Server” (port 1234)
#   or: lms server start --model llama3:8b --port 1234

# run discovery once
python main.py --once

# or keep it running hourly
python main.py