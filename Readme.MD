# Esphome nevermore controller

> ⚠️⚠️ Work in progress, breaking changes are expected even if I try to avoid it ⚠️⚠️ 

## Why ?
- I like home assistant / esphome
- Less issues with badly crimped usb wires
- Code that is easy to understand

## Working / planned features
- [x] Automatic reconnect 
- [x] Fan speed reporting
- [x] Fan speed control
- [x] Sensors values reporting as nevermore fan
- [ ] Sensors values reporting as individual temps (for temp/voc plotting on graph)
- [ ] Servo control

## Config
```
[esphome_nevermore]
host: clementine-filter.home

# All the below options are optional, the shown values are the default values

password:
encryption_key:

keepalive: 2.0  # esphome has a default timeout ratio of 4.5, so after keep_alive*4.5 esp will be considered as disconnected 

# Optional overrides for esp home object name
override_id_fan_rpm: fan_rpm
override_id_fan_speed: fan_speed
override_id_intake_humidity : intake_humidity
override_id_intake_temperature: intake_temperature
override_id_intake_pressure: intake_pressure
override_id_intake_voc: intake_voc
override_id_exhaust_humidity: exhaust_humidity
override_id_exhaust_temperature: exhaust_temperature
override_id_exhaust_pressure: exhaust_pressure
override_id_exhaust_voc: exhaust_voc
```

## Not planned
- Led support
- Screen support

## Credits

* [igiannakas/Stealthmax-v2-ESPHome-Controller](https://github.com/igiannakas/Stealthmax-v2-ESPHome-Controller) Esphome controller config
* [SanaaHamel/nevermore-controller](https://github.com/SanaaHamel/nevermore-controller/) Original nevermore controller software
* [andrewmcgr/klipper_tmc_autotune](https://github.com/andrewmcgr/klipper_tmc_autotune/blob/main/install.sh) installation script (derived)
