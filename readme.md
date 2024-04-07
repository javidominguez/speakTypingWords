# speak typing words enhancement - NVDA addon

NVDA reads the entire word when it is modified, instead of just the added part, which is the default behavior.

This code has been extracted from NVDAExtensionGlobalPlugin add-on by Paulber19.
https://github.com/paulber19/NVDAExtensionGlobalPlugin
According to the GNU General Public License.
All credit belongs to its original authors: Paulber19 and Leonardder.

The function that executes this code was removed from the original addon in version 13.3, however, some users missed it.
This fork recovers the function by adapting it to work independently in a small addon for those users.

Copyright of this adaptation by Javi Dominguez (2024)

### Warnings:  

* If an older version of NVDAExtensionGlobalPlugin is running and has enabled the improved echo per words option, handling will be delegated to that addon. When the option is disabled or NVDAExtensionGlobalPlugin is removed/updated, speakTypingWords will take control of word echo.  
* There have been reported errors running this feature in Musescore that could not be fixed. It will remain disabled in that app meanwhile errors are not fixed.  
* Some users have reported problems using imroved echo per words feature with Braille keyboards. I can not guarantee that it will work correctly with all Braille devices.  