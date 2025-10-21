# D-Pop Campaign - Generation Guide

This guide explains how to use Glow to generate creative concepts and assets for the D-Pop campaign. The process involves three main steps:

1. Generating concepts from the campaign brief
2. Generating assets from the concepts

## Motivating Examples

The D-Pop campaign demonstrates how Glow can generate creative assets for diverse target audiences with different product lines under the same brand umbrella.

### Example 1: Demon Pop - Teen-focused Energy Drink

From product reference:

<table>
  <tr>
    <td><img src="https://drive.google.com/uc?export=view&id=1HPEQMLPiyGGyutxz3-L4gFlDSVaSiZRE" width="200" alt="Demon Pop Bottle"></td>
    <td><img src="https://drive.google.com/uc?export=view&id=1Vwj46nE9mlVzTwW3YDfX8age8uaezyP6" width="200" alt="Reference image"></td>
  </tr>
</table>

To sample assets:

<table>
  <tr>
    <td><img src="https://drive.google.com/uc?export=view&id=1rfjQ8o-MWnlA8cNRLnsmo6lGRbSxrt1B" width="300" alt="Demon Pop Sample Asset 1"></td>
    <td><img src="https://drive.google.com/uc?export=view&id=13EyRnbkgzIkMIimAsbQ2DPDVNHAqQJS6" width="300" alt="Demon Pop Sample Asset 2"></td>
  </tr>
</table>

### Example 2: D-Pop Golf Collection - Parent-focused Fashion

From product reference to generated campaign asset:

<table>
  <tr>
    <td><img src="https://drive.google.com/uc?export=view&id=1vgxnE5O-VNbqX5pX4YuWrZs8iZ0MWep5" width="200" alt="Beach Shirt"></td>
    <td>
  </tr>
</table>

To sample assets:

<table>
  <tr>
    <td><img src="https://drive.google.com/uc?export=view&id=1PxOuyfsXgHl5mMQfNDjdWfaDdoePmhWk" width="300" alt="Golf Family Campaign 1"></td>
    <td><img src="https://drive.google.com/uc?export=view&id=1GQvXkvyKOxPerRpUYLNeCeFW7CQdUtMh" width="300" alt="Golf Family Campaign 2"></td>
  </tr>
</table>

## Prerequisites

Before you begin, you'll need:

- Python 3.8 or higher
- Glow installed
- An OpenRouter API key

