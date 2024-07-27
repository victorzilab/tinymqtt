<h1 align="center">Tiny MQTT</h1>

<p><strong>Tiny MQTT</strong> is a lightweight MQTT client built with PyQt5 and Paho MQTT. It provides a user-friendly graphical interface for connecting to, publishing to, and subscribing to MQTT topics. This tool is part of a larger project for a microcontrollers class, demonstrating MQTT usage by controlling GPIO with multiple ESP32 devices, each on a separate topic.</p>

<h2>Features</h2>
<ul>
    <li><strong>Connect and Disconnect:</strong> Easily connect to and disconnect from an MQTT broker.</li>
    <li><strong>Publish Messages:</strong> Send messages to specified topics.</li>
    <li><strong>Subscribe to Topics:</strong> Receive and view messages from subscribed topics.</li>
    <li><strong>Graphical Configuration:</strong> Configure broker settings through an intuitive graphical interface.</li>
    <li><strong>Configuration Management:</strong> Save and load MQTT settings from a JSON file.</li>
</ul>

<h2>Known Issues</h2>
<p><strong>Disconnect Issue:</strong> After disconnecting, the application requires a restart to reconnect. If you identify the cause, please contribute a fix through a pull request.</p>

<h2>Future Implementations</h2>
<ul>
    <li>Configurable topics and text for buttons</li>
    <li>Customizable user interface with icons</li>
    <li>Customizable subscription fields</li>
</ul>

<h2>Requirements</h2>
<ul>
    <li>Python 3.x</li>
    <li>PyQt5</li>
    <li>paho-mqtt</li>
</ul>
![image](https://github.com/user-attachments/assets/98e68e95-8fa0-4461-9ec0-62543c894216)

<p>Feel free to explore and contribute to the project! If you find any issues or have suggestions, please open an issue or submit a pull request.</p>
