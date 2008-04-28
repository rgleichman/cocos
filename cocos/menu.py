#
# Menu class for pyglet
#
# Ideas borrowed from:
#    pygext: http://opioid-interactive.com/~shang/projects/pygext/
#    pyglet astraea: http://www.pyglet.org
#    Grossini's Hell: http://www.pyweek.org/e/Pywiii/ 
# 
#
"""A menu layer for los-cocos.

Menu
====

This module provides a Menu class, which is a layer you can use in cocos
apps. Menus can contain regular items (which trigger a function when selected)
or toggle items (which toggle a flag when selected).

When you need a menu, you can define a class inheriting `Menu`, and setting
some attributes which control the menu appearance. Then you add `MenuItem` s to
it, prepare it, and use it as you would use any layer.

There is a menu demo in the samples folder.

"""

__docformat__ = 'restructuredtext'

import pyglet
from pyglet import font
from pyglet.window import key
from pyglet.gl import *

from layer import *
from director import *
from cocosnode import *
from actions import *

__all__ = [ 'Menu',                                 # menu class

    'MenuItem', 'ToggleMenuItem',                   # menu items classes
    'MultipleMenuItem', 'EntryMenuItem',

    'CENTER', 'LEFT', 'RIGHT', 'TOP', 'BOTTOM',     # menu aligment

    'shake', 'shake_back','zoom_in','zoom_out'      # Some useful actions for the menu items
    ]

#
# Class Menu
#

# Horizontal Align
CENTER = font.Text.CENTER
LEFT = font.Text.LEFT
RIGHT = font.Text.RIGHT

# Vertical Align
TOP = font.Text.TOP
BOTTOM = font.Text.BOTTOM

