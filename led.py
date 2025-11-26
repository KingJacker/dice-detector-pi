import lgpio
import time

class LED:
	def __init__(self, pin, led_handler_id=4):
		self.pin = pin
		self.handler = lgpio.gpiochip_open(led_handler_id)
		self.isOn = False 

		lgpio.gpio_claim_output(self.handler, self.pin)

		self.off()

	def toggle(self):
		self.isOn = not self.isOn
		lgpio.gpio_write(self.handler, self.pin, not self.isOn) 
		return self.isOn


	def on(self):
		self.isOn = True
		lgpio.gpio_write(self.handler, self.pin, not self.isOn) 
		return self.isOn


	def off(self):
		self.isOn = False
		lgpio.gpio_write(self.handler, self.pin, not self.isOn) 
		return self.isOn


	def flash(self, flash_ms=100):
		lgpio.gpio_write(self.handler, self.pin, 0) # on 
		time.sleep(flash_ms/1000)
		lgpio.gpio_write(self.handler, self.pin, 1) # off


	def free(self):
		lgpio.gpio_free(self.handler, self.pin)