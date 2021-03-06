# Ancient Text Fixer:

#### Installation:
* Using PipEnv:
   1. install pipenv - https://pipenv.pypa.io/en/latest/#install-pipenv-today
   2. ```
      pipenv shell
      pipenv install
      ```

#### Runing program:
```
pipenv shell
python main.py
```
* `python main.py -d` loads a test source image at startup

#### Menu Options:
* *File -> open -* opens a source image (this will remove all the current letters on canvas)
* *File -> save image as.. -* saves an image file of the source image which contains the placed and modified letter images on it
* *File -> save contours as.. - * saves a json file with the placed letter's coords and contours

#### Instructions:
1. Load a source image to work on
3. Place letters by doing the following:
   1. Select a letter by *Left* clicking on it's image on the toolbar
   2. Move your mouse over the output image, and carefully choose the right spot to position it
   4. Use the algorithm and letter modifiers to better fit the letter to it's correct form and position
   3. *Left* click to place the letter image at its current form and position
   4. You can select letters already placed by *Left* clicking to manipulate them using the selected letter modifiers:

#### Controls:
##### Letter Modifiers:
   1. *Right* / *Left* - rotate letter
   2. *Up* / *Down* - scale letter
   3. *=* - toggle letter fill (filled letter / contours only)


##### Selected Letter Modifiers:
   1. *Delete* / *BackSpace* - remove letter from canvas
   2. *Arrow Keys* - move letter around the canvas
   3. *R* - Edit window for selected letter
   
#### Edit Mode(R option):
   1. press twice on the image to generate a line.
   2. save - save the image as tif format and adds it to the menu
   3. close - wont save any changes
   4. deformat - will call deformator class with all relevant details and make the chosen interpolation
   
##### Zoom:
   1. *<Motion>* - to toggle screen zoom

##### Algorithm Modifiers:
   1. *+* / *-* - increase or decrease the snakes algorithm strength
   2. *** - toggle letter fit mode (snap to dark parts / snap to light parts)

#### About The Project:
The project uses `skikit-image` active_contour algorithm behind the scenes, with a simple user interface created using tkinter (a built in ui library for python).
The live feedback is generated via back and forth comunication between the ui and the algorithm backend to give a smooth and monitored letter placing experience.
`scikit-image` uses numpy and thus compatible with other image processing libraries.

#### Enriching Letter Arsenal:
letters are automaticly loaded from the `resources/letters` folder, letter files should contain a black letter which will be used to extract the contours, later used in the snakes algorithm.