class Menu(Layer):
    """Abstract base class for menu layers.
    
    Normal usage is:

     - create a subclass
     - override __init__ to set all style attributes, 
       and then call `create_menu()`
     - Finally you shall add the menu to a `Scene`
    """

    select_sound = None
    activate_sound = None
    def __init__( self, title = ''):
        super(Menu, self).__init__()

        #
        # Items and Title
        #
        self.title = title
        self.title_text = None

        self.menu_halign = CENTER
        self.menu_valign = CENTER

        #
        # Menu default options
        # Menus can be customized changing these variables
        #

        # Title
        self.font_title = {
            'text':'title',
            'font_name':'Arial',
            'font_size':56,
            'color':(192,192,192,255),
            'bold':False,
            'italic':False,
            'valign':'center',
            'halign':'center',
            'dpi':96,
            'x':0, 'y':0,
        }

        self.font_item= {
            'font_name':'Arial',
            'font_size':32,
            'bold':False,
            'italic':False,
            'valign':'center',
            'halign':'center',
            'color':(192,192,192,255),
            'dpi':96,
        }
        self.font_item_selected = {
            'font_name':'Arial',
            'font_size':42,
            'bold':False,
            'italic':False,
            'valign':'center',
            'halign':'center',
            'color':(255,255,255,255),
            'dpi':96,
        }

        self.title_height = 0

     
    def _generate_title( self ):
        width, height = director.get_window_size()

        self.font_title['x'] = width // 2
        self.font_title['text'] = self.title
        self.title_label = pyglet.text.Label( **self.font_title )
        self.title_label.y = height - self.title_label.content_height //2

        fo = font.load( self.font_title['font_name'], self.font_title['font_size'] )
        self.title_height = self.title_label.content_height

    def _generate_items( self ):
        width, height = director.get_window_size()

        fo = font.load( self.font_item['font_name'], self.font_item['font_size'] )
        fo_height = int( (fo.ascent - fo.descent) * 0.9 )

        if self.menu_halign == CENTER:
            pos_x = width // 2
        elif self.menu_halign == RIGHT:
            pos_x = width - 2
        elif self.menu_halign == LEFT:
            pos_x = 2
        else:
            raise Exception("Invalid halign value for menu")

        for idx,i in enumerate( self.children):
            item = i[1]

            if self.menu_valign == CENTER:
                pos_y = height / 2 + (fo_height * len(self.children) )/2 - (idx * fo_height ) - self.title_height * 0.2
            elif self.menu_valign == TOP:
                pos_y = height - (idx * fo_height ) - self.title_height
            elif self.menu_valign == BOTTOM:
                pos_y = 0 + fo_height * len(self.children) - (idx * fo_height )

            item.transform_anchor = (pos_x, pos_y)

            self.font_item['x'] = pos_x
            self.font_item['y'] = pos_y
            self.font_item['text'] = item.label
            item.text = pyglet.text.Label( **self.font_item )

            self.font_item_selected['x'] = pos_x
            self.font_item_selected['y'] = pos_y
            self.font_item_selected['text'] = item.label
            item.text_selected = pyglet.text.Label( **self.font_item_selected )

    def _build_items( self ):
        self.font_item_selected['halign'] = self.menu_halign
        self.font_item_selected['valign'] = 'center'

        self.font_item['halign'] = self.menu_halign
        self.font_item['valign'] = 'center'

        self._generate_title()
        self._generate_items()
        self.selected_index = 0
        self.children[ self.selected_index ][1].is_selected = True

    def _select_item(self, new_idx):
        if new_idx == self.selected_index:
            return

        if self.select_sound:
            self.select_sound.play()

        self.children[ self.selected_index][1].is_selected = False
        self.children[ self.selected_index][1].on_unselected()

        self.children[ new_idx ][1].is_selected = True 
        self.children[ new_idx ][1].on_selected()

        self.selected_index = new_idx

    def _activate_item( self ):
        if self.activate_sound:
            self.activate_sound.play()
        self.children[ self.selected_index][1].on_activated()
        self.children[ self.selected_index ][1].on_key_press( key.ENTER, 0 )

    def create_menu( self, items, selected_effect=None, unselected_effect=None, activated_effect=None ):
        """Creates the menu

        The order of the list important since the
        first one will be shown first.

        Example::
    
            l = []
            l.append( MenuItem('Options', self.on_new_game ) )
            l.append( MenuItem('Quit', self.on_quit ) )
            self.create_menu( l, zoom_in(), zoom_out() )

        :Parameters:
            `items` : list
                list of `MenuItem` that will be part of the `Menu`
            `selected_effect` : callback
                This action will be executed when the `MenuItem` is selected
            `unselected_effect` : callback
                This action will be executed when the `MenuItem` is unselected
            `activated_effect` : callback
                this action will executed when the `MenuItem` is activated (pressing Enter or by clicking on it)
        """
        z=0
        for i in items:
            # calling super.add(). Z is important to mantain order
            self.add( i, z=z )

            i.activated_effect = activated_effect
            i.selected_effect = selected_effect
            i.unselected_effect = unselected_effect
            i.halign = self.menu_halign
            i.valign = self.menu_valign
            z += 1

        self._build_items()

    def on_draw( self ):
        self.title_label.draw()

    def on_text( self, text ):
        if text=='\r':
            return
        return self.children[self.selected_index][1].on_text(text)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            self.on_quit()
            return True
        elif symbol in (key.ENTER, key.NUM_ENTER):
            self._activate_item()
            return True
        elif symbol in (key.DOWN, key.UP):
            if symbol == key.DOWN:
                new_idx = self.selected_index + 1
            elif symbol == key.UP:
                new_idx = self.selected_index - 1

            if new_idx < 0:
                new_idx = len(self.children) -1
            elif new_idx > len(self.children) -1:
                new_idx = 0
            self._select_item( new_idx )
            return True
        else:
            # send the menu item the rest of the keys
            return self.children[self.selected_index][1].on_key_press(symbol, modifiers)

    def on_mouse_release( self, x, y, buttons, modifiers ):
        (x,y) = director.get_virtual_coordinates(x,y)
        if self.children[ self.selected_index ][1].is_inside_box(x,y):
            self._activate_item()

    def on_mouse_motion( self, x, y, dx, dy ):
        (x,y) = director.get_virtual_coordinates(x,y)
        self._x = x
        self._y = y
        for idx,i in enumerate( self.children):
            item = i[1]
            if item.is_inside_box( x, y):
                self._select_item( idx )
                break

