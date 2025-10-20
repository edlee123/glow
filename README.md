![Glow Logo]()

# Glow - AI to Scale Your Social Media Campaigns

Glow up your social campaigns!  Creating high-quality, brand-compliant assets for every product, in every format, for every market is a massive undertaking. Marketing teams struggle with maintaining brand consistency across hundreds of products, concepts, assets, formats, and meanwhile adapt campaigns for different markets and languages. It's no small feet to meet tight deadlines with limited creative resources, while ensuring legal compliance in the fast moving world of social media.

Glow is a Python package designed to use AI to automate the generation of creative concepts and assets for social ad campaigns to make things a snap. 

Included are example campaigns for global consumer goods companies that need to launch hundreds of social ad campaigns monthly.

## Features

- Uses LLMs to generate multiple creative concepts compliant with campaign briefs, brand guidelines, and legal requirements like prohibited wording
- Generates new assets using AI models like Google Gemini 2.5 Flash Image from OpenRouter.ai, with flexible pipeline architecture to add other APIs like Adobe Firefly or Adobe Photoshop APIs for post-processing.
- Accepts input assets from local storage or URL using AI to incorporate the style and composition into new AI generated assets.
- Produces creatives in multiple aspect ratios (1:1, 9:16, 16:9) for different social platforms.
- Displays concept messages on the final assets.
- Saves generated outputs and their configuration in an organized folder structure

### PLUS Nice to Have Features

- ✅ **Brand compliance**:
  - Campaign briefs include brand guidelines with color palette, typography, and prohibited content. The `glow campaign2concept` command will have an LLM generate concepts to adhere to campaign brand guidelines.
  - ✅ Logo detection: OpenCV-based logo detection to verify logo presence in generated assets
    - Command-line tool: `glow reviewlogo` to check for logo presence.
  - ✅ **Legal content checks**:
    - A new additional guard with `glow reviewlanguage` to check concept files for prohibited words and phrases post concept generation.
  - ✅ **Logging and reporting of results**:
    - Comprehensive logging system captures all steps of the generation process
    - Each concept includes detailed logs stored in .log files
    - Metrics for asset generation.
    - Structured output organization for easy review and analysis

## How It Works

Glow implements a two-stage creative automation pipeline:

### Stage 1: Campaign to Concept (campaign2concept)

The `glow campaign2concept` automates the creation of multiple creative concepts from a campaign brief:

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
   - Output organization
   - Future: localization settings and language configurations to localize concept pipelines.
   
### Stage 2: Concept to Asset (concept2asset)

The `glow concept2asset` process takes a concept pipeline json file and processes it into final creative assets:

1. **Input**: A concept pipeline JSON file

2. **Processing**:
   - Image generation by default uses Google Gemini 2.5 Flash Image (Nano Banana) via OpenRouter.ai.
   - Text processing and styling, reference assets if provided currently with Pillow. Other image processors or APIs can be added.
   - Output organization in desired formats.

3. **Output**: Final creative assets in the specified format:
   - Base image (raw generated image)
   - Image with text overlay
   - Image with logo overlay
   - Adjusted image (with color/contrast adjustments)
   - Logs and metadata in metrics.log and glow.log

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
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package and dependencies
pip install -e .
```

#### 2. Get an OpenRouter API Key

To use Glow with Google Gemini 2.5 Flash Image, you'll need an OpenRouter API key:

   i. Visit [OpenRouter.ai](https://openrouter.ai/) and create an account

   ii. After logging in, navigate to the API Keys section

   iii. Create a new API key and set up credit card (can specify rate limits etc.)

   iv. Copy your API key for use in the next step

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
- Using the `glow campaign2concept` to use AI to generate creative concept files for multiple products and aspect ratios. This step generates concept pipeline files that define the entire asset generation for each concept.
- Using `glow concept2asset` to process concept pipeline files to generate the assets.
- Using the `glow reviewlanguage` and `glow reviewlogo` commands for post generation checks.

This is the perfect starting point for new users to start Glow-ing and scaling up their social media workflows!

### 2. [D-Pop Campaign](examples/dpop_campaign/campaign_brief_example.json)

The D-Pop campaign demonstrates advanced features:
- Using product-specific brand reference images to guide AI-generated assets with style and composition strength.
- Creating concepts for diverse target audiences (teens and parents) that may have sub-brands.

This example shows how Glow can handle complex, multi-product campaigns with more varied visual requirements.

## Usage

### Command-Line Interface

Glow provides the following commands:

#### 1. Generate concept configurations from a campaign brief

```bash
glow campaign2concept ./examples/starter_campaign/campaign_brief_test.json -f campaign
```

Options:
- `-n`: Number of concepts to generate (default: 3)
- `--format`: Output format (default: 1_1, options: 1_1, 9_16, 16_9, campaign). The `campaign` option will generate concepts for all formats specified in the campaign brief file.

This command will create concept files that define the entire asset generation process. These files can be reviewed, edited, and retained for generating assets.

#### 2. Generate assets from a concept configuration

```bash
glow concept2asset ./examples/starter_campaign/energy_drink_x/concept1_1_1.json
```

This use text-to-image generation and post-image processing to generate asset.

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
glow reviewlanguage examples/starter_campaign/energy_drink_x/concept1_1_1.json

# Check files recursively using the ** pattern
glow reviewlanguage "examples/starter_campaign/**/*.json" > language_report.txt
```

#### 4. Check logo presence in images

```bash
glow reviewlogo "examples/starter_campaign/**/*.png" --campaign-file examples/starter_campaign/campaign_brief_test.json
```

This command checks if a logo is present in image assets recursing through sub directories and outputs a report. The command uses the logo information from the campaign brief file. Under the hood, it uses OpenCV with a FLANN-based matcher for feature detection and matching, providing robust logo recognition even with scaling, rotation, and partial occlusion. Learn more about the technique [here](https://docs.opencv.org/4.x/dc/dc3/tutorial_py_matcher.html#:~:text=In%20this%20chapter%201.%20W).


### Running Tests

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/concept2asset/
pytest tests/campaign2concept/test_input_validator.py

# Run with verbose output
pytest -v
```

## License

[Apache 2.0 License](LICENSE)
