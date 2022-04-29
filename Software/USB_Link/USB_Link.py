import sys, os
import pynput
import time
v_gimbal_value = 0 

def on_move(x, y):
    print('Pointer moved to {0}'.format((x, y)))
def on_press(key):
    '按下按键时执行。'
    global v_gimbal_value

    try:
        v_key = 0
        v_key = format(key.char)
        if format(key.char) == 'w' :
            v_gimbal_value = 100
        elif format(key.char) == 's' :
            v_gimbal_value = -100
        else :
            v_gimbal_value = 0
    except AttributeError:
        v_key = 0
        v_key = format(key.char)
        if format(key.char) == 'w' :
            v_gimbal_value = 100
        elif format(key.char) == 's' :
            v_gimbal_value = -100
        else :
            v_gimbal_value = 0

def on_click(x, y, button, pressed):
    print('{0} at {1}'.format(
        'Pressed' if pressed else 'Released',
        (x, y)))
    if not pressed:
        # Stop listener


        return False

def on_scroll(x, y, dx, dy):
    print('Scrolled {0} at {1}'.format(
        'down' if dy < 0 else 'up',
        (x, y)))

# Collect events until released
while 1:

    #listener = pynput.mouse.Listener(on_move=on_move)
    listener = pynput.keyboard.Listener(on_press=on_press) 
    listener.start()
    print(v_gimbal_value)
    v_gimbal_value = 0
    
        
            