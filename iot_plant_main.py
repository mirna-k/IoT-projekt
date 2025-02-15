import json
import sys
import signal
import paho.mqtt.client as mqtt
import MySQLdb as mdb
import tornado.ioloop
import tornado.web
import tornado.websocket
from datetime import date, datetime, timedelta

# MQTT Configuration
MQTT_BROKER = "rpi2.local"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_TOPIC = "iot_plant/senzori/podaci"
MQTT_OUTPUT_TOPIC = "iot_plant/output"

# Database Settings
DB_HOST = 'localhost'
DB_USER = 'sensor_writer'
DB_PASS = 'password'
DB_NAME = 'iot_plant'


class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.client.loop_start()  # Run MQTT in the background

        self.web_notification = False
        self.next_watering_date = date.today()
        self.should_water = 0

    def on_connect(self, client, userdata, flags, rc):
        """Handles MQTT connection"""
        if rc == 0:
            print("Connected to MQTT broker.")
            client.subscribe(MQTT_TOPIC, qos=1)
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        """Handles incoming sensor data and saves it to the database"""
        try:
            con = mdb.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
            cursor = con.cursor()

            plant_id = 1
            data = json.loads(msg.payload.decode("utf-8"))
            temperatura = float(data["temperatura"])
            vlaga = float(data["vlaga"])
            is_watered = int(data["zalijevanje"])

            if datetime.now().minute % 5 == 0 and datetime.now().second >= 0 and datetime.now().second < 1:
            # Save sensor data to database
                sql = "INSERT INTO senzorski_podaci (biljka_id, temperatura, vlaga) VALUES (%s, %s, %s)"
                cursor.execute(sql, (plant_id, temperatura, vlaga))
                con.commit()
                print(f"Spremljeno: Temperatura={temperatura}, Vlaga={vlaga}")

            # Get last watering date
            sql = "SELECT datum_zalijevanja FROM zalijevanja ORDER BY datum_zalijevanja DESC LIMIT 1"
            cursor.execute(sql)
            result = cursor.fetchone()

            if result is None:
                self.next_watering_date = date.today()
                print("Nema prethodnog zapisa. Potrebno je danas zaliti biljku:", self.next_watering_date)
            else:
                last_watering_date = result[0]
                print("Posljednji zapis zalijevanja:", last_watering_date)
                self.next_watering_date = last_watering_date + timedelta(days=5)
                print(f"Datum sljedećeg zalijevanja: {self.next_watering_date}")

            # Save watering event
            if is_watered == 1:
                sql = "INSERT INTO zalijevanja (biljka_id) VALUES (%s)"
                cursor.execute(sql, (plant_id,))
                con.commit()
                print(f"Spremljeno: Zapisano vrijeme zalijevanja")

            # Decide whether to water the plant
            self.should_water = 1 if self.next_watering_date == date.today() or self.web_notification == True else 0
            client.publish(MQTT_OUTPUT_TOPIC, str(self.should_water))

        except ValueError:
            print(f"Invalid temperature value received: {msg.payload}")
        except mdb.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if cursor:
                cursor.close()
            if con:
                con.close()

    def send_command(self, command):
        """Send a command to the MQTT output topic"""
        self.client.publish(MQTT_OUTPUT_TOPIC, str(command))
        self.web_notification = True if command == '1' else False 


# Tornado Web Server
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket connection opened")

    def on_message(self, message):
        """Receive messages from WebSocket and send MQTT commands"""
        print(f"Received WebSocket message: {message}")
        if message == "1":
            mqtt_client.send_command("1")
        elif message == "0":
            mqtt_client.send_command("0")
        elif message == "status":
            self.send_sensor_data()
            self.send_watering_data()

    def send_sensor_data(self):
        """Fetch the latest sensor data from the database and send it via WebSocket"""
        try:
            con = mdb.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
            cursor = con.cursor()

            sql = "SELECT temperatura, vlaga, vrijeme_zapisa FROM senzorski_podaci ORDER BY vrijeme_zapisa DESC LIMIT 1"
            cursor.execute(sql)
            rows = cursor.fetchall()

            sensor_data = []
            for row in rows:
                sensor_data.append({
                    "temperatura": row[0],
                    "vlaga": row[1],
                    "timestamp": row[2].strftime("%d-%m-%Y  %H:%M:%S")
                })
            self.write_message({"type": "sensor_data", "data": sensor_data})

        except mdb.Error as e:
            print(f"Database error: {e}")
            self.write_message("Error retrieving sensor data.")
        finally:
            if cursor:
                cursor.close()
            if con:
                con.close()

    def send_watering_data(self):
        try:
            con = mdb.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
            cursor = con.cursor()

            sql = "SELECT datum_zalijevanja FROM zalijevanja ORDER BY datum_zalijevanja DESC LIMIT 1"
            cursor.execute(sql)
            row = cursor.fetchone()

            if row:
                last_watering = date.strptime(row[0], '%d-%m-%Y') 
                next_watering = mqtt_client.next_watering_date
                should_water = mqtt_client.should_water

                watering_data = {
                    "last_watering": last_watering.strftime('%d-%m-%Y'),
                    "next_watering": next_watering.strftime('%d-%m-%Y'),
                    "should_water": should_water
                }

                self.write_message({"type": "watering_data", "data": watering_data})
            else:
                print("No watering data found.")
                self.write_message({"type": "watering_data", "data": None})

        except mdb.Error as e:
            print(f"Database error: {e}")
            self.write_message("Error retrieving watering data.")
        finally:
            if cursor:
                cursor.close()
            if con:
                con.close()

    def on_close(self):
        print("WebSocket connection closed")


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws", WebSocketHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "./"}),
    ], debug=True)


def stop_tornado(signum, frame):
    """Stop Tornado and MQTT when SIGINT is received"""
    print("Stopping Tornado and MQTT...")
    tornado.ioloop.IOLoop.instance().add_callback_from_signal(lambda: tornado.ioloop.IOLoop.current().stop())
    mqtt_client.client.loop_stop()  # Stop MQTT loop
    sys.exit(0)


if __name__ == "__main__":
    # Initialize MQTT client
    mqtt_client = MQTTClient()

    # Start Tornado web server
    app = make_app()
    app.listen(8888)
    print("Tornado server running on http://localhost:8888")

    # Handle SIGINT for clean exit
    signal.signal(signal.SIGINT, stop_tornado)

    tornado.ioloop.IOLoop.current().start()
