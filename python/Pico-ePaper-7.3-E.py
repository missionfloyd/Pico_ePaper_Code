# *****************************************************************************
# * | File        :   Pico-ePaper-7.3-E.py
# * | Author      :
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2026-06-08
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
EPD_WIDTH       = 800
EPD_HEIGHT      = 480

RST_PIN         = 12
DC_PIN          = 8
CS_PIN          = 9
BUSY_PIN        = 13

class EPD_7in0_E:
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)

        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.BLACK  = 0x00   #   0000
        self.WHITE  = 0x01   #   0001
        self.YELLOW = 0x02   #   0010
        self.RED    = 0x03   #   0011
        self.ORANGE = 0x04   #   0100
        self.BLUE   = 0x05   #   0101
        self.GREEN  = 0x06   #   0110
        self.buffer = bytearray(self.height * self.width // 2)
        self.image = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.GS4_HMSB)
        self.init()

    # Hardware reset
    def reset(self):
        self.reset_pin.value(1)
        utime.sleep_ms(20)
        self.reset_pin.value(0)
        utime.sleep_ms(2)
        self.reset_pin.value(1)
        utime.sleep_ms(20)

    def send_command(self, command):
        self.dc_pin.value(0)
        self.cs_pin.value(0)
        self.spi.write(bytearray([command]))
        self.cs_pin.value(1)

    def send_data(self, data):
        self.dc_pin.value(1)
        self.cs_pin.value(0)
        self.spi.write(bytearray(data))
        self.cs_pin.value(1)

    def ReadBusyH(self):
        print("e-Paper busy H")
        while self.busy_pin.value() == 0: # 0: busy, 1: idle
            utime.sleep_ms(5)
        print("e-Paper busy H release")

    def TurnOnDisplay(self):
        self.send_command(0x17) # AUTO: AUTO SEQUENCE
        self.send_data([0XA5])    # A5: PON->DRF->POF / A7: PON->DRF->POF->DSLP
        self.ReadBusyH()

    def init(self):
        # EPD hardware init start
        self.reset()
        self.ReadBusyH()
        utime.sleep_ms(30)

        self.send_command(0xAA)
        self.send_data([0x49, 0x55, 0x20, 0x08, 0x09, 0x18])

        self.send_command(0x01) # PWR: POWER SETTING (REGISTER)
        self.send_data([0x3F])

        self.send_command(0x00) # PSR: PANEL SETTING (REGISTER)
        self.send_data([0x1F])

        self.send_command(0x03) # PFS: POWER OFF SEQUENCE SETTING
        self.send_data([0x00, 0x54, 0x00, 0x44])

        self.send_command(0x06) # BTST: BOOSTER SOFT START
        self.send_data([0x10, 0x10, 0x10])

        self.send_command(0x30) # PLL: PLL CONTROL
        self.send_data([0x07])  # 0x03 -> slow, 0x07 -> fast

        self.send_command(0x50) # CDI: VCOM AND DATA INTERVAL SETTING
        self.send_data([0x3F])

        self.send_command(0x60) # TCON: TCON SETTING
        self.send_data([0x02, 0x00])

        self.send_command(0x61)                  # TRES: RESOLUTION SETTING
        self.send_data([0x03, 0x20, 0x01, 0xE0]) # [0x0320][0x01E0] -> displaysize

        self.send_command(0x82)
        self.send_data([0x01])

        self.send_command(0xE3) # PWS: POWER SAVING
        self.send_data([0x2F])

        self.ReadBusyH()
        return 0

    def display(self, image):
        self.send_command(0x10)
        for i in range(self.width // 2):
            self.send_data(image[i * self.height : (i + 1) * self.height])

        self.TurnOnDisplay()
    
    def displayPartial(self, image, x, y, width, height):
        x_end = x + width - 1
        y_end = y + height - 1
        self.send_command(0x83)
        self.send_data([(x >> 8) & 0x03, x & 0xff, (x_end >> 8) & 0x03, x_end & 0xff,
                        (y >> 8) & 0x03, y & 0xff, (y_end >> 8) & 0x03, y_end & 0xff, 0x01])
        self.send_command(0x10)
        self.send_data([0x00])
        for i in range(width // 2):
            self.send_data(image[i * height : (i + 1) * height])

        self.TurnOnDisplay()

    def Clear(self, color=0x01):
        self.send_command(0x10)
        for i in range(self.width // 2):
            self.send_data([color << 4 | color] * self.width)

        self.TurnOnDisplay()

    def sleep(self):
        self.send_command(0x07) # DEEP_SLEEP
        self.send_data(0XA5)

        utime.sleep_ms(2000)
        self.reset_pin.value(0)

if __name__=='__main__':
    epd = EPD_7in0_E()
    epd.Clear()

    epd.image.fill(epd.WHITE)
    epd.image.text("Waveshare", 5, 10, epd.BLACK)
    epd.image.text("Pico_ePaper-7.3-E", 5, 40, epd.BLACK)
    epd.image.text("Raspberry Pi Pico", 5, 70, epd.BLACK)
    epd.display(epd.buffer)
    epd.delay_ms(5000)

    epd.image.vline(10, 90, 60, epd.BLACK)
    epd.image.vline(120, 90, 60, epd.BLACK)
    epd.image.hline(10, 90, 110, epd.BLACK)
    epd.image.hline(10, 150, 110, epd.BLACK)
    epd.image.line(10, 90, 120, 150, epd.BLACK)
    epd.image.line(120, 90, 10, 150, epd.BLACK)
    epd.display(epd.buffer)
    epd.delay_ms(5000)

    epd.image.fill_rect(10, 180, 50, 50, epd.BLACK)
    epd.image.rect(70, 180, 50, 50, epd.BLACK)
    epd.image.fill_rect(10, 240, 50, 50, epd.YELLOW)
    epd.image.fill_rect(70, 240, 50, 50, epd.RED)
    epd.image.fill_rect(10, 300, 50, 50, epd.ORANGE)
    epd.image.fill_rect(70, 300, 50, 50, epd.BLUE)
    epd.image.fill_rect(10, 360, 50, 50, epd.GREEN)
    epd.display(epd.buffer)
    epd.delay_ms(5000)

    epd.image.fill_rect(250, 150, 480, 20, epd.BLACK)
    epd.image.fill_rect(250, 310, 480, 20, epd.BLACK)
    epd.image.fill_rect(400, 0, 20, 480, epd.BLACK)
    epd.image.fill_rect(560, 0, 20, 480, epd.BLACK)

    for j in range(3):
        for i in range(15):
            epd.image.line(270+j*160+i, 20+j*160, 375+j*160+i, 140+j*160, epd.RED)
            epd.image.line(375+j*160+i, 20+j*160, 270+j*160+i, 140+j*160, epd.RED)
            epd.image.line(270+j*160, 20+j*160+i, 390+j*160, 125+j*160+i, epd.RED)
            epd.image.line(270+j*160, 125+j*160+i, 390+j*160, 20+j*160+i, epd.RED)

    epd.image.ellipse(320, 240, 60, 60, epd.GREEN, True)
    epd.image.ellipse(320, 400, 60, 60, epd.GREEN, True)
    epd.image.ellipse(320, 240, 40, 40, epd.WHITE, True)
    epd.image.ellipse(320, 400, 40, 40, epd.WHITE, True)
    epd.display(epd.buffer)
    epd.delay_ms(5000)

    epd.Clear()
    epd.delay_ms(2000)

    print("sleep")
    epd.sleep()
