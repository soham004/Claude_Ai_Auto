import os
import json
import shutil

def create_config_helper():
    """Main function to create or update a configuration file"""
    print("\n" + "=" * 80)
    print(" Claude AI Automation Config Creator ".center(80, "="))
    print("=" * 80)
    
    # Check if accounts directory exists
    if not os.path.exists("accounts"):
        print("Creating accounts directory...")
        os.makedirs("accounts")
    
    # Get existing accounts
    accounts = [f for f in os.listdir("accounts") if os.path.isdir(os.path.join("accounts", f))]
    
    # Present options
    print("\n📝 What would you like to do?")
    print("1. Create config for a new account")
    if accounts:
        print("2. Update config for an existing account")
    
    choice = input("\nEnter your choice (1" + ("/2" if accounts else "") + "): ")
    
    if choice == "1":
        account_name = create_new_account()
    elif choice == "2" and accounts:
        account_name = select_account(accounts)
    else:
        print("Invalid choice. Please try again.")
        return
    
    # Create the config file for the selected account
    create_config_file(account_name)
    
    print("\n✅ Config file created successfully!")
    print(f"Location: accounts/{account_name}/config.json")
    print("\nYou can now run the main script to use this configuration.")

def create_new_account():
    """Create a new account directory"""
    print("\n🆕 Creating a new account")
    account_name = input("Enter account name (e.g., 'my_claude_account'): ").strip()
    
    # Validate account name
    if not account_name or any(c in account_name for c in '\\/:*?"<>|'):
        print("Invalid account name. Please avoid special characters.")
        return create_new_account()
    
    account_path = os.path.join("accounts", account_name)
    
    if os.path.exists(account_path):
        print(f"Account '{account_name}' already exists!")
        overwrite = input("Do you want to overwrite it? (y/n): ")
        if overwrite.lower() != 'y':
            return create_new_account()
    
    # Create account directory
    os.makedirs(account_path, exist_ok=True)
    
    return account_name

def select_account(accounts):
    """Select an existing account"""
    print("\n📂 Select an account to update its config:")
    for i, account in enumerate(accounts):
        print(f"{i+1}. {account}")
    
    try:
        choice = int(input("\nEnter account number: "))
        if 1 <= choice <= len(accounts):
            return accounts[choice-1]
    except ValueError:
        pass
    
    print("Invalid selection. Please try again.")
    return select_account(accounts)

def get_multiline_input(prompt=""):
    """Get multi-line input from user"""
    print(prompt)
    print("(Type your text. Press Enter twice on an empty line when finished)")
    
    lines = []
    empty_line = False
    
    while True:
        line = input()
        if not line:
            if empty_line:  # Second empty line
                break
            empty_line = True
        else:
            empty_line = False
            lines.append(line)
    
    return "\n".join(lines)

