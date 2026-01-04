# AI Prompt Templates

This directory contains generic prompt templates used by the AI system.

## Files

- `tools_policy_improved.md` - Tool usage instructions for trading
- `system_base_improved.md` - Base system prompt template
- `personality_speech_improved.md` - Personality template (filled with profile data)
- `trade_loop.md` - Trading loop instructions

## Usage

These templates are loaded by `prompt_loader_improved.py` and filled with profile-specific data from:
- Account persona data
- Persona templates in `data/personas/templates/`
- Real-time market and position data

Profile-specific prompts and overrides are stored in `data/personas/{account_id}/`.