# *****************************************************************************
# * | File        :   Pico-ePaper-3.0-G.py
# * | Author      :   
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V1
# * | Date        :   2026-06-07
# # | Info        :   python demo
# -----------------------------------------------------------------------------
# ******************************************************************************/
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

from machine import Pin, SPI
import framebuf
import utime

# Display resolution
EPD_WIDTH       = 168
EPD_HEIGHT      = 400

RST_PIN         = 12
DC_PIN          = 8
CS_PIN          = 9
BUSY_PIN        = 13

class EPD_3in0_G:
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        
        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.BLACK  = 0x00   #   00
        self.WHITE  = 0x01   #   01
        self.YELLOW = 0x02   #   10
        self.RED    = 0x03   #   11
        self.buffer = bytearray(self.height * self.width // 4)
        self.image = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.GS2_HMSB)
        self.init()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)
    
    # Hardware reset
    def reset(self):
        self.reset_pin.value(1)
        self.delay_ms(200)
        self.reset_pin.value(0)
        self.delay_ms(2)
        self.reset_pin.value(1)
        self.delay_ms(200)

    def send_command(self, command):
        self.dc_pin.value(0)
        self.cs_pin.value(0)
        self.spi.write(bytearray([command]))
        self.cs_pin.value(1)

    @micropython.viper
    def send_data(self, data: ptr8):
        self.dc_pin.value(1)
        self.cs_pin.value(0)
        self.spi.write(bytearray([data]))
        self.cs_pin.value(1)

    def ReadBusyH(self):
        print("e-Paper busy H")
        while self.busy_pin.value() == 0:      # 0: idle, 1: busy
            self.delay_ms(5)
        print("e-Paper busy H release")

    def ReadBusyL(self):
        print("e-Paper busy L")
        while self.busy_pin.value() == 1:      # 0: busy, 1: idle
            self.delay_ms(5)
        print("e-Paper busy L release")

    def TurnOnDisplay(self):
        self.send_command(0x12) # DISPLAY_REFRESH
        self.send_data(0x01)
        self.ReadBusyH()

        self.send_command(0x02) # POWER_OFF
        self.send_data(0X00)
        self.ReadBusyH()
        
    def init(self):
        # EPD hardware init start

        self.reset()

        self.send_command(0x66)
        self.send_data(0x49)
        self.send_data(0x55)
        self.send_data(0x13)
        self.send_data(0x5D)
        self.send_data(0x05)
        self.send_data(0x10)

        self.send_command(0xB0)
        self.send_data(0x00) # 1 boost

        self.send_command(0x01)
        self.send_data(0x0F)
        self.send_data(0x00)

        self.send_command(0x00)
        self.send_data(0x4F)
        self.send_data(0x6B)

        self.send_command(0x06)
        self.send_data(0xD7)
        self.send_data(0xDE)
        self.send_data(0x12)

        self.send_command(0x61)
        self.send_data(0x00)
        self.send_data(0xA8)
        self.send_data(0x01)
        self.send_data(0x90)

        self.send_command(0x50)
        self.send_data(0x37)

        self.send_command(0x60)
        self.send_data(0x0C)
        self.send_data(0x05)

        self.send_command(0xE3)
        self.send_data(0xFF)

        self.send_command(0x84)
        self.send_data(0x00)
        return 0

    @micropython.viper
    def display(self, image: ptr8):
        self.send_command(0x04)
        self.ReadBusyH()

        self.send_command(0x10)
        for i in range(16800): # self.height * self.width // 4
            self.send_data(((image[i] & 0x03) << 6 | (image[i] & 0x0c) << 2 | (image[i] & 0x30) >> 2 | (image[i] & 0xC0) >> 6))

        self.TurnOnDisplay()

    @micropython.native
    def Clear(self, color=0x01):
        self.send_command(0x04)
        self.ReadBusyH()

        self.send_command(0x10)
        for i in range(self.height * self.width // 4):
            self.send_data(color << 6 | color << 4 | color << 2 | color)

        self.TurnOnDisplay()

    def sleep(self):
        self.send_command(0x02) # POWER_OFF
        self.send_data(0x00)

        self.send_command(0x07) # DEEP_SLEEP
        self.send_data(0XA5)
        
        self.delay_ms(2000)
        self.reset_pin.value(0)

if __name__=='__main__':
    epd = EPD_3in0_G()
    epd.Clear()
    epd.delay_ms(2000)

    epd.image.fill(epd.WHITE)
    epd.image.text("Waveshare", 5, 10, epd.BLACK)
    epd.image.text("Pico_ePaper-3.0-G", 5, 40, epd.BLACK)
    epd.image.text("Raspberry Pi Pico", 5, 70, epd.BLACK)
    epd.image.rect(10, 90, 40, 80, epd.BLACK)
    epd.image.fill_rect(60, 90, 40, 80, epd.RED)
    epd.image.fill_rect(110, 90, 40, 80, epd.YELLOW)
    epd.init()
    epd.display(epd.buffer)
    epd.delay_ms(5000)
    
    epd.init()
    epd.Clear()
    epd.sleep()
