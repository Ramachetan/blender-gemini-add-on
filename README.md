# Blender Gemini Assistant Add-on

A Blender add-on that integrates Google's Gemini AI to help you generate Python scripts for Blender operations. This add-on provides a chat interface where you can describe what you want to create or modify in Blender, and Gemini will generate the appropriate Python code.

## Requirements

- Blender 3.0.0 or newer
- Internet connection
- Google Gemini API key

## Installation

1. Download the latest release ZIP file from this repository
2. In Blender, go to Edit > Preferences > Add-ons
3. Click "Install..." and select the downloaded ZIP file
4. Enable the add-on by checking the checkbox next to "Development: Gemini Chat Assistant"

## Configuration

1. Get your Gemini API key from the [Google AI Studio](https://makersuite.google.com/)
2. In Blender, open the Gemini panel in the 3D Viewport's sidebar (press N to show the sidebar)
3. Enter your API key in the "API Key" field at the top of the panel

## Usage

1. Open the Gemini panel in the 3D Viewport's sidebar (press N and select the "Gemini" tab)
2. Enter your question or request in the text field at the bottom
3. Click "Send Message" or press Enter
4. If the response contains code:
   - It will be automatically saved to Blender's Text Editor
   - If auto-execute is enabled, it will run automatically
   - You can manually copy or execute the code using the buttons below the code block

### Example Prompts

- "Create a simple cube and sphere scene"
- "Generate a spiral staircase"
- "Add a camera that orbits around the selected object"
- "Create a procedural wood texture for the selected object"

## Customization

You can modify the following parameters in the `CONFIG` dictionary at the top of the script
