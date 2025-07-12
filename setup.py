#!/usr/bin/env python3
"""
VaultCoin Bot Setup Script
Run this to configure your bot easily!
"""

import os
import json

def setup_bot():
    print("🚀 VaultCoin Bot Setup")
    print("=" * 40)
    
    # Get bot token
    print("\n1. Bot Configuration:")
    bot_token = input("Enter your bot token (or press Enter to use existing): ").strip()
    if bot_token:
        # Update bot.py with the token
        with open('bot.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the token line
        import re
        content = re.sub(
            r'BOT_TOKEN = os\.getenv\(\'BOT_TOKEN\', "[^"]*"\)',
            f'BOT_TOKEN = os.getenv(\'BOT_TOKEN\', "{bot_token}")',
            content
        )
        
        with open('bot.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Bot token updated!")
    
    # Get webapp URL
    print("\n2. WebApp Configuration:")
    webapp_url = input("Enter your WebApp URL: ").strip()
    if webapp_url:
        with open('bot.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('"https://your-webapp-url.com"', f'"{webapp_url}"')
        
        with open('bot.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ WebApp URL updated!")
    
    # Get channel URL
    print("\n3. Channel Configuration:")
    channel_url = input("Enter your Telegram channel URL: ").strip()
    if channel_url:
        with open('bot.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('"https://t.me/yourchannel"', f'"{channel_url}"')
        
        with open('bot.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Channel URL updated!")
    
    # Get admin IDs
    print("\n4. Admin Configuration:")
    admin_ids = input("Enter admin Telegram IDs (comma separated): ").strip()
    if admin_ids:
        try:
            admin_list = [int(x.strip()) for x in admin_ids.split(',')]
            with open('bot.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = content.replace('ADMIN_IDS = [123456789]', f'ADMIN_IDS = {admin_list}')
            
            with open('bot.py', 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Admin IDs updated!")
        except:
            print("❌ Invalid admin IDs format. Please use comma-separated numbers.")
    
    print("\n" + "=" * 40)
    print("🎉 Setup Complete!")
    print("\nNext steps:")
    print("1. Test locally: python bot.py")
    print("2. Deploy to Render:")
    print("   - Push to GitHub")
    print("   - Connect to Render")
    print("   - Set BOT_TOKEN environment variable")
    print("   - Deploy!")
    
    # Create .env file
    if bot_token:
        with open('.env', 'w') as f:
            f.write(f'BOT_TOKEN={bot_token}\n')
        print("\n✅ .env file created!")

if __name__ == "__main__":
    setup_bot() 