# Quick Start Guide

Get your Arbitrage API up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure (Optional)

For basic usage, the default configuration works out of the box. For DEX support:

1. Get a free Infura API key from https://infura.io
2. Edit `config.py` and update the `INFURA_URL` with your key
3. Adjust `COMMON_PAIRS` to monitor your preferred trading pairs

## Step 3: Start the API

```bash
python main.py
```

You should see:
```
✓ Connected to binance
✓ Connected to coinbase
✓ Connected to kraken
...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 4: Test the API

Open a new terminal and run:

```bash
python example_client.py
```

Or test with curl:

```bash
# Health check
curl http://localhost:8000/

# Get prices
curl http://localhost:8000/prices/BTC/USDT

# Find arbitrage opportunities
curl http://localhost:8000/arbitrage/simple?min_profit_percent=0.5

# Get triangular arbitrage
curl http://localhost:8000/arbitrage/triangular
```

## Step 5: Access Documentation

Visit http://localhost:8000/docs for interactive API documentation

## Docker Deployment (Alternative)

If you prefer Docker:

```bash
# Build and run
docker-compose up --build

# Or run in background
docker-compose up -d
```

## Next Steps

1. **Customize**: Edit `config.py` to add more exchanges or trading pairs
2. **Monitor**: Use the WebSocket endpoint for real-time opportunities
3. **Integrate**: Build your trading bot using the API endpoints
4. **Scale**: Deploy to production with proper security and monitoring

## Common Issues

### Issue: "Module not found"
**Solution**: Make sure you installed all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: "Failed to connect to exchange"
**Solution**: Some exchanges may have rate limits or require API keys. Check the exchange's documentation.

### Issue: "No opportunities found"
**Solution**: This is normal! Arbitrage opportunities are rare. Try:
- Lowering `min_profit_percent` to 0.1%
- Adding more exchanges in `config.py`
- Checking during high market volatility

### Issue: Port 8000 already in use
**Solution**: Change the port in `main.py`:
```python
uvicorn.run("main:app", host="0.0.0.0", port=8080)
```

## Support

For detailed documentation, see `README.md`

For issues, check the logs or open an issue on the repository.

Happy arbitraging! 🚀
