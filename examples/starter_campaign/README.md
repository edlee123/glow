# @starter_campaign - Campaign Generation Guide

This guide explains how to use Glow to generate creative concepts and assets for the @starter_campaign. The process involves two main steps:

1. Generating concepts from the campaign brief
2. Generating assets from the concepts

## Prerequisites

Before you begin, you'll need:

- Python 3.8 or higher
- Glow installed (see [main project README.md](../../README.md) for installation instructions)
- An OpenRouter API key

## Setting up the OpenRouter API Key

The application uses OpenRouter to access AI models like Google Gemini for image generation. You need to set up an API key:

1. Visit [OpenRouter](https://openrouter.ai/keys) to create an account and obtain an API key
2. Set the API key as an environment variable:

   **For Bash/Zsh (Linux/Mac):**
   ```bash
   export OPENROUTER_API_KEY=your_api_key_here
   ```

   **For Windows Command Prompt:**
   ```cmd
   set OPENROUTER_API_KEY=your_api_key_here
   ```

   **For Windows PowerShell:**
   ```powershell
   $env:OPENROUTER_API_KEY="your_api_key_here"
   ```

3. To make this permanent, add the export/set command to your shell profile.

You can verify the API key is set correctly by running one of the example curl commands in the terminal:

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -d '{
  "model": "google/gemini-pro-1.5",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Hello, world!"
        }
      ]
    }
  ]
}'
```

## Step 1: Generating Concepts

The first step is to generate concept configurations from the campaign brief. These concepts will define the creative direction for each product in your campaign.

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
glow campaign2concept examples/starter_campaign/campaign_brief_test.json -f campaign
```

Using the above command without the -f argument will by default generate concept for 1_1 aspect.

Generate concepts with specific formats:
```bash
glow campaign2concept examples/starter_campaign/campaign_brief_test.json -f 1_1,16_9
```

Generate a specific number of concepts:
```bash
glow campaign2concept examples/starter_campaign/campaign_brief_test.json -n 5
```

### Output

The command will create a directory for each product in the campaign brief, containing JSON files for each concept in the specified formats. For example:

```
examples/starter_campaign/
├── energy_drink_x/
│   ├── concept1_1_1.json
│   ├── concept2_1_1.json
│   ├── concept1_9_16.json
│   └── concept2_9_16.json
└── relaxation_tea/
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
glow concept2asset examples/starter_campaign/relaxation_tea/concept1_1_1.json
```

Generate assets for all concepts in a product directory:
```bash
glow concept2asset "examples/starter_campaign/relaxation_tea/concept*.json"
```

Generate assets for all concepts in the campaign:
```bash
glow concept2asset "examples/starter_campaign/**/*.json"
```

> **IMPORTANT**: When using the `**` recursive glob pattern, you **must** enclose the pattern in quotes to prevent shell expansion. For example: `"examples/starter_campaign/**/concept7*.json"`. Without quotes, the shell will expand the pattern before passing it to the command, which can cause errors.

Generate a single image for concept7 files:
```bash
glow concept2asset "examples/starter_campaign/**/concept7*.json" -n1
```

Generate multiple images per concept:
```bash
glow concept2asset examples/starter_campaign/relaxation_tea/concept1_1_1.json --num-images 5
```

### Output

The command will create a subfolder based on the aspect ratio (e.g., 1_1, 9_16) in the concept file's directory, containing the generated images:

```
examples/starter_campaign/
├── energy_drink_x/
│   ├── concept1_1_1.json
│   ├── concept2_1_1.json
│   └── 1_1/
│       ├── energy_drink_x_concept1_img1_a1b2c3d4.png
│       ├── energy_drink_x_concept1_img1_a1b2c3d4_with_logo.png
│       ├── energy_drink_x_concept1_img1_a1b2c3d4_with_logo_with_text.png
│       ├── energy_drink_x_concept2_img1_e5f6g7h8.png
│       ├── energy_drink_x_concept2_img1_e5f6g7h8_with_logo.png
│       └── energy_drink_x_concept2_img1_e5f6g7h8_with_logo_with_text.png
└── ...
```

## Campaign Brief Schema

The campaign brief is a JSON file that defines the campaign details, products, target audience, and output requirements. Here's an explanation of the key sections:

### Basic Structure

```json
{
  "campaign_id": "starter_campaign_2025",
  "products": [...],
  "target_market": {...},
  "target_audience": {...},
  "campaign_message": {...},
  "visual_direction": {...},
  "brand_guidelines": {...},
  "output_requirements": {...}
}
```

### Key Sections

