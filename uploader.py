import os
import sys
import asyncio
from telethon import TelegramClient, events, sync, errors
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
SESSION_NAME = 'telegram_uploader_session'

if not API_ID or not API_HASH or not PHONE_NUMBER:
    print("Error: API_ID, API_HASH, and PHONE_NUMBER must be set in the .env file or environment variables.")
    sys.exit(1)

async def upload_file(channel_username, file_path, caption=None):
    """
    Uploads a file to a Telegram channel.

    Args:
        channel_username (str): The username or ID of the channel.
        file_path (str): The path to the file to upload.
        caption (str, optional): Caption for the file.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    print(f"Connecting to Telegram...")
    client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH)
    
    # Start the client with phone number for user auth
    await client.start(phone=PHONE_NUMBER)

    async with client:
        # Resolve the entity first
        try:
            # Check if it's an ID (integer or string resembling integer)
            if channel_username.lstrip('-').isdigit():
                 entity_input = int(channel_username)
            else:
                 entity_input = channel_username
            
            entity = await client.get_entity(entity_input)
            print(f"Resolved entity: {entity.title} (ID: {entity.id})")
        except ValueError:
            print(f"Error: Could not find entity '{channel_username}'. Ensure you are subscribed or have sent a message to it.")
            return
        except Exception as e:
            print(f"Error resolving entity: {e}")
            return

        print(f"Uploading {file_path} to {entity.title}...")
        
        # progress_callback to show upload progress
        def progress_callback(current, total):
            print(f"Uploaded: {current / total * 100:.1f}%", end='\r')

        try:
            await client.send_file(
                entity,
                file_path,
                caption=caption,
                progress_callback=progress_callback
            )
            print(f"\nUpload complete!")
        
        except errors.FloodWaitError as e:
            print(f"\nRate limit exceeded. Waiting for {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            # Retry once RECURSIVELY (simple retry logic)
            print("Retrying upload...")
            await client.send_file(
                entity,
                file_path,
                caption=caption,
                progress_callback=progress_callback
            )
            print(f"\nUpload complete!")

        except errors.RPCError as e:
             print(f"\nTelegram RPC Error: {e} (Code: {e.code})")
             if "Too many requests" in str(e):
                 print("Hint: This might be a temporary server-side limit. Try again later.")

        except Exception as e:
            print(f"\nError uploading file: {type(e).__name__}: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python uploader.py <channel_username> <file_path> [caption]")
        sys.exit(1)

    channel = sys.argv[1]
    file = sys.argv[2]
    capt = sys.argv[3] if len(sys.argv) > 3 else None

    asyncio.run(upload_file(channel, file, capt))
