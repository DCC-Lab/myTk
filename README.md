# myTk

## What is it?
Making a UI interface should not be complicated. **myTk** is a set of UI classes that simplifies the use of Tkinter to make simple (and not so simple) GUIs in Python.

It is a single file (`mytk.py`) that you import into your project.

## Why Tk?
I know Qt, wxWidgets, and the many other ways to make an interface in Python, and I have programmed macOS since System 7 (Quickdraw, Powerplant) and Mac OS X (Carbon, Aqua, .nib and .xib files in Objective-C and in Swift). 
I now use SwiftUI in other personnal projects. The issues I have found for UIs in Python is either the lack of portability or the complexity of the UI strategy. 
Qt is very powerful but for most applications (and most scientific programmers) it is too complex, and my experience is that it is fairly fragile to transport to another platform (same or different OS).
On the other hand, `Tkinter` is standard on Python, but uses UI strategies that date from the 90s (for example, function callbacks for events). It was easier to encapsulate Tkinter into something easy to use than to simplify Qt or other UI frameworks. This is therefore the objective of this micro-project: make `Tkinter` simple to use for non-professional programmers.

## Design
Having been a macOS programmer since the 90s, I have lived through the many incarnations of UI frameworks. Over the years, I have come to first understand and second appreciate good design patterns. 
To start, I would recommend reading [Design Patterns](https://refactoring.guru/design-patterns)
Therefore, I sought to make Tkinter a bit more mac-like because many design patterns in Apple's libraries are particularly mature and useful.  For instance, Tkinter requires the 
parent of the UI-element to be specified at creation, even though it should not be required.  In addition, the many callbacks get complicated to organize when they are all over the place, therefore 
I implemented a simple delegate pattern to handle many cases by default, and offer the option to extend the behaviour with delegate-functions (which are a bit cleaner than raw callbacks).

## Examples

The following interface to the module ["Raytracing"](https://github.com/DCC-Lab/RayTracing) was created with **myTk**.  It shows a list of lenses with their properties in a Tableview, clicking on the headers will sort the rows, clicking on a link will open the URL
in a browser.  The figures underneath will reflect the properties of the selected item.
<img width="1451" alt="image" src="https://github.com/DCC-Lab/myTk/assets/14200944/c5c127cd-5894-49c2-a3f1-76ee4d2c015a">

## Classes

Anything visible on screen is a referred to as a View, except the Window.

`App`: The main Application class, that holds the reference to the main window.

`Window`: A window that can hold other views

`BaseView`: A class grouping functions common to all View classes

`View`: A plain, empty view. It can be used as a container for other views in grid, so that the View is a single element of the grid even if it holds several elements itself also in a grid.

`PopupMenu`: A popup menu button to select an item in a list

`Label`: Static Onscreen text 

`URLLabel`: Static URL that can be clicked and opened in your webbrowser.

`Box`: A box with an optional title at the top and possibly an outline

`Entry`: An entry box for single line text

`TableView`: A Table of items

`MPLFigure`: A matplotlib figure