- **campaign_id**: Unique identifier for the campaign
- **products**: Array of products in the campaign, each with:
  - **name**: Product name
  - **description**: Product description
  - **target_emotions**: Emotions the product should evoke
  - **target_audience**: Specific audience for this product
- **target_market**: Geographic and language information
- **target_audience**: Overall campaign audience demographics and interests
- **campaign_message**: Primary, secondary, and call-to-action messages
- **visual_direction**: Style, color palette, and mood guidance
- **brand_guidelines**: Logo placement, typography, and restrictions
- **output_requirements**: Formats and number of concepts to generate

## Seasonal Campaign Prompting

You can create seasonal campaigns by adding a `seasonal_promotion` section to your campaign brief:

```json
"seasonal_promotion": {
  "season": "Winter Holidays",
  "theme": "Cozy Winter Wonderland",
  "start_date": "2025-11-01",
  "end_date": "2026-01-15",
  "special_elements": ["snow", "holiday lights", "fireplaces", "cozy sweaters", "pine trees"],
  "seasonal_colors": ["#8B0000", "#006400", "#FFFFFF", "#C0C0C0", "#FFD700"],
  "seasonal_messaging": {
    "tagline": "Sip the season",
    "greetings": "Happy Holidays!"
  }
}
```

This section provides seasonal context that influences the generated concepts:

- **season**: The specific season or holiday period
- **theme**: The creative theme for the season
- **start_date/end_date**: Campaign duration
- **special_elements**: Seasonal visual elements to include
- **seasonal_colors**: Color palette specific to the season
- **seasonal_messaging**: Special taglines and greetings

## Additional Commands

### Check Language Compliance

```bash
glow reviewlanguage <concept_file_pattern> [options]
```

You can pipe the output to a file:
```bash
glow reviewlanguage "examples/starter_campaign/**/*.json" > language_report.txt
```

### Check Logo Presence in Images

```bash
glow reviewlogo <asset_path> [--logo-path <logo_path> | --logo-url <logo_url> | --campaign-file <campaign_file>] [options]
```

You can check if a logo is present in images and get a confidence score:
```bash
# Using a campaign brief file that contains logo information
glow reviewlogo "examples/starter_campaign/**/*.png" --campaign-file examples/starter_campaign/campaign_brief_test.json

# Using a local logo file
glow reviewlogo "examples/starter_campaign/**/*.png" --logo-path examples/starter_campaign/logo.png

# Using a logo URL
glow reviewlogo "examples/starter_campaign/**/*.png" --logo-url https://example.com/logo.png

# Adjusting the matching threshold (0.0 to 1.0, higher is more strict)
glow reviewlogo "examples/starter_campaign/**/*.png" --logo-path examples/starter_campaign/logo.png --threshold 0.7

# Saving the report to a file
glow reviewlogo "examples/starter_campaign/**/*.png" --campaign-file examples/starter_campaign/campaign_brief_test.json --output logo_report.txt
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
glow textapply --concept-file examples/starter_campaign/energy_drink_x/concept1_1_1.json examples/starter_campaign/energy_drink_x/1_1/energy_drink_x_concept1_img1_58c468a1.png custom_text_overlay.png

# Method 2: Apply text directly with inline configuration (no concept file needed)
glow textapply examples/starter_campaign/energy_drink_x/1_1/energy_drink_x_concept1_img1_58c468a1.png custom_text_overlay.png --text-config '{"primary_text": "NEW PROMO!", "text_position": "center", "font": "Arial", "color": "#FF0000", "shadow": true}'

# Apply custom text with a different position and color
glow textapply examples/starter_campaign/energy_drink_x/1_1/energy_drink_x_concept1_img1_58c468a1.png --text-config '{"primary_text": "Limited Time Offer", "text_position": "top", "color": "#00FF00"}'

# Combine both methods (inline config takes precedence)
glow textapply --concept-file examples/starter_campaign/energy_drink_x/concept1_1_1.json examples/starter_campaign/energy_drink_x/1_1/energy_drink_x_concept1_img1_58c468a1.png --text-config '{"primary_text": "OVERRIDE TEXT"}'
```

This command is useful when you want to:
- Apply text overlays to images without needing a concept file
- Modify the text_overlay_config in the concept file and rerender the asset
- Experiment with different text overlays on the same image
- Create variations of text placement and styling
- Quickly test different text messages without modifying the concept file
- Apply seasonal or promotional text overlays to existing assets


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
glow newasset "A futuristic sports car on a mountain road" ./car_image.png

# Generate a landscape image
glow newasset "A serene beach at sunset" ./beach.png --aspect-ratio 16:9

# Generate an image with a negative prompt
glow newasset "A modern office workspace" ./office.png --negative-prompt "people, clutter, dark lighting"