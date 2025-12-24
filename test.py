import gpiod
import time

# GPIO chip and line numbers
chip = gpiod.Chip('gpiochip0')
lines = chip.get_lines([49, 103])  # PH.06 (pin 7), PQ.03 (pin 15)

# Request lines as output, initially low
lines.request(consumer="toggle", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0, 0])

# Toggle for 25 seconds
start_time = time.time()
while time.time() - start_time < 25:
    lines.set_values([1, 1])
    time.sleep(0.5)
    lines.set_values([0, 0])
    time.sleep(0.5)

# Release the lines
lines.release()