def create_config_file(account_name):
    """Create a config.json file with user input"""
    print("\n" + "-" * 80)
    print(f" Creating config for '{account_name}' ".center(80, "-"))
    print("-" * 80)
    
    config = {}
    
    # Check if config already exists and offer to load it as a starting point
    config_path = os.path.join("accounts", account_name, "config.json")
    if os.path.exists(config_path):
        print(f"\nFound existing config for '{account_name}'.")
        load_existing = input("Do you want to use it as a starting point? (y/n): ")
        if load_existing.lower() == 'y':
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                print("Existing config loaded. You can update the values as needed.")
            except json.JSONDecodeError:
                print("Error reading existing config. Starting fresh.")
    
    # Project link
    print("\n" + "-" * 40)
    print("🔗 PROJECT LINK")
    print("-" * 40)
    print("This is the URL to your Claude.ai project/chat.")
    print("Example: https://claude.ai/chat/12345abc-1234-5678-90ab-1234567890ab")
    default = config.get("project_link", "")
    if default:
        print(f"Current value: {default}")
    config["project_link"] = input(f"Enter project link{' (press Enter to keep current)' if default else ''}: ").strip() or default
    
    # Number of chapters
    print("\n" + "-" * 40)
    print("📚 NUMBER OF CHAPTERS")
    print("-" * 40)
    print("Enter how many chapters you want to generate.")
    print("Typical sleep stories or similar content have 12 chapters.")
    current_chapters = len(config.get("generation_prompts", []))
    if current_chapters:
        print(f"Current chapters: {current_chapters}")
    
    try:
        num_chapters_input = input(f"Number of chapters{' (press Enter to keep current)' if current_chapters else ''}: ")
        if num_chapters_input:
            num_chapters = int(num_chapters_input)
            if num_chapters <= 0:
                raise ValueError
        elif current_chapters:
            num_chapters = current_chapters
        else:
            num_chapters = 12
            print(f"Using default: {num_chapters} chapters")
    except ValueError:
        num_chapters = 12 if not current_chapters else current_chapters
        print(f"Invalid input. Using {'default' if not current_chapters else 'current'}: {num_chapters} chapters")
    
    # Text to be replaced
    print("\n" + "-" * 40)
    print("🔄 TEXT PLACEHOLDER")
    print("-" * 40)
    print("This is the text in your initial prompt that will be replaced by the video number.")
    print("The script will automatically replace this text with the video number during execution.")
    print("Example: VIDEO_NUMBER")
    print("\nExample of replacement:")
    print("- Initial prompt with placeholder: 'Write a sleep story for VIDEO_NUMBER about dreams.'")
    print("- When video number is '42': 'Write a sleep story for 42 about dreams.'")
    default = config.get("text_to_be_replaced_by_video_number", "")
    if default:
        print(f"\nCurrent value: {default}")
    text_to_replace = input(f"Enter text placeholder{' (press Enter to keep current)' if default else ''}: ").strip()
    if not text_to_replace:
        text_to_replace = default or "VIDEO_NUMBER"
        if not default:
            print(f"Using default placeholder: {text_to_replace}")
    config["text_to_be_replaced_by_video_number"] = text_to_replace
    
    # Initial prompt
    print("\n" + "-" * 40)
    print("🏁 INITIAL PROMPT")
    print("-" * 40)
    print("This is the first prompt sent to Claude. Include the placeholder text where the video number should appear.")
    print(f"Example: Create a sleep story for Video {text_to_replace} about the nine hells of D&D lore.")
    print("The initial prompt sets up the entire generation process, so be specific about what you want.")
    print(f"\nMake sure to include the placeholder text '{text_to_replace}' somewhere in your prompt.")
    
    default = config.get("initial_prompt", "")
    if default:
        print("\nCurrent initial prompt:")
        print("-" * 40)
        print(default)
        print("-" * 40)
        # Show example of replacement for the current prompt
        if text_to_replace in default:
            replaced_example = default.replace(text_to_replace, "42")
            print(f"Example with video number 42:")
            print("-" * 40)
            print(replaced_example)
            print("-" * 40)
        keep_current = input("Do you want to update this prompt? (y/n, press Enter to keep current): ").strip().lower()
        if keep_current == 'y':
            config["initial_prompt"] = get_multiline_input("\nEnter your new initial prompt:")
        else:
            config["initial_prompt"] = default
            print("Keeping current prompt.")
    else:
        config["initial_prompt"] = get_multiline_input("\nEnter your initial prompt:")
    
    if not config["initial_prompt"]:
        print("Initial prompt cannot be empty!")
        return create_config_file(account_name)
    
    # Check if placeholder is in the initial prompt
    if text_to_replace not in config["initial_prompt"]:
        print(f"\n⚠️ Warning: Placeholder '{text_to_replace}' not found in the initial prompt.")
        print("The video number won't be inserted correctly.")
        print(f"Please add '{text_to_replace}' somewhere in your prompt where the video number should appear.")
        fix = input("Do you want to update your placeholder or initial prompt? (y/n): ")
        if fix.lower() == 'y':
            return create_config_file(account_name)
    
    # Generation prompts
    print("\n" + "-" * 40)
    print("📝 GENERATION PROMPTS")
    print("-" * 40)
    print(f"You'll need to enter {num_chapters} prompts, one for each chapter.")
    print("These prompts will be sent to Claude sequentially after the initial prompt.")
    print("Be specific about what you want in each chapter.")
    
    current_prompts = config.get("generation_prompts", [])
    config["generation_prompts"] = []
    
    for i in range(num_chapters):
        print(f"\n--- CHAPTER {i+1} PROMPT ---")
        default = current_prompts[i] if i < len(current_prompts) else ""
        
        if default:
            print("\nCurrent prompt:")
            print("-" * 40)
            print(default)
            print("-" * 40)
            keep_current = input("Do you want to update this prompt? (y/n, press Enter to keep current): ").strip().lower()
            if keep_current == 'y':
                chapter_prompt = get_multiline_input(f"\nEnter prompt for Chapter {i+1}:")
                if not chapter_prompt:
                    print(f"Empty input - keeping current prompt for Chapter {i+1}")
                    chapter_prompt = default
            else:
                chapter_prompt = default
                print("Keeping current prompt.")
        else:
            print(f"\nEnter prompt for Chapter {i+1}:")
            if i == 0:
                print("Example: Write Chapter 1 of the sleep story about the infernal hierarchy of the Nine Hells.")
            elif i == num_chapters - 1:
                print("Example: Write the final chapter (Chapter 12) that concludes the sleep story.")
            else:
                print(f"Example: Write Chapter {i+1} about [specific topic related to your story].")
            
            chapter_prompt = get_multiline_input()
            
            if not chapter_prompt:
                print(f"Using default prompt for Chapter {i+1}")
                chapter_prompt = f"Write Chapter {i+1}"
        
        config["generation_prompts"].append(chapter_prompt)
    
    # Video numbers
    print("\n" + "-" * 40)
    print("🎬 VIDEO NUMBERS")
    print("-" * 40)
    print("Enter the video numbers to generate content for (comma-separated).")
    print("These numbers will replace the placeholder in your initial prompt.")
    print("Example: 1,2,3")
    print("Leave empty to enter the video number when running the main script.")
    
    default = config.get("video_numbers", [])
    if default:
        print(f"Current video numbers: {', '.join(default)}")
    
    video_numbers_input = input(f"Enter video numbers{' (press Enter to keep current)' if default else ''}: ").strip()
    if video_numbers_input:
        config["video_numbers"] = [num.strip() for num in video_numbers_input.split(",")]
    elif default:
        config["video_numbers"] = default
    else:
        config["video_numbers"] = []
        print("No video numbers specified. You'll be prompted during execution.")
    
    # Review config before saving
    print("\n" + "=" * 60)
    print(" CONFIGURATION REVIEW ".center(60, "="))
    print("=" * 60)
    print(f"Account: {account_name}")
    print(f"Project Link: {config['project_link']}")
    print(f"Text Placeholder: {config['text_to_be_replaced_by_video_number']}")
    print(f"Initial Prompt: {config['initial_prompt'][:50]}..." if len(config['initial_prompt']) > 50 else f"Initial Prompt: {config['initial_prompt']}")
    print(f"Number of Chapters: {len(config['generation_prompts'])}")
    print(f"Video Numbers: {', '.join(config['video_numbers']) if config['video_numbers'] else 'To be entered during execution'}")
    
    save = input("\nSave this configuration? (y/n): ")
    if save.lower() != 'y':
        print("Configuration not saved.")
        retry = input("Do you want to start over? (y/n): ")
        if retry.lower() == 'y':
            return create_config_file(account_name)
        return
    
    # Create a backup of the existing config if it exists
    if os.path.exists(config_path):
        backup_path = config_path + ".backup"
        shutil.copy2(config_path, backup_path)
        print(f"Backup of previous config saved to: {backup_path}")
    
    # Save config
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        print("Configuration saved successfully!")
    except Exception as e:
        print(f"Error saving configuration: {e}")
        if os.path.exists(backup_path):
            print("Restoring from backup...")
            shutil.copy2(backup_path, config_path)

if __name__ == "__main__":
    try:
        create_config_helper()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user. Exiting...")
    except Exception as e:
        print(f"\n\nAn error occurred: {e}")
        print("Please try again.")