class MenuItem( CocosNode ):
    """A menu item triggering a function."""

    selected_effect = None
    unselected_effect = None
    activated_effect = None

    def __init__(self, label, activate_func):
        """Creates a new menu item

        :Parameters:
            `label` : string
                The label the of the menu item
            `activate_func` : function
                The callback function
        """

        super( MenuItem, self).__init__()

        self.label = label
        self.activate_func = activate_func

        self.is_selected = False

        # Variables that will be set when init_font() is called
        self.text = None
        self.text_selected = None

        self.halign = None
        self.valign = None

    def get_box( self ):
        """Returns the box that contains the menu item.

        :rtype: (x1,x2,y1,y2)
        :returns: returns a tuple (a rectangle) that sets the boundaries of the menu item."""

        width = self.text.content_width
        height = self.text.content_height

        if self.halign == CENTER:
            x_diff = - width / 2
        elif self.halign == RIGHT:
            x_diff = - width
        elif self.halign == LEFT:
            x_diff = 0
        else:
            raise Exception("Invalid halign: %s" % str(self.halign) )

        if self.valign == CENTER:
            y_diff = - height/ 2
        elif self.valign == TOP:
            y_diff = - height
        elif self.valign == BOTTOM:
            y_diff = 0
        else:
            raise Exception("Invalid valign: %s" % str(self.valign) )

        x1 = self.text.x + x_diff
        y1 = self.text.y + y_diff
        x2 = x1 + width
        y2 = y1 + height
        return (x1,y1,x2,y2)

    def on_draw( self ):
        glPushMatrix()
        self.transform()

        if self.is_selected:
            self.text_selected.draw()
        else:
            self.text.draw()

        glPopMatrix()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.ENTER and self.activate_func:
            self.activate_func()
            return True

    def on_text( self, text ):
        return True

    def is_inside_box( self, x, y ):
        """Returns whether the point (x,y) is inside the menu item.

        :rtype: Boolean
        :Returns: Whether or not the point (x,y) is inside the menu item
        """
        (ax,ay,bx,by) = self.get_box()
        if( x >= ax and x <= bx and y >= ay and y <= by ):
            return True
        return False

    def on_selected( self ):
        if self.selected_effect:
            self.flush()
            self.do( self.selected_effect )

    def on_unselected( self ):
        if self.unselected_effect:
            self.flush()
            self.do( self.unselected_effect )

    def on_activated( self ):
        if self.activated_effect:
            self.flush()
            self.do( self.activated_effect )


class MultipleMenuItem( MenuItem ):
    """A menu item for switching between multiple values.
    
    toggle_func will be called for switching when selected, and
    get_value_func should be a function returning the value as a
    string"""

    def __init__(self, label, toggle_func, get_value_func):
        """Creates a Toggle Menu Item

        :Parameters:
            `label` : string
                Item's label
            `toggle_func` : function
                Callback function
            `get_value_func` : function
                This function returns the item's
                actual value as a String
        """
        self.toggle_label = label
        self.toggle_func = toggle_func
        self.get_value_func = get_value_func
        self.value = get_value_func()
        super( MultipleMenuItem, self).__init__( self._get_label(), None )


    def _get_label(self):
        return self.toggle_label+self.get_value_func()

    def on_key_press(self, symbol, modifiers):
        if symbol in ( key.LEFT, key.RIGHT, key.ENTER):
            self.toggle_func( )
            self.text.text = self._get_label()
            self.text_selected.text = self._get_label()
            return True

class ToggleMenuItem( MultipleMenuItem ):
    """A menu item for a boolean toggle option.
    
    When selected, ``self.value`` is toggled, the callback function is
    called with ``self.value`` as argument."""

    def __init__(self, label, value, toggle_func):
        """Creates a Toggle Menu Item

        :Parameters:
            `label` : string
                Item's label
            `value` : Bool
                Default value: False is OFF, True is ON
            `toggle_func` : function
                Callback function
        """
        self.__value = value
        
        def switch_value():
            self.__value=not self.__value
            toggle_func(self.__value)
    
        super(ToggleMenuItem, self).__init__( label, switch_value, 
                lambda :['OFF','ON'][int(self.__value)] )          

class EntryMenuItem(MenuItem):
    """A menu item for entering a value.

    When selected, ``self.value`` is toggled, the callback function is
    called with ``self.value`` as argument."""

    value = property(lambda self: u''.join(self._value),
                     lambda self, v: setattr(self, '_value', list(v)))

    def __init__(self, label, value, set_func):
        """Creates an Entry Menu Item

        :Parameters:
            `label` : string
                Item's label
            `value` : String
                Default value: any string
            `set_func` : function
                Callback function taking one argument.
        """
        self.set_func = set_func
        self._value = list(value)
        self._label = label
        super(EntryMenuItem, self).__init__( "%s %s" %(label,value), None)

    def on_text( self, text ):
        self._value.append(text)
        self._calculate_value()
        return True

    def on_key_press(self, symbol, modifiers):
        if symbol == key.BACKSPACE:
            try:
                self._value.pop()
            except IndexError:
                pass
            self._calculate_value()
            return True

    def _calculate_value( self ):
        new_text = u"%s %s" % (self._label, self.value)
        self.text.text = new_text
        self.text_selected.text = new_text
        self.set_func(self.value)


def shake():
    '''Action that performs a slight rotation and then goes back to the original rotation
    position.
    '''
    angle = 05
    duration = 0.05

    rot = Accelerate(RotateBy( angle, duration ), 2)
    rot2 = Accelerate(RotateBy( -angle*2, duration), 2)
    return rot + (rot2 + Reverse(rot2)) * 2 + Reverse(rot)

def shake_back():
    return RotateTo(0,0.1)

def zoom_in():
    return ScaleTo( 1.5, duration=0.2 )

def zoom_out():
    return ScaleTo( 1.0, duration=0.2 )
