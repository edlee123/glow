![Glow Logo]()

# Glow - Creative Campaign Automation

Glow up your social campaigns! Glow is a Python package designed to automate the generation of creative assets for social ad campaigns. Included are example campaigns for global consumer goods companies that need to launch hundreds of localized social ad campaigns monthly.

## Features

- Uses LLM to generate multiple creative concepts compliant with campaign briefs, brand guidelines, legal checks (prohibited wording).
- Accept input assets from local storage or URL and incorporate the style and composition into generated content
- Generate new assets using AI models like Google Gemini 2.5 Flash Image via OpenRouter.ai (with future Adobe Firefly integration)
- Produce creatives in multiple aspect ratios (1:1, 9:16, 16:9) for different social platforms.
- Display concept messages on the final assets.
- Save generated outputs and their configuration in an organized folder structure
- Adapter architecture provides flexiblity in concept2asset pipelines to incorporate APIs from different providers e.g. text-to-image models, Firefly, or photo-editing like PhotoShop . 

### PLUS Nice to Have Features (from requirements)

- ✅ **Brand compliance**:
  - Campaign briefs include brand guidelines with color palette, typography, and prohibited content. The `campaign2concept` command will have an LLM generate concepts to adhere to campaign brand guidelines.
  - ✅ Logo detection: OpenCV-based logo detection to verify logo presence in generated assets
    - Command-line tool: `glow reviewlogo` to check for logo presence.
  - ✅ **Legal content checks**:
    - Campaign briefs include "do_not_use" section to specify prohibited words and imagery from the outset from `campaign2concept`
    - And as an added guard the new `reviewlanguage` command checks concept files for prohibited words and phrases post concept generation.
  - ✅ **Logging and reporting of results**:
    - Comprehensive logging system captures all steps of the generation process
    - Each concept includes detailed logs stored in .log files
    - Metrics for asset generation.
    - Structured output organization for easy review and analysis

## How It Works: The Creative Automation Pipeline

Glow implements a two-stage creative automation pipeline:

### Stage 1: Campaign to Concept (campaign2concept)

The `campaign2concept` process transforms a campaign brief into multiple creative concepts:

1. **Input**: A JSON campaign brief containing:
   - Campaign details (name, objectives, messaging)
   - Product information
   - Target audience data
   - Brand guidelines and visual direction
   - Reference product and brand images used by AI to generate new assets.
   - Legal restrictions ("do_not_use" words/imagery)

2. **Processing**:
   - The campaign brief is validated against a schema
   - LLM processing generates multiple creative concepts. Each concept file represents an entire processing pipeline to generate the base image of an asset, and any post image editing like text overlay, or image editing.
   - Each concept file includes the generated image prompt for text-to-image model e.g., Google Gemini 2.5 Flash Image or GPT Image Mini.

3. **Output**: Multiple concept pipeline files (json), each containing:
   - Complete pipeline definition for asset generation including format / aspect ratio.
   - Image generation prompts and model settings
   - API parameters for image generation services
   - Text overlay specifications and styling rules
   - Image processing instructions
   - Output organization directives
   - Future: localization settings and language configurations to localize concept pipelines.
   
### Stage 2: Concept to Asset (concept2asset)

The `concept2asset` process transforms a concept pipeline json file into final creative assets:

1. **Input**: A concept configuration JSON file

2. **Processing**:
   - Image generation by default uses Google Gemini 2.5 Flash Image (Nano Banana) via OpenRouter.ai
   - Text processing and styling, reference assets if provided.
   - Image editing (applying text overlays, adjustments)
   - Output organization and metadata creation in desired formats.

3. **Output**: Final creative assets in the specified format:
   - Base image (raw generated image)
   - Image with text overlay
   - Image with logo overlay
   - Adjusted image (with color/contrast adjustments)
   - Localized versions (if applicable)
   - Logs and metadata

## Installation

### Requirements

- Python 3.8+
- OpenRouter.ai API key (for Google Gemini 2.5 Flash Image access)

### Setup

#### 1. Clone and install the project.

```bash
# Clone the repository
git clone https://github.com/edlee123/glow.git
cd glow

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package and dependencies
pip install -e .

#### 2. Get an OpenRouter API Key

To use Glow with Google Gemini 2.5 Flash Image, you'll need an OpenRouter API key:

1. Visit [OpenRouter.ai](https://openrouter.ai/) and create an account
2. After logging in, navigate to the API Keys section
3. Create a new API key with appropriate rate limits for your usage, and set up credit card.
4. Copy your API key for use in the next step

OpenRouter provides access to various AI models including Google Gemini 2.5 Flash Image which is used by Glow for image generation.

#### 3. Set the OpenRouter API Key

Set your OpenRouter API key as an environment variable:

```bash
# If Linux/macOS
export OPENROUTER_API_KEY="your_api_key_here"

