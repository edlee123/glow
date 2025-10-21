# Fonts Directory for Glow

This directory contains font files used by the Glow concept2asset module for text overlays on images.

## Essential Fonts

For this demo app, you only need a few key fonts to ensure proper functionality:

### Required Fonts (Must Have)

1. **Montserrat Bold** - Primary font used in text overlays and specifically mentioned in error logs
2. **OpenSans-Regular** - Great alternative to Arial that works as a default fallback font

### Recommended Fonts (Nice to Have)

Instead of having multiple fonts per category, you can use just one representative font from each:

- **Serif**: PlayfairDisplay-Regular
- **Sans-serif**: Roboto-Regular (in addition to Montserrat and OpenSans above)
- **Display**: Anton-Regular
- **Script**: DancingScript-Regular
- **Monospace**: RobotoMono-Regular

These 7 fonts will cover all the font categories used in the text processor while keeping the download size minimal.

## Adding Custom Fonts

To add custom fonts:

1. Place TTF or OTF font files in this directory
2. Font files should be named according to how they are referenced in the text overlay configuration
   - For example, if your text config uses "Montserrat Bold", name the file "Montserrat Bold.ttf" or "MontserratBold.ttf"
   - The font loader will try variations with spaces, underscores, and without spaces

## Font Loading Behavior

If a specified font cannot be found:
1. The system will first try to load the font from this directory
2. Then it will try to load the font from the system fonts
3. If both fail, it will fall back to the default font (Arial/OpenSans)
4. If the default font is not available, it will use the Pillow default font

## Font File Naming Conventions

When adding fonts to this directory, use the following naming conventions:

1. Exact name with extension: `Montserrat Bold.ttf`
2. Name with underscores: `Montserrat_Bold.ttf`
3. Name without spaces: `MontserratBold.ttf`

The font loader will try all these variations when looking for a font.

## Where to Get These Fonts

All of the recommended fonts are available for free from Google Fonts:

1. **Google Fonts** (https://fonts.google.com/) - Search for each font name and download
2. **Direct GitHub Repository**: https://github.com/jongrover/all-google-fonts-ttf-only/tree/master/fonts

## Downloading Fonts Automatically

This directory includes a script `download_fonts_from_github.py` that can automatically download the recommended fonts from the GitHub repository. To use it:

1. Navigate to this directory: `cd glow/concept2asset/fonts/`
2. Run the script: `python download_fonts_from_github.py`

## Legal Note

All the recommended fonts are open source with licenses that allow free use in both personal and commercial projects. If you add your own fonts, ensure you have the appropriate license for any fonts you include in your project.