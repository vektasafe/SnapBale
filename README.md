# SnapBale

Automated product photography for African informal traders.

---

## What It Does

A trader places an item on a conveyor belt. The unit photographs
it inside a fully enclosed, controlled lighting environment,
removes the background automatically, and transfers the images
to the trader's phone within 30 seconds. No photography skill
required. No editing required. No app installation required.

---

## Running in Simulation Mode

You do not need a Raspberry Pi to run the software.
Simulation mode runs the full stack on any laptop.

Install dependencies:

    pip install -r requirements.txt --break-system-packages

Run:

    python main.py

Open your browser at:

    http://localhost:5000

In simulation mode, use the "Simulate Item" button on the
session screen to trigger a fake item passing through the unit.

---

## Project Structure

    config.py           All configuration and simulation flag
    main.py             Entry point
    hardware/           Belt, LED, sensor, camera, flip board controllers
    session/            Session state machine and conveyor loop
    processing/         Image processing pipeline (rembg, Pillow, OpenCV)
    storage/            SQLite database and file system management
    server/             Flask web server, routes, SocketIO events
    server/templates/   Trader interface HTML (Swahili)
    tests/              Unit tests

---

## Switching to Raspberry Pi

1. Set SIMULATION_MODE = False in config.py
2. Uncomment Pi dependencies in requirements.txt
3. Install Pi dependencies:
       pip install -r requirements.txt --break-system-packages
4. Connect hardware per GPIO pin assignments in config.py
5. Run: python main.py

---

## Hardware

Full hardware design, bill of materials, and Nairobi sourcing
guide are in the Research-Ideas repository:

    https://github.com/vektasafe/Research-Ideas

---

## Author

James Kabingu
Vektasafe, Nairobi
github.com/vektasafe