# If Windows (Command Prompt)
set OPENROUTER_API_KEY=your_api_key_here

# If Windows (PowerShell)
$env:OPENROUTER_API_KEY="your_api_key_here"
```

## Example Campaigns

Glow includes two example campaigns to help you get started:

### 1. [Starter Campaign](examples/starter_campaign/README.md)

The starter campaign provides a basic introduction to:
- Campaign brief schema and structure
- Using the `campaign2concept` command to use AI to generate creative concept files for multiple products and aspect ratios. This step generates concept pipeline files that define the entire asset generation for each concept.
- Using the `concept2asset` to process concept pipeline files to generate  visual assets.
- Using the `reviewlanguage` and `reviewlogo` commands for compliance checks.

This is the perfect starting point for new users to understand Glow's workflow.

### 2. [D-Pop Campaign](examples/dpop_campaign/campaign_brief_example.json)

The D-Pop campaign demonstrates more advanced features:
- Using product-specific reference images to guide AI-generated assets.
- Creating concepts for diverse target audiences (teens and parents).
- Incorporating visual brand assets and guidelines into the generation process with style and composition strength.

This example shows how Glow can handle complex, multi-product campaigns with more specific visual requirements.

## Usage

### Command-Line Interface

Glow provides the following commands:

#### 1. Generate concept configurations from a campaign brief

```bash
glow campaign2concept ./campaigns/summer2025/brief.json ./campaigns/summer2025/output
```

Options:
- `-n`: Number of concepts to generate (default: 3)
- `-format`: Output format (default: 1_1, options: 1_1, 9_16, 16_9)

The above create entire concept pipeline files to generate assets. They can
be reviewed, edited, and retained for generating assets.

#### 2. Generate assets from a concept configuration

```bash
glow concept2asset ./campaigns/summer2025/output/tropical_breeze/1_1/concept1/concept_config.json
```

#### 3. Check concept files for language compliance issues

```bash
glow reviewlanguage <concept_file_pattern> [options]
```

Options:
- `--output`, `-o`: Output file to save the report to
- `--custom-words`, `-c`: Custom file containing prohibited words

This command checks concept files for prohibited words or phrases that may violate legal or compliance requirements. It can check a single file or multiple files using glob patterns:

```bash
# Check a single file
glow reviewlanguage examples/dpop_campaign/d-pop_golf_collection/concept1_1_1.json

# Check multiple files using a glob pattern
glow reviewlanguage "examples/dpop_campaign/*/concept*.json"

# Check files recursively using the ** pattern
glow reviewlanguage "examples/seasonal_campaign/**/*.json"

# Save the report to a file
glow reviewlanguage "examples/dpop_campaign/*/concept*.json" --output report.txt

# Use a custom list of prohibited words
glow reviewlanguage "examples/dpop_campaign/*/concept*.json" --custom-words prohibited_words.txt

# Pipe output to a file
glow reviewlanguage "examples/starter_campaign/**/*.json" > language_report.txt
```

#### 4. Check logo presence in images

```bash
glow reviewlogo <asset_path> [--logo-path <logo_path> | --logo-url <logo_url> | --campaign-file <campaign_file>] [options]
```

Options:
- `--logo-path`: Path to a local logo image file
- `--logo-url`: URL to a remote logo image
- `--campaign-file`: Path to a campaign brief JSON file containing logo information
- `--threshold`: Matching threshold (0.0 to 1.0, higher is more strict, default: 0.7)
- `--output`, `-o`: Output file to save the report to
- `--save-marked`: Directory to save images with marked logo locations

This command checks if a logo is present in image assets and provides a confidence score (0-100):

```bash
# Using a campaign brief file that contains logo information
glow reviewlogo "examples/starter_campaign/**/*.png" --campaign-file examples/starter_campaign/campaign_brief_test.json

# Using a local logo file
glow reviewlogo "examples/starter_campaign/**/*.png" --logo-path examples/starter_campaign/logo.png

# Using a logo URL
glow reviewlogo "examples/starter_campaign/**/*.png" --logo-url https://example.com/logo.png

# Adjusting the matching threshold
glow reviewlogo "examples/dpop_campaign/**/*.png" --logo-path examples/dpop_campaign/demon_pop_bottle.png --threshold 0.7

# Saving the report to a file
glow reviewlogo "examples/dpop_campaign/**/*.png" --logo-path examples/dpop_campaign/demon_pop_bottle.png --output logo_report.txt

# Saving marked images showing logo locations
glow reviewlogo "examples/dpop_campaign/**/*.png" --logo-path examples/dpop_campaign/demon_pop_bottle.png --save-marked ./marked_images
```


### Running Tests

```bash
pytest
```

## License

[Apache 2.0 License](LICENSE)
