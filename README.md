# Home Assistant SMA EV Charger Integration

Integration for controlling and monitoring Ennexos SMA EV Chargers in Home Assistant.

## Features

- Monitor charging status and power output
- Control charging start/stop
- View energy consumption data
- Real-time charger state updates
- Support for multiple charger devices

## Installation

1. Copy the `custom_components/sma_ev_charger` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Create Integration
4. Search for "SMA EV Charger" and follow the setup wizard

## Configuration

### Setup via UI

1. Navigate to Settings → Devices & Services
2. Click "Create Integration"
3. Select "SMA EV Charger"
4. Enter the following information:
   - **Hostname/IP Address**: IP address of your charger
   - **Username**: Login username for your Ennexos SMA charger
   - **Password**: Login password for your Ennexos SMA charger
   - **Port** (optional): Default is 80 for HTTP

### Manual YAML Configuration

Add to your `configuration.yaml`:

```yaml
sma_ev_charger:
  - host: 192.168.1.100
    username: your_username
    password: your_password
    port: 80
```

## Usage

After configuration, your charger will appear as a device in Home Assistant with the following entities:

- **Sensor**: Current charging status, power output, energy consumption
- **Switch**: Enable/disable charging
- **Number**: Set charging power limit

## Support

For issues and feature requests, please visit the GitHub repository.

## License

This integration is provided as-is under the MIT License.
