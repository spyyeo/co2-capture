import smbus2
import time
import thingspeak
import csv
from datetime import datetime

# I2C Address
CO2_SENSOR_ADDR = 0x69  # Default I2C address for Atlas Scientific EZO-CO2

# ThingSpeak API
THINGSPEAK_API_KEY = "V94UAJQB0QVB5TE5"  # Replace with your actual API key
THINGSPEAK_CHANNEL_ID = 2943678  # Replace with your actual channel ID

# Log file path
LOG_FILE = "co2_log.csv"

# Initialize ThingSpeak channel
channel = thingspeak.Channel(id=THINGSPEAK_CHANNEL_ID, api_key=THINGSPEAK_API_KEY)

# I2C Bus
bus = smbus2.SMBus(1)

# Initialize log file with headers if it doesn't exist
try:
    with open(LOG_FILE, 'x', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "CO2 (ppm)"])
except FileExistsError:
    pass

# Function to read CO2 data from Atlas Scientific sensor (with diagnostics)
def read_co2_sensor(sensor_addr):
    try:
        bus.write_byte(sensor_addr, ord('R'))  # Send 'R' command
        time.sleep(0.9)  # Wait 900ms

        response = bus.read_i2c_block_data(sensor_addr, 0x00, 16)
        if response[0] != 1:
            print(f"Sensor returned error code: {response[0]}")
            return None

        # Extract characters from response, skipping first byte (status)
        chars = [chr(b) for b in response[1:] if 32 <= b <= 126]
        co2_data = ''.join(chars).strip()

        if co2_data.isdigit():
            return int(co2_data)
        else:
            print(f"Error: Non-numeric response from sensor: {co2_data!r}")
            return None
    except Exception as e:
        print(f"Error reading from sensor {hex(sensor_addr)}: {e}")
        return None

# Function to upload data to ThingSpeak
def upload_to_thingspeak(co2):
    try:
        response = channel.update({"field1": co2})
        print("Data uploaded successfully")
    except Exception as e:
        print(f"Error uploading data: {e}")

# Function to log data locally to a CSV file
def log_to_csv(timestamp, co2):
    try:
        with open(LOG_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, co2])
    except Exception as e:
        print(f"Error writing to log file: {e}")

# Main loop
print("Warming up sensor...")
time.sleep(15)  # Warm-up period after power on

while True:
    co2 = read_co2_sensor(CO2_SENSOR_ADDR)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if co2 is not None:
        print(f"{timestamp} - CO2: {co2} ppm")
        upload_to_thingspeak(co2)
        log_to_csv(timestamp, co2)
    else:
        print(f"{timestamp} - Sensor Error")

    time.sleep(15)  # Update every 15 seconds
