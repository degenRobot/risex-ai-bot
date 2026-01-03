# New Profile Creation Guide

## Overview

Creating a new AI trading profile involves generating cryptographic keys, registering for gasless trading, depositing funds, and integrating with our chat/trading systems.

## Complete Flow

### 0. Personality Extraction (Optional)

For creating profiles based on real X/Twitter personalities, use our enhanced Grok prompt to extract detailed persona information:

#### Using Grok for Persona Extraction

1. **Copy the Enhanced Prompt**: Use this comprehensive Grok prompt below

**Enhanced Grok Prompt for X Profile Extraction:**

```
You are extracting a detailed trading persona from a public X profile to create an engaging AI trading personality. 

IMPORTANT: Be extremely thorough and verbose in your analysis. Spend significant time analyzing tweets, replies, quote tweets, and interactions to capture the full personality. The goal is to create a unique, fun AI trader that people will enjoy following and chatting with.

Target profile: {HANDLE_OR_URL}

Please analyze:
1. Last 20-50 tweets and interactions
2. Bio, pinned posts, and linked content  
3. Reply patterns and engagement style
4. Recurring themes, interests, and obsessions
5. Trading mindset and market commentary
6. Personality quirks and unique speech patterns

Produce detailed JSON, matching this enhanced schema:

{
  "profile_handle": "{HANDLE_OR_URL}",
  "display_name": "",
  "bio_summary": "comprehensive summary of their public persona",
  
  "personality_deep_dive": {
    "core_traits": ["5-7 defining personality characteristics"],
    "quirks_and_habits": ["unique behaviors, catchphrases, running jokes"],
    "emotional_triggers": ["what gets them excited, angry, or passionate"],
    "humor_style": "sarcastic / memey / dad jokes / dry wit / absurdist / none",
    "energy_level": "high / manic / chill / varies / analytical",
    "social_dynamics": "how they interact - confrontational / supportive / educational / trolly"
  },
  
  "voice_and_communication": {
    "tone": "e.g., snarky, formal, hype, academic, unhinged, wise",
    "pacing": "rapid-fire / measured / varies by topic / verbose / concise", 
    "vocabulary_level": "street / technical / academic / mixed",
    "signature_phrases": ["exact phrases they use repeatedly - be specific"],
    "emoji_usage": "heavy / selective / none / specific favorites",
    "punctuation_style": "proper / casual / excessive / ellipses / caps",
    "meme_fluency": "normie / degen / terminally online / boomer / none",
    "first_person_samples": [
      "quote about bull markets in their exact style",
      "quote about bear markets in their exact style", 
      "quote reacting to big crypto news in their exact style"
    ]
  },
  
  "trading_philosophy": {
    "core_beliefs": ["fundamental beliefs about markets and trading"],
    "strategy_preference": "detailed description of their approach",
    "risk_tolerance": 0.0-1.0,
    "time_horizon": "scalps / intraday / swing / long-term / varies",
    "position_sizing_attitude": "aggressive / conservative / calculated / yolo",
    "asset_focus": ["BTC", "ETH", "alts", "memes", "perps", "options", "stocks", "bonds"],
    "market_bias": "perma-bull / perma-bear / adaptive / contrarian / momentum",
    "decision_triggers": ["TA", "fundamentals", "sentiment", "news", "on-chain", "vibes"],
    "loss_handling": "how they deal with losing trades - emotionally and practically",
    "win_celebration": "how they react to successful trades",
    "favorite_setups": ["specific trading patterns or scenarios they love"]
  },
  
  "interests_and_obsessions": {
    "crypto_focus": ["specific coins, protocols, or sectors they talk about most"],
    "non_crypto_interests": ["hobbies, sports, culture, tech topics they engage with"],
    "recurring_narratives": ["stories or themes they constantly reference"],
    "pet_peeves": ["things that consistently annoy them"],
    "influences": ["people they quote, retweet, or reference frequently"],
    "communities": ["groups, servers, or spaces they're active in"]
  },
  
  "content_patterns": {
    "posting_frequency": "multiple daily / daily / weekly / sporadic",
    "peak_activity_times": "when they're most active",
    "content_mix": "% original thoughts / % retweets / % replies / % shitposts",
    "thread_tendency": "writes long threads / short takes / varies",
    "engagement_style": "responds to everyone / selective / ignores most",
    "controversy_level": "avoids drama / occasional hot takes / constant chaos"
  },
  
  "market_commentary_style": {
    "chart_analysis": "heavy TA user / basic levels / fundamentals only / ignores charts",
    "news_reaction": "immediate hot takes / thoughtful analysis / waits for confirmation",
    "prediction_style": "specific price targets / vague directional / timeline focused",
    "accountability": "admits mistakes / doubles down / deletes bad takes",
    "educational_value": "teaches others / keeps insights private / learning publicly"
  },
  
  "social_proof_and_credibility": {
    "follower_engagement": "high interaction / lurker audience / bot followers",
    "respected_voices": "who treats them as credible / who they respect",
    "track_record_claims": "verifiable wins they reference / unverifiable boasts",
    "transparency_level": "shares everything / selective disclosure / very private"
  },
  
  "ai_personality_recommendations": {
    "most_entertaining_aspects": ["what makes them fun to follow"],
    "chat_conversation_hooks": ["topics that would get them excited to discuss"],
    "trading_decision_triggers": ["market conditions that would activate their strategy"],
    "personality_conflicts": ["types of users or ideas they'd clash with"],
    "unique_value_proposition": "what makes this persona different from generic trading bots"
  },
  
  "profile_archetype": "creative label capturing their essence (e.g., 'Degen Prophet', 'Chart Wizard', 'Macro Doomer')",
  "entertainment_factor": 0.0-1.0,
  "educational_value": 0.0-1.0, 
  "authenticity_score": 0.0-1.0,
  "overall_confidence": 0.0-1.0,
  
  "implementation_notes": [
    "specific suggestions for making this persona engaging in our AI trading bot",
    "potential chat scenarios that would showcase their personality", 
    "trading behaviors that would feel authentic to their style",
    "content they'd create that users would want to see"
  ]
}

CRITICAL INSTRUCTIONS:
- Be extremely detailed and specific - extract exact phrases and language patterns
- Focus on what makes them unique and entertaining, not generic trader traits  
- Capture their authentic voice through direct quotes and specific examples
- Consider how this personality would be fun to interact with via chat
- Think about what trading decisions would feel authentic to their character
- If profile is sparse, lower confidence scores but still provide creative analysis
- Aim for personalities that are memorable, distinct, and engaging

Remember: The goal is creating an AI trader people will enjoy following and chatting with!
```

