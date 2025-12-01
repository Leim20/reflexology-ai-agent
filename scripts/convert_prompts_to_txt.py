"""
Convert prompts.yaml to individual .txt files
Extracts each prompt type to a separate text file
"""
import yaml
import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def convert_prompts():
    """Extract prompts from YAML to TXT files"""

    yaml_file = "config/prompts.yaml"
    output_dir = "config/prompts"

    print("="*80)
    print("CONVERTING PROMPTS FROM YAML TO TXT")
    print("="*80)
    print()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"✓ Created directory: {output_dir}")

    # Load YAML
    print(f"✓ Loading {yaml_file}...")
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    prompts = data["prompts"]
    print(f"✓ Found {len(prompts)} prompt types")
    print()

    # Extract each prompt to .txt file
    for prompt_name, prompt_content in prompts.items():
        output_file = os.path.join(output_dir, f"{prompt_name}.txt")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(prompt_content)

        print(f"✓ Created: {output_file}")
        print(f"  Length: {len(prompt_content):,} characters")

    print()
    print("="*80)
    print("✅ CONVERSION COMPLETE!")
    print("="*80)
    print()
    print("Created files:")
    for prompt_name in prompts.keys():
        print(f"  - config/prompts/{prompt_name}.txt")
    print()
    print("Next steps:")
    print("1. Verify the .txt files are correct")
    print("2. Update config_loader.py to read from .txt files")
    print("3. Test the application")

if __name__ == "__main__":
    convert_prompts()
