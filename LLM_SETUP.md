# Quick LLM Setup Guide

## Enable LLM Features (Optional)

The tool works great without LLM, but LLM adds senior trader-level insights.

### Option 1: OpenAI (Recommended)

```bash
# Set API key
export STOCK_OPENAI_API_KEY=sk-your-key-here

# Enable LLM
export STOCK_LLM_ENABLED=true
export STOCK_LLM_PROVIDER=openai
export STOCK_LLM_MODEL=gpt-4o-mini  # Cost-effective, high quality

# Run scan
python scripts/main.py scan --mode intraday
```

### Option 2: Disable LLM (Use Keyword-Based Methods)

```bash
# Disable LLM
export STOCK_LLM_ENABLED=false

# Or edit stock_discovery/config.py:
# LLM_ENABLED = False
```

### Option 3: Local Ollama (Free)

```bash
# Install Ollama: https://ollama.ai
# Run: ollama pull llama2

export STOCK_LLM_PROVIDER=local
export STOCK_LLM_MODEL=llama2
export STOCK_LLM_ENABLED=true
```

## What LLM Adds

- **Advanced News Analysis**: Context-aware sentiment (not just keywords)
- **Trade Rationale**: Detailed explanations of why setups work
- **Risk Assessment**: Identifies failure modes and mitigation
- **Market Context**: How trades fit into current regime
- **Learning Insights**: Pattern recognition from outcomes

## Cost Estimate

With GPT-4o-mini:
- ~$0.01-0.05 per scan (depends on picks found)
- Caching reduces costs significantly
- Daily scans: ~$0.30-1.50/month

See `docs/LLM_INTEGRATION.md` for full details.
