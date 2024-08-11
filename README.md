# Greeblefier
_Note: WIP for now, so little rough around the edges._

## What it does
Allows you to add random pixels to your sprite by associating selected __colors__ with their __probability distribution__.<br />
It's a quick and easy way to break up flat surfaces and make them look more lively.

![](/_readme/grey.png)

<br />

Thanks to its __copy-and-paste__ functionality (a whole sprite or changed/added pixels only), it's best to use this app in conjuction with an image editor of your choice, going back and forth as needed.

You can take advantage of the option to __save and load presets__ to speed up your editing workflow.

![](/_readme/presets.png)
<br />
<br />

## How to use it

1. Open an image from a file or paste it from the clipboard.
1. Choose the target color to which you wish to add random pixels by clicking on it.
2. Select greeble colors by clicking on the "Color preview" rectangle or the RGB value, and then clicking on a color from the palettes on the left.
3. Assign probabilites to each color (the entry fields next to the RGB values) - if needed, the probabilities are automatically recalculated and normalized to 100 %.
4. You can use the green refresh button (_keyboard shortcut R_) repeatedly, until you get a satisfactory result.
5. Export the result (depends on the checkbox _"Gr."_ in the upper left corner - if checked, only changed/added pixels will be used):
   - By saving the sprite as a file (button _"Save image"_)
   - By copying into the clipboard (_keyboard shortcut Ctrl + C_)
6. You can save your current settings as a preset for future use (button _"Save preset"_).
<br />

## Examples

By using the presets, the app can be conveniently used to quickly add large areas of snow (and then just fine tune the details in an image editor).

![](/_readme/snow.png)
<br />
<br />

## TODOs

- implement RGBA support
- fix problems with pixel coordinates: after zooming in/out, especially when the GUI window isn't maximized (for now solved by a restart)
- create sets of premade presets + their management in the program