For detailed installation instructions and API key setup (including verification), please refer to the [main project README.md](../../README.md#installation).

## Step 1: Setting up Reference Images

Before generating concepts, you need to set up the reference images specified in the campaign brief. These images guide the AI to generate assets with consistent style and composition.

### Using the Download Script

The `download_images.py` script automatically downloads the required reference images:

```bash
# Navigate to the dpop_campaign directory
cd examples/dpop_campaign

# Ensure you've sourced the venv from your installation in the main README.md
pip install requests

# Run the download script
python download_images.py
```

The script will download the following reference images:
- `demon_pop_bottle.png`: Purple bottle
- `Saja_Boys_-_Soda_Pop.png`: K-pop group with soda
- `beach_shirt.png`: Floral shirt

These images are used in the campaign brief to guide the AI in generating assets with consistent style and composition.

## Step 2: Generating Concepts

The next step is to generate concept configurations from the campaign brief. These concepts will define the creative direction for each product in your campaign.

### Command Syntax

```bash
glow campaign2concept <campaign_brief_path> [options]
```

### Options

- `-n, --num-concepts`: Number of concepts to generate (overrides value in campaign brief)
- `-f, --format`: Output format(s): 1_1, 9_16, 16_9, or "campaign" (uses formats defined in the campaign brief)
- `-o, --output-dir`: Output directory (default: same directory as campaign brief)
- `--model`: LLM model to use (default: anthropic/claude-haiku-4.5)
- `--log`: Enable detailed logging

### Example Commands

Generate concepts for ALL formats defined in the campaign brief:
```bash
glow campaign2concept examples/dpop_campaign/campaign_brief_example.json -f campaign
```

Using the above command without the -f argument will by default generate concept for 1_1 aspect.

Generate concepts with specific formats:
```bash
glow campaign2concept examples/dpop_campaign/campaign_brief_example.json -f 1_1,16_9
```

Generate a specific number of concepts:
```bash
glow campaign2concept examples/dpop_campaign/campaign_brief_example.json -n 5
```

### Output

The command will create a directory for each product in the campaign brief, containing JSON files for each concept in the specified formats. For example:

```
examples/dpop_campaign/
├── demon_pop/
│   ├── concept1_1_1.json
│   ├── concept2_1_1.json
│   ├── concept1_9_16.json
│   └── concept2_9_16.json
└── d-pop_golf_collection/
    ├── concept1_1_1.json
    ├── concept2_1_1.json
    ├── concept1_9_16.json
    └── concept2_9_16.json
```

## Step 2: Generating Assets

Once you have generated concept configurations, you can use them to generate visual assets.

### Command Syntax

```bash
glow concept2asset <concept_config_pattern> [options]
```

### Options

- `--output-dir, -o`: Output directory (default: same directory as each concept file)
- `--no-text`: Generate image without text overlay
- `--num-images, -n`: Number of images to generate (default: 3)
- `--recursive, -r`: Search subdirectories recursively

### Example Commands

Generate assets for a single concept:
```bash
glow concept2asset examples/dpop_campaign/demon_pop/concept1_1_1.json
```

Generate assets for all concepts in a product directory:
```bash
glow concept2asset "examples/dpop_campaign/demon_pop/concept*.json"
```

Generate assets for all concepts in the campaign:
```bash
glow concept2asset "examples/dpop_campaign/**/*.json"
```

> **IMPORTANT**: When using the `**` recursive glob pattern, you **must** enclose the pattern in quotes to prevent shell expansion. For example: `"examples/dpop_campaign/**/concept7*.json"`. Without quotes, the shell will expand the pattern before passing it to the command, which can cause errors.

Generate a single image for concept7 files:
```bash
glow concept2asset "examples/dpop_campaign/**/concept7*.json" -n1
```

Generate multiple images per concept:
```bash
glow concept2asset examples/dpop_campaign/demon_pop/concept1_1_1.json --num-images 5
```

### Output

The command will create a subfolder based on the aspect ratio (e.g., 1_1, 9_16) in the concept file's directory, containing the generated images:

```
examples/dpop_campaign/
├── demon_pop/
│   ├── concept1_1_1.json
│   ├── concept2_1_1.json
│   └── 1_1/
│       ├── demon_pop_concept1_img1_a1b2c3d4.png
│       ├── demon_pop_concept1_img1_a1b2c3d4_with_logo.png
│       ├── demon_pop_concept1_img1_a1b2c3d4_with_logo_with_text.png
│       ├── demon_pop_concept2_img1_e5f6g7h8.png
│       ├── demon_pop_concept2_img1_e5f6g7h8_with_logo.png
│       └── demon_pop_concept2_img1_e5f6g7h8_with_logo_with_text.png
└── ...
```

## Campaign Brief Schema

The D-Pop campaign brief demonstrates advanced features:

1. **Multi-product campaign** with different target audiences:
   - Demon Pop: Teen-focused energy drink targeting Gen Z (16-24)
   - D-Pop Golf Collection: Parent-focused fashion targeting adults (35-55)

2. **Reference images** with style and composition strength:
   - Product images guide the AI to generate assets with consistent style
   - Style and composition strength parameters control how closely the generated assets match the reference images

3. **Diverse visual directions** for different product lines:
   - Demon Pop: Bright, vibrant colors with an energetic mood
   - D-Pop Golf Collection: Photo-realistic professional golf aesthetic with a warm, inclusive mood

4. **Seasonal promotion** with a fall theme:
   - "You're My Soda Pop" theme for the fall season

## Additional Commands

### Check Language Compliance

```bash
glow reviewlanguage <concept_file_pattern> [options]
```

You can pipe the output to a file:
```bash
glow reviewlanguage "examples/dpop_campaign/**/*.json" > language_report.txt
```

### Check Logo Presence in Images

```bash
glow reviewlogo <asset_path> [--logo-path <logo_path> | --logo-url <logo_url> | --campaign-file <campaign_file>] [options]
```

You can check if a logo is present in images and get a confidence score:
```bash
# Using a campaign brief file that contains logo information
glow reviewlogo "examples/dpop_campaign/**/*.png" --campaign-file examples/dpop_campaign/campaign_brief_example.json

# Using a local logo file
glow reviewlogo "examples/dpop_campaign/**/*.png" --logo-path examples/dpop_campaign/logo.png

# Using a logo URL
glow reviewlogo "examples/dpop_campaign/**/*.png" --logo-url https://example.com/logo.png

# Adjusting the matching threshold (0.0 to 1.0, higher is more strict)
glow reviewlogo "examples/dpop_campaign/**/*.png" --logo-path examples/dpop_campaign/logo.png --threshold 0.7

# Saving the report to a file
glow reviewlogo "examples/dpop_campaign/**/*.png" --campaign-file examples/dpop_campaign/campaign_brief_example.json --output logo_report.txt
```

### Apply Text Overlay to Existing Images

```bash
glow textapply <image_path> [output_path] [options]
```

Options:
- `--concept-file, -c`: Path to the concept configuration JSON file
- `--text-config, -t`: JSON string with text overlay configuration (overrides config from concept file)

You must provide either a concept file or an inline text configuration.

Examples:
```bash
# Method 1: Apply text from a concept file to an image
glow textapply --concept-file examples/dpop_campaign/demon_pop/concept1_1_1.json examples/dpop_campaign/demon_pop/1_1/demon_pop_concept1_img1_58c468a1.png custom_text_overlay.png

# Method 2: Apply text directly with inline configuration (no concept file needed)
glow textapply examples/dpop_campaign/demon_pop/1_1/demon_pop_concept1_img1_58c468a1.png custom_text_overlay.png --text-config '{"primary_text": "NEW PROMO!", "text_position": "center", "font": "Arial", "color": "#FF0000", "shadow": true}'

# Apply custom text with a different position and color
glow textapply examples/dpop_campaign/demon_pop/1_1/demon_pop_concept1_img1_58c468a1.png --text-config '{"primary_text": "Limited Time Offer", "text_position": "top", "color": "#00FF00"}'

# Combine both methods (inline config takes precedence)
glow textapply --concept-file examples/dpop_campaign/demon_pop/concept1_1_1.json examples/dpop_campaign/demon_pop/1_1/demon_pop_concept1_img1_58c468a1.png --text-config '{"primary_text": "OVERRIDE TEXT"}'
```

### Generate a New Asset Directly

```bash
glow newasset <prompt> <output_path> [options]
```

Options:
- `--aspect-ratio`: Aspect ratio (e.g., "1:1", "16:9", "9:16"). Default: 1:1
- `--negative-prompt`: Negative prompt to guide what should not be in the image

Examples:
```bash
# Generate a square image
glow newasset "A K-pop group enjoying Demon Pop drinks" ./kpop_image.png

# Generate a landscape image
glow newasset "A family on a golf course wearing D-Pop Golf Collection shirts" ./golf_family.png --aspect-ratio 16:9

# Generate an image with a negative prompt
glow newasset "A vibrant Demon Pop advertisement" ./demon_pop_ad.png --negative-prompt "explicit demonic imagery, religious symbols, Halloween elements"