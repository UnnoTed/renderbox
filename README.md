# renderb0x

### what is renderb0x?
> renderb0x is a tool writen in python to "join" a sequence of image files (a1\_0000.jpg-a1\_7230.jpg => a1.mp4)

you should recognize that from Team Fortress 2

### features
* automatically gets the right fps
* change file sequence without need to search for it
* support 4 and 5 number sequence
* x64 support
* really easy to use
* perfect to use with Lawena recording tool for fast rendering

### preview

![Main Window](https://i.gyazo.com/66808eaa5f362c1f73e99f2738f19f24.png "Main Window")

![Render Window](https://i.gyazo.com/64edc52ae704406fb029dfbfe4dc5a92.png "Render Window")

### how to use it?
1. download it from: [github releases - renderb0x v0.1](https://github.com/sk1LLb0X/renderb0x/releases/download/0.1/renderb0x_0.1.rar)
2. run main.exe
3. set the input path (folder where sequence files are)
4. set the output path (folder where movie will be rendered to)
5. choose the file ID in the input
6. click render

### the program won't run!
remove config.json

### what if the file sequence is over 9999?
it will be renamed to 5 a number number sequence and then render it.

### what image extensions are supported?
* .tga
* .jpg

### why 30000 bitrate?
it's enough for good quality and small size.

### how to run it from the code?
1. download and install python 2.7 x86
2. download and install pyqt4 for python 2.7 x86
3. download it from github release, copy/paste ffmpeg_x64.exe & ffmpeg_x86.exe into the same folder as main.pyw
4. run the code below
 
>python main.pyw

### how to build?
1. install py2exe

>python build.py py2exe

### how to convert pyqt4 gui files into python code?
>python convert.py