2. **Target Selection**: Choose an interesting X profile with:
   - Active trading commentary
   - Distinctive personality/voice
   - Engaging content style  
   - Clear trading philosophy

3. **Run Analysis**: Replace `{HANDLE_OR_URL}` in the prompt above with your target profile and paste into Grok
   ```
   Target profile: @ExampleTrader
   ```

4. **Extract Key Data**: Focus on these elements for AI personality:
   - **Voice patterns**: Exact phrases, tone, communication style
   - **Trading philosophy**: Risk tolerance, strategy, market bias
   - **Personality traits**: Quirks, humor style, emotional triggers
   - **Content themes**: Favorite topics, recurring narratives
   - **Social dynamics**: How they interact with others

5. **Map to Our System**: Convert Grok output to our personality structure:
   ```python
   # Example mapping from Grok analysis
   personality_type = "cynical"  # Based on social dynamics
   risk_tolerance = 0.7         # From trading philosophy  
   trading_style = "aggressive" # From strategy preference
   speech_style = "ct"          # From voice analysis
   personality_traits = [       # From personality deep dive
       "snarky", "contrarian", "analytical"
   ]
   ```

6. **Create Unique Profile**: Use extracted data in profile creation below

**Benefits of Grok Extraction**:
- ✅ Authentic personality based on real behavior
- ✅ Distinctive voice that stands out  
- ✅ Engaging chat interactions
- ✅ Realistic trading decisions
- ✅ Fun personalities users want to follow

### 1. Key Generation
```python
from web3 import Web3
w3 = Web3()

# Generate main account key (holds funds)
main_account = w3.eth.account.create()
main_address = main_account.address
main_private_key = main_account.key.hex()

# Generate separate signer key (for gasless trades) 
signer_account = w3.eth.account.create()
signer_address = signer_account.address
signer_private_key = signer_account.key.hex()

# CRITICAL: Keys must be different for security
assert main_address != signer_address
```

### 2. Signer Registration

**API Endpoint**: `POST /v1/auth/register-signer`  
**Purpose**: Enable gasless trading by registering the signer key with RISE

```python
registration_result = await rise_client.register_signer(
    account_key=main_private_key,
    signer_key=signer_private_key
)

# Expected response:
{
  "data": {
    "transaction_hash": "0x6ec6c13716f9d80a7c21bec8b2fdb5ea2a5d6edd9c9eae01acec65c00dc42283",
    "success": True,
    "status": 1,
    "block_number": "32259643"
  }
}
```

**What happens**:
- Main account signs a `RegisterSigner` message
- Signer account signs a `VerifySigner` message  
- RISE API validates both signatures
- Transaction is submitted to register the signer on-chain

### 3. USDC Deposit 

