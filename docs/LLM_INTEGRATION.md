# LLM Integration Guide

## Overview

The stock discovery tool now includes comprehensive LLM (Large Language Model) integration to provide senior trader-level analysis and insights. The LLM enhances:

1. **News Sentiment Analysis** - Advanced context-aware sentiment analysis
2. **Trade Rationale** - Detailed explanations of why setups are compelling
3. **Risk Assessment** - Identification of failure modes and mitigation strategies
4. **Market Context** - Analysis of how trades fit into current market regime
5. **Outcome Learning** - Pattern recognition and strategy improvement insights

## Configuration

### Environment Variables

Set these environment variables to enable LLM features:

```bash
# LLM Provider Selection
export STOCK_LLM_PROVIDER=openai  # Options: openai, anthropic, local, none
export STOCK_OPENAI_API_KEY=sk-...  # Your OpenAI API key
export STOCK_LLM_MODEL=gpt-4o-mini  # Model name
export STOCK_LLM_ENABLED=true
export STOCK_LLM_CACHE_ENABLED=true
```

### Config File

Alternatively, edit `stock_discovery/config.py`:

```python
# LLM Configuration
LLM_ENABLED: bool = True
LLM_PROVIDER: str = "openai"  # openai, anthropic, local, none
LLM_MODEL: str = "gpt-4o-mini"
LLM_TEMPERATURE: float = 0.3
LLM_CACHE_ENABLED: bool = True
LLM_CACHE_DURATION: int = 3600  # 1 hour
```

## Supported Providers

### 1. OpenAI (Recommended)
- **Models**: `gpt-4o-mini` (recommended), `gpt-3.5-turbo`, `gpt-4`
- **Cost**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens (gpt-4o-mini)
- **Quality**: Excellent
- **Setup**: Requires `OPENAI_API_KEY` or `STOCK_OPENAI_API_KEY`

### 2. Anthropic Claude
- **Models**: `claude-3-haiku-20240307`, `claude-3-sonnet-20240229`
- **Cost**: Similar to OpenAI
- **Quality**: Excellent
- **Setup**: Requires `ANTHROPIC_API_KEY` or `STOCK_ANTHROPIC_API_KEY`

### 3. Local (Ollama)
- **Models**: `llama2`, `mistral`, `codellama` (any Ollama model)
- **Cost**: Free (runs on your machine)
- **Quality**: Good (depends on model)
- **Setup**: Requires Ollama running locally on `http://localhost:11434`

### 4. Disabled
- Set `LLM_ENABLED=False` or `STOCK_LLM_PROVIDER=none`
- Tool falls back to keyword-based methods
- All functionality works without LLM

## Usage

### Basic Usage

The LLM integration is automatic when enabled:

```bash
# LLM will be used automatically if API key is set
python scripts/main.py scan --mode intraday
```

### Disable LLM

```bash
# Disable via environment variable
export STOCK_LLM_ENABLED=false
python scripts/main.py scan --mode intraday

# Or edit config.py: LLM_ENABLED = False
```

## Enhanced Output

When LLM is enabled, each pick includes:

### 1. Trade Rationale
**LLM-generated explanation** of why the setup is compelling:
- Technical factors highlighted
- Market context included
- Key indicators explained

### 2. Risk Assessment
**LLM-identified risks** and mitigation:
- Primary risk factors
- Potential failure modes
- Risk mitigation strategies

### 3. Market Context
**LLM analysis** of market fit:
- How trade fits current regime
- Sector trends
- Correlation considerations

### 4. News Impact
**LLM-summarized news** implications:
- Key events identified
- Market impact assessment
- Sentiment with context

## Example Output

```
1. KOTAKBANK - MOMENTUM_SWING
   Conviction: 76.4/100 | Risk: Medium Risk
   Entry: ₹2195.10 | SL: ₹2140.74 | Target: ₹2273.27
   
   Setup: Strong momentum setup with MA crossover above 20/50 day averages. 
   RSI at 55 shows healthy momentum without overbought conditions. 
   Volume increasing 15% above average confirms institutional interest.
   
   ⚠️  Risk Assessment: Primary risk is market-wide correction dragging down 
   financials. Stop-loss at 2.5% protects against false breakouts. 
   Watch for negative banking sector news.
   
   📊 Market Context: Banking sector showing relative strength vs NIFTY. 
   Recent RBI policy stance favorable for private banks.
   
   📰 News Impact: Positive sentiment from recent earnings beat. 
   Sector rotation into financials observed.
```

## Cost Management

### Caching
- Responses are cached for 1 hour (configurable)
- Reduces API calls for repeated queries
- Cache key based on prompt content

### Model Selection
- **gpt-4o-mini**: Best cost/quality balance (~10x cheaper than GPT-4)
- **gpt-3.5-turbo**: Faster, slightly lower quality
- **Local models**: Free but requires local setup

### Usage Tracking
Monitor API usage through your provider's dashboard:
- OpenAI: https://platform.openai.com/usage
- Anthropic: https://console.anthropic.com/

## Fallback Behavior

The tool gracefully falls back when LLM is unavailable:

1. **No API Key**: Falls back to keyword-based methods
2. **API Error**: Falls back to keyword-based methods
3. **Rate Limit**: Falls back to keyword-based methods
4. **Network Error**: Falls back to keyword-based methods

All fallbacks are automatic and transparent - the tool continues working.

## Testing

### Test LLM Service

```python
from stock_discovery.llm_service import LLMService

llm = LLMService(provider="openai", model="gpt-4o-mini")
if llm.available:
    response = llm.analyze("Test prompt")
    print(response)
else:
    print("LLM not available - check API key")
```

### Test Without LLM

```python
from stock_discovery.config import Config
from stock_discovery.scanner_engine import ScannerEngine

config = Config()
config.LLM_ENABLED = False
scanner = ScannerEngine(config)
# Tool works normally with keyword-based methods
```

## Troubleshooting

### LLM Not Working

1. **Check API Key**: Verify `STOCK_OPENAI_API_KEY` or `OPENAI_API_KEY` is set
2. **Check Provider**: Verify `STOCK_LLM_PROVIDER` matches your API key
3. **Check Model**: Verify model name is correct for your provider
4. **Check Network**: Ensure internet connection for API calls
5. **Check Logs**: Look for "LLM service not available" messages

### High Costs

1. **Enable Caching**: Set `LLM_CACHE_ENABLED=True`
2. **Use Cheaper Model**: Switch to `gpt-4o-mini` or `gpt-3.5-turbo`
3. **Disable LLM**: Set `LLM_ENABLED=False` for keyword-based methods
4. **Use Local**: Set up Ollama for free local LLM

### Slow Performance

1. **Enable Caching**: Reduces repeated API calls
2. **Use Faster Model**: `gpt-3.5-turbo` is faster than `gpt-4o-mini`
3. **Reduce Max Tokens**: Lower `max_tokens` in LLM calls (already optimized)

## Best Practices

1. **Start with LLM Disabled**: Test tool works first
2. **Enable LLM Gradually**: Start with news analysis, then add rationale
3. **Monitor Costs**: Track API usage, especially with high-volume scans
4. **Use Caching**: Always enable caching to reduce costs
5. **Fallback Ready**: Tool works without LLM - don't depend on it

## Future Enhancements

- [ ] Batch LLM requests for multiple picks
- [ ] Custom prompt templates
- [ ] LLM response quality scoring
- [ ] Multi-model ensemble (combine multiple LLM responses)
- [ ] Fine-tuned models for trading-specific tasks

