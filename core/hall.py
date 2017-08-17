import RPi.GPIO as GPIO

PIN = 11
try:
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(PIN, GPIO.IN)
    if GPIO.input(PIN):
        # No Magnet
        print "HIGH"
    else:
        # Magnet
        print "LOW"
except KeyboardInterrupt:
    GPIO.cleanup()