**API Endpoint**: `POST /v1/account/deposit-usdc`  
**Purpose**: Mint testnet USDC and deposit to trading account

```python
deposit_result = await rise_client.deposit_usdc(
    account_key=main_private_key,
    amount=100.0  # Amount in USDC
)

# Expected response:
{
  "data": {
    "transaction_hash": "0xbd91ab62598872628b29d6a9b4af545435bf17452cb494001a73135733ee197b",
    "block_number": "32259643", 
    "success": True
  }
}
```

**What happens**:
- Main account signs a `Deposit` message
- RISE backend mints testnet USDC to the account
- Funds are deposited into the trading balance
- Transaction is submitted on-chain

### 4. Verification

After registration and deposit, verify the account status:

```python
# Check on-chain equity
equity = await equity_monitor.fetch_equity(main_address)
# Should show deposited amount (e.g., $100.00)

# Check trading balance  
balance = await rise_client.get_balance(main_address)
# Should show available margin balance

# Check account info
account_info = await rise_client.get_account(main_address) 
# Should show registered status
```

## Integration with AI System

### 5. Profile Creation

#### Option A: Manual Creation (Advanced)

```python
from app.models import Account, Persona
from app.trader_profiles import create_trader_profile

# Create trader profile with personality
trader_profile = create_trader_profile("cynical")  # or "leftCurve", "midwit"

# Create Account model
account = Account(
    id=f"profile_{timestamp}",
    address=main_address,
    private_key=main_private_key,
    signer_key=signer_private_key,
    persona=Persona(
        name=trader_profile.base_persona.name,
        handle=f"{trader_profile.base_persona.handle}_{timestamp}",
        bio=trader_profile.base_persona.core_personality,
        trading_style="conservative",  # Map from risk_profile
        risk_tolerance=0.5,
        favorite_assets=["BTC", "ETH"],
        personality_traits=trader_profile.base_persona.base_traits,
        sample_posts=["Ready to trade!"]
    ),
    is_active=True,
    is_registered=True,
    registered_at=datetime.now(),
    has_deposited=True, 
    deposited_at=datetime.now(),
    deposit_amount=100.0
)

# Save to storage
storage.save_account(account)
```

#### Option B: Admin API (Recommended)

Use the automated profile creation endpoint that handles everything:

**API Endpoint**: `POST /api/admin/profiles`  
**Authentication**: Requires `X-API-Key` header with `ADMIN_API_KEY`

```bash
curl -X POST "https://risex-trading-bot.fly.dev/api/admin/profiles" \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Crypto Sage",
    "handle": "crypto_sage_42",
    "bio": "Wise trader who speaks in ancient market wisdom",
    "trading_style": "conservative",
    "risk_tolerance": 0.4,
    "personality_type": "cynical",
    "initial_deposit": 150.0,
    "favorite_assets": ["BTC", "ETH", "SOL"],
    "personality_traits": ["wise", "patient", "philosophical"]
  }'
```

**Response:**
```json
{
  "profile_id": "f1a96dac-89fd-4eeb-9dc6-5612085425d0",
  "address": "0xdE3244FCBf035A374c556d3E1c1774ebA74436fD", 
  "signer_address": "0x6A37D8A9213489a273bf037C20090d7804388FD8",
  "persona": {...},
  "initial_deposit": 150.0,
  "message": "Profile created and funded with 150.0 USDC"
}
```

**Trading Styles**: `aggressive`, `conservative`, `contrarian`, `momentum`, `degen`  
**Personality Types**: `cynical`, `leftCurve`, `midwit`

#### Option C: Grok-Enhanced Profile Creation

Combine Grok persona extraction with API creation:

1. **Extract with Grok**: Use enhanced prompt to analyze target X profile
2. **Map Grok Output**: Convert analysis to API parameters:

```python
# Example: Converting Grok analysis to API request
grok_analysis = {
    "profile_archetype": "Chart Wizard", 
    "trading_philosophy": {
        "risk_tolerance": 0.8,
        "strategy_preference": "technical analysis with momentum plays",
        "market_bias": "adaptive"
    },
    "voice_and_communication": {
        "tone": "snarky",
        "signature_phrases": ["gm chart addicts", "cope harder", "this is gentlemen"],
        "meme_fluency": "terminally online"
    }
}

# Map to API request
api_request = {
    "name": grok_analysis["profile_archetype"],
    "handle": "chart_wizard_2024",
    "bio": f"Snarky TA expert who {grok_analysis['trading_philosophy']['strategy_preference']}",
    "trading_style": "aggressive",  # Based on risk_tolerance > 0.7
    "risk_tolerance": grok_analysis["trading_philosophy"]["risk_tolerance"],
    "personality_type": "cynical",  # Based on snarky tone
    "personality_traits": ["snarky", "analytical", "memey"],
    "initial_deposit": 200.0
}
```

