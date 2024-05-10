'''

Written by alfredc333
'''

import time
import smbus2
import bme280
import serial
import sqlite3
from lcd16x2 import lcd16x2
import requests
import traceback
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime

# BME280 sensor address (default address)
address = 0x76

# Initialize I2C bus
bus = smbus2.SMBus(1)

# Load calibration parameters
calibration_params = bme280.load_calibration_params(bus, address)

#K30 serial connection
try:
    ser = serial.Serial("/dev/ttyS0")
    ser.flushInput()
except:
    print("Failed to open serial com")
    exit()
    
#LCD I2C connection
try:
    lcd = lcd16x2(0x27, 1)
    lcd.initDisplay()
except:
    print("Failed to initialize LCD")
    exit()

#Connect to ATLAS Mongodb

DB = DB_NAME
COLLECTION = COLLECTION_NAME
uri = "YOUR_MONGODB_ATLAS_CONNECTION_STRING"
SENSOR_ID = 333
SENSOR_TYPE = "T H AP CO2"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    
db = client[DB]
col = db[COLLECTION]
  

while True:
    try:
        # Read sensor data
        data = bme280.sample(bus, address, calibration_params)

        # Extract temperature, pressure, and humidity
        temperature_celsius = data.temperature
        pressure = data.pressure
        humidity = data.humidity

        #read K30 CO2 sensor
        ser.write(b'\xFE\x44\x00\x08\x02\x9F\x25')
        time.sleep(.01)
        resp = ser.read(7)
        high = ord(chr(resp[3]))
        low = ord(chr(resp[4]))
        co2Level = (high * 256) + low
        
        #timestamp from RTC clock
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        x = timestamp.split()
        dateStr = x[0]
        timeStr = x[1] 
        # Print the readings
        print("*************")
        print(timestamp)
        print("Temperature: {:.2f} °C".format(temperature_celsius))
        print("Pressure: {:.2f} hPa".format(pressure))
        print("Humidity: {:.2f} %".format(humidity))
        print("CO2 Level: {: } ppm".format(co2Level))
        
        try:    
            ts = datetime.datetime.now()
            dict = {  "Timestamp": ts,
                      "metadata": { "sensorId": SENSOR_ID, "type": SENSOR_TYPE },
                      "measurements": { "Temperature": round(temperature_celsius,2), "Humidity": round(humidity,2),
                                        "AirPressure": round(pressure,2), "CO2level": co2Level}
                    }
            '''
            test record 
            dict = {  "Timestamp": ts,
                      "metadata": { "sensorId": 31333, "type": "temp, hum, ap, co2" },
                      "measurements": { "Temperature": 21, "Humidity": 52, "AirPressure": 1234, "CO2level": 111}
                    }
            '''
            x = col.insert_one(dict)
            print(x)
        except Exception as e:
            print(e)
    
        
        # Wait for one minute before the next reading
        #LCD display cycle, 4 x 5 sec x 3TICK = 60 sec
        TICK = 0
        TIME = 4
        
        while (TICK < 3):
            lcd.cleanFirstLine()        
            lcd.cleanSecondLine() 
            lcd.writeFirstLine(f"TIME {timeStr }")
            lcd.writeSecondLine(f"DATE {dateStr}")
            time.sleep(TIME)
            
            lcd.cleanFirstLine()        
            lcd.cleanSecondLine()    
            lcd.writeFirstLine("TEMPERATURE")
            lcd.writeSecondLine("{:.2f} C".format(temperature_celsius))
            time.sleep(TIME)
            
            lcd.cleanFirstLine()        
            lcd.cleanSecondLine()    
            lcd.writeFirstLine("HUMIDITY")
            lcd.writeSecondLine("{:.2f} %".format(humidity))
            time.sleep(TIME)
            
            lcd.cleanFirstLine()        
            lcd.cleanSecondLine()
            lcd.writeFirstLine("AIR PRESSURE")
            lcd.writeSecondLine("{:.2f} hPa".format(pressure))
            time.sleep(TIME)
            
            lcd.cleanFirstLine()        
            lcd.cleanSecondLine()    
            lcd.writeFirstLine("CO2 Level")
            lcd.writeSecondLine("{:} ppm".format(co2Level))
            time.sleep(TIME)
            
            TICK +=1
        
    except KeyboardInterrupt:
        print('Program stopped')
        break
    
    except Exception as e:
        print('An unexpected error occurred:', str(e))
        break