3. **Create Enhanced Persona**: The profile will have authentic personality based on real behavior

**Benefits of Grok-Enhanced Creation**:
- 🎯 Realistic trading psychology
- 💬 Authentic chat responses  
- 🎭 Unique personality that stands out
- 📊 Trading decisions that match character
- 🔥 Higher user engagement

This endpoint automatically:
- ✅ Generates secure key pairs
- ✅ Registers signer on RISE
- ✅ Deposits initial USDC  
- ✅ Creates persona and account
- ✅ Activates for trading

### 6. Enable Services

The profile is now ready for:

- **🤖 AI Chat**: Users can chat with the personality 
- **📈 Trading**: AI makes autonomous trading decisions
- **💰 Equity Tracking**: Real-time on-chain balance monitoring
- **📊 Analytics**: P&L tracking and performance metrics

## Key Security Requirements

### Address Separation
- **Main Address**: Holds funds, signs deposits, owns account
- **Signer Address**: Signs trading orders, must be different from main

### EIP-712 Signatures
All operations use typed signatures:
- `RegisterSigner`: Links signer to main account
- `VerifySigner`: Proves signer key ownership  
- `Deposit`: Authorizes USDC minting/deposit
- `PlaceOrder`: Gasless trading orders

### Testnet Environment
- Uses RISE Sepolia testnet
- USDC is minted, not real
- Trades are gasless (no ETH fees)
- Accounts must be whitelisted for full functionality

## Common Issues & Solutions

### ❌ Registration Fails
```
Error: "Signer already registered" 
```
**Solution**: Each signer can only be used once. Generate new keys.

### ❌ Deposit Fails  
```
Error: "insufficient funds" or "missing nonce"
```
**Solution**: 
- Account may not be whitelisted
- Try smaller amounts (start with $1)
- Ensure main account has some ETH for gas

### ❌ Zero Equity
If on-chain equity shows $0 after deposit:
- Wait for block confirmations
- Check transaction was successful
- Verify correct contract address

### ❌ Trading Disabled
```
Error: "Account not registered"
```
**Solution**: Ensure both registration and deposit completed successfully.

## Testing Checklist

For new profiles, verify:

- [ ] ✅ **Keys Generated**: Two different addresses created
- [ ] ✅ **Signer Registered**: Transaction hash received
- [ ] ✅ **Funds Deposited**: Transaction hash received  
- [ ] ✅ **Equity Visible**: On-chain balance shows deposit amount
- [ ] ✅ **Profile Saved**: Account exists in `data/accounts.json`
- [ ] ✅ **Chat Works**: AI responds with context and positions data
- [ ] ✅ **Trading Active**: Profile participates in trading cycles
- [ ] ✅ **Positions Tracked**: Real-time position data from RISE API
- [ ] ✅ **Orders History**: Historical order execution data
- [ ] ✅ **API Access**: Profile accessible via API endpoints

## API References

- **Signer Registration**: [RISE Docs](https://docs.risechain.com/docs/risex/api/register-signer)
- **Deposit USDC**: [API Reference](https://developer.rise.trade/reference/accountservice_depositusdc)
- **Account Management**: [API Docs](https://developer.rise.trade/reference/accountservice_getaccount)

## File Locations

- **Models**: `app/models.py` - Account, Persona definitions
- **Profiles**: `app/trader_profiles.py` - Base personalities  
- **Client**: `app/services/rise_client.py` - API interactions with RISE
- **Profile Manager**: `app/api/profile_manager.py` - Admin API for profile creation
- **Storage**: `data/accounts.json` - Profile persistence
- **Enhanced Grok Prompt**: Included in this document for X profile extraction
- **API Documentation**: `API.md` - Complete API reference

### Testing Scripts

- **Position/Orders**: `scripts/test_positions_orders.py` - Verify data fetching
- **Full Trading Flow**: `tests/trading/test_full_trading_flow.py` - Complete trading test
- **API Testing**: `tests/api/test_profile_creation.py` - Profile creation via API
- **Fresh Account**: `scripts/test_fresh_account_flow.py` - End-to-end account setup

### Useful Commands

```bash
# Test profile creation via API
poetry run python tests/api/test_profile_creation.py

# Test position and order data fetching  
poetry run python scripts/test_positions_orders.py

# Create profile using admin API
curl -X POST "https://risex-trading-bot.fly.dev/api/admin/profiles" \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d @profile_data.json

# Check live positions for all profiles
curl -s "https://risex-trading-bot.fly.dev/api/profiles/all" | jq '.[].position_count'